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

            def get_val(eid):
                state = s(eid)
                if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, "unknown", "unavailable"):
                    try:
                        return float(state.state)
                    except ValueError:
                        return 0.0
                return 0.0

            # 1. Haal huidige Ampère waarden op
            g1, g2, g3 = get_val(conf["l1_grid"]), get_val(conf["l2_grid"]), get_val(conf["l3_grid"])
            r1, r2, r3 = get_val(conf["l1_ratio"]), get_val(conf["l2_ratio"]), get_val(conf["l3_ratio"])

            # 2. ZONNESTROOM LOGICA:
            # We berekenen het huisverbruik: P1-waarde minus wat de lader nu verbruikt.
            # Als P1 negatief is (zon), wordt huis_verbruik ook negatief, wat de ruimte vergroot.
            h1, h2, h3 = (g1 - r1), (g2 - r2), (g3 - r3)
            
            # We kijken welke fase het drukst is (hoogste huisverbruik)
            h_max = max(h1, h2, h3)
            
            # Bereken ideaal doel (Hoofdzekering 25A - 2A marge = 23A)
            # Voorbeeld: h_max is -10A (zon), dan wordt het: 23 - (-10) = 33A -> begrensd op 18A.
            ideal_target = max(6.0, min(23.0 - h_max, 18.0))

            # 3. Status check (Register 16396)
            status_obj = s(conf["ratio_state_sensor"])
            status_val = status_obj.state if status_obj else "0"
            
            # 4. Modbus sturing (Alleen als de lader op status 5 'Laden' staat)
            new_value_needed = False
            diff = abs(ideal_target - self._last_sent_target)

            if status_val == "5":
                if ideal_target < self._last_sent_target or diff >= self._threshold:
                    self._last_sent_target = round(ideal_target, 0) # Modbus wil gehele getallen
                    new_value_needed = True

            if new_value_needed:
                _LOGGER.info("Ratio: Schrijf %s A naar Modbus voor zonnestroom optimalisatie", self._last_sent_target)
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
                    _LOGGER.error("Ratio: Modbus schrijf fout: %s", e)

            return {
                "target": self._last_sent_target,
                "status": "Laden" if status_val == "5" else "Stand-by/Gereed",
                "h_max": round(h_max, 2),
                "vrije_ruimte": round(23.0 - h_max, 2)
            }

        except Exception as err:
            _LOGGER.error("Ratio: Kritieke fout in coordinator: %s", err)
            raise UpdateFailed(f"Fout in Ratio berekening: {err}")
