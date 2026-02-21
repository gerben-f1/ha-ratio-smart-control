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
        self._attr_unique_id = f"{DOMAIN}_target_calc"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERES
        self._attr_icon = "mdi:target-variant"

    @property
    def native_value(self):
        try:
            h = self.hass.states.get
            
            # 1. Haal P1 Grid data op (Totaalverbruik woning + lader)
            g1 = float(h(self._config["l1_grid"]).state or 0)
            g2 = float(h(self._config["l2_grid"]).state or 0)
            g3 = float(h(self._config["l3_grid"]).state or 0)
            
            # 2. Haal Lader data op (Wat de lader nu verbruikt)
            r1 = float(h(self._config["l1_ratio"]).state or 0)
            r2 = float(h(self._config["l2_ratio"]).state or 0)
            r3 = float(h(self._config["l3_ratio"]).state or 0)

            # 3. Bereken puur huisverbruik per fase (Grid minus Lader)
            # Dit is de belasting van apparaten zoals oven, wasmachine, etc.
            house_l1 = max(g1 - r1, 0)
            house_l2 = max(g2 - r2, 0)
            house_l3 = max(g3 - r3, 0)
            
            # 4. Pak de drukste fase in huis
            busiest_house_phase = max(house_l1, house_l2, house_l3)
            
            # 5. Bereken beschikbare ruimte op de 25A hoofdzekering
            # Geen marge meer: 25A - huisverbruik
            available_for_charger = 25.0 - busiest_house_phase
            
            # 6. Begrenzen op jouw harde limiet van 18A (en minimaal 6A)
            final_target = min(available_for_charger, 18.0)
            final_target = max(6, int(final_target))

            _LOGGER.debug(f"Ratio Calc: House Max={busiest_house_phase}, Available={available_for_charger}, Target={final_target}")
            
            return final_target

        except Exception as e:
            _LOGGER.error(f"Error calculating Ratio Target: {e}")
            return 6

class RatioStatusSensor(SensorEntity):
    def __init__(self, data):
        self._config = data
        self._attr_name = "Ratio Lader Status"
        self._attr_unique_id = f"{DOMAIN}_status_text"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        s = self.hass.states.get(self._config["ratio_state_sensor"])
        if not s:
            return "Onbekend"
        
        state_map = {
            "0": "Stand-by (Vrij)",
            "1": "Stand-by (Verbonden)",
            "2": "Gepauzeerd / Ontgrendeld",
            "3": "Klaar (Kabel vergrendeld)",
            "5": "Aan het laden"
        }
        return state_map.get(s.state, f"Status {s.state}")
