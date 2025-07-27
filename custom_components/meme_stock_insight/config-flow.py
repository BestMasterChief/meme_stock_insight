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
                # Validate credentials with aggressive timeout
                await self._validate_reddit_credentials(
                    user_input["client_id"],
                    user_input["client_secret"],
                    user_input["username"],
                    user_input["password"],
                )
                
                # Create entry if validation successful
                return self.async_create_entry(
                    title=f"Meme Stock Insight ({user_input['username']})",
                    data=user_input,
                )
                
            except ValueError as err:
                _LOGGER.warning("Reddit credential validation failed: %s", err)
                errors["base"] = "reddit_auth_failed"
            except asyncio.TimeoutError:
                _LOGGER.warning("Reddit credential validation timed out")
                errors["base"] = "timeout"
            except Exception as err:
                _LOGGER.exception("Unexpected error during validation: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _validate_reddit_credentials(
        self, client_id: str, client_secret: str, username: str, password: str
    ) -> None:
        """Validate Reddit credentials with timeout protection."""
        
        def _quick_validate():
            """Quick credential validation in executor."""
            import praw
            import prawcore
            
            try:
                # Create Reddit instance with short timeout
                reddit = praw.Reddit(
                    client_id=client_id.strip(),
                    client_secret=client_secret.strip() or None,
                    user_agent=f"homeassistant:meme_stock_insight:v0.0.3 (by /u/{username.strip()})",
                    username=username.strip(),
                    password=password,
                    ratelimit_seconds=5,
                    check_for_updates=False,
                    check_for_async=False,
                    timeout=10,  # Short timeout for validation
                )
                
                # Quick authentication test
                me = reddit.user.me()
                if me is None:
                    raise ValueError("Authentication successful but read-only mode detected. "
                                   "Ensure your Reddit app is created as 'script' type and "
                                   "the username matches the app owner.")
                
                _LOGGER.debug(f"Reddit credentials validated for user: {me.name}")
                return True
                
            except prawcore.exceptions.OAuthException as err:
                raise ValueError("Reddit OAuth authentication failed. Please check: "
                               "1) Reddit app is created as 'script' type, "
                               "2) Client ID and Client Secret are correct, "
                               "3) Username owns the Reddit app") from err
            except prawcore.exceptions.ResponseException as err:
                if "401" in str(err):
                    raise ValueError("Invalid Reddit credentials. Please verify your "
                                   "Client ID, Client Secret, username, and password.") from err
                elif "403" in str(err):
                    raise ValueError("Reddit access forbidden. Your account may be "
                                   "suspended or the app credentials are invalid.") from err
                else:
                    raise ValueError(f"Reddit API error: {err}") from err
            except prawcore.exceptions.RequestException as err:
                raise ValueError(f"Network error connecting to Reddit: {err}") from err
            except Exception as err:
                raise ValueError(f"Unexpected error during Reddit validation: {err}") from err

        try:
            # Run validation with timeout
            await asyncio.wait_for(
                self.hass.async_add_executor_job(_quick_validate),
                timeout=15  # 15 second timeout for entire validation
            )
            
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("Reddit credential validation timed out after 15 seconds. "
                                     "This may indicate network issues or Reddit API problems.")
        except Exception:
            raise  # Re-raise other exceptions as-is

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""