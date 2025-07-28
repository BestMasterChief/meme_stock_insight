"""__init__.py for Meme Stock Insight v0.6.0
Sets up coordinator and forwards platforms.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL, VERSION
from .coordinator import MemeStockCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]

async def async_setup(_hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up from yaml (noop)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from UI config flow."""
    reddit_conf = {
        "client_id": entry.data["client_id"],
        "client_secret": entry.data["client_secret"],
        "username": entry.data[CONF_USERNAME],
        "password": entry.data[CONF_PASSWORD],
        "user_agent": f"homeassistant:meme_stock_insight:{VERSION} (by /u/{entry.data[CONF_USERNAME]})",
    }

    coordinator = MemeStockCoordinator(hass, reddit_conf, entry.options)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok