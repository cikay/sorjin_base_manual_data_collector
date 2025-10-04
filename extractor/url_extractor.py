import re
from urllib.parse import urlparse

re_html = re.compile("text/html")


class UrlExtractor:

    IGNORE_FILE_EXTENSIONS = "(pdf)|(docx?)|(xlsx?)|(pptx?)|(epub)|(jpe?g)|(png)|(bmp)|(gif)|(tiff)|(webp)|(avi)|(mpe?g)|(mov)|(qt)|(webm)|(ogg)|(midi)|(mid)|(mp3)|(wav)|(zip)|(rar)|(exe)|(apk)|(css)"

    IGNORE_REGEX = "(mail[tT]o)|([jJ]avascript)|(tel)|(fax)"

    def extract(self, response) -> set[str]:
        urls = set()
        domain = self.get_domain(response.url)
        for href in response.css("a::attr(href)").getall():
            url = response.urljoin(href)
            url = url.split("#")[0]  # drop fragment
            if self.should_request(url, domain):
                urls.add(url)

        return urls

    @staticmethod
    def content_type(response):
        return re_html.match(response.headers.get("Content-Type").decode("utf-8"))

    @classmethod
    def should_request(cls, url, domain):
        return (
            domain in url
            and not cls._is_media_url(url)
            and not cls._is_matched_ignore_regex(url)
        )

    @staticmethod
    def get_domain(url):
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    @classmethod
    def _is_media_url(cls, url: str):
        matched = re.match(
            r".*\." + cls.IGNORE_FILE_EXTENSIONS + r"$",
            url,
            re.IGNORECASE,
        )
        is_matched = bool(matched)
        if is_matched:
            print("It is media url")

        return is_matched

    @classmethod
    def _is_matched_ignore_regex(cls, url):
        matched = re.search(cls.IGNORE_REGEX, url)
        return bool(matched)
