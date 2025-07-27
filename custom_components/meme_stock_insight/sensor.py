"""Enhanced Sensor platform for Meme Stock Insight with individual meme stock entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, SENSOR_TYPES, VERSION, STAGE_ICONS
from .coordinator import MemeStockInsightCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the enhanced sensor platform."""
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
        elif self._sensor_type in ["meme_1", "meme_2", "meme_3"]:
            return self._get_top_meme_stock_value()
        elif self._sensor_type == "stage":
            return self.coordinator.data.get("meme_stage", "Start")

        return None

    def _get_top_meme_stock_value(self) -> str:
        """Get the value for top meme stock entities."""
        top_stocks = self.coordinator.data.get("top_stocks", [])
        
        # Map sensor type to index
        index_map = {"meme_1": 0, "meme_2": 1, "meme_3": 2}
        index = index_map.get(self._sensor_type, 0)
        
        if index < len(top_stocks):
            stock = top_stocks[index]
            return stock.get("display_name", f"{stock.get('symbol', 'N/A')} - Unknown")
        
        return "No data"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        # Dynamic icon for stage sensor
        if self._sensor_type == "stage":
            stage_key = self.coordinator.data.get("meme_stage_key", "start")
            return STAGE_ICONS.get(stage_key, "mdi:help-circle")
        
        return self._attr_icon

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
                "subreddits_processed": self.coordinator.data.get("subreddits_processed", []),
            })
        elif self._sensor_type == "sentiment":
            attributes.update({
                "sentiment_distribution": self.coordinator.data.get("sentiment_distribution", {}),
                "average_sentiment": self.coordinator.data.get("average_sentiment", 0.0),
            })
        elif self._sensor_type == "trending":
            attributes.update({
                "trending_stocks": self.coordinator.data.get("trending_stocks", []),
                "trending_count": self.coordinator.data.get("trending_count", 0),
            })
        elif self._sensor_type in ["meme_1", "meme_2", "meme_3"]:
            attributes.update(self._get_meme_stock_attributes())
        elif self._sensor_type == "stage":
            attributes.update({
                "stage_key": self.coordinator.data.get("meme_stage_key", "start"),
                "stage_reason": self.coordinator.data.get("stage_reason", "No analysis available"),
                "stage_analysis": self.coordinator.data.get("stage_analysis", {}),
                "top_stock_symbol": self._get_top_stock_symbol(),
                "stage_description": self._get_stage_description(),
            })

        return attributes

    def _get_meme_stock_attributes(self) -> dict[str, Any]:
        """Get attributes for individual meme stock entities."""
        top_stocks = self.coordinator.data.get("top_stocks", [])
        
        # Map sensor type to index
        index_map = {"meme_1": 0, "meme_2": 1, "meme_3": 2}
        index = index_map.get(self._sensor_type, 0)
        
        if index < len(top_stocks):
            stock = top_stocks[index]
            stock_prices = self.coordinator.data.get("stock_prices", {})
            symbol = stock.get("symbol", "")
            stock_data = stock_prices.get(symbol, {})
            
            return {
                "symbol": symbol,
                "company_name": stock.get("company_name", "Unknown"),
                "mentions": stock.get("mentions", 0),
                "current_price": stock.get("current_price"),
                "price_change_pct": stock.get("price_change_pct", 0),
                "volume": stock_data.get("volume", 0),
                "avg_volume": stock_data.get("avg_volume", 0),
                "market_cap": stock_data.get("market_cap", 0),
                "price_history": stock_data.get("price_history", []),
                "rank": index + 1,
            }
        
        return {
            "symbol": None,
            "company_name": "No data",
            "mentions": 0,
            "current_price": None,
            "price_change_pct": 0,
            "volume": 0,
            "avg_volume": 0,
            "market_cap": 0,
            "price_history": [],
            "rank": index + 1,
        }

    def _get_top_stock_symbol(self) -> str:
        """Get the symbol of the top meme stock for stage analysis."""
        top_stocks = self.coordinator.data.get("top_stocks", [])
        return top_stocks[0].get("symbol", "") if top_stocks else ""

    def _get_stage_description(self) -> str:
        """Get a description of the current meme stock stage."""
        stage_key = self.coordinator.data.get("meme_stage_key", "start")
        
        descriptions = {
            "start": "Early phase - Limited activity and mentions",
            "rising_interest": "Growing interest - Increased mentions and social media activity",
            "stock_rising": "Momentum building - Price rising with strong volume",
            "estimated_peak": "Near peak - High activity, consider taking profits",
            "do_not_buy": "Danger zone - Avoid buying, consider selling",
            "dropping": "Declining phase - Falling prices and sentiment"
        }
        
        return descriptions.get(stage_key, "Unknown stage")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success or self.coordinator.data is not None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Meme Stock Insight",
            "manufacturer": "Meme Stock Insight",
            "model": "Reddit & Stock Analysis",
            "sw_version": VERSION,
        }