import argparse
import logging
import time
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar

from extractor.text_extractor import ArticleExtractor

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from kurdish_scrapy.spiders.recursive import RecursiveSpider
from kurdish_scrapy.spiders.sitemap import SitemapSpider
from extractor.protocol import ContentExtractorProtocol


logger = logging.getLogger("benchmark")
logger.setLevel(logging.INFO)
logger.propagate = False

SUPPORTED_FEED_FORMATS = {
    ".csv": "csv",
    ".json": "json",
    ".jsonl": "jsonlines",
}

F = TypeVar("F", bound=Callable)


def log_spent_time(name: str | None = None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            label = name or func.__name__
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                logger.info("%s finished in %.2f seconds", label, elapsed)

        return wrapper  # type: ignore[return-value]

    return decorator


def _infer_feed_format(output_path: str) -> str:
    ext = Path(output_path).suffix.lower()
    feed_format = SUPPORTED_FEED_FORMATS.get(ext)
    if not feed_format:
        supported = ", ".join(SUPPORTED_FEED_FORMATS.keys())
        raise ValueError(
            f"Unsupported output extension '{ext}'. Use one of: {supported}"
        )
    return feed_format


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sitemap and recursive crawlers with timing logs."
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Domain to crawl",
    )
    parser.add_argument(
        "--sitemap",
        required=True,
        help="Sitemap spider output file path (supported: .csv, .json, .jsonl)",
    )
    parser.add_argument(
        "--recursive",
        required=True,
        help="Recursive spider output file path (supported: .csv, .json, .jsonl)",
    )
    parser.add_argument(
        "--benchmark-log",
        default="benchmark.log",
        help="Benchmark log file path (default: benchmark.log)",
    )
    return parser.parse_args()


def configure_benchmark_logger(log_path: str) -> None:
    logger.handlers.clear()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    logger.addHandler(file_handler)


def run_crawler(
    crawler_process: CrawlerProcess,
    output_path: str,
    content_extractor: ContentExtractorProtocol,
    spider_cls,
    **kwargs
):
    spider_name = spider_cls.__name__
    feed_format = _infer_feed_format(output_path)
    crawler_process.settings.set(
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
    crawler = crawler_process.create_crawler(spider_cls)
    start_time: float | None = None

    def _on_spider_opened(spider):
        nonlocal start_time
        start_time = time.perf_counter()
        logger.info("Starting %s -> %s", spider_name, output_path)

    def _on_spider_closed(spider, reason):
        if start_time is None:
            return
        elapsed = time.perf_counter() - start_time
        logger.info("%s finished in %.2f seconds (reason=%s)", spider_name, elapsed, reason)

    crawler.signals.connect(
        _on_spider_opened, signal=signals.spider_opened, weak=False
    )
    crawler.signals.connect(
        _on_spider_closed, signal=signals.spider_closed, weak=False
    )
    return crawler_process.crawl(crawler, content_extractor=content_extractor, **kwargs)


def main():
    args = parse_args()
    configure_benchmark_logger(args.benchmark_log)
    logger.info("Benchmark logs are written to %s", args.benchmark_log)
    crawler_process = CrawlerProcess(get_project_settings())
    total_start = time.perf_counter()

    sitemap_urls = SitemapSpider.get_sitemap_urls(args.domain)
    first_crawl = run_crawler(
        crawler_process=crawler_process,
        output_path=args.sitemap,
        content_extractor=ArticleExtractor(),
        spider_cls=SitemapSpider,
        sitemap_urls=sitemap_urls,
    )

    def _run_recursive(_):
        return run_crawler(
            crawler_process=crawler_process,
            output_path=args.recursive,
            content_extractor=ArticleExtractor(),
            spider_cls=RecursiveSpider,
            url=args.domain,
        )

    def _log_failure(failure):
        logger.error("Benchmark failed: %s", failure.getErrorMessage())
        return failure

    def _finish(result):
        total_elapsed = time.perf_counter() - total_start
        logger.info("total benchmark finished in %.2f seconds", total_elapsed)
        crawler_process.stop()
        return result

    first_crawl.addCallback(_run_recursive)
    first_crawl.addErrback(_log_failure)
    first_crawl.addBoth(_finish)
    crawler_process.start()


if __name__ == "__main__":
    main()
