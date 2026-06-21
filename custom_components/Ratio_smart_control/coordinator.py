import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from .const import DOMAIN, REGISTER_WRITE_AMPERAGE, DEFAULT_FUSE_LIMIT, DEFAULT_MAX_CHARGE_CURRENT

_LOGGER = logging.getLogger(__name__)

class RatioCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.entry = entry
        self.hub = entry.data.get("hub", "modbus_ratio")
        self.slave_id = int(entry.data.get("slave_id", 127))
        super().__init__(hass, _LOGGER, name="Ratio Coordinator", update_interval=timedelta(seconds=3))
        self._last_sent_target = 6.0
        self._threshold = 0.0 

    async def _async_update_data(self):
        try:
            s = self.hass.states.get
            conf = self.entry.data
            max_limit = float(conf.get("main_fuse_limit", DEFAULT_FUSE_LIMIT))
            LADER_LIMIET = float(conf.get("max_charge_current", DEFAULT_MAX_CHARGE_CURRENT))  # Instelbaar via UI

            def get_val(eid):
                state = s(eid)
                if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, "unknown", "unavailable"):
                    try: return float(state.state)
                    except ValueError: return 0.0
                return 0.0

            def get_netto(imp, exp, v):
                return ((get_val(imp) - get_val(exp)) * 1000) / max(v, 230.0)

            v1, v2, v3 = [max(get_val(f"sensor.electricity_meter_spanning_fase_l{i}"), 230.0) for i in (1,2,3)]
            g1, g2, g3 = [get_netto(conf.get(f"l{i}_grid"), conf.get(f"l{i}_export"), v) for i, v in zip((1,2,3), (v1,v2,v3))]
            r1, r2, r3 = [get_val(conf.get(f"l{i}_ratio")) for i in (1,2,3)]
            is_charging = s(conf.get("ratio_state_sensor")).state in ("5", 5.0, "5.0")
            
            # Schakelaar voor Solar Only
            solar_mode_state = s("input_boolean.laden_op_alleen_zon")
            is_solar_only = solar_mode_state and solar_mode_state.state == "on"

            # Load balancing
            other_l1, other_l2, other_l3, other_chargers_charging = 0.0, 0.0, 0.0, 0
            for entry_id, coord in self.hass.data[DOMAIN].items():
                if entry_id != self.entry.entry_id:
                    o_conf = coord.entry.data
                    if s(o_conf.get("ratio_state_sensor")).state in ("5", 5.0, "5.0"):
                        other_chargers_charging += 1
                        other_l1 += get_val(o_conf.get("l1_ratio"))
                        other_l2 += get_val(o_conf.get("l2_ratio"))
                        other_l3 += get_val(o_conf.get("l3_ratio"))

            # Bereken het "huis-verbruik" (jouw stabiele methode)
            h_max = max(g1 - r1 - other_l1, g2 - r2 - other_l2, g3 - r3 - other_l3)
            # Wat is er over op de hoofdzekering?
            total_available = max(0.0, min(max_limit, max_limit - h_max))

            if is_solar_only:
                # Solar Only: 6A basis + Netto Export (die negatief is, dus we flippen het teken)
                # We cappen dit op de beschikbare ruimte op de zekering EN op de 18A laderlimiet
                overschot = max(0.0, -(g1 + g2 + g3))
                ideal_target = max(6.0, min(6.0 + overschot, total_available, LADER_LIMIET)) if is_charging else 6.0
            else:
                # Normaal: Verdeel de beschikbare ruimte over het aantal laders
                ideal_target = max(6.0, min(total_available / (other_chargers_charging + 1), LADER_LIMIET)) if is_charging else 6.0

            if is_charging and (ideal_target < self._last_sent_target or abs(ideal_target - self._last_sent_target) >= self._threshold):
                self._last_sent_target = round(ideal_target, 1)
                await self.hass.services.async_call("modbus", "write_register", {
                    "hub": self.hub, "unit": self.slave_id, "address": REGISTER_WRITE_AMPERAGE, "value": int(self._last_sent_target)
                }, blocking=True)

            return {"target": self._last_sent_target, "status": s(conf.get("ratio_state_sensor")).state, 
                    "vrije_ruimte": round(max_limit - max(g1, g2, g3), 1), "grid_l1": round(g1, 1), "grid_l2": round(g2, 1), "grid_l3": round(g3, 1)}
        except Exception as err:
            raise UpdateFailed(f"Update mislukt: {err}")
