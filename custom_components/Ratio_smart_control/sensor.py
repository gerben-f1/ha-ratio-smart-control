from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfElectricCurrent
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup de sensoren op basis van de config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # We voegen de basis sensoren toe en de drie fase-specifieke sensoren
    async_add_entities([
        RatioTargetSensor(coordinator),
        RatioStatusSensor(coordinator),
        RatioVrijeRuimteSensor(coordinator),
        RatioGridSensor(coordinator, "l1"),
        RatioGridSensor(coordinator, "l2"),
        RatioGridSensor(coordinator, "l3")
    ])

class RatioGridSensor(CoordinatorEntity, SensorEntity):
    """Sensor die de netto stroom (in Ampère) per fase weergeeft."""
    def __init__(self, coordinator, fase):
        super().__init__(coordinator)
        self._fase = fase
        self._attr_name = f"Ratio Grid Ampere {fase.upper()}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_grid_amp_{fase}"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_device_class = "current"
        self._attr_icon = "mdi:transmission-tower"

    @property
    def native_value(self):
        # Haalt de door de coordinator omgerekende waarde (kW -> A) op
        return self.coordinator.data.get(f"grid_{self._fase}")

class RatioTargetSensor(CoordinatorEntity, SensorEntity):
    """Sensor die laat zien welke stroomsterkte de integratie naar de lader stuurt."""
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ratio Smart Control Target"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_target"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_device_class = "current"
        self._attr_icon = "mdi:target-variant"

    @property
    def native_value(self):
        return self.coordinator.data.get("target")

class RatioVrijeRuimteSensor(CoordinatorEntity, SensorEntity):
    """Sensor die laat zien hoeveel Ampère er nog over is op de zwaarst belaste fase."""
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ratio Vrije Ruimte"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_vrije_ruimte"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_device_class = "current"
        self._attr_icon = "mdi:gauge"

    @property
    def native_value(self):
        return self.coordinator.data.get("vrije_ruimte")

class RatioStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor die de leesbare status van de lader weergeeft."""
    _mapping = {"0": "Stand-by", "1": "Verbonden", "2": "Gepauzeerd", "3": "Klaar", "5": "Laden"}

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ratio Lader Status"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_status"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        raw = str(self.coordinator.data.get("status"))
        return self._mapping.get(raw, f"Status {raw}")