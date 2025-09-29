# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from scrapy.exceptions import DropItem

import fasttext
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="facebook/fasttext-language-identification", filename="model.bin"
)

model = fasttext.load_model(model_path)


class LenPipeline:
    def process_item(self, item, spider):
        text_list = item["text"].split()
        if len(text_list) < 300:
            print("Text is too short, dropping item")
            raise DropItem("Text is too short")

        return item


class LanguagePipeline:
    def process_item(self, item, spider):
        text = item["text"].replace("\n", " ")
        lang = model.predict(text)
        label = lang[0][0]
        if label == "__label__kmr_Latn":
            return item

        print("It is not Kurdish Kurmanji, dropping item")
        raise DropItem("Item is not Kurdish Kurmanji")
