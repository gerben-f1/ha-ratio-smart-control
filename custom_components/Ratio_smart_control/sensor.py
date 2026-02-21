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
            
            # 1. Haal de hoogste stroomwaarde op die NU door de hoofdzekering gaat (P1 meter)
            g1 = float(h(self._config["l1_grid"]).state or 0)
            g2 = float(h(self._config["l2_grid"]).state or 0)
            g3 = float(h(self._config["l3_grid"]).state or 0)
            current_grid_max = max(g1, g2, g3)
            
            # 2. Haal op wat de lader op dit moment daadwerkelijk verbruikt (Modbus)
            # We kijken naar de hoogste waarde van de lader om veilig te blijven
            r1 = float(h(self._config["l1_ratio"]).state or 0)
            r2 = float(h(self._config["l2_ratio"]).state or 0)
            r3 = float(h(self._config["l3_ratio"]).state or 0)
            current_charger_max = max(r1, r2, r3)

            # 3. Bereken de vrije ruimte op de zekering
            # Ruimte = Hoofdzekering (25) - Huidige belasting Grid - Veiligheidsmarge (2)
            spare_capacity = self._config["max_main_fuse"] - current_grid_max - self._config["safety_margin"]
            
            # 4. Nieuwe Target = Wat de lader nu al doet + de vrije ruimte die we nog hebben
            # Voorbeeld: Lader doet 14A, we hebben 5A over op P1 -> Target wordt 19A.
            calculated_target = current_charger_max + spare_capacity
            
            # 5. Pas de harde grenzen toe
            # Nooit hoger dan de Max Charger Limit (bijv. 18A) en nooit lager dan 6A
            final_target = min(calculated_target, self._config["max_charger_limit"])
            final_target = max(6, int(final_target))

            _LOGGER.debug(f"Ratio Calc: GridMax={current_grid_max}, ChargerMax={current_charger_max}, Spare={spare_capacity}, Target={final_target}")
            
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
        
        # Statussen zoals doorgegeven door gebruiker
        state_map = {
            "0": "Stand-by (Vrij)",
            "1": "Stand-by (Verbonden)",
            "2": "Gepauzeerd / Ontgrendeld",
            "3": "Klaar (Kabel vergrendeld)",
            "5": "Aan het laden"
        }
        return state_map.get(s.state, f"Status {s.state}")
