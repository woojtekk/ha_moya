"""Encja obrazu z banerem aktualnej promocji."""

from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import MoyaConfigEntry
from .coordinator import MoyaPromoCoordinator
from .entity import MoyaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MoyaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MoyaPromoImage(entry.runtime_data, "banner")])


class MoyaPromoImage(MoyaEntity, ImageEntity):
    """Baner promocji pobierany z artykułu (og:image)."""

    _attr_icon = "mdi:image"

    def __init__(self, coordinator: MoyaPromoCoordinator, key: str) -> None:
        MoyaEntity.__init__(self, coordinator, key)
        ImageEntity.__init__(self, coordinator.hass)
        self._set_url_from_data()

    def _set_url_from_data(self) -> None:
        promo = self.promotion
        url = promo.image_url if promo else None
        if url != self._attr_image_url:
            self._attr_image_url = url
            self._cached_image = None
            self._attr_image_last_updated = dt_util.utcnow()

    @property
    def available(self) -> bool:
        return super().available and self._attr_image_url is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._set_url_from_data()
        super()._handle_coordinator_update()
