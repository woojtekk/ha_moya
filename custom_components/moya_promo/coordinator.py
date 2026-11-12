"""Koordynator pobierający promocje ze strony MOYA express."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    BASE_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    EVENT_NEW_PROMOTION,
    MAX_ARTICLES_PER_UPDATE,
    MAX_STORED_PROMOTIONS,
    NEWS_URL,
    REQUEST_TIMEOUT,
    STATUS_EXPIRED,
    STATUS_NONE,
    STORAGE_VERSION,
    USER_AGENT,
)
from .parser import NewsItem, Promotion, is_promo_item, parse_article, parse_news_list

_LOGGER = logging.getLogger(__name__)


@dataclass
class MoyaData:
    """Wynik jednego odświeżenia."""

    promotion: Promotion | None
    status: str
    promotions: list[Promotion] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)


class MoyaPromoCoordinator(DataUpdateCoordinator[MoyaData]):
    """Pobiera listę aktualności, parsuje promocje i trzyma ich historię."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        hours = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=hours),
            config_entry=entry,
        )
        self._session = async_get_clientsession(hass)
        self._store: Store[dict] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        # url -> Promotion (artykuły się nie zmieniają, więc pobieramy je raz)
        self._promotions: dict[str, Promotion] = {}
        # URL ostatniej promocji, dla której wysłano zdarzenie EVENT_NEW_PROMOTION
        self._last_announced: str | None = None

    async def _async_setup(self) -> None:
        """Wczytanie zapisanej historii promocji."""
        stored = await self._store.async_load()
        if not stored:
            return
        self._last_announced = stored.get("last_announced")
        for raw in stored.get("promotions", []):
            try:
                promo = Promotion.from_dict(raw)
            except (TypeError, ValueError):
                continue
            if promo.url:
                self._promotions[promo.url] = promo
        _LOGGER.debug("Wczytano %d zapisanych promocji", len(self._promotions))

    async def _fetch(self, url: str) -> str:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            resp = await self._session.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "pl-PL,pl;q=0.9"},
            )
            resp.raise_for_status()
            return await resp.text()

    def _sorted_promotions(self) -> list[Promotion]:
        return sorted(self._promotions.values(), key=lambda p: p.sort_key, reverse=True)

    async def _async_save(self) -> None:
        promos = self._sorted_promotions()[:MAX_STORED_PROMOTIONS]
        self._promotions = {p.url: p for p in promos}
        await self._store.async_save(
            {
                "last_announced": self._last_announced,
                "promotions": [p.as_dict() for p in promos],
            }
        )

    @callback
    def async_announce(self, promo: Promotion, status: str, test: bool = False) -> None:
        """Wysyła zdarzenie o promocji – dopiero gdy HA w pełni wystartuje.

        Dzięki temu automatyzacje są już załadowane i nie przegapią zdarzenia,
        nawet jeśli promocja pojawiła się w trakcie restartu.
        """
        payload = {**promo.as_dict(), "status": status, "test": test}

        @callback
        def _fire(hass: HomeAssistant) -> None:
            hass.bus.async_fire(EVENT_NEW_PROMOTION, payload)
            _LOGGER.debug("Wysłano zdarzenie %s: %s", EVENT_NEW_PROMOTION, payload)

        async_at_started(self.hass, _fire)

    async def _async_update_data(self) -> MoyaData:
        try:
            list_html = await self._fetch(NEWS_URL)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Nie udało się pobrać {NEWS_URL}: {err}") from err

        news = parse_news_list(list_html, BASE_URL)
        promo_items = [item for item in news if is_promo_item(item)]

        latest: Promotion | None = None
        changed = False
        for index, item in enumerate(promo_items[:MAX_ARTICLES_PER_UPDATE]):
            promo = self._promotions.get(item.url)
            if promo is None:
                try:
                    article_html = await self._fetch(item.url)
                except (aiohttp.ClientError, TimeoutError) as err:
                    if index == 0:
                        raise UpdateFailed(
                            f"Nie udało się pobrać {item.url}: {err}"
                        ) from err
                    _LOGGER.warning("Pominięto artykuł %s: %s", item.url, err)
                    continue
                promo = parse_article(article_html, item.url, item)
                self._promotions[item.url] = promo
                changed = True
                _LOGGER.debug("Nowa promocja: %s", promo.as_dict())
            if index == 0:
                latest = promo

        if latest is None:
            _LOGGER.debug("Brak promocji na liście aktualności (%d pozycji)", len(news))
            status = STATUS_NONE
        else:
            status = latest.status(dt_util.now().date())
            # Nowa (jeszcze nie zgłoszona) i nie zakończona promocja -> zdarzenie.
            if latest.url != self._last_announced and status != STATUS_EXPIRED:
                self._last_announced = latest.url
                changed = True
                self.async_announce(latest, status)

        if changed:
            await self._async_save()

        return MoyaData(
            promotion=latest,
            status=status,
            promotions=self._sorted_promotions(),
            news=news,
        )
