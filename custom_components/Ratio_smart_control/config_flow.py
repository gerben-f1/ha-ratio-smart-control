import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class RatioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Ratio Smart Control", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("l1_grid_con"): str, vol.Required("l1_grid_pro"): str,
                vol.Required("l2_grid_con"): str, vol.Required("l2_grid_pro"): str,
                vol.Required("l3_grid_con"): str, vol.Required("l3_grid_pro"): str,
                vol.Required("l1_ratio"): str, vol.Required("l2_ratio"): str, vol.Required("l3_ratio"): str,
                vol.Required("ratio_state_sensor"): str,
            })
        )
