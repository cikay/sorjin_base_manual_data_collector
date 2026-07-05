# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from scrapy.exceptions import DropItem


from kurdish_scrapy.settings import ALLOWED_LANGS, TEXT_MIN_WORD_COUNT


class LenPipeline:
    def process_item(self, item, spider):
        if item["word_count"] < TEXT_MIN_WORD_COUNT:
            spider.logger.debug(
                "Dropping short text (%s words, min=%s): %s",
                item["word_count"],
                TEXT_MIN_WORD_COUNT,
                item.get("url", "<unknown-url>"),
            )
            raise DropItem("Text is too short")

        return item


class LanguagePipeline:
    def process_item(self, item, spider):
        lang = item["lang"]
        if lang not in ALLOWED_LANGS:
            spider.logger.debug(
                "Dropping text in disallowed language (%s): %s",
                lang,
                item.get("url", "<unknown-url>"),
            )
            raise DropItem(f"Language not in ALLOWED_LANGS ({lang})")

        return item
