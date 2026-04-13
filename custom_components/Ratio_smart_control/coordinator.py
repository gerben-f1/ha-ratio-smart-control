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
                        # Omrekenen: kW naar Watt, dan delen door 230V voor Ampère
                        return (val * 1000 / 230) if is_kw else val
                    except (ValueError, ZeroDivisionError):
                        return 0.0
                return 0.0

            # 1. Haal waarden op (Grid is kW -> omzetten naar A, Ratio is al A)
            g1 = get_val(conf["l1_grid"], is_kw=True)
            g2 = get_val(conf["l2_grid"], is_kw=True)
            g3 = get_val(conf["l3_grid"], is_kw=True)
            
            r1 = get_val(conf["l1_ratio"], is_kw=False)
            r2 = get_val(conf["l2_ratio"], is_kw=False)
            r3 = get_val(conf["l3_ratio"], is_kw=False)

            # 2. Bereken huisverbruik in Ampère (P1_netto - Lader)
            # Dit werkt ook bij zonnestroom (als g negatief is, wordt h nog kleiner)
            h1, h2, h3 = (g1 - r1), (g2 - r2), (g3 - r3)
            h_max = max(h1, h2, h3)
            
            # 3. Bepaal Target (Max 23A beschikbaar op zekering)
            ideal_target = max(6.0, min(23.0 - h_max, 18.0))

            # 4. Status check
            status_obj = s(conf["ratio_state_sensor"])
            status_val = status_obj.state if status_obj else "0"
            
            # 5. Modbus actie
            new_value_needed = False
            if status_val == "5": # Alleen tijdens laden
                diff = abs(ideal_target - self._last_sent_target)
                if ideal_target < self._last_sent_target or diff >= self._threshold:
                    self._last_sent_target = round(ideal_target, 0)
                    new_value_needed = True

            if new_value_needed:
                await self.hass.services.async_call(
                    "modbus", "write_register",
                    {
                        "hub": MODBUS_HUB,
                        "unit": SLAVE_ID,
                        "address": REGISTER_WRITE_AMPERAGE,
                        "value": int(self._last_sent_target)
                    },
                    blocking=True
                )

            return {
                "target": self._last_sent_target,
                "status": status_val,
                "vrije_ruimte": round(23.0 - h_max, 1),
                "grid_l1_amps": round(g1, 1),
                "grid_l2_amps": round(g2, 1),
                "grid_l3_amps": round(g3, 1)
            }

        except Exception as err:
            _LOGGER.error("Ratio Error: %s", err)
            raise UpdateFailed(f"Fout: {err}")
