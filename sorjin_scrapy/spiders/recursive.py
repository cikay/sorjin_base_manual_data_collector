import scrapy

from extractor.url_extractor import UrlExtractor
from sorjin_scrapy.spiders.base import BaseSpider


class RecursiveSpider(BaseSpider):
    name = "recursive_spider"

    def parse(self, response):
        self.logger.debug("Processing %s", response.url)
        if not UrlExtractor.content_type(response):
            self.logger.debug("Skipped non-HTML response: %s", response.url)
            return

        result = self.content_extractor.extract(response.text, response.url)
        if result:
            self.logger.debug("Yielding article item: %s", response.url)
            yield result
        else:
            self.logger.debug("Extraction returned None: %s", response.url)

        # Follow internal links recursively when enabled.
        url_extractor = UrlExtractor()
        current_page_contained_urls = url_extractor.extract(response)
        for current_page_contained_url in current_page_contained_urls:
            yield scrapy.Request(
                current_page_contained_url,
                callback=self.parse,
                dont_filter=False,
            )
