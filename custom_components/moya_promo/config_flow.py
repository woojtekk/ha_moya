"""Config flow i opcje integracji MOYA Promocje."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .const import (
    BASE_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    MAX_SCAN_INTERVAL_HOURS,
    MIN_SCAN_INTERVAL_HOURS,
    NAME,
    NEWS_URL,
    USER_AGENT,
)
from .parser import parse_news_list

INTERVAL_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=MIN_SCAN_INTERVAL_HOURS,
        max=MAX_SCAN_INTERVAL_HOURS,
        step=1,
        unit_of_measurement="h",
        mode=selector.NumberSelectorMode.SLIDER,
    )
)


class MoyaPromoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Dodawanie integracji z interfejsu."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                resp = await session.get(NEWS_URL, headers={"User-Agent": USER_AGENT})
                resp.raise_for_status()
                if not parse_news_list(await resp.text(), BASE_URL):
                    errors["base"] = "parse_error"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=NAME,
                    data={},
                    options={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_HOURS
                    ): INTERVAL_SELECTOR
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MoyaPromoOptionsFlow()


class MoyaPromoOptionsFlow(OptionsFlow):
    """Zmiana częstotliwości sprawdzania."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            )

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_SCAN_INTERVAL, default=current): INTERVAL_SELECTOR}
            ),
        )
