from scrapy.spiders import SitemapSpider as BaseSitemapSpider

from extractor.url_extractor import UrlExtractor
from sorjin_scrapy import sitemap_discovery


class SitemapSpider(BaseSitemapSpider):
    name = "sitemap_spider"

    def __init__(self, content_extractor, sitemap_urls, url_filter=None, *args, **kwargs):
        # Set sitemap_rules before super().__init__ so Scrapy compiles _cbs from it
        if url_filter is not None:
            self.sitemap_rules = [(url_filter.pattern, "parse")]
        else:
            self.sitemap_rules = [("", "parse")]
        super().__init__(*args, **kwargs)
        self.content_extractor = content_extractor
        self.sitemap_urls = sitemap_urls

    def parse(self, response):
        self.logger.debug("Processing %s", response.url)
        if not UrlExtractor.content_type(response):
            self.logger.debug("Skipped non-HTML response: %s", response.url)
            return

        result = self.content_extractor.extract(response.text, response.url)
        if result:
            yield result

    @classmethod
    def get_sitemap_urls(cls, url):
        return sitemap_discovery.get_sitemap_urls(url)
