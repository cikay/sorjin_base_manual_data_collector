# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DataItem(scrapy.Item):
    text: str = scrapy.Field()
    title: str = scrapy.Field()
    url: str = scrapy.Field()
    publisher: str = scrapy.Field()
    word_count: int = scrapy.Field(serializer=int)
    lang: str = scrapy.Field()
    lang_score: float = scrapy.Field()
    source_type: str = scrapy.Field()
