"""Integracja MOYA Promocje dla Home Assistant."""

from __future__ import annotations

from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SERVICE_ANNOUNCE_CURRENT, STORAGE_VERSION
from .coordinator import MoyaPromoCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.IMAGE,
    Platform.SENSOR,
]

type MoyaConfigEntry = ConfigEntry[MoyaPromoCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MoyaConfigEntry) -> bool:
    """Konfiguracja wpisu."""
    coordinator = MoyaPromoCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    @callback
    def _midnight(_now: datetime) -> None:
        # Status promocji (nadchodzi / trwa / zakończona) zmienia się o północy.
        coordinator.async_update_listeners()

    entry.async_on_unload(
        async_track_time_change(hass, _midnight, hour=0, minute=0, second=30)
    )

    async def _announce_current(call: ServiceCall) -> None:
        """Ręczne wysłanie zdarzenia o bieżącej promocji (test powiadomień)."""
        data = coordinator.data
        if not data or data.promotion is None:
            raise HomeAssistantError("Brak bieżącej promocji MOYA.")
        promo = data.promotion
        coordinator.async_announce(
            promo, promo.status(dt_util.now().date()), test=True
        )

    hass.services.async_register(DOMAIN, SERVICE_ANNOUNCE_CURRENT, _announce_current)
    entry.async_on_unload(
        lambda: hass.services.async_remove(DOMAIN, SERVICE_ANNOUNCE_CURRENT)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MoyaConfigEntry) -> bool:
    """Usunięcie wpisu."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: MoyaConfigEntry) -> None:
    """Usunięcie zapisanej historii promocji razem z integracją."""
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()


async def _async_reload(hass: HomeAssistant, entry: MoyaConfigEntry) -> None:
    """Przeładowanie po zmianie opcji (np. częstotliwości)."""
    await hass.config_entries.async_reload(entry.entry_id)
