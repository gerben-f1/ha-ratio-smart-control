import asyncio
import logging
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from datetime import timedelta
from .const import DOMAIN, MODBUS_HUB, SLAVE_ID

_LOGGER = logging.getLogger(__name__)

# We kijken naar de nieuwe Target sensor en de Status tekst
TARGET_SENSOR_ID = "sensor.ratio_smart_control_target"
STATUS_SENSOR_ID = "sensor.ratio_lader_status"

async def async_setup_entry(hass, entry):
    """Setup van de Ratio Smart Control acties."""

    async def update_charger(val):
        """Stuurt het nieuwe Ampère-getal naar de lader."""
        try:
            _LOGGER.info(f"RATIO ACTIE: Modbus schrijven naar 16640 -> {val}A")
            await hass.services.async_call("modbus", "write_register", {
                "hub": MODBUS_HUB, 
                "slave": SLAVE_ID, 
                "address": 16640, 
                "value": int(val)
            })
        except Exception as e:
            _LOGGER.error(f"RATIO: Modbus fout bij schrijven: {e}")

    async def check_and_adjust(event_or_now=None):
        """Controleert of de lader bijgesteld moet worden."""
        t_state = hass.states.get(TARGET_SENSOR_ID)
        s_state = hass.states.get(STATUS_SENSOR_ID)
        
        # 1. Basis check: is de sensor beschikbaar?
        if not t_state or t_state.state in ["unknown", "unavailable"]:
            return

        # 2. Status check: Alleen sturen als de status 'Laden' is
        # Dit voorkomt onnodig geklapper van relais als er geen auto is
        if s_state and s_state.state == "Laden":
            try:
                target_val = int(float(t_state.state))
                await update_charger(target_val)
            except Exception as e:
                _LOGGER.error(f"RATIO: Fout bij converteren target waarde: {e}")

    # TRIGGER 1: Direct reageren als de Target sensor verandert (elke seconde mogelijk)
    entry.async_on_unload(
        async_track_state_change_event(hass, [TARGET_SENSOR_ID], check_and_adjust)
    )
    
    # TRIGGER 2: Elke 3 seconden een extra check (vangnet)
    entry.async_on_unload(
        async_track_time_interval(hass, check_and_adjust, timedelta(seconds=3))
    )
    
    # Start de sensoren
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass, entry):
    """Unload de integratie."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])