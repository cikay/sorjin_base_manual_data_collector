import scrapy

from urllib.parse import urlparse

from extractor.extractor_registry import DOMAIN_TO_EXTRACTOR


class RecursiveSpider(scrapy.Spider):
    name = "recursive_spider"
    allowed_domains = list(DOMAIN_TO_EXTRACTOR.keys())
    start_urls = [f"https://{domain}" for domain in allowed_domains]

    custom_settings = {
        "DEPTH_LIMIT": 0,  # 0 = no depth limit (crawl entire site)
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",  # default, filters duplicates
    }

    def parse(self, response):
        domain = urlparse(response.url).netloc
        if domain.startswith("www."):
            domain = domain[4:]

        extractor_klass = DOMAIN_TO_EXTRACTOR[domain]

        extractor = extractor_klass()
        yield extractor.parse(response)

        # follow links recursively
        for href in response.css("a::attr(href)").getall():
            url = response.urljoin(href)
            url = url.split("#")[0]  # drop fragment
            if domain in url:  # stay within domain
                yield scrapy.Request(url, callback=self.parse, dont_filter=False)
