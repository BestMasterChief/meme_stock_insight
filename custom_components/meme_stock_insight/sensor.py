"""Sensor platform for Meme Stock Insight integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import MemeStockInsightCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Meme Stock Insight sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = []
    
    # Create sensors for each type
    for sensor_type, config in SENSOR_TYPES.items():
        sensors.append(
            MemeStockInsightSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_type=sensor_type,
                config=config,
            )
        )
    
    async_add_entities(sensors)

class MemeStockInsightSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Meme Stock Insight sensor."""

    def __init__(
        self,
        coordinator: MemeStockInsightCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self.entry = entry
        self.sensor_type = sensor_type
        self.sensor_config = config
        
        # Entity properties
        self._attr_name = f"{config['name']}"
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_icon = config["icon"]
        self._attr_native_unit_of_measurement = config.get("unit")
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Meme Stock Insight",
            "manufacturer": "Custom Integration",
            "model": "Reddit Stock Tracker",
            "sw_version": "0.0.3",
        }

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        data = self.coordinator.data
        
        if self.sensor_type == "mentions":
            # Return total number of mentions
            mentions = data.get("mentions", {})
            return sum(mentions.values()) if mentions else 0
            
        elif self.sensor_type == "sentiment":
            # Return overall sentiment score
            return round(data.get("overall_sentiment", 0), 2)
            
        elif self.sensor_type == "trending":
            # Return number of trending stocks
            trending = data.get("trending_stocks", {})
            return len(trending) if trending else 0
            
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None
            
        data = self.coordinator.data
        attributes = {
            "last_updated": data.get("last_updated"),
            "subreddits_scanned": data.get("subreddits_scanned", []),
            "total_posts_analyzed": data.get("total_posts_analyzed", 0),
        }
        
        if self.sensor_type == "mentions":
            # Include detailed mention counts
            mentions = data.get("mentions", {})
            attributes.update({
                "mention_details": dict(sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:10]),
                "total_symbols_found": len(mentions),
            })
            
        elif self.sensor_type == "sentiment":
            # Include sentiment scores by stock
            sentiment_scores = data.get("sentiment_scores", {})
            attributes.update({
                "sentiment_by_stock": dict(sorted(sentiment_scores.items(), key=lambda x: x[1], reverse=True)[:10]),
                "stocks_analyzed": len(sentiment_scores),
            })
            
        elif self.sensor_type == "trending":
            # Include trending stock details
            trending = data.get("trending_stocks", {})
            attributes.update({
                "trending_details": trending,
                "top_stock": max(trending.items(), key=lambda x: x[1])[0] if trending else None,
                "top_mentions": max(trending.values()) if trending else 0,
            })
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success