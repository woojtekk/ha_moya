"""Sensory: wysokość rabatu, kod, dni, daty, status, tytuł."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MoyaConfigEntry
from .const import STATUSES
from .entity import MoyaEntity
from .parser import Promotion


@dataclass(frozen=True, kw_only=True)
class MoyaSensorDescription(SensorEntityDescription):
    """Opis sensora z funkcją wyciągającą wartość."""

    value_fn: Callable[[Promotion], Any]
    attrs_fn: Callable[[Promotion], dict[str, Any]] | None = None


SENSORS: tuple[MoyaSensorDescription, ...] = (
    MoyaSensorDescription(
        key="discount",
        icon="mdi:cash-minus",
        native_unit_of_measurement="gr/l",
        suggested_display_precision=0,
        value_fn=lambda p: p.amount,
    ),
    MoyaSensorDescription(
        key="code",
        icon="mdi:ticket-percent",
        value_fn=lambda p: p.code,
        attrs_fn=lambda p: {"source": p.code_source},
    ),
    MoyaSensorDescription(
        key="days",
        icon="mdi:calendar-range",
        value_fn=lambda p: p.days_text,
    ),
    MoyaSensorDescription(
        key="start_date",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda p: p.start,
    ),
    MoyaSensorDescription(
        key="end_date",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda p: p.end,
    ),
    MoyaSensorDescription(
        key="title",
        icon="mdi:newspaper-variant-outline",
        value_fn=lambda p: p.title,
        attrs_fn=lambda p: {
            "url": p.url,
            "description": p.description,
            "published": p.published.isoformat() if p.published else None,
            "terms_url": p.terms_url,
            "stations_url": p.stations_url,
            "image_url": p.image_url,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MoyaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [MoyaSensor(coordinator, d) for d in SENSORS]
    entities.append(MoyaStatusSensor(coordinator, "status"))
    async_add_entities(entities)


class MoyaSensor(MoyaEntity, SensorEntity):
    """Sensor oparty na opisie."""

    entity_description: MoyaSensorDescription

    def __init__(self, coordinator, description: MoyaSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | float | date | None:
        promo = self.promotion
        return self.entity_description.value_fn(promo) if promo else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        promo = self.promotion
        fn = self.entity_description.attrs_fn
        return fn(promo) if promo and fn else None


class MoyaStatusSensor(MoyaEntity, SensorEntity):
    """Status promocji: active / upcoming / expired / unknown / none."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUSES
    _attr_icon = "mdi:list-status"

    @property
    def native_value(self) -> str:
        return self.current_status
