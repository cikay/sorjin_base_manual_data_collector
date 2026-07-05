import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests
from requests.exceptions import RequestException

from extractor.text_extractor import ArticleExtractor
from run_crawler import run_crawler

logger = logging.getLogger(__name__)

_RESOLVE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RecursiveSpider with output file."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path (supported: .csv, .json, .jsonl)",
    )
    parser.add_argument(
        "--log-file",
        default=f"logs/crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        help="Path to log file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def load_urls(domains_file: Path) -> list[str]:
    if not domains_file.is_file():
        raise FileNotFoundError(f"Domains file not found: {domains_file}")

    seen: set[str] = set()
    urls: list[str] = []
    for entry in json.loads(domains_file.read_text(encoding="utf-8")):
        if isinstance(entry, str):
            url = entry.strip().rstrip("/")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def _normalize_domain(url: str) -> str:
    """Reduce a URL to scheme://host, dropping a leading ``www.`` and any
    trailing slash so equivalent domains collapse to one entry."""
    parts = urlsplit(url)
    host = parts.netloc
    if host.lower().startswith("www."):
        host = host[4:]
    return urlunsplit((parts.scheme, host, "", "", "")).rstrip("/")


def _resolve_one(url: str) -> str:
    """Follow redirects for ``url`` and return its normalized final domain.
    Falls back to the normalized original URL if the request fails."""
    try:
        resp = requests.get(
            url, timeout=10, headers=_RESOLVE_HEADERS, allow_redirects=True
        )
        final = _normalize_domain(resp.url)
        if final != _normalize_domain(url):
            logger.info("Resolved %s -> %s", url, final)
        return final
    except RequestException as exc:
        logger.warning("Could not resolve %s (%s); keeping original", url, exc)
        return _normalize_domain(url)


def resolve_redirected_domains(urls: list[str]) -> list[str]:
    """Request every domain, collect the (possibly redirected) final domains,
    and return a deduplicated list. Kurdish news domains change often, so the
    URLs in ``domains.json`` may now redirect elsewhere."""
    seen: set[str] = set()
    resolved: list[str] = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        for final in executor.map(_resolve_one, urls):
            if final and final not in seen:
                seen.add(final)
                resolved.append(final)
    logger.info(
        "Resolved %d domain(s) down to %d unique domain(s)", len(urls), len(resolved)
    )
    return resolved


def configure_logging(log_file: str, log_level: str) -> None:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
        force=True,
    )


def main():
    args = parse_args()
    configure_logging(args.log_file, args.log_level)
    logger = logging.getLogger(__name__)

    def handle_uncaught(exc_type, exc_value, exc_traceback):
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_uncaught

    urls = load_urls(Path("domains.json"))
    normalized_urls = resolve_redirected_domains(urls)
    logger.info(
        "Starting crawler for %d domain(s). Output: %s, log file: %s",
        len(normalized_urls),
        args.output,
        args.log_file,
    )
    try:
        run_crawler(
            output_path=args.output,
            content_extractor=ArticleExtractor(),
            urls=normalized_urls,
            log_file=args.log_file,
            log_level=args.log_level,
        )
    except Exception:
        logger.exception("Crawler run failed")
        raise
    logger.info("Crawler completed successfully")


if __name__ == "__main__":
    main()
