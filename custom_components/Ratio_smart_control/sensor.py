import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricCurrent
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    # We voegen hier de sensoren toe aan Home Assistant
    async_add_entities([
        RatioTargetSensor(entry.data),
        RatioStatusSensor(entry.data)
    ])

class RatioTargetSensor(SensorEntity):
    def __init__(self, data):
        self._config = data
        self._attr_name = "Ratio Smart Control Target"
        self._attr_unique_id = f"ratio_target_calculation" # Hardcoded ID voor zekerheid
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERES
        self._attr_icon = "mdi:target-variant"

    @property
    def native_value(self):
        try:
            # Haal de status van alle benodigde sensoren op
            s = self.hass.states.get
            
            # Grid (P1 Meter) waarden
            g1 = float(s(self._config["l1_grid"]).state or 0)
            g2 = float(s(self._config["l2_grid"]).state or 0)
            g3 = float(s(self._config["l3_grid"]).state or 0)
            
            # Lader (Modbus) waarden
            r1 = float(s(self._config["l1_ratio"]).state or 0)
            r2 = float(s(self._config["l2_ratio"]).state or 0)
            r3 = float(s(self._config["l3_ratio"]).state or 0)

            # Stap 1: Bereken wat de woning verbruikt (Totaal - Lader)
            # We doen dit per fase om de drukste fase te vinden
            house_l1 = max(g1 - r1, 0)
            house_l2 = max(g2 - r2, 0)
            house_l3 = max(g3 - r3, 0)
            
            # Stap 2: Pak de hoogste belasting van de woning
            highest_house_load = max(house_l1, house_l2, house_l3)
            
            # Stap 3: Wat is er over van de 25A?
            # Als huis 3A trekt, is er 22A over.
            available = 25.0 - highest_house_load
            
            # Stap 4: Limiteer dit op jouw maximum van 18A en minimum van 6A
            target = min(available, 18.0)
            
            _LOGGER.debug(f"Ratio Berekening: Huis={highest_house_load}A, Beschikbaar={available}A, Target={target}A")
            
            return max(6, int(target))
        except Exception as e:
            _LOGGER.error(f"Fout in Ratio berekening: {e}")
            return 6

class RatioStatusSensor(SensorEntity):
    def __init__(self, data):
        self._config = data
        self._attr_name = "Ratio Lader Status"
        self._attr_unique_id = f"ratio_status_text_display"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        try:
            state_val = self.hass.states.get(self._config["ratio_state_sensor"])
            if not state_val:
                return "Onbekend"
            
            # Jouw specifieke statussen
            mapping = {
                "0": "Stand-by (Vrij)",
                "1": "Stand-by (Verbonden)",
                "2": "Gepauzeerd / Ontgrendeld",
                "3": "Klaar (Kabel vergrendeld)",
                "5": "Aan het laden"
            }
            return mapping.get(str(state_val.state), f"Status {state_val.state}")
        except:
            return "Fout"
