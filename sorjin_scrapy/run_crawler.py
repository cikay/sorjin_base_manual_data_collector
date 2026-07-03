import logging
from pathlib import Path

import requests
from requests.exceptions import RequestException
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.python.failure import Failure

from sorjin_scrapy.spiders.recursive import RecursiveSpider
from sorjin_scrapy.spiders.sitemap import SitemapSpider
from sorjin_scrapy.settings import ALLOWED_LANGS
from extractor.protocol import ContentExtractorProtocol
from extractor.lang_url_filter import discover_lang_prefixes, build_url_filter


SUPPORTED_FEED_FORMATS = {
    ".csv": "csv",
    ".json": "json",
    ".jsonl": "jsonlines",
}

logger = logging.getLogger(__name__)


def _infer_feed_format(output_path: str) -> str:
    ext = Path(output_path).suffix.lower()
    feed_format = SUPPORTED_FEED_FORMATS.get(ext)
    if not feed_format:
        supported = ", ".join(SUPPORTED_FEED_FORMATS.keys())
        raise ValueError(
            f"Unsupported output extension '{ext}'. Use one of: {supported}"
        )
    return feed_format


def get_root_page_lang(url: str, content_extractor: ContentExtractorProtocol) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        resp = requests.get(url, timeout=10, headers=headers)
    except RequestException:
        return None
    result = content_extractor.extract(resp.text, url)
    return result.get("lang") if result else None


def _build_url_filter_for_domain(url: str, content_extractor: ContentExtractorProtocol):
    prefixes = discover_lang_prefixes(url)
    if prefixes is None:
        logger.info("Skipping %s — homepage unreachable", url)
        return None, True
    if prefixes:
        url_filter = build_url_filter(prefixes)
        logger.info("URL filter for %s: %s", url, url_filter.pattern)
        return url_filter, False
    # No prefix found: scrape the root page and detect its language
    lang = get_root_page_lang(url, content_extractor)
    if lang and lang in ALLOWED_LANGS:
        logger.info(f"Root page is target language for {url} — crawling entire site")
        return None, False

    logger.info(f"Skipping {url} — root page is {lang} and not a target language")
    return None, True


def run_crawler(
    output_path: str,
    content_extractor: ContentExtractorProtocol,
    urls: list[str],
    log_file: str = "logs/crawler.log",
    log_level: str = "INFO",
) -> None:
    feed_format = _infer_feed_format(output_path)
    settings = get_project_settings()
    settings.set(
        "FEEDS",
        {
            output_path: {
                "format": feed_format,
                "encoding": "utf-8",
                "overwrite": False,
            }
        },
        priority="cmdline",
    )
    settings.set("LOG_ENABLED", True, priority="cmdline")
    settings.set("LOG_FILE", log_file, priority="cmdline")
    settings.set("LOG_LEVEL", log_level.upper(), priority="cmdline")
    crawler_process = CrawlerProcess(settings)
    crawl_failures: list[Failure] = []

    def _log_crawl_failure(failure: Failure) -> Failure:
        crawl_failures.append(failure)
        logger.error(
            "Crawler deferred failed: %s",
            failure.getErrorMessage(),
            exc_info=(
                failure.type,
                failure.value,
                failure.getTracebackObject(),
            ),
        )
        return failure

    logger.info("Scheduling spiders for %d domain(s)", len(urls))
    for url in urls:
        url_filter, skip = _build_url_filter_for_domain(url, content_extractor)
        if skip:
            continue
        sitemap_urls = SitemapSpider.get_sitemap_urls(url)
        if sitemap_urls:
            logger.info(
                "Using sitemap spider for %s (%d sitemap URL candidates)",
                url,
                len(sitemap_urls),
            )
            deferred = crawler_process.crawl(
                SitemapSpider,
                content_extractor=content_extractor,
                sitemap_urls=sitemap_urls,
                url_filter=url_filter,
            )
            deferred.addErrback(_log_crawl_failure)
        else:
            logger.info("Using recursive spider for %s", url)
            deferred = crawler_process.crawl(
                RecursiveSpider,
                url=url,
                content_extractor=content_extractor,
                url_filter=url_filter,
            )
            deferred.addErrback(_log_crawl_failure)

    try:
        crawler_process.start()
    except Exception as e:
        logger.exception(f"Crawler process crashed: {e}")
        raise

    if crawl_failures:
        logger.error("Crawler finished with %d deferred failure(s)", len(crawl_failures))
        raise RuntimeError(
            f"Crawler finished with {len(crawl_failures)} deferred failure(s)."
        )
