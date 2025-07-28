"""Sensor platform for Meme Stock Insight v0.6.0
Adds new entities: days_active, price_since_start and dynamic_subreddit.
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfTime, Currency
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VERSION,
    ATTRIBUTION,
    SENSOR_MENTIONS,
    SENSOR_SENTIMENT,
    SENSOR_TRENDING,
    SENSOR_MEME_1,
    SENSOR_MEME_2,
    SENSOR_MEME_3,
    SENSOR_STAGE,
    SENSOR_DAYS_ACTIVE,
    SENSOR_PRICE_SINCE_START,
    SENSOR_DYNAMIC_SUBREDDIT,
)

TOP_SENSORS = [SENSOR_MEME_1, SENSOR_MEME_2, SENSOR_MEME_3]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        MemeInsightSensor(coordinator, SENSOR_MENTIONS, "Total Mentions"),
        MemeInsightSensor(coordinator, SENSOR_SENTIMENT, "Market Sentiment", PERCENTAGE),
        MemeInsightSensor(coordinator, SENSOR_TRENDING, "Trending Stocks"),
        MemeInsightSensor(coordinator, SENSOR_STAGE, "Meme Stock Stage"),
        MemeInsightSensor(coordinator, SENSOR_DAYS_ACTIVE, "Days Active", UnitOfTime.DAYS),
        MemeInsightSensor(coordinator, SENSOR_PRICE_SINCE_START, "Price Since Start", PERCENTAGE),
        MemeInsightSensor(coordinator, SENSOR_DYNAMIC_SUBREDDIT, "Dynamic Subreddit"),
    ]

    for idx, sensor_id in enumerate(TOP_SENSORS, start=1):
        entities.append(TopMemeSensor(coordinator, sensor_id, f"Meme Stock #{idx}"))

    add_entities(entities)

class MemeInsightSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id: str, name: str, unit: str | None = None):
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}"
        self._attr_native_unit_of_measurement = unit
        self._attr_attribution = ATTRIBUTION

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        if self._sensor_id == SENSOR_MENTIONS:
            return data.get("total_mentions")
        if self._sensor_id == SENSOR_SENTIMENT:
            return data.get("average_sentiment")
        if self._sensor_id == SENSOR_TRENDING:
            return data.get("trending_count")
        if self._sensor_id == SENSOR_STAGE:
            return data.get("stage")
        if self._sensor_id == SENSOR_DAYS_ACTIVE:
            top = data.get("top_entities", [])
            return top[0].get("days_active") if top else None
        if self._sensor_id == SENSOR_PRICE_SINCE_START:
            top = data.get("top_entities", [])
            return top[0].get("price_since_start") if top else None
        if self._sensor_id == SENSOR_DYNAMIC_SUBREDDIT:
            return data.get("dynamic_subreddit")
        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        if self._sensor_id == SENSOR_MENTIONS:
            return {"stock_mentions": data.get("mentions_dict"), "integration": VERSION}
        if self._sensor_id == SENSOR_SENTIMENT:
            return {"distribution": data.get("sentiment_distribution")}
        if self._sensor_id == SENSOR_TRENDING:
            return {"trending_list": data.get("trending")}
        if self._sensor_id in (SENSOR_STAGE,):
            return {"reason": data.get("stage_reason")}
        return {"integration": VERSION}

class TopMemeSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = "monetary"
    _attr_native_unit_of_measurement = Currency.USD

    def __init__(self, coordinator, sensor_id: str, name: str):
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        idx = TOP_SENSORS.index(self._sensor_id)
        if idx < len(data.get("top_entities", [])):
            return data["top_entities"][idx].get("current_price")
        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        idx = TOP_SENSORS.index(self._sensor_id)
        if idx < len(data.get("top_entities", [])):
            return data["top_entities"][idx]
        return {}