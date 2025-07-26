"""Sensor platform for Meme Stock Insight."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_TICKER,
    ATTR_NAME,
    ATTR_IMPACT_SCORE,
    ATTR_MEME_LIKELIHOOD,
    ATTR_DAYS_ACTIVE,
    ATTR_STAGE,
    ATTR_SHORTABLE,
    ATTR_DECLINE_FLAG,
    ATTR_VOLUME_SCORE,
    ATTR_SENTIMENT_SCORE,
    ATTR_MOMENTUM_SCORE,
    ATTR_SHORT_INTEREST,
)
from .coordinator import MemeStockDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    # Create entities for each meme stock
    if coordinator.data:
        for ticker, stock_data in coordinator.data.items():
            entities.extend([
                MemeStockSensor(coordinator, ticker, "impact_score", "Impact Score", "%", SensorDeviceClass.POWER_FACTOR),
                MemeStockSensor(coordinator, ticker, "meme_likelihood", "Meme Likelihood", "%", SensorDeviceClass.POWER_FACTOR),
                MemeStockSensor(coordinator, ticker, "days_active", "Days Active", "days", None),
                MemeStockStageSensor(coordinator, ticker),
                MemeStockBooleanSensor(coordinator, ticker, "shortable", "Shortable"),
                MemeStockBooleanSensor(coordinator, ticker, "decline_flag", "Decline Flag"),
                MemeStockSensor(coordinator, ticker, "volume_score", "Volume Score", "%", SensorDeviceClass.POWER_FACTOR),
                MemeStockSensor(coordinator, ticker, "sentiment_score", "Sentiment Score", "%", SensorDeviceClass.POWER_FACTOR),
                MemeStockSensor(coordinator, ticker, "momentum_score", "Momentum Score", "%", SensorDeviceClass.POWER_FACTOR),
                MemeStockSensor(coordinator, ticker, "short_interest", "Short Interest", "%", SensorDeviceClass.POWER_FACTOR),
            ])

    async_add_entities(entities)


class MemeStockBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for meme stock sensors."""

    def __init__(
        self,
        coordinator: MemeStockDataUpdateCoordinator,
        ticker: str,
        sensor_type: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ticker = ticker
        self._sensor_type = sensor_type
        self._attr_name = f"{ticker} {name}"
        self._attr_unique_id = f"{DOMAIN}_{ticker}_{sensor_type}"

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._ticker)},
            "name": f"Meme Stock {self._ticker}",
            "manufacturer": "Meme Stock Insight",
            "model": "Meme Stock Monitor",
            "sw_version": "1.0.0",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._ticker in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}

        stock_data = self.coordinator.data[self._ticker]
        return {
            "ticker": stock_data.get("ticker"),
            "company_name": stock_data.get("name"),
            "post_count": stock_data.get("post_count"),
            "total_karma": stock_data.get("total_karma"),
            "last_updated": self.coordinator.last_update_success_time,
        }


class MemeStockSensor(MemeStockBaseSensor):
    """Sensor for numeric meme stock data."""

    def __init__(
        self,
        coordinator: MemeStockDataUpdateCoordinator,
        ticker: str,
        sensor_type: str,
        name: str,
        unit: Optional[str] = None,
        device_class: Optional[SensorDeviceClass] = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, ticker, sensor_type, name)
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        if not self.available:
            return None

        stock_data = self.coordinator.data[self._ticker]
        return stock_data.get(self._sensor_type)


class MemeStockStageSensor(MemeStockBaseSensor):
    """Sensor for meme stock stage."""

    def __init__(self, coordinator: MemeStockDataUpdateCoordinator, ticker: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, ticker, "stage", "Stage")
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["Initiation", "Up-Ramp", "Tipping Point", "Do Not Invest"]

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        if not self.available:
            return None

        stock_data = self.coordinator.data[self._ticker]
        return stock_data.get("stage")


class MemeStockBooleanSensor(MemeStockBaseSensor):
    """Sensor for boolean meme stock data."""

    def __init__(
        self, coordinator: MemeStockDataUpdateCoordinator, ticker: str, sensor_type: str, name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, ticker, sensor_type, name)
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["on", "off"]

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        if not self.available:
            return None

        stock_data = self.coordinator.data[self._ticker]
        value = stock_data.get(self._sensor_type, False)
        return "on" if value else "off"

    @property
    def is_on(self) -> bool:
        """Return true if the boolean sensor is on."""
        return self.native_value == "on"
