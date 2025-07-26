"""Config flow for Meme Stock Insight integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_SUBREDDITS

_LOGGER = logging.getLogger(__name__)

# Configuration schema
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("reddit_client_id"): str,
    vol.Required("reddit_client_secret"): str,
    vol.Required("reddit_username"): str,
    vol.Required("reddit_password"): str,
    vol.Optional("polygon_api_key", default=""): str,
    vol.Optional("trading212_api_key", default=""): str,
    vol.Optional("subreddits", default=",".join(DEFAULT_SUBREDDITS)): str,
    vol.Optional("update_interval", default=12): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
    vol.Optional("min_posts", default=5): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
    vol.Optional("min_karma", default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=10000)),
})

class MemeStockInsightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meme Stock Insight."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate Reddit credentials
            try:
                await self._validate_reddit_credentials(
                    user_input["reddit_client_id"],
                    user_input["reddit_client_secret"],
                    user_input["reddit_username"], 
                    user_input["reddit_password"]
                )
            except ValueError as err:
                _LOGGER.warning(str(err))
                errors["base"] = "reddit_auth_failed"
            except ConnectionError as err:
                _LOGGER.warning(f"Reddit API connection error: {err}")
                errors["base"] = "api_error"
            except Exception as err:
                _LOGGER.exception("Unexpected error validating Reddit credentials")
                errors["base"] = "unknown"

            # Convert subreddits string to list
            if "subreddits" in user_input:
                user_input["subreddits"] = [
                    s.strip() for s in user_input["subreddits"].split(",")
                    if s.strip()
                ]

            if not errors:
                return self.async_create_entry(
                    title="Meme Stock Insight",
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "reddit_setup_url": "https://www.reddit.com/prefs/apps",
                "polygon_setup_url": "https://polygon.io/dashboard", 
                "trading212_setup_url": "https://www.trading212.com/en/login"
            }
        )

    async def _validate_reddit_credentials(
        self, client_id: str, client_secret: str,
        username: str, password: str
    ) -> None:
        """Raise on invalid credentials; return on success."""
        import praw
        import prawcore
        
        try:
            reddit = praw.Reddit(
                client_id=client_id.strip(),
                client_secret=client_secret.strip() or None,
                user_agent=(
                    "homeassistant:meme_stock_insight:v0.0.3 "
                    f"(by /u/{username})"
                ),
                username=username.strip(),
                password=password,
                ratelimit_seconds=5,   # polite retry window
            )
            me = reddit.user.me()       # triggers the login
            if me is None:
                raise ValueError("Credentials accepted but read-only; "
                               "app is not a script-type or wrong user.")
        except prawcore.exceptions.OAuthException as err:
            raise ValueError("OAuth refused: check app type (must be script), "
                           "client_id/secret, and user-agent.") from err
        except prawcore.exceptions.ResponseException as err:
            raise ConnectionError(f"Reddit API refused connection: {err}") from err
        except Exception:
            raise   # bubble the rest

    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MemeStockInsightOptionsFlow(config_entry)

class MemeStockInsightOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Meme Stock Insight."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert subreddits string to list
            if "subreddits" in user_input:
                user_input["subreddits"] = [
                    s.strip() for s in user_input["subreddits"].split(",")
                    if s.strip()
                ]

            return self.async_create_entry(title="", data=user_input)

        # Get current options or defaults from config entry
        current_subreddits = self.config_entry.options.get(
            "subreddits",
            self.config_entry.data.get("subreddits", DEFAULT_SUBREDDITS)
        )

        if isinstance(current_subreddits, list):
            current_subreddits = ",".join(current_subreddits)

        options_schema = vol.Schema({
            vol.Optional(
                "subreddits",
                default=current_subreddits
            ): str,
            vol.Optional(
                "update_interval",
                default=self.config_entry.options.get("update_interval", 12)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
            vol.Optional(
                "min_posts",
                default=self.config_entry.options.get("min_posts", 5)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
            vol.Optional(
                "min_karma",
                default=self.config_entry.options.get("min_karma", 100)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=10000)),
            vol.Optional(
                "volume_weight",
                default=self.config_entry.options.get("volume_weight", 0.40)
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
            vol.Optional(
                "sentiment_weight",
                default=self.config_entry.options.get("sentiment_weight", 0.30)
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
            vol.Optional(
                "momentum_weight",
                default=self.config_entry.options.get("momentum_weight", 0.20)
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
            vol.Optional(
                "short_interest_weight",
                default=self.config_entry.options.get("short_interest_weight", 0.10)
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema
        )