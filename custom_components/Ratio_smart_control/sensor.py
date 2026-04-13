import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RatioTargetSensor(coordinator),
        RatioStatusSensor(coordinator),
        RatioSolarPowerSensor(coordinator)
    ])

class RatioTargetSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Ratio Target Amperage"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_target"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_icon = "mdi:target-variant"

    @property
    def native_value(self):
        return self.coordinator.data.get("target")

class RatioSolarPowerSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Mazda Solar Power"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_solar"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = "power"
        self._attr_icon = "mdi:solar-power"

    @property
    def native_value(self):
        return self.coordinator.data.get("solar_power")

class RatioStatusSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Ratio Status"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_status"

    @property
    def native_value(self):
        status_raw = self.coordinator.data.get("status")
        mapping = {"0": "Stand-by", "1": "Verbonden", "2": "Pauze", "3": "Klaar", "5": "Laden"}
        return mapping.get(str(status_raw), f"Status {status_raw}")
