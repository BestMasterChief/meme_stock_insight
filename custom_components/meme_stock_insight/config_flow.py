"""Config flow for Meme Stock Insight integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("client_id"): str,
        vol.Required("client_secret"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Optional("subreddits", default="wallstreetbets,stocks,investing"): str,
        vol.Optional("update_interval", default=300): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    def _validate_reddit_credentials(client_id: str, client_secret: str, username: str, password: str) -> None:
        """Validate Reddit credentials in executor thread."""
        import praw
        import prawcore

        try:
            reddit = praw.Reddit(
                client_id=client_id.strip(),
                client_secret=client_secret.strip() or None,
                user_agent=f"homeassistant:meme_stock_insight:v0.0.3 (by /u/{username.strip()})",
                username=username.strip(),
                password=password,
                ratelimit_seconds=5,
                check_for_updates=False,  # Disable update check to prevent blocking calls
                check_for_async=False,    # Disable async check since we're in executor
            )
            me = reddit.user.me()  # triggers the login
            if me is None:
                raise ValueError("Credentials accepted but read-only; app is not a script-type or wrong user.")
        except prawcore.exceptions.OAuthException as err:
            raise ValueError("OAuth refused: check app type (must be script), client_id/secret, and user-agent.") from err
        except prawcore.exceptions.ResponseException as err:
            raise ConnectionError(f"Reddit API refused connection: {err}") from err
        except Exception as err:
            raise ConnectionError(f"Unexpected error connecting to Reddit: {err}") from err

    # Run the validation in executor to avoid blocking the event loop
    await hass.async_add_executor_job(
        _validate_reddit_credentials,
        data["client_id"],
        data["client_secret"],
        data["username"],
        data["password"]
    )

    # Return info that you want to store in the config entry.
    return {"title": f"Meme Stock Insight ({data['username']})"}


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
                info = await validate_input(self.hass, user_input)
            except ValueError as err:
                _LOGGER.warning("Reddit authentication failed: %s", err)
                errors["base"] = "reddit_auth_failed"
            except ConnectionError as err:
                _LOGGER.warning("Connection error: %s", err)
                errors["base"] = "api_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
