import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricCurrent
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Instellingen voor de berekening
MAIN_FUSE = 25.0
SAFETY_MARGIN = 2.0
MAX_CHARGER_LIMIT = 18.0

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
            # Haal Grid (P1) waarden op
            g1 = float(s(self._config["l1_grid"]).state or 0)
            g2 = float(s(self._config["l2_grid"]).state or 0)
            g3 = float(s(self._config["l3_grid"]).state or 0)
            
            # Haal huidige lader verbruik op
            r1 = float(s(self._config["l1_ratio"]).state or 0)
            r2 = float(s(self._config["l2_ratio"]).state or 0)
            r3 = float(s(self._config["l3_ratio"]).state or 0)

            # Bereken verbruik van het huis (Grid minus wat de lader nu pakt)
            house_l1 = max(g1 - r1, 0)
            house_l2 = max(g2 - r2, 0)
            house_l3 = max(g3 - r3, 0)
            house_max = max(house_l1, house_l2, house_l3)
            
            # Berekening met expliciete marge:
            # Beschikbaar = 25.0 - Huisverbruik - 2.0
            available = MAIN_FUSE - house_max - SAFETY_MARGIN
            
            # We gebruiken 0.99 marge voor de 'int' afronding om op 18A uit te komen
            target = min(available, MAX_CHARGER_LIMIT + 0.99)
            
            # Altijd minimaal 6A (Modbus standaard)
            return max(6, int(target))
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
            if not state_val: return "Onbekend"
            mapping = {"0":"Stand-by","1":"Verbonden","2":"Gepauzeerd","3":"Klaar","5":"Laden"}
            return mapping.get(str(state_val.state), f"Status {state_val.state}")
        except:
            return "Fout"
