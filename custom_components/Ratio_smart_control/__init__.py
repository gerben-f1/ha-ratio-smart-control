import asyncio
import logging
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from datetime import timedelta
from .const import DOMAIN, MODBUS_HUB, SLAVE_ID

_LOGGER = logging.getLogger(__name__)

TARGET_SENSOR_ID = "sensor.ratio_smart_control_target"
CURRENT_LIMIT_ID = "sensor.ratio_current_limit"

async def async_setup_entry(hass, entry):
    conf = entry.data

    async def update_charger(val):
        _LOGGER.warning(f"RATIO ACTIE: Schrijven naar 16640 -> {val}A")
        try:
            await hass.services.async_call("modbus", "write_register", {
                "hub": MODBUS_HUB, 
                "slave": SLAVE_ID, 
                "address": 16640, 
                "value": int(val)
            })
        except Exception as e:
            _LOGGER.error(f"RATIO FOUT: Modbus schrijven mislukt: {e}")

    async def check_and_adjust(event_or_now=None):
        t_state = hass.states.get(TARGET_SENSOR_ID)
        c_state = hass.states.get(CURRENT_LIMIT_ID)
        # Haal de ruwe status op (bijv. "5")
        status_state = hass.states.get(conf["ratio_state_sensor"])
        
        if not t_state or not c_state or not status_state:
            return

        # VEILIGHEID: Alleen actie ondernemen als de lader status "5" (Laden) heeft
        if status_state.state != "5":
            _LOGGER.debug(f"RATIO: Geen actie nodig, status is {status_state.state}")
            return

        try:
            target = int(float(t_state.state))
            current = int(float(c_state.state or 0))

            if target != current:
                await update_charger(target)
        except Exception as e:
            _LOGGER.error(f"RATIO: Fout bij vergelijken: {e}")

    # Directe listener voor snelle reactie
    async_track_state_change_event(hass, [TARGET_SENSOR_ID], check_and_adjust)
    # Backup timer (elke 15 sec)
    async_track_time_interval(hass, check_and_adjust, timedelta(seconds=15))
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
