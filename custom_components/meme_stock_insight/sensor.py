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
        self._attr_attribution = ATTRIBUTION

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        if self._sensor_type == "mentions":
            return self.coordinator.data.get("total_mentions", 0)
        elif self._sensor_type == "sentiment":
            return self.coordinator.data.get("average_sentiment", 0.0)
        elif self._sensor_type == "trending":
            return self.coordinator.data.get("trending_count", 0)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "last_updated": self.coordinator.data.get("last_updated"),
            "status": self.coordinator.data.get("status", "unknown"),
            "integration_version": VERSION,
        }

        if self._sensor_type == "mentions":
            attributes.update({
                "stock_mentions": self.coordinator.data.get("stock_mentions", {}),
                "posts_processed": self.coordinator.data.get("posts_processed", 0),
            })
        elif self._sensor_type == "sentiment":
            attributes.update({
                "sentiment_distribution": self.coordinator.data.get("sentiment_distribution", {}),
            })
        elif self._sensor_type == "trending":
            attributes.update({
                "trending_stocks": self.coordinator.data.get("trending_stocks", []),
            })

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success or self.coordinator.data is not None