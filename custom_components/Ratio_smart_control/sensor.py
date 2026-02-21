from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricCurrent
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RatioTargetSensor(entry.data), RatioStatusSensor(entry.data)])

class RatioTargetSensor(SensorEntity):
    def __init__(self, data):
        self._config = data
        self._attr_name = "Ratio Smart Control Target"
        self._attr_unique_id = f"{DOMAIN}_target_calc"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERES

    @property
    def native_value(self):
        try:
            h = self.hass.states.get
            g1, g2, g3 = float(h(self._config["l1_grid"]).state or 0), float(h(self._config["l2_grid"]).state or 0), float(h(self._config["l3_grid"]).state or 0)
            r1, r2, r3 = float(h(self._config["l1_ratio"]).state or 0), float(h(self._config["l2_ratio"]).state or 0), float(h(self._config["l3_ratio"]).state or 0)

            house_max = max(max(g1-r1, 0), max(g2-r2, 0), max(g3-r3, 0))
            available = self._config["max_main_fuse"] - house_max - self._config["safety_margin"]
            return max(6, int(min(available, self._config["max_charger_limit"])))
        except: return 6

class RatioStatusSensor(SensorEntity):
    def __init__(self, data):
        self._config = data
        self._attr_name = "Ratio Lader Status"
        self._attr_unique_id = f"{DOMAIN}_status_text"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        s = self.hass.states.get(self._config["ratio_state_sensor"])
        if not s: return "Onbekend"
        
        state_map = {
            "0": "Stand-by (Vrij)",
            "1": "Stand-by (Verbonden)",
            "2": "Gepauzeerd / Ontgrendeld",
            "3": "Klaar (Kabel vergrendeld)",
            "5": "Aan het laden"
        }
        return state_map.get(s.state, f"Status {s.state}")
