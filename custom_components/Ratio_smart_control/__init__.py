import asyncio
import logging
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from .const import DOMAIN, MODBUS_HUB, SLAVE_ID, REGISTER_WRITE_AMPERAGE

_LOGGER = logging.getLogger(__name__)

# De twee belangrijke sensoren voor de check
TARGET_SENSOR_ID = "sensor.ratio_smart_control_target"
CURRENT_LIMIT_ID = "sensor.ratio_current_limit"

async def async_setup_entry(hass, entry):
    conf = entry.data

    async def update_charger(val):
        _LOGGER.info(f"Ratio Smart Control: Aanpassen van lader limiet naar {val}A")
        try:
            await hass.services.async_call("modbus", "write_register", {
                "hub": MODBUS_HUB, 
                "slave": SLAVE_ID, 
                "address": REGISTER_WRITE_AMPERAGE, 
                "value": int(val)
            })
        except Exception as e:
            _LOGGER.error(f"Ratio Smart Control: Fout bij schrijven naar Modbus: {e}")

    async def check_and_adjust(now=None):
        # 1. Haal de berekende target op
        target_state = hass.states.get(TARGET_SENSOR_ID)
        # 2. Haal de huidige limiet uit de lader op (Register 16398)
        current_limit_state = hass.states.get(CURRENT_LIMIT_ID)
        # 3. Haal de laadstatus op
        status_state = hass.states.get(conf["ratio_state_sensor"])
        
        # Veiligheidscheck: bestaan alle sensoren?
        if not target_state or not current_limit_state or not status_state:
            _LOGGER.debug("Ratio Smart Control: Wachten op sensoren...")
            return

        # Stop als waarden onbekend zijn
        if target_state.state in ["unknown", "unavailable"] or current_limit_state.state in ["unknown", "unavailable"]:
            return

        try:
            target = int(float(target_state.state))
            current_limit = int(float(current_limit_state.state))

            # Alleen bijsturen als de lader echt aan het laden is (Status 5)
            if status_state.state == "5":
                # Als de lader niet op de gewenste waarde staat, stuur update
                if target != current_limit:
                    await update_charger(target)
            else:
                _LOGGER.debug(f"Ratio Smart Control: Geen actie nodig, status is {status_state.state}")
                
        except ValueError:
            _LOGGER.error("Ratio Smart Control: Kon sensorwaarden niet omzetten naar getallen")

    # Controleer elke 15 seconden of de lader nog goed staat
    async_track_time_interval(hass, check_and_adjust, timedelta(seconds=15))
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
