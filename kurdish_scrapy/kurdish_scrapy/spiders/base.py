import scrapy
from typing import Optional
from urllib.parse import urlparse

from extractor.protocol import ContentExtractorProtocol


class BaseSpider(scrapy.Spider):
    custom_settings = {
        "DEPTH_LIMIT": 0,  # 0 = no depth limit (crawl entire site)
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",  # default, filters duplicates
    }

    def __init__(
        self,
        url: str,
        content_extractor: Optional[ContentExtractorProtocol] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.allowed_domains = [self.get_domain(url)]
        self.content_extractor = content_extractor
        self.start_urls = [url]

    def get_domain(self, url):
        parsed = urlparse(url)
        return parsed.netloc
