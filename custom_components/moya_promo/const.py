"""Stałe integracji MOYA Promocje."""

from __future__ import annotations

DOMAIN = "moya_promo"
NAME = "MOYA Promocje"
MANUFACTURER = "MOYA express (Anwim S.A.)"

BASE_URL = "https://moyaexpress.pl"
NEWS_URL = f"{BASE_URL}/aktualnosci"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL_HOURS = 4
MIN_SCAN_INTERVAL_HOURS = 1
MAX_SCAN_INTERVAL_HOURS = 24

REQUEST_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 HomeAssistant-moya_promo"
)

STATUS_ACTIVE = "active"
STATUS_UPCOMING = "upcoming"
STATUS_EXPIRED = "expired"
STATUS_UNKNOWN = "unknown"
STATUS_NONE = "none"
STATUSES = [STATUS_ACTIVE, STATUS_UPCOMING, STATUS_EXPIRED, STATUS_UNKNOWN, STATUS_NONE]
