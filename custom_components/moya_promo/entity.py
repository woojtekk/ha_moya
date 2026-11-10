"""Wspólna klasa bazowa encji."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import BASE_URL, DOMAIN, MANUFACTURER, NAME, STATUS_NONE
from .coordinator import MoyaPromoCoordinator
from .parser import Promotion


class MoyaEntity(CoordinatorEntity[MoyaPromoCoordinator]):
    """Encja powiązana z urządzeniem-usługą MOYA."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MoyaPromoCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=BASE_URL,
        )

    @property
    def promotion(self) -> Promotion | None:
        data = self.coordinator.data
        return data.promotion if data else None

    @property
    def current_status(self) -> str:
        """Status liczony na bieżąco (zmienia się o północy bez pobierania strony)."""
        promo = self.promotion
        if promo is None:
            return STATUS_NONE
        return promo.status(dt_util.now().date())
