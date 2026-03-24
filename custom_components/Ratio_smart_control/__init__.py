import asyncio
import logging
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from datetime import timedelta
from .const import DOMAIN, MODBUS_HUB, SLAVE_ID, REGISTER_WRITE_AMPERAGE

_LOGGER = logging.getLogger(__name__)

TARGET_SENSOR_ID = "sensor.ratio_smart_control_target"
STATUS_SENSOR_ID = "sensor.ratio_lader_status"

async def async_setup_entry(hass, entry):
    async def update_charger(val):
        """Schrijft de waarde naar de lader."""
        try:
            _LOGGER.info(f"RATIO ACTIE: Schrijven naar {REGISTER_WRITE_AMPERAGE} -> {val}A")
            await hass.services.async_call("modbus", "write_register", {
                "hub": MODBUS_HUB, 
                "slave": SLAVE_ID, 
                "address": REGISTER_WRITE_AMPERAGE, 
                "value": int(val)
            })
        except Exception as e:
            _LOGGER.error(f"RATIO: Modbus fout bij schrijven: {e}")

    async def check_and_adjust(event_or_now=None):
        t_state = hass.states.get(TARGET_SENSOR_ID)
        s_state = hass.states.get(STATUS_SENSOR_ID)
        
        if not t_state or t_state.state in ["unknown", "unavailable"]:
            return

        # Tijdens het laden de berekening volgen
        if s_state and s_state.state == "Laden":
            target_val = int(float(t_state.state))
            await update_charger(target_val)

    async def on_status_change(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        
        if not old_state or not new_state:
            return

        # Reset naar 6A als de status niet meer 'Laden' is
        if old_state.state == "Laden" and new_state.state != "Laden":
            _LOGGER.info("RATIO: Status veranderd van Laden naar iets anders. Reset naar 6A.")
            await update_charger(6)

    # Triggers voor actie
    entry.async_on_unload(async_track_state_change_event(hass, [TARGET_SENSOR_ID], check_and_adjust))
    entry.async_on_unload(async_track_state_change_event(hass, [STATUS_SENSOR_ID], on_status_change))
    entry.async_on_unload(async_track_time_interval(hass, check_and_adjust, timedelta(seconds=3)))
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])