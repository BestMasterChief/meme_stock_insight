"""HA entry points – v0.6.0."""
from __future__ import annotations
import logging, voluptuous as vol
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import MemeStockCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup(_hass: HomeAssistant, _config: ConfigType) -> bool:
    return True  # YAML not supported


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    reddit_conf = {
        "client_id":     entry.data["client_id"],
        "client_secret": entry.data["client_secret"],
        "username":      entry.data[CONF_USERNAME],
        "password":      entry.data[CONF_PASSWORD],
        "user_agent":    f"homeassistant:meme_stock_insight:{entry.version} (by /u/{entry.data[CONF_USERNAME]})",
    }
    options = entry.options
    coord = MemeStockCoordinator(hass, reddit_conf, options)
    await coord.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload
