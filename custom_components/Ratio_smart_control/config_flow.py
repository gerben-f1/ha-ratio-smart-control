import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN

class RatioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Ratio Smart Control", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                # De P1 stroom sensoren (L1, L2, L3)
                vol.Required("l1_grid"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("l2_grid"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("l3_grid"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                
                # De Ratio stroom sensoren (hoeveel de lader nu verbruikt)
                vol.Required("l1_ratio"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("l2_ratio"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("l3_ratio"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                
                # De Status van de lader
                vol.Required("ratio_state_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            })
        )
