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
        self._threshold = 1.0

    async def _async_update_data(self):
        try:
            s = self.hass.states.get
            conf = self.entry.data

            def get_val(eid, is_kw=False):
                state = s(eid)
                if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, "unknown", "unavailable"):
                    try:
                        val = float(state.state)
                        # Omrekenen: kW naar Watt (x1000) en dan delen door 230V voor Ampère
                        return (val * 1000 / 230) if is_kw else val
                    except (ValueError, ZeroDivisionError):
                        return 0.0
                return 0.0

            # 1. Haal waarden op
            # Grid-sensoren zijn in kW (dus we zetten is_kw op True)
            g1 = get_val(conf["l1_grid"], is_kw=True)
            g2 = get_val(conf["l2_grid"], is_kw=True)
            g3 = get_val(conf["l3_grid"], is_kw=True)
            
            # Ratio-sensoren zijn al in Ampère
            r1 = get_val(conf["l1_ratio"], is_kw=False)
            r2 = get_val(conf["l2_ratio"], is_kw=False)
            r3 = get_val(conf["l3_ratio"], is_kw=False)

            # 2. Bereken het huisverbruik (Netto stroom - Lader stroom)
            # Dit werkt perfect met zonnestroom: als g1 negatief is, wordt h1 nog kleiner.
            h1, h2, h3 = (g1 - r1), (g2 - r2), (g3 - r3)
            
            # Pak de zwaarst belaste fase
            h_max = max(h1, h2, h3)
            
            # 3. Bereken het ideale laaddoel
            # 25A hoofdzekering - 2A marge = 23A beschikbaar.
            ideal_target = max(6.0, min(23.0 - h_max, 18.0))

            # 4. Status van de lader ophalen
            status_obj = s(conf["ratio_state_sensor"])
            status_val = status_obj.state if status_obj else "0"
            
            # 5. Modbus aansturing
            new_value_needed = False
            # We schrijven alleen als de lader echt in de laad-modus staat (Status 5)
            if status_val == "5":
                diff = abs(ideal_target - self._last_sent_target)
                # Schrijf als het doel lager wordt (veiligheid) of als het verschil groter is dan de drempel
                if ideal_target < self._last_sent_target or diff >= self._threshold:
                    self._last_sent_target = round(ideal_target, 0)
                    new_value_needed = True

            if new_value_needed:
                _LOGGER.info("Ratio: Schrijf %s A naar lader (Huisverbruik max: %s A)", self._last_sent_target, round(h_max, 1))
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
                    _LOGGER.error("Ratio: Fout bij schrijven naar Modbus: %s", e)

            # 6. Gegevens terugsturen naar de sensoren
            return {
                "target": self._last_sent_target,
                "status": status_val,
                "vrije_ruimte": round(23.0 - h_max, 1),
                "grid_l1": round(g1, 2), # Dit zijn nu Ampères voor je tabel!
                "grid_l2": round(g2, 2),
                "grid_l3": round(g3, 2),
                "h_max": round(h_max, 2)
            }

        except Exception as err:
            _LOGGER.error("Ratio: Kritieke fout in coordinator: %s", err)
            raise UpdateFailed(f"Update mislukt: {err}")