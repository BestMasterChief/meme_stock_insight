"""__init__.py for Meme Stock Insight v0.6.0 - Fixed version with better error handling"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, VERSION
from .coordinator import MemeStockCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up from yaml (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from UI config flow."""
    
    # Build Reddit configuration
    reddit_conf = {
        "client_id": entry.data["client_id"],
        "client_secret": entry.data["client_secret"],
        "username": entry.data[CONF_USERNAME],
        "password": entry.data[CONF_PASSWORD],
        "user_agent": f"homeassistant:meme_stock_insight:{VERSION} (by /u/{entry.data[CONF_USERNAME]})",
    }
    
    # Get options with defaults
    options = dict(entry.options)
    if not options:
        options = {}
    
    # Merge data and options, with options taking precedence
    merged_options = {**entry.data, **options}
    
    try:
        # Create and initialize coordinator
        coordinator = MemeStockCoordinator(hass, reddit_conf, merged_options)
        
        # Perform first refresh
        await coordinator.async_config_entry_first_refresh()
        
        # Store coordinator
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
        
        # Forward to platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        # Add update listener for options changes
        entry.async_on_unload(entry.add_update_listener(async_update_options))
        
        _LOGGER.info("Meme Stock Insight v%s setup completed for user: %s", VERSION, entry.data[CONF_USERNAME])
        return True
        
    except Exception as exc:
        _LOGGER.error("Failed to set up Meme Stock Insight: %s", exc)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)