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
        domain = self.get_domain(response.url)
        extractor_klass = DOMAIN_TO_EXTRACTOR[domain]

        extractor = extractor_klass()
        yield extractor.extract(response)

        # follow links recursively
        for href in response.css("a::attr(href)").getall():
            url = response.urljoin(href)
            url = url.split("#")[0]  # drop fragment

            if self.should_request(url, domain):
                yield scrapy.Request(url, callback=self.parse, dont_filter=False)

    def should_request(self, url, domain):
        return domain in url and not self.is_media_url(url)

    def get_domain(self, url):
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    def is_media_url(self, url: str):
        parsed = urlparse(url)
        path = parsed.path.lower()
        path = path.removesuffix("/")
        return path.endswith(
            (
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".svg",
                ".webp",
                ".mp4",
                ".avi",
                ".mov",
                ".mkv",
                ".mp3",
                ".wav",
                ".ogg",
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".zip",
                ".rar",
            )
        )
