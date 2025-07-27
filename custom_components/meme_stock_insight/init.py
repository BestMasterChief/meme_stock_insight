"""The Meme Stock Insight integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import MemeStockInsightCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meme Stock Insight from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = MemeStockInsightCoordinator(
        hass,
        entry.data["client_id"],
        entry.data["client_secret"],
        entry.data["username"],
        entry.data["password"],
        entry.data.get("subreddits", "wallstreetbets,stocks,investing"),
        entry.data.get("update_interval", 300),
    )

    try:
        # First refresh is now very lightweight and should not fail
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        _LOGGER.error("Error during first refresh (will continue anyway): %s", exc)
        # Don't raise ConfigEntryNotReady - let it continue with empty data
        # The coordinator will handle retries on subsequent updates

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok