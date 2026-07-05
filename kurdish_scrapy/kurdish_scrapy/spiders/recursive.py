import scrapy

from extractor.url_extractor import UrlExtractor
from kurdish_scrapy.settings import ALLOWED_LANGS
from kurdish_scrapy.spiders.base import BaseSpider


class RecursiveSpider(BaseSpider):
    name = "recursive_spider"

    def __init__(self, url, content_extractor=None, url_filter=None, *args, **kwargs):
        super().__init__(url=url, content_extractor=content_extractor, *args, **kwargs)
        self.url_filter = url_filter

    def parse(self, response):
        self.logger.debug("Processing %s", response.url)
        if not UrlExtractor.content_type(response):
            self.logger.debug("Skipped non-HTML response: %s", response.url)
            return

        result = self.content_extractor.extract(response.text, response.url)
        if result:
            self.logger.debug("Yielding article item: %s", response.url)
            yield result

        # When no URL filter was set (language probe failed), only follow links
        # from target-language pages so non-target-language sites self-terminate.
        if self.url_filter is None and result and result.get("lang") not in ALLOWED_LANGS:
            return

        url_extractor = UrlExtractor()
        for url in url_extractor.extract(response):
            if self.url_filter is None or self.url_filter.search(url):
                yield scrapy.Request(url, callback=self.parse, dont_filter=False)
