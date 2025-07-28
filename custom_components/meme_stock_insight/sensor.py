"""Sensor platform – v0.6.0: new entities & adaptive attributes."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE, UnitOfTime, Currency

from .const import (
    DOMAIN, VERSION, ATTRIBUTION,
    SENSOR_TYPES, ALL_SENSORS,
    SENSOR_TOP_N, SENSOR_DAYS_ACTIVE, SENSOR_SINCE_START, SENSOR_DYNAMIC_SR,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            add: AddEntitiesCallback) -> None:
    coord = hass.data[DOMAIN][entry.entry_id]
    add([MemeSensor(coord, sid, entry) for sid in ALL_SENSORS])


class MemeSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, sid, entry):
        super().__init__(coordinator)
        meta = SENSOR_TYPES[sid]
        self._sid = sid
        self._attr_unique_id = f"{entry.entry_id}_{sid}"
        self._attr_name = f"Meme Stock {meta['name']}"
        self._attr_icon = meta["icon"]
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_attribution = ATTRIBUTION

    # ───────────── state values ─────────────
    @property
    def native_value(self):
        d = self.coordinator.data or {}
        if self._sid == "mentions":
            return d.get("total_mentions")
        if self._sid == "sentiment":
            return d.get("average_sentiment")
        if self._sid == "trending":
            return d.get("trending_count")
        if self._sid in SENSOR_TOP_N:
            idx = SENSOR_TOP_N.index(self._sid)
            if idx < len(d.get("top_stocks", [])):
                return d["top_stocks"][idx]["display_name"]
            return "No data"
        if self._sid == "stage":
            return d.get("meme_stage")
        if self._sid == SENSOR_DAYS_ACTIVE:
            top = d.get("top_stocks", [])
            return top[0].get(SENSOR_DAYS_ACTIVE) if top else None
        if self._sid == SENSOR_SINCE_START:
            top = d.get("top_stocks", [])
            return top[0].get(SENSOR_SINCE_START) if top else None
        if self._sid == SENSOR_DYNAMIC_SR:
            return d.get("dynamic_subreddit")
        return None

    # ───────────── extras ─────────────
    @property
    def extra_state_attributes(self):
        d = self.coordinator.data or {}
        base = {"integration_version": VERSION, "last_updated": d.get("last_updated")}
        if self._sid == "mentions":
            base["stock_mentions"] = d.get("stock_mentions")
        elif self._sid == "sentiment":
            base["sentiment_distribution"] = d.get("sentiment_distribution")
        elif self._sid == "trending":
            base["trending_stocks"] = d.get("trending_stocks")
        elif self._sid in SENSOR_TOP_N:
            idx = SENSOR_TOP_N.index(self._sid)
            if idx < len(d.get("top_stocks", [])):
                base |= d["top_stocks"][idx]
        elif self._sid == "stage":
            base |= {
                "stage_key": d.get("meme_stage_key"),
                "stage_reason": d.get("stage_reason"),
            }
        return base
