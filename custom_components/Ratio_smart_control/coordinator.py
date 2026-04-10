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
            update_interval=timedelta(seconds=10),
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

            # Bereken Netto per fase: (Verbruik - Productie)
            n1 = get_val(conf.get("l1_grid_con")) - get_val(conf.get("l1_grid_pro"))
            n2 = get_val(conf.get("l2_grid_con")) - get_val(conf.get("l2_grid_pro"))
            n3 = get_val(conf.get("l3_grid_con")) - get_val(conf.get("l3_grid_pro"))

            # Huidige lader verbruik
            r1, r2, r3 = get_val(conf.get("l1_ratio")), get_val(conf.get("l2_ratio")), get_val(conf.get("l3_ratio"))

            # Ruimte = (Hoofdzekering 25A - 2A marge) - Netto P1 + Huidig Lader
            t1, t2, t3 = (23.0 - n1 + r1), (23.0 - n2 + r2), (23.0 - n3 + r3)

            ideal = max(6.0, min(min(t1, t2, t3), 18.0))

            if abs(ideal - self._last_sent_target) >= 1.0 or ideal < self._last_sent_target:
                self._last_sent_target = round(ideal, 1)
                await self.hass.services.async_call(
                    "modbus", "write_register",
                    {"hub": MODBUS_HUB, "unit": SLAVE_ID, "address": REGISTER_WRITE_AMPERAGE, "value": int(self._last_sent_target)}
                )

            return {"target": self._last_sent_target, "status": s(conf.get("ratio_state_sensor")).state if s(conf.get("ratio_state_sensor")) else "Unknown"}
        except Exception as err:
            raise UpdateFailed(f"Fout: {err}")
