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
                vol.Required("l1_grid"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="current")),
                vol.Required("l2_grid"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="current")),
                vol.Required("l3_grid"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="current")),
                vol.Required("l1_ratio"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="current")),
                vol.Required("l2_ratio"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="current")),
                vol.Required("l3_ratio"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="current")),
                vol.Required("ratio_state_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("max_main_fuse", default=25): int,
                vol.Required("max_charger_limit", default=18): int,
                vol.Required("safety_margin", default=2): int,
            })
        )
