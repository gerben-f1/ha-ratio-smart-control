import asyncio
import logging
from .const import DOMAIN, MODBUS_HUB, SLAVE_ID, REGISTER_WRITE_AMPERAGE, SLOW_UP_DELAY, STEP_SIZE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    conf = entry.data

    async def update_charger(val):
        await hass.services.async_call("modbus", "write_register", {
            "hub": MODBUS_HUB, "slave": SLAVE_ID, "address": REGISTER_WRITE_AMPERAGE, "value": int(val)
        })

    async def handle_logic(event):
        if event.data.get("entity_id") != f"sensor.ratio_smart_control_target": return
        
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in ["unknown", "unavailable"]: return
        
        target = int(float(new_state.state))
        # Gebruik de hoogste waarde van de 3 fases van de lader als referentie voor huidige stroom
        h = hass.states.get
        current_val = max(float(h(conf["l1_ratio"]).state or 0), float(h(conf["l2_ratio"]).state or 0), float(h(conf["l3_ratio"]).state or 0))
        status_state = h(conf["ratio_state_sensor"])

        if not status_state or status_state.state != "5": return
        
        if target < current_val:
            await update_charger(target)
        elif target > (current_val + 1): # Kleine marge om onnodig sturen te voorkomen
            await asyncio.sleep(SLOW_UP_DELAY)
            latest = int(float(hass.states.get(f"sensor.ratio_smart_control_target").state))
            if latest > current_val:
                await update_charger(min(current_val + STEP_SIZE, latest))

    hass.bus.async_listen("state_changed", handle_logic)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True
