"""Configuration flow for Meme Stock Insight integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("reddit_client_id"): str,
    vol.Required("reddit_client_secret"): str,
    vol.Required("reddit_username"): str,
    vol.Required("reddit_password"): str,
    vol.Optional("subreddits", default="wallstreetbets,stocks,investing"): str,
    vol.Optional("stock_symbols", default="GME,AMC,TSLA,AAPL,NVDA"): str,
    vol.Optional("scan_limit", default=100): int,
})

class MemeStockInsightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meme Stock Insight."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate Reddit credentials
            try:
                await self._validate_reddit_credentials(
                    user_input["reddit_client_id"],
                    user_input["reddit_client_secret"],
                    user_input["reddit_username"],
                    user_input["reddit_password"],
                )
                
                # Create unique entry ID based on username
                await self.async_set_unique_id(user_input["reddit_username"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"Meme Stock Insight ({user_input['reddit_username']})",
                    data=user_input,
                )
            except ValueError as err:
                _LOGGER.warning("Reddit authentication failed: %s", err)
                errors["base"] = "reddit_auth_failed"
            except ConnectionError as err:
                _LOGGER.error("API connection error: %s", err)
                errors["base"] = "api_error"
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
        """Raise on invalid credentials; return on success."""
        import praw
        import prawcore
        
        try:
            reddit = praw.Reddit(
                client_id=client_id.strip(),
                client_secret=client_secret.strip() or None,
                user_agent=f"homeassistant:meme_stock_insight:v0.0.3 (by /u/{username})",
                username=username.strip(),
                password=password,
                ratelimit_seconds=5,
            )
            
            # Test authentication by getting user info
            me = reddit.user.me()
            if me is None:
                raise ValueError(
                    "Credentials accepted but read-only; "
                    "app is not a script-type or wrong user."
                )
                
            _LOGGER.info("Successfully authenticated Reddit user: %s", me.name)
            
        except prawcore.exceptions.OAuthException as err:
            raise ValueError(
                "OAuth refused: check app type (must be script), "
                "client_id/secret, and user-agent."
            ) from err
        except prawcore.exceptions.ResponseException as err:
            raise ConnectionError(f"Reddit API refused connection: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected Reddit authentication error: %s", err)
            raise