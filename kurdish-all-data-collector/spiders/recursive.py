import scrapy

from extractor.extractor_registry import DOMAIN_TO_EXTRACTOR
from extractor.url_extractor import UrlExtractor


class RecursiveSpider(scrapy.Spider):
    name = "recursive_spider"
    allowed_domains = list(DOMAIN_TO_EXTRACTOR.keys())
    start_urls = [f"https://{domain}" for domain in allowed_domains]

    custom_settings = {
        "DEPTH_LIMIT": 0,  # 0 = no depth limit (crawl entire site)
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",  # default, filters duplicates
    }

    def parse(self, response):
        if not UrlExtractor.content_type(response):
            return

        domain = UrlExtractor.get_domain(response.url)
        extractor_klass = DOMAIN_TO_EXTRACTOR[domain]

        extractor = extractor_klass()
        yield extractor.extract(response)

        # follow links recursively
        url_extractor = UrlExtractor()
        current_page_contained_urls = url_extractor.extract(response)
        for current_page_contained_url in current_page_contained_urls:
            yield scrapy.Request(
                current_page_contained_url, callback=self.parse, dont_filter=False
            )
