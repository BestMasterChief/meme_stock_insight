"""Config flow for Meme Stock Insight integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_SUBREDDITS, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("client_id"): str,
        vol.Required("client_secret"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Optional("subreddits", default=",".join(DEFAULT_SUBREDDITS)): str,
        vol.Optional("update_interval", default=300): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=3600)
        ),
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meme Stock Insight."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Check if already configured
                await self.async_set_unique_id(user_input["username"])
                self._abort_if_unique_id_configured()

                # Validate Reddit credentials
                await self._validate_reddit_credentials(
                    user_input["client_id"],
                    user_input["client_secret"],
                    user_input["username"],
                    user_input["password"],
                )

                # Process subreddits input
                if "subreddits" in user_input:
                    subreddits = [s.strip() for s in user_input["subreddits"].split(",")]
                    user_input["subreddits"] = subreddits

                # Create the config entry
                return self.async_create_entry(
                    title=f"Meme Stock Insight ({user_input['username']})",
                    data=user_input,
                )

            except AlreadyConfigured:
                return self.async_abort(reason="already_configured")
            except InvalidAuth:
                errors["base"] = "reddit_auth_failed"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during setup: %s", exc)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "reddit_app_url": "https://www.reddit.com/prefs/apps",
                "default_subreddits": ",".join(DEFAULT_SUBREDDITS),
                "default_interval": "300",
            },
        )

    async def _validate_reddit_credentials(
        self, client_id: str, client_secret: str, username: str, password: str
    ) -> None:
        """Validate Reddit credentials."""

        def _validate_credentials():
            """Validate credentials in executor thread."""
            try:
                import praw
                import prawcore

                reddit = praw.Reddit(
                    client_id=client_id.strip(),
                    client_secret=client_secret.strip() or None,
                    user_agent=f"homeassistant:meme_stock_insight:v0.6.0 (by /u/{username.strip()})",
                    username=username.strip(),
                    password=password,
                    ratelimit_seconds=5,
                    check_for_updates=False,
                    check_for_async=False,
                    timeout=20,
                )

                # Test authentication
                me = reddit.user.me()
                if me is None:
                    raise InvalidAuth("Authentication successful but read-only mode detected")

                _LOGGER.info("Reddit credentials validated for user: %s", me.name)
                return True

            except prawcore.exceptions.OAuthException as err:
                _LOGGER.error("Reddit OAuth error: %s", err)
                raise InvalidAuth from err
            except prawcore.exceptions.ResponseException as err:
                _LOGGER.error("Reddit API error: %s", err)
                if "401" in str(err) or "403" in str(err):
                    raise InvalidAuth from err
                raise CannotConnect from err
            except Exception as err:
                _LOGGER.error("Unexpected Reddit error: %s", err)
                raise CannotConnect from err

        try:
            await asyncio.wait_for(
                self.hass.async_add_executor_job(_validate_credentials),
                timeout=30
            )
        except asyncio.TimeoutError:
            _LOGGER.error("Reddit credential validation timed out")
            raise

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Meme Stock Insight."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Process subreddits input
            if "subreddits" in user_input:
                subreddits = [s.strip() for s in user_input["subreddits"].split(",")]
                user_input["subreddits"] = subreddits
            return self.async_create_entry(title="", data=user_input)

        current_subreddits = self.config_entry.options.get(
            "subreddits", self.config_entry.data.get("subreddits", DEFAULT_SUBREDDITS)
        )
        if isinstance(current_subreddits, list):
            current_subreddits = ",".join(current_subreddits)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "subreddits",
                        default=current_subreddits,
                        description="Comma-separated list of subreddits to monitor",
                    ): str,
                    vol.Optional(
                        "update_interval",
                        default=self.config_entry.options.get(
                            "update_interval", self.config_entry.data.get("update_interval", 300)
                        ),
                        description="Update interval in seconds (60-3600)",
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                    vol.Optional(
                        "alpha_vantage_key",
                        default=self.config_entry.options.get("alpha_vantage_key", ""),
                        description="Alpha Vantage API key (optional backup for price data)",
                    ): str,
                    vol.Optional(
                        "polygon_key", 
                        default=self.config_entry.options.get("polygon_key", ""),
                        description="Polygon.io API key (optional backup for price data)",
                    ): str,
                }
            ),
            description_placeholders={
                "backup_info": "Adding backup API keys prevents 'exhausted' status when Yahoo Finance is blocked",
                "alpha_url": "https://www.alphavantage.co/support/#api-key",
                "polygon_url": "https://polygon.io/",
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class AlreadyConfigured(HomeAssistantError):
    """Error to indicate integration is already configured."""