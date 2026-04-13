from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RatioTargetSensor(coordinator),
        RatioStatusSensor(coordinator),
        RatioVrijeRuimteSensor(coordinator)
    ])

class RatioTargetSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ratio Smart Control Target"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_target"
        self._attr_native_unit_of_measurement = "A"
        self._attr_icon = "mdi:target-variant"

    @property
    def native_value(self):
        return self.coordinator.data.get("target")

class RatioVrijeRuimteSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ratio Vrije Ruimte"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_vrije_ruimte"
        self._attr_native_unit_of_measurement = "A"
        self._attr_icon = "mdi:gauge"

    @property
    def native_value(self):
        return self.coordinator.data.get("vrije_ruimte")

class RatioStatusSensor(CoordinatorEntity, SensorEntity):
    _mapping = {"0": "Stand-by", "1": "Verbonden", "2": "Gepauzeerd", "3": "Klaar", "5": "Laden"}

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ratio Lader Status"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_status"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        # We pakken de status direct uit de coordinator data
        val = self.coordinator.data.get("status")
        # Als de coordinator er al een tekst van heeft gemaakt ("Laden"),
        # geven we die terug, anders checken we de mapping.
        if isinstance(val, str) and not val.isdigit():
            return val
        raw = str(val)
        return self._mapping.get(raw, f"Status {raw}")
