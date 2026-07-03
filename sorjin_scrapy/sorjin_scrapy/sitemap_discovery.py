import gzip
import io
import re
from urllib.parse import urljoin, urlparse

import requests
from requests import Response
from requests.exceptions import RequestException

from sorjin_scrapy.settings import SITEMAP_PATTERNS


SITEMAP_REGEX = re.compile(r"Sitemap:\s([^\r\n#]*)", re.MULTILINE)


def get_sitemap_urls(url: str) -> set[str]:
    sitemap_urls_from_robots = get_sitemap_urls_from_robots(url)
    if sitemap_urls_from_robots:
        return sitemap_urls_from_robots
    return get_sitemap_urls_from_patterns(url)


def get_sitemap_urls_from_robots(url: str) -> set[str]:
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    try:
        response = requests.get(url=robots_url, timeout=10)
    except RequestException:
        response = None

    if not response or response.status_code != 200:
        return set()

    sitemap_urls: set[str] = set()
    for sitemap_url in SITEMAP_REGEX.findall(response.text):
        normalized_sitemap_url = urljoin(robots_url, sitemap_url.strip())
        if _is_same_domain(url, normalized_sitemap_url):
            probed = _probe_sitemap_url(normalized_sitemap_url)
            if probed:
                sitemap_urls.add(probed)
    return sitemap_urls


def get_sitemap_urls_from_patterns(url: str) -> set[str]:
    sitemap_urls: set[str] = set()
    for sitemap_path in SITEMAP_PATTERNS:
        url_sitemap = urljoin(url, sitemap_path)
        probed = _probe_sitemap_url(url_sitemap)
        if probed:
            sitemap_urls.add(probed)
    return sitemap_urls


def _is_same_domain(base_url: str, candidate_url: str) -> bool:
    base_host = (urlparse(base_url).hostname or "").lower().removeprefix("www.")
    candidate_host = (urlparse(candidate_url).hostname or "").lower().removeprefix(
        "www."
    )
    return base_host == candidate_host


def _probe_sitemap_url(url: str) -> str | None:
    """
    Fetch a sitemap candidate URL and return the final resolved URL only if it
    looks like an actual sitemap (not an HTML page such as `/latest`).
    """
    headers = {
        "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
        "User-Agent": "Mozilla/5.0 (compatible; SorjinScrapy/1.0)",
    }
    try:
        response = requests.get(
            url=url, timeout=10, headers=headers, allow_redirects=True
        )
    except RequestException:
        return None

    if response.status_code != 200:
        return None

    if not _is_sitemap_response(response):
        return None

    return response.url


def _is_sitemap_response(response: Response) -> bool:
    content_type = (response.headers.get("Content-Type", "") or "").lower()
    response_url = (getattr(response, "url", "") or "").lower()

    preview_bytes = (getattr(response, "content", b"") or b"")[:8192]
    if preview_bytes.startswith(b"\x1f\x8b"):
        try:
            with gzip.GzipFile(
                fileobj=io.BytesIO(getattr(response, "content", b"") or b"")
            ) as gz:
                preview_bytes = gz.read(8192)
        except OSError:
            preview_bytes = b""

    body_preview = preview_bytes.decode("utf-8", errors="ignore").lstrip().lower()
    has_sitemap_root_tag = "<urlset" in body_preview or "<sitemapindex" in body_preview
    if has_sitemap_root_tag:
        return True

    # Fall back to URL/content-type heuristics for gzipped sitemaps (Scrapy can parse them),
    # but avoid obvious HTML pages.
    if "html" in content_type:
        return False

    looks_like_sitemap_url = "sitemap" in response_url and response_url.endswith(
        (".xml", ".xml.gz", ".gz")
    )
    looks_like_xmlish = (
        "xml" in content_type
        or "gzip" in content_type
        or "x-gzip" in content_type
        or content_type == ""
    )
    return looks_like_sitemap_url and looks_like_xmlish

