import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricCurrent
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        RatioTargetSensor(entry.data),
        RatioStatusSensor(entry.data)
    ])

class RatioTargetSensor(SensorEntity):
    def __init__(self, data):
        self._config = data
        self._attr_name = "Ratio Smart Control Target"
        self.entity_id = "sensor.ratio_smart_control_target"
        self._attr_unique_id = "ratio_target_calculation_fixed"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_icon = "mdi:target-variant"

    @property
    def native_value(self):
        try:
            s = self.hass.states.get
            
            # 1. Haal Grid (P1) waarden op per fase
            g1 = float(s(self._config["l1_grid"]).state or 0)
            g2 = float(s(self._config["l2_grid"]).state or 0)
            g3 = float(s(self._config["l3_grid"]).state or 0)
            
            # 2. Haal Lader verbruik op per fase
            r1 = float(s(self._config["l1_ratio"]).state or 0)
            r2 = float(s(self._config["l2_ratio"]).state or 0)
            r3 = float(s(self._config["l3_ratio"]).state or 0)

            # 3. Bereken huisverbruik per fase (Grid - Lader)
            h1 = max(g1 - r1, 0)
            h2 = max(g2 - r2, 0)
            h3 = max(g3 - r3, 0)
            
            # 4. Bepaal de zwaarst belaste fase in huis
            house_max = max(h1, h2, h3)
            
            # 5. Bereken beschikbare ruimte op basis van 23A (25A zekering - 2A marge)
            available = 23.0 - house_max
            
            # 6. Target begrenzen tussen 6A en 18A
            # Zodra house_max > 5A (23 - 5 = 18), zakt de target onder de 18
            target = min(available, 18.0)
            
            final_value = max(6, int(target))

            return final_value

        except Exception as e:
            _LOGGER.error(f"Ratio Fout in berekening: {e}")
            return 6

class RatioStatusSensor(SensorEntity):
    def __init__(self, data):
        self._config = data
        self._attr_name = "Ratio Lader Status"
        self.entity_id = "sensor.ratio_lader_status"
        self._attr_unique_id = "ratio_status_text_fixed"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        try:
            state_val = self.hass.states.get(self._config["ratio_state_sensor"])
            if not state_val: 
                return "Onbekend"
            
            # Deze tekst "Laden" wordt door __init__.py gebruikt om te mogen schrijven
            mapping = {
                "0": "Stand-by",
                "1": "Verbonden",
                "2": "Gepauzeerd",
                "3": "Klaar / Finished",
                "5": "Laden"
            }
            return mapping.get(str(state_val.state), f"Status {state_val.state}")
        except:
            return "Fout"