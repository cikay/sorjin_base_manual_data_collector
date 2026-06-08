"""Discover language-specific URL sections by scanning a site's homepage."""

import re
import unicodedata
import logging
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# BCP-47 subtags, common language names, and URL path variants
HREFLANG = frozenset([
    "ku", "kmr", "kurdish", "kurmanji", "kurmanci", "kurdi", "kirmancki",
    "ckb", "sorani",
    "zza", "diq", "zazaki",
])

_LANG_CONTAINER_RE = re.compile(r"lang|ziman", re.IGNORECASE)


def _normalize(text: str) -> str:
    text = text.lower().replace("ı", "i")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


@dataclass
class _ParseState:
    hreflang_links: list[str] = field(default_factory=list)
    a_hreflang_links: list[str] = field(default_factory=list)
    anchor_hrefs: list[str] = field(default_factory=list)
    lang_menu_links: list[tuple[str, str]] = field(default_factory=list)
    html_lang: str = ""
    in_head: bool = True
    lang_menu_depth: int = 0
    lang_menu_tag_stack: list[str] = field(default_factory=list)
    current_a_href: str | None = None
    current_a_texts: list[str] = field(default_factory=list)


class _PageParser(HTMLParser):
    def __init__(self, state: _ParseState):
        super().__init__()
        self._state = state

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "html":
            self._state.html_lang = d.get("lang", "").lower()
            return
        if tag == "body":
            self._state.in_head = False

        id_class = f"{d.get('id', '')} {d.get('class', '')}"
        if _LANG_CONTAINER_RE.search(id_class):
            self._state.lang_menu_depth += 1
            self._state.lang_menu_tag_stack.append(tag)

        if self._state.in_head and tag == "link":
            if d.get("rel") == "alternate":
                hreflang = (d.get("hreflang") or "").lower()
                href = d.get("href") or ""
                if href and hreflang.split("-")[0] in HREFLANG:
                    self._state.hreflang_links.append(href)
        elif tag == "a":
            href = d.get("href", "")
            self._state.anchor_hrefs.append(href)
            hreflang = (d.get("hreflang") or "").lower()
            if href and hreflang and _normalize(hreflang.split("-")[0]) in HREFLANG:
                self._state.a_hreflang_links.append(href)
            if self._state.lang_menu_depth > 0:
                self._state.current_a_href = href
                self._state.current_a_texts = []

    def handle_endtag(self, tag):
        if tag == "a":
            if self._state.current_a_href is not None and self._state.current_a_texts:
                self._state.lang_menu_links.append(
                    (self._state.current_a_href, " ".join(self._state.current_a_texts))
                )
            self._state.current_a_href = None
            self._state.current_a_texts = []
            return
        if self._state.lang_menu_tag_stack and self._state.lang_menu_tag_stack[-1] == tag:
            self._state.lang_menu_tag_stack.pop()
            self._state.lang_menu_depth = max(0, self._state.lang_menu_depth - 1)

    def handle_data(self, data):
        if self._state.current_a_href is not None:
            text = data.strip()
            if text:
                self._state.current_a_texts.append(text)


def _lang_prefix_from_url(url: str, base_url: str) -> str | None:
    """Return the URL prefix if the first path segment is a language keyword, else None."""
    base_host = urlparse(base_url).netloc.lower().removeprefix("www.")
    parsed = urlparse(url)
    if parsed.netloc.lower().removeprefix("www.") != base_host:
        return None
    segments = [s for s in parsed.path.split("/") if s]
    if segments and _normalize(segments[0]) in HREFLANG:
        return f"{parsed.scheme}://{parsed.netloc}/{segments[0]}/"
    return None


def _prefixes_from_head_hreflang(state: _ParseState, base_url: str) -> list[str]:
    return [urljoin(base_url, href) for href in state.hreflang_links]


def _prefixes_from_anchor_hreflang(state: _ParseState, base_url: str, origin: str) -> list[str]:
    seen: set[str] = set()
    prefixes: list[str] = []
    for href in state.a_hreflang_links:
        prefix = _lang_prefix_from_url(urljoin(base_url, href), origin) or urljoin(base_url, href)
        if prefix not in seen:
            seen.add(prefix)
            prefixes.append(prefix)
    return prefixes


def _prefixes_from_lang_menu(state: _ParseState, base_url: str, origin: str) -> list[str]:
    seen: set[str] = set()
    prefixes: list[str] = []
    for href, text in state.lang_menu_links:
        if _normalize(text) not in HREFLANG:
            continue
        abs_url = urljoin(base_url, href) if href else base_url
        prefix = _lang_prefix_from_url(abs_url, origin) or abs_url
        if prefix not in seen:
            seen.add(prefix)
            prefixes.append(prefix)
    return prefixes


def _prefixes_from_link_scan(state: _ParseState, base_url: str, origin: str) -> list[str]:
    seen: set[str] = set()
    prefixes: list[str] = []
    for href in state.anchor_hrefs:
        prefix = _lang_prefix_from_url(urljoin(base_url, href), origin)
        if prefix and prefix not in seen:
            seen.add(prefix)
            prefixes.append(prefix)
    return prefixes


def discover_lang_prefixes(url: str) -> list[str] | None:
    """Fetch url and return URL prefixes for target-language sections.

    Returns a non-empty list when specific prefixes are found, an empty list
    when the page is reachable but no prefix was identified, or None when the
    page could not be fetched (caller should skip the domain).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        resp = requests.get(url, timeout=10, headers=headers)
    except RequestException as exc:
        logger.warning("Language probe failed for %s: %s", url, exc)
        return None

    state = _ParseState()
    _PageParser(state).feed(resp.text)

    prefixes = _prefixes_from_head_hreflang(state, resp.url)
    if prefixes:
        logger.info("hreflang links: %d prefix(es) for %s: %s", len(prefixes), url, prefixes)
        return prefixes

    prefixes = _prefixes_from_anchor_hreflang(state, resp.url, url)
    if prefixes:
        logger.info("anchor hreflang: %d prefix(es) for %s: %s", len(prefixes), url, prefixes)
        return prefixes

    prefixes = _prefixes_from_lang_menu(state, resp.url, url)
    if prefixes:
        logger.info("lang menu scan: %d prefix(es) for %s: %s", len(prefixes), url, prefixes)
        return prefixes

    prefixes = _prefixes_from_link_scan(state, resp.url, url)
    if prefixes:
        logger.info("link scan: %d prefix(es) for %s: %s", len(prefixes), url, prefixes)
        return prefixes

    logger.info("No language prefix found for %s", url)
    return []


def build_url_filter(prefixes: list[str]) -> re.Pattern | None:
    """Build a compiled regex filter from URL prefixes. Returns None if empty."""
    if not prefixes:
        return None
    return re.compile("|".join(re.escape(p.rstrip("/")) + r"/?" for p in prefixes))
