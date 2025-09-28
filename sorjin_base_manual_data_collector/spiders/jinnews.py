import scrapy


class JinnewsSpider(scrapy.Spider):
    name = "jinnews"
    allowed_domains = ["jinnews.net"]
    start_urls = ["https://jinnews.net/kr/HEMU-NUCE?page=1"]

    def parse(self, response):
        articles = response.css(".table.table-striped.table-sm a::attr(href)").getall()
        for article in articles:
            article_url = f"https://jinnews.net{article}"
            yield scrapy.Request(article_url, callback=self.parse_article)

        next_page_endpoint = response.css('a[aria-label="Paştir"]::attr(href)').get()
        next_page = f"https://jinnews.net/kr/HEMU-NUCE{next_page_endpoint}"
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse)

    def parse_article(self, response):
        title = response.css(".post-entry.single-post-box h2::text").get()
        text_array = response.css(".post-entry.single-post-box .body ::text").getall()

        yield {
            "title": title,
            "content": "\n".join([text.strip() for text in text_array if text.strip()]),
            "url": response.url,
        }
