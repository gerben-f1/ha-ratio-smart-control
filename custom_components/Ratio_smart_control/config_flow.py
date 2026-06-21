import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, DEFAULT_FUSE_LIMIT, DEFAULT_MAX_CHARGE_CURRENT


def _schema(defaults: dict, include_name_and_id: bool) -> vol.Schema:
    """Bouw het formulier-schema. include_name_and_id=False voor de options flow
    (naam en slave_id wijzig je niet meer na het aanmaken van de entry)."""
    fields = {}

    if include_name_and_id:
        fields[vol.Required("name", default=defaults.get("name", "Ratio Lader"))] = str
        fields[vol.Required("hub", default=defaults.get("hub", "modbus_ratio"))] = str
        fields[vol.Required("slave_id", default=defaults.get("slave_id", 127))] = int

    fields[vol.Required("main_fuse_limit", default=defaults.get("main_fuse_limit", DEFAULT_FUSE_LIMIT))] = vol.All(
        vol.Coerce(float), vol.Range(min=6.0, max=25.0)
    )
    fields[vol.Required("max_charge_current", default=defaults.get("max_charge_current", DEFAULT_MAX_CHARGE_CURRENT))] = vol.All(
        vol.Coerce(float), vol.Range(min=6.0, max=32.0)
    )

    for key in ("l1_grid", "l1_export", "l2_grid", "l2_export", "l3_grid", "l3_export",
                "l1_ratio", "l2_ratio", "l3_ratio", "ratio_state_sensor"):
        fields[vol.Required(key, default=defaults.get(key)) if defaults.get(key) else vol.Required(key)] = \
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))

    return vol.Schema(fields)


class RatioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(f"ratio_{user_input['hub']}_{user_input['slave_id']}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema({}, include_name_and_id=True))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RatioOptionsFlow()


class RatioOptionsFlow(config_entries.OptionsFlow):
    """Hiermee kun je de sensoren en de hoofdzekeringlimiet later aanpassen
    via Instellingen > Apparaten & diensten > [integratie] > Configureren,
    zonder de integratie te moeten verwijderen en opnieuw toevoegen."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Naam, hub en slave_id blijven ongewijzigd; we mergen alleen de aanpasbare velden.
            new_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data={})

        current = self.config_entry.data
        return self.async_show_form(step_id="init", data_schema=_schema(current, include_name_and_id=False))
