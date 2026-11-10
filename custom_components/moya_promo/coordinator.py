"""Koordynator pobierający promocje ze strony MOYA express."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    BASE_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    NEWS_URL,
    REQUEST_TIMEOUT,
    STATUS_NONE,
    USER_AGENT,
)
from .parser import NewsItem, Promotion, is_promo_item, parse_article, parse_news_list

_LOGGER = logging.getLogger(__name__)


@dataclass
class MoyaData:
    """Wynik jednego odświeżenia."""

    promotion: Promotion | None
    status: str
    news: list[NewsItem] = field(default_factory=list)


class MoyaPromoCoordinator(DataUpdateCoordinator[MoyaData]):
    """Pobiera listę aktualności i parsuje najnowszą promocję."""

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
        self._article_cache: dict[str, Promotion] = {}

    async def _fetch(self, url: str) -> str:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            resp = await self._session.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "pl-PL,pl;q=0.9"},
            )
            resp.raise_for_status()
            return await resp.text()

    async def _async_update_data(self) -> MoyaData:
        try:
            list_html = await self._fetch(NEWS_URL)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Nie udało się pobrać {NEWS_URL}: {err}") from err

        news = parse_news_list(list_html, BASE_URL)
        promo_items = [item for item in news if is_promo_item(item)]
        if not promo_items:
            _LOGGER.debug("Brak promocji na liście aktualności (%d pozycji)", len(news))
            return MoyaData(promotion=None, status=STATUS_NONE, news=news)

        latest = promo_items[0]
        promo = self._article_cache.get(latest.url)
        if promo is None:
            try:
                article_html = await self._fetch(latest.url)
            except (aiohttp.ClientError, TimeoutError) as err:
                raise UpdateFailed(f"Nie udało się pobrać {latest.url}: {err}") from err
            promo = parse_article(article_html, latest.url, latest)
            # Trzymamy w pamięci tylko bieżący artykuł.
            self._article_cache = {latest.url: promo}
            _LOGGER.debug("Nowa promocja: %s", promo.as_dict())

        status = promo.status(dt_util.now().date())
        return MoyaData(promotion=promo, status=status, news=news)
