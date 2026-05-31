import logging
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.python.failure import Failure

from sorjin_scrapy.spiders.recursive import RecursiveSpider
from sorjin_scrapy.spiders.sitemap import SitemapSpider
from extractor.protocol import ContentExtractorProtocol


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


def run_crawler(
    output_path: str,
    content_extractor: ContentExtractorProtocol,
    urls_to_crawl: set[str],
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

    logger.info("Scheduling spiders for %d domain(s)", len(urls_to_crawl))
    for url_to_crawl in urls_to_crawl:
        sitemap_urls = SitemapSpider.get_sitemap_urls(url_to_crawl)
        if sitemap_urls:
            logger.info(
                "Using sitemap spider for %s (%d sitemap URL candidates)",
                url_to_crawl,
                len(sitemap_urls),
            )
            deferred = crawler_process.crawl(
                SitemapSpider,
                content_extractor=content_extractor,
                sitemap_urls=sitemap_urls,
            )
            deferred.addErrback(_log_crawl_failure)
        else:
            logger.info("Using recursive spider for %s", url_to_crawl)
            deferred = crawler_process.crawl(
                RecursiveSpider,
                url=url_to_crawl,
                content_extractor=content_extractor,
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
