"""Czujniki binarne: czy jest promocja, czy trwa dziś."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MoyaConfigEntry
from .const import STATUS_ACTIVE, STATUS_UNKNOWN, STATUS_UPCOMING
from .entity import MoyaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MoyaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            MoyaPromoAvailable(coordinator, "promo_available"),
            MoyaPromoActiveToday(coordinator, "promo_active_today"),
        ]
    )


class MoyaPromoAvailable(MoyaEntity, BinarySensorEntity):
    """Włączony, gdy promocja trwa albo dopiero się zacznie."""

    _attr_icon = "mdi:sale"

    @property
    def is_on(self) -> bool:
        return self.current_status in (STATUS_ACTIVE, STATUS_UPCOMING, STATUS_UNKNOWN)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs: dict[str, Any] = {"status": self.current_status}
        if self.promotion:
            attrs.update(self.promotion.as_dict())
        return attrs


class MoyaPromoActiveToday(MoyaEntity, BinarySensorEntity):
    """Włączony, gdy promocja obowiązuje dzisiaj."""

    _attr_icon = "mdi:gas-station"

    @property
    def is_on(self) -> bool:
        return self.current_status == STATUS_ACTIVE
