"""Parser stron moyaexpress.pl (czysty Python, bez zależności od Home Assistant)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import html as html_lib
import re
from urllib.parse import urljoin, urlparse

WEEKDAYS_PL = ["pon", "wt", "śr", "czw", "pt", "sob", "nd"]

PROMO_KEYWORDS = ("rabat", "taniej", "promocj", "gr/l", "zniżk", "znizk", "kod")

_ANCHOR_RE = re.compile(
    r"<a\b[^>]*?href\s*=\s*[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S
)
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style|noscript)\b.*?</\1>", re.I | re.S)
_HEAD_RE = re.compile(r"<head\b.*?</head>", re.I | re.S)
_META_RE = re.compile(r"<meta\b[^>]*>", re.I)
_ATTR_RE = re.compile(r"([\w:-]+)\s*=\s*[\"']([^\"']*)[\"']")
_IMG_RE = re.compile(r"<img\b[^>]*?src\s*=\s*[\"']([^\"']+)[\"']", re.I)
_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_AMOUNT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*gr\s*/\s*l", re.I)
_CODE_RE = re.compile(
    r"kod(?:em)?\s+rabatow\w*\s*[:\-–]?\s*[\"„”']?([A-Za-z0-9]{3,20})\b", re.I
)
_RANGE_RE = re.compile(
    r"(\d{1,2})(?:\.(\d{1,2}))?(?:\.(\d{4}))?\s*(?:r\.)?\s*(?:-|–|—|do)\s*"
    r"(\d{1,2})\.(\d{1,2})\.(\d{4})"
)
_SINGLE_DAY_RE = re.compile(r"w\s+dniu\s+(\d{1,2})\.(\d{1,2})\.(\d{4})", re.I)
_WS_RE = re.compile(r"\s+")

_ARTICLE_START_MARKERS = ("Wróć do listy", "Wroc do listy")
_ARTICLE_END_MARKERS = ("Pozostałe aktualności", "Pozostale aktualnosci")
_IGNORED_IMAGE_PARTS = ("logo", "button", "kodrabatowy", "/images/games/")


@dataclass
class NewsItem:
    """Pozycja z listy aktualności."""

    title: str
    url: str
    published: date | None
    summary: str


@dataclass
class Promotion:
    """Dane promocji wyciągnięte z artykułu."""

    title: str
    url: str
    published: date | None = None
    amount: float | None = None
    code: str | None = None
    code_source: str | None = None
    start: date | None = None
    end: date | None = None
    image_url: str | None = None
    description: str | None = None
    terms_url: str | None = None
    stations_url: str | None = None

    def status(self, today: date) -> str:
        """Zwraca: active, upcoming, expired albo unknown."""
        if self.start is None or self.end is None:
            return "unknown"
        if today < self.start:
            return "upcoming"
        if today > self.end:
            return "expired"
        return "active"

    @property
    def days_text(self) -> str | None:
        """Czytelny opis dni, np. '06.11 – 08.11.2026 (pt, sob, nd)'."""
        if self.start is None or self.end is None:
            return None
        if self.start == self.end:
            return f"{self.start:%d.%m.%Y} ({WEEKDAYS_PL[self.start.weekday()]})"
        span = (self.end - self.start).days
        names = ""
        if 0 < span <= 13:
            names = " (" + ", ".join(
                WEEKDAYS_PL[(self.start.weekday() + i) % 7] for i in range(span + 1)
            ) + ")"
        start_fmt = "%d.%m" if self.start.year == self.end.year else "%d.%m.%Y"
        return f"{self.start.strftime(start_fmt)} – {self.end:%d.%m.%Y}{names}"

    def as_dict(self) -> dict:
        """Słownik z datami w ISO (do atrybutów)."""
        data = asdict(self)
        for key in ("published", "start", "end"):
            if data[key] is not None:
                data[key] = data[key].isoformat()
        data["days"] = self.days_text
        return data


def html_to_text(raw: str) -> str:
    """Usuwa tagi, encje i nadmiarowe spacje."""
    raw = _SCRIPT_RE.sub(" ", raw)
    raw = re.sub(r"<br\s*/?>", " ", raw, flags=re.I)
    raw = _TAG_RE.sub(" ", raw)
    raw = html_lib.unescape(raw).replace("\xa0", " ")
    return _WS_RE.sub(" ", raw).strip()


def _parse_date(text: str) -> date | None:
    match = _DATE_RE.search(text)
    if not match:
        return None
    day, month, year = (int(x) for x in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _same_site(url: str, base_url: str) -> bool:
    return urlparse(url).netloc.lower().removeprefix("www.") == urlparse(
        base_url
    ).netloc.lower().removeprefix("www.")


def parse_news_list(raw_html: str, base_url: str) -> list[NewsItem]:
    """Wyciąga pozycje z listy aktualności (od najnowszej)."""
    items: list[NewsItem] = []
    seen: set[str] = set()
    for href, inner in _ANCHOR_RE.findall(raw_html):
        url = urljoin(base_url + "/", html_lib.unescape(href.strip()))
        if not _same_site(url, base_url):
            continue
        path = urlparse(url).path.rstrip("/")
        if not path or path.startswith("/aktualnosci") or path.startswith("/uploads"):
            continue
        text = html_to_text(inner)
        date_match = _DATE_RE.search(text)
        if not date_match or url in seen:
            continue
        title = text[: date_match.start()].strip(" -–|")
        summary = text[date_match.end():]
        summary = re.split(r"Czytaj\s+więcej", summary, flags=re.I)[0].strip(" .")
        if not title:
            continue
        seen.add(url)
        items.append(
            NewsItem(
                title=title,
                url=url,
                published=_parse_date(date_match.group(0)),
                summary=summary,
            )
        )
    return items


def is_promo_item(item: NewsItem) -> bool:
    """Czy pozycja z listy wygląda na promocję."""
    haystack = f"{item.title} {item.summary}".lower()
    return any(word in haystack for word in PROMO_KEYWORDS)


def _meta_content(raw_html: str, name: str) -> str | None:
    for tag in _META_RE.findall(raw_html):
        attrs = {k.lower(): v for k, v in _ATTR_RE.findall(tag)}
        if name in (attrs.get("property"), attrs.get("name")):
            content = attrs.get("content")
            if content:
                return html_lib.unescape(content).strip()
    return None


def _article_region(body: str) -> str:
    """Wycina z HTML sam artykuł (bez stopki, gry i listy innych newsów)."""
    start = 0
    for marker in _ARTICLE_START_MARKERS:
        idx = body.find(marker)
        if idx != -1:
            start = idx
            break
    end = len(body)
    for marker in _ARTICLE_END_MARKERS:
        idx = body.find(marker, start)
        if idx != -1:
            end = idx
            break
    return body[start:end]


def _parse_range(text: str) -> tuple[date | None, date | None]:
    # Najpierw szukamy w okolicy "w dniach", potem w całym tekście.
    candidates = []
    lowered = text.lower()
    idx = lowered.find("w dniach")
    if idx != -1:
        candidates.append(text[idx : idx + 80])
    candidates.append(text)

    for chunk in candidates:
        match = _RANGE_RE.search(chunk)
        if match:
            s_day, s_month, s_year, e_day, e_month, e_year = match.groups()
            try:
                end = date(int(e_year), int(e_month), int(e_day))
                start_month = int(s_month) if s_month else end.month
                start_year = int(s_year) if s_year else end.year
                start = date(start_year, start_month, int(s_day))
                if start > end and not s_year:
                    start = date(start_year - 1, start_month, int(s_day))
                if start <= end:
                    return start, end
            except ValueError:
                pass

    match = _SINGLE_DAY_RE.search(text)
    if match:
        day, month, year = (int(x) for x in match.groups())
        try:
            single = date(year, month, day)
            return single, single
        except ValueError:
            pass
    return None, None


def parse_article(
    raw_html: str, url: str, list_item: NewsItem | None = None
) -> Promotion:
    """Wyciąga dane promocji z pojedynczego artykułu."""
    title = (
        _meta_content(raw_html, "og:title")
        or (list_item.title if list_item else None)
        or "Promocja MOYA"
    )
    description = _meta_content(raw_html, "og:description") or (
        list_item.summary if list_item else None
    )

    body = _HEAD_RE.sub(" ", raw_html)
    region_html = _article_region(body)
    text = html_to_text(region_html)

    promo = Promotion(title=title, url=url, description=description)
    region_start = body.find(region_html) if region_html else -1
    header_text = html_to_text(body[:region_start]) if region_start > 0 else ""
    # Data publikacji stoi tuż przed tytułem artykułu – bierzemy ostatnią datę z nagłówka.
    header_dates = _DATE_RE.findall(header_text[-300:])
    published_from_page = None
    if header_dates:
        d, m, y = (int(x) for x in header_dates[-1])
        try:
            published_from_page = date(y, m, d)
        except ValueError:
            published_from_page = None
    promo.published = (list_item.published if list_item else None) or published_from_page

    # Wysokość rabatu
    amount_match = _AMOUNT_RE.search(text) or _AMOUNT_RE.search(title)
    if amount_match:
        promo.amount = float(amount_match.group(1).replace(",", "."))

    # Kod rabatowy
    code_match = _CODE_RE.search(text)
    if code_match:
        promo.code = code_match.group(1)
        promo.code_source = "article"
    else:
        slug = urlparse(url).path.strip("/")
        if re.fullmatch(r"[A-Za-z0-9]{3,12}", slug or ""):
            promo.code = slug
            promo.code_source = "url"

    # Dni obowiązywania
    promo.start, promo.end = _parse_range(text)

    # Zdjęcie
    image = _meta_content(raw_html, "og:image")
    if not image:
        for src in _IMG_RE.findall(region_html):
            if not any(part in src.lower() for part in _IGNORED_IMAGE_PARTS):
                image = src
                break
    if image:
        promo.image_url = urljoin(url, image)

    # Regulamin i lista stacji (tylko z obszaru artykułu)
    for href, inner in _ANCHOR_RE.findall(region_html):
        link = urljoin(url, html_lib.unescape(href))
        lower = link.lower()
        if not lower.endswith(".pdf"):
            continue
        label = html_to_text(inner).lower()
        if "regulamin" in lower or "regulamin" in label:
            promo.terms_url = promo.terms_url or link
        elif "stacj" in lower or "lokalizac" in lower or "<img" in inner.lower():
            promo.stations_url = promo.stations_url or link

    return promo
