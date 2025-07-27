"""Sensor platform for Meme Stock Insight."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, SENSOR_TYPES, VERSION
from .coordinator import MemeStockInsightCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(MemeStockInsightSensor(coordinator, sensor_type, config_entry))

    async_add_entities(entities)


class MemeStockInsightSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Meme Stock Insight sensor."""

    def __init__(
        self,
        coordinator: MemeStockInsightCoordinator,
        sensor_type: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._config_entry = config_entry
        self._attr_name = f"Meme Stock {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        if self._sensor_type == "mentions":
            return self.coordinator.data.get("total_mentions", 0)
        elif self._sensor_type == "sentiment":
            sentiment_data = self.coordinator.data.get("sentiment", {})
            if sentiment_data:
                # Return average sentiment across all tracked stocks
                return round(sum(sentiment_data.values()) / len(sentiment_data), 2)
            return 0.0
        elif self._sensor_type == "trending":
            trending_data = self.coordinator.data.get("trending", [])
            return len(trending_data)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "attribution": ATTRIBUTION,
            "version": VERSION,
            "last_update": self.coordinator.data.get("last_update"),
            "subreddits": ", ".join(self.coordinator.subreddits),
        }

        if self._sensor_type == "mentions":
            mentions = self.coordinator.data.get("mentions", {})
            # Show top 10 most mentioned stocks
            sorted_mentions = dict(sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:10])
            attributes["top_mentioned_stocks"] = sorted_mentions
            attributes["total_unique_stocks"] = len(mentions)

        elif self._sensor_type == "sentiment":
            sentiment = self.coordinator.data.get("sentiment", {})
            # Show sentiment for top stocks
            sorted_sentiment = dict(sorted(sentiment.items(), key=lambda x: x[1], reverse=True)[:10])
            attributes["stock_sentiment"] = {k: round(v, 2) for k, v in sorted_sentiment.items()}

            # Calculate sentiment distribution
            positive_count = sum(1 for v in sentiment.values() if v > 0.1)
            negative_count = sum(1 for v in sentiment.values() if v < -0.1)
            neutral_count = len(sentiment) - positive_count - negative_count

            attributes["sentiment_distribution"] = {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            }

        elif self._sensor_type == "trending":
            trending = self.coordinator.data.get("trending", [])
            attributes["trending_stocks"] = trending[:10]

            # Calculate trending momentum
            if trending:
                top_stock = trending[0]
                attributes["top_trending_stock"] = top_stock["symbol"]
                attributes["top_trending_mentions"] = top_stock["mentions"]

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Meme Stock Insight",
            "manufacturer": "Custom Integration",
            "model": "Reddit Stock Tracker",
            "sw_version": VERSION,
        }
