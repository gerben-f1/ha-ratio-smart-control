import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from .const import DOMAIN, MODBUS_HUB, SLAVE_ID, REGISTER_WRITE_AMPERAGE

_LOGGER = logging.getLogger(__name__)

class RatioCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name="Ratio Smart Control",
            update_interval=timedelta(seconds=10),
        )
        self.entry = entry
        self._last_sent_target = 6.0
        self._threshold = 0.5 # Iets gevoeliger gezet voor strakkere regeling

    async def _async_update_data(self):
        try:
            s = self.hass.states.get
            conf = self.entry.data

            def get_val(eid):
                state = s(eid)
                if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, "unknown", "unavailable"):
                    try:
                        return float(state.state)
                    except ValueError:
                        return 0.0
                return 0.0

            # 1. Haal de ECHTE spanning per fase op
            v1 = get_val("sensor.electricity_meter_spanning_fase_l1")
            v2 = get_val("sensor.electricity_meter_spanning_fase_l2")
            v3 = get_val("sensor.electricity_meter_spanning_fase_l3")
            
            # Veiligheid: Gebruik 230V als de sensor faalt
            v1 = v1 if v1 > 100 else 230.0
            v2 = v2 if v2 > 100 else 230.0
            v3 = v3 if v3 > 100 else 230.0

            # 2. Haal grid-vermogen op (kW) en reken om naar Ampère met de actuele spanning
            g1 = (get_val(conf["l1_grid"]) * 1000) / v1
            g2 = (get_val(conf["l2_grid"]) * 1000) / v2
            g3 = (get_val(conf["l3_grid"]) * 1000) / v3
            
            # 3. Ratio-stroom (is al Ampère)
            r1 = get_val(conf["l1_ratio"])
            r2 = get_val(conf["l2_ratio"])
            r3 = get_val(conf["l3_ratio"])

            # 4. Bereken het huisverbruik
            h1, h2, h3 = (g1 - r1), (g2 - r2), (g3 - r3)
            h_max = max(h1, h2, h3)
            
            # 5. Het Target bepalen (met +0.7A push om de 18A echt te raken)
            # De min(..., 18.0) zorgt dat we NOOIT boven je 16A groep-limiet van de lader gaan
            ideal_target = max(6.0, min(23.0 - h_max + 0.7, 18.0))

            # 6. Status van de lader ophalen
            status_obj = s(conf["ratio_state_sensor"])
            status_val = status_obj.state if status_obj else "0"
            
            # 7. Modbus aansturing
            new_value_needed = False
            if status_val == "5": # Status 'Laden'
                diff = abs(ideal_target - self._last_sent_target)
                
                # Schrijf als het doel lager wordt of als het verschil groot genoeg is
                if ideal_target < self._last_sent_target or diff >= self._threshold:
                    # We ronden af op 1 decimaal voor nauwkeurigheid
                    self._last_sent_target = round(ideal_target, 1)
                    new_value_needed = True

            if new_value_needed:
                _LOGGER.info("Ratio: Schakel naar %s A (V1: %s V, L1 Net: %s A)", self._last_sent_target, round(v1,1), round(g1,1))
                try:
                    await self.hass.services.async_call(
                        "modbus",
                        "write_register",
                        {
                            "hub": MODBUS_HUB,
                            "unit": SLAVE_ID,
                            "address": REGISTER_WRITE_AMPERAGE,
                            "value": int(self._last_sent_target)
                        },
                        blocking=True
                    )
                except Exception as e:
                    _LOGGER.error("Ratio: Modbus fout: %s", e)

            # 8. Gegevens terugsturen naar de sensoren
            # We berekenen de 'echte' vrije ruimte op de 25A hoofdzekering (met 2A marge)
            grid_max = max(g1, g2, g3)
            return {
                "target": self._last_sent_target,
                "status": status_val,
                "vrije_ruimte": round(23.0 - grid_max, 1),
                "grid_l1": round(g1, 2),
                "grid_l2": round(g2, 2),
                "grid_l3": round(g3, 2),
                "h_max": round(h_max, 2)
            }

        except Exception as err:
            _LOGGER.error("Ratio: Kritieke fout: %s", err)
            raise UpdateFailed(f"Update mislukt: {err}")
