"""Config flow for Tineco integration."""

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN
from .tineco_client_impl import TinecoClient, TinecoNewDeviceException

_LOGGER = logging.getLogger(__name__)

REGIONS = ["IE", "PL", "DE", "FR", "ES", "IT", "US"]

class TinecoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tineco."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        temp_client = TinecoClient()
        self._device_id = temp_client.DEVICE_ID

        self._tineco_client = None

        self._email = None
        self._password = None
        self._region = "IE"
        self._verify_id = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._email = user_input["email"]
            self._password = user_input["password"]
            self._region = user_input["region"]

            self._tineco_client = TinecoClient(device_id=self._device_id, region=self._region)

            await self.async_set_unique_id(self._email)
            self._abort_if_unique_id_configured()

            try:
                result = await self.hass.async_add_executor_job(
                    self._tineco_client.login, self._email, self._password, True
                )

                if result and result[0]:
                    return self._create_entry()
                else:
                    errors["base"] = "invalid_auth"

            except TinecoNewDeviceException as e:
                self._verify_id = e.verify_id
                return await self.async_step_otp()
            except Exception:
                _LOGGER.exception("Unexpected exception during login")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required("email"): str,
            vol.Required("password"): str,
            vol.Required("region", default="IE"): vol.In(REGIONS),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_otp(self, user_input=None):
        """Handle verification code."""
        errors = {}

        if user_input is not None:
            code = user_input["code"]
            try:
                result = await self.hass.async_add_executor_job(
                    self._tineco_client.quick_login_by_email,
                    self._email,
                    self._verify_id,
                    code
                )
                if result and result[0]:
                    return self._create_entry()
                else:
                    errors["base"] = "invalid_code"
            except Exception:
                _LOGGER.exception("Error during OTP")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="otp",
            data_schema=vol.Schema({
                vol.Required("code"): str,
            }),
            errors=errors,
            description_placeholders={"email": self._email},
        )

    def _create_entry(self):
        return self.async_create_entry(
            title=self._email,
            data={
                "email": self._email,
                "password": self._password,
                "device_id": self._device_id,
                "region": self._region
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Tineco."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            new_data = self.entry.data.copy()
            if "region" in user_input:
                new_data["region"] = user_input["region"]

            self.hass.config_entries.async_update_entry(self.entry, data=new_data)

            return self.async_create_entry(title="", data=user_input)

        current_region = self.entry.data.get("region", "IE")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "scan_interval",
                    default=self.entry.options.get("scan_interval", 60),
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                vol.Required("region", default=current_region): vol.In(REGIONS),
            }),
        )