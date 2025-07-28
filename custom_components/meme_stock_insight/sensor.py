"""Sensor platform for Meme Stock Insight integration - Fixed provider handling."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    DOMAIN,
    SENSOR_DAYS_ACTIVE,
    SENSOR_DYNAMIC_SUBREDDIT,
    SENSOR_MENTIONS,
    SENSOR_MEME_1,
    SENSOR_MEME_2,
    SENSOR_MEME_3,
    SENSOR_PRICE_SINCE_START,
    SENSOR_SENTIMENT,
    SENSOR_STAGE,
    SENSOR_TRENDING,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Meme Stock Insight sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = [
        MemeStockSensor(coordinator, SENSOR_MENTIONS, "Stock Mentions", "mdi:chart-line"),
        MemeStockSensor(coordinator, SENSOR_SENTIMENT, "Market Sentiment", "mdi:emoticon-happy"),
        MemeStockSensor(coordinator, SENSOR_TRENDING, "Trending Stocks", "mdi:trending-up"),
        MemeStockTopSensor(coordinator, SENSOR_MEME_1, "Meme Stock #1", "mdi:trophy", 0),
        MemeStockTopSensor(coordinator, SENSOR_MEME_2, "Meme Stock #2", "mdi:medal", 1),
        MemeStockTopSensor(coordinator, SENSOR_MEME_3, "Meme Stock #3", "mdi:podium-bronze", 2),
        MemeStockSensor(coordinator, SENSOR_STAGE, "Meme Stock Stage", "mdi:chart-timeline"),
        MemeStockSensor(coordinator, SENSOR_DAYS_ACTIVE, "Days Active", "mdi:calendar-clock"),
        MemeStockSensor(coordinator, SENSOR_PRICE_SINCE_START, "Price Since Start", "mdi:cash-plus"),
        MemeStockSensor(coordinator, SENSOR_DYNAMIC_SUBREDDIT, "Dynamic Subreddit", "mdi:reddit"),
    ]

    async_add_entities(sensors)


class MemeStockSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for Meme Stock Insight."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id: str, name: str, icon: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        data = self.coordinator.data or {}
        
        if self._sensor_id == SENSOR_MENTIONS:
            return data.get("total_mentions", 0)
        elif self._sensor_id == SENSOR_SENTIMENT:
            return data.get("average_sentiment", 0.0)
        elif self._sensor_id == SENSOR_TRENDING:
            return len(data.get("trending", []))
        elif self._sensor_id == SENSOR_STAGE:
            return data.get("stage", "Start")
        elif self._sensor_id == SENSOR_DAYS_ACTIVE:
            top_entities = data.get("top_entities", [])
            return top_entities[0].get("days_active", 0) if top_entities else 0
        elif self._sensor_id == SENSOR_PRICE_SINCE_START:
            top_entities = data.get("top_entities", [])
            return top_entities[0].get("price_since_start", 0.0) if top_entities else 0.0
        elif self._sensor_id == SENSOR_DYNAMIC_SUBREDDIT:
            return getattr(self.coordinator, '_dynamic_sr', None) or "None"
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data or {}
        attributes = {
            "integration_version": VERSION,
            "last_updated": data.get("last_updated"),
        }

        if self._sensor_id == SENSOR_MENTIONS:
            attributes["mentions_breakdown"] = data.get("mentions_dict", {})
            # Add provider status info
            attributes["providers_exhausted"] = data.get("providers_exhausted", [])
            attributes["providers_available"] = data.get("providers_available", [])
        elif self._sensor_id == SENSOR_SENTIMENT:
            attributes["trending_stocks"] = data.get("trending", [])
        elif self._sensor_id == SENSOR_TRENDING:
            attributes["trending_list"] = data.get("trending", [])

        return attributes


class MemeStockTopSensor(CoordinatorEntity, SensorEntity):
    """Sensor for individual top meme stocks."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id: str, name: str, icon: str, index: int):
        """Initialize the top stock sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._index = index
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}"

    @property
    def native_value(self) -> str:
        """Return the stock symbol and company name or status."""
        data = self.coordinator.data or {}
        top_entities = data.get("top_entities", [])
        
        if self._index < len(top_entities):
            entity = top_entities[self._index]
            symbol = entity.get("symbol", "")
            company = entity.get("company", "")
            provider_status = entity.get("provider", "")
            
            # Handle different provider statuses
            if provider_status == "max_api_calls_used":
                return "Max API calls used"
            elif provider_status == "recently_failed":
                return "Recently failed to fetch"
            elif provider_status == "no_data_available":
                return "No price data found, symbol may be delisted"
            elif provider_status == "error":
                return "Error fetching data"
            elif entity.get("current_price") is None:
                return f"{symbol} - Price unavailable"
            else:
                return f"{symbol} - {company}" if symbol and company else symbol or "No data"
        
        return "No data"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        data = self.coordinator.data or {}
        top_entities = data.get("top_entities", [])
        
        if self._index < len(top_entities):
            entity = top_entities[self._index]
            provider_status = entity.get("provider", "")
            # Entity is available even if provider status indicates issues
            return provider_status not in ["error"]
        
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes for the top stock."""
        data = self.coordinator.data or {}
        top_entities = data.get("top_entities", [])
        
        attributes = {
            "integration_version": VERSION,
            "rank": self._index + 1,
        }
        
        if self._index < len(top_entities):
            entity = top_entities[self._index]
            provider_status = entity.get("provider", "unknown")
            
            attributes.update({
                "symbol": entity.get("symbol"),
                "company_name": entity.get("company"),
                "mentions": entity.get("mentions", 0),
                "current_price": entity.get("current_price"),
                "price_change_pct": entity.get("price_change_pct", 0.0),
                "volume": entity.get("volume", 0),
                "days_active": entity.get("days_active", 0),
                "price_since_start": entity.get("price_since_start", 0.0),
                "provider": provider_status,
            })
            
            # Add helpful info based on provider status
            if provider_status == "max_api_calls_used":
                attributes["info"] = "All price providers have reached their daily limits. Configure backup API keys in integration options."
            elif provider_status == "recently_failed":
                attributes["info"] = "Symbol failed recently and is temporarily skipped to prevent repeated errors."
            elif provider_status == "no_data_available":
                attributes["info"] = "No price data available from any provider. Symbol may be delisted or inactive."
            elif provider_status in ["yfinance", "alpha_vantage", "polygon"]:
                attributes["info"] = f"Price data successfully fetched from {provider_status}"
        
        return attributes