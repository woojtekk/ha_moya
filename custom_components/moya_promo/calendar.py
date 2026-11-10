"""Kalendarz z promocjami MOYA (wydarzenia całodniowe)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import MoyaConfigEntry
from .entity import MoyaEntity
from .parser import Promotion


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MoyaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MoyaPromoCalendar(entry.runtime_data, "calendar")])


def _to_event(promo: Promotion) -> CalendarEvent | None:
    """Promocja -> wydarzenie całodniowe (koniec jest wyłączny, więc +1 dzień)."""
    if promo.start is None or promo.end is None:
        return None

    summary = "MOYA"
    if promo.amount is not None:
        summary += f" −{promo.amount:g} gr/l"
    if promo.code:
        summary += f" (kod {promo.code})"

    lines = []
    if promo.code:
        lines.append(f"Kod rabatowy: {promo.code}")
    if promo.amount is not None:
        lines.append(f"Rabat: {promo.amount:g} gr/l")
    if promo.days_text:
        lines.append(f"Dni: {promo.days_text}")
    if promo.description:
        lines.append("")
        lines.append(promo.description)
    lines.append("")
    lines.append(f"Artykuł: {promo.url}")
    if promo.stations_url:
        lines.append(f"Lista stacji: {promo.stations_url}")
    if promo.terms_url:
        lines.append(f"Regulamin: {promo.terms_url}")

    return CalendarEvent(
        start=promo.start,
        end=promo.end + timedelta(days=1),
        summary=summary,
        description="\n".join(lines),
        uid=promo.url,
    )


def _overlaps(event: CalendarEvent, start: date, end: date) -> bool:
    return event.start < end and event.end > start


class MoyaPromoCalendar(MoyaEntity, CalendarEntity):
    """Wszystkie znane promocje jako wydarzenia kalendarza."""

    _attr_icon = "mdi:calendar-star"

    def _events(self) -> list[CalendarEvent]:
        data = self.coordinator.data
        if not data:
            return []
        events = [e for p in data.promotions if (e := _to_event(p)) is not None]
        return sorted(events, key=lambda e: e.start)

    @property
    def event(self) -> CalendarEvent | None:
        """Trwająca promocja, a jeśli żadna nie trwa – najbliższa przyszła."""
        today = dt_util.now().date()
        for event in self._events():
            if event.end > today:
                return event
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        start = dt_util.as_local(start_date).date()
        end = dt_util.as_local(end_date).date()
        if dt_util.as_local(end_date).time() != datetime.min.time():
            end += timedelta(days=1)
        return [e for e in self._events() if _overlaps(e, start, end)]
