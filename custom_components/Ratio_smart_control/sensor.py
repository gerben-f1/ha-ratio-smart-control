from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfElectricCurrent
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RatioTargetSensor(coordinator, entry), RatioStatusSensor(coordinator, entry),
        RatioVrijeRuimteSensor(coordinator, entry), RatioGridAmpereSensor(coordinator, entry, "l1", "Grid Ampere L1"),
        RatioGridAmpereSensor(coordinator, entry, "l2", "Grid Ampere L2"), RatioGridAmpereSensor(coordinator, entry, "l3", "Grid Ampere L3")
    ])

class RatioBaseEntity(CoordinatorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._slave_id = entry.data.get("slave_id", 127)
        self._attr_device_info = {"identifiers": {(DOMAIN, f"ratio_charger_{self.entry.entry_id}_{self._slave_id}")}, "name": entry.title, "manufacturer": "Ratio Electric", "model": "Smart Control Hub"}

class RatioTargetSensor(RatioBaseEntity, SensorEntity):
    _attr_state_class, _attr_device_class = SensorStateClass.MEASUREMENT, "current"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name, self._attr_unique_id = "Smart Control Target", f"{entry.entry_id}_target"
        self._attr_native_unit_of_measurement, self._attr_icon = UnitOfElectricCurrent.AMPERE, "mdi:target-variant"
    @property
    def native_value(self): return self.coordinator.data.get("target")

class RatioVrijeRuimteSensor(RatioBaseEntity, SensorEntity):
    _attr_state_class, _attr_device_class = SensorStateClass.MEASUREMENT, "current"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name, self._attr_unique_id = "Vrije Ruimte", f"{entry.entry_id}_vrije_ruimte"
        self._attr_native_unit_of_measurement, self._attr_icon = UnitOfElectricCurrent.AMPERE, "mdi:gauge"
    @property
    def native_value(self): return self.coordinator.data.get("vrije_ruimte")

class RatioGridAmpereSensor(RatioBaseEntity, SensorEntity):
    _attr_state_class, _attr_device_class = SensorStateClass.MEASUREMENT, "current"
    def __init__(self, coordinator, entry, phase, name):
        super().__init__(coordinator, entry)
        self._phase = phase
        self._attr_name, self._attr_unique_id = name, f"{entry.entry_id}_grid_ampere_{phase}"
        self._attr_native_unit_of_measurement, self._attr_icon = UnitOfElectricCurrent.AMPERE, "mdi:flash"
    @property
    def native_value(self): return self.coordinator.data.get(f"grid_{self._phase}")

class RatioStatusSensor(RatioBaseEntity, SensorEntity):
    _mapping = {"0": "Stand-by", "1": "Verbonden", "2": "Gepauzeerd", "3": "Klaar", "5": "Laden"}
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name, self._attr_unique_id, self._attr_icon = "Lader Status", f"{entry.entry_id}_status", "mdi:ev-station"
    @property
    def native_value(self):
        raw = str(self.coordinator.data.get("status", "0")).split(".")[0]
        return self._mapping.get(raw, f"Status {raw}")
