import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from .const import DOMAIN, MODBUS_HUB, SLAVE_ID, REGISTER_WRITE_AMPERAGE

_LOGGER = logging.getLogger(__name__)

class RatioCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass, _LOGGER, name="Ratio Smart Control",
            update_interval=timedelta(seconds=5), # Sneller voor veiligheid
        )
        self.entry = entry
        self._last_sent_target = 6.0

    async def _async_update_data(self):
        try:
            s = self.hass.states.get
            conf = self.entry.data

            def get_val(eid):
                state = s(eid) if eid else None
                if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                    return float(state.state)
                return 0.0

            # P1 Data (Netto verbruik op L1)
            p1_pro_l1 = get_val(conf.get("l1_grid_pro"))
            n1 = get_val(conf.get("l1_grid_con")) - p1_pro_l1
            
            # Huidig verbruik lader op L1 (voor je Mazda)
            r1 = get_val(conf.get("l1_ratio"))

            # Berekening ruimte op L1 (25A hoofdzekering - 2A veiligheidsmarge)
            # t1 = wat de lader maximaal mag trekken
            t1 = (23.0 - n1 + r1)

            # Begrens de lader tussen 6A (min) en 18A (jouw max voor de 20A groep)
            ideal = max(6.0, min(t1, 18.0))

            # Alleen sturen bij wijziging van >= 1A of als we omlaag moeten (veiligheid)
            if abs(ideal - self._last_sent_target) >= 1.0 or ideal < self._last_sent_target:
                self._last_sent_target = round(ideal, 1)
                
                # [span_3](start_span)FIX: Vermenigvuldig met 10 (0.1A schaal) volgens Modbus notities[span_3](end_span)
                modbus_value = int(self._last_sent_target * 10) 
                
                await self.hass.services.async_call(
                    "modbus", "write_register",
                    {
                        "hub": MODBUS_HUB, 
                        "unit": SLAVE_ID, 
                        "address": REGISTER_WRITE_AMPERAGE, 
                        "value": modbus_value
                    }
                )

            # Dashboard berekening: Hoeveel Watt zon gaat er in de auto?
            solar_amps = min(p1_pro_l1, r1) if r1 > 1.0 else 0.0
            solar_watt = round(solar_amps * 230, 0)

            return {
                "target": self._last_sent_target,
                "solar_power": solar_watt,
                "status": s(conf.get("ratio_state_sensor")).state if s(conf.get("ratio_state_sensor")) else "Unknown"
            }
        except Exception as err:
            raise UpdateFailed(f"Modbus fout: {err}")
