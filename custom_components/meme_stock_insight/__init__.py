"""The Meme Stock Insight integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, DEFAULT_SUBREDDITS, DEFAULT_UPDATE_INTERVAL
from .coordinator import MemeStockInsightCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meme Stock Insight from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration with options override
    config = entry.data.copy()
    if entry.options:
        config.update(entry.options)

    coordinator = MemeStockInsightCoordinator(
        hass,
        config["client_id"],
        config["client_secret"],
        config["username"],
        config["password"],
        config.get("subreddits", DEFAULT_SUBREDDITS),
        config.get("update_interval", DEFAULT_UPDATE_INTERVAL),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        _LOGGER.error("Error setting up Meme Stock Insight: %s", exc)
        raise ConfigEntryNotReady from exc

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok