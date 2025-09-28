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


class SorjinBaseManualDataCollectorPipeline:
    def process_item(self, item, spider):
        return item


class LanguagePipeline:
    def process_item(self, item, spider):
        text = item["content"].replace("\n", " ")

        lang = model.predict(text)
        label = lang[0][0]
        if label == "__label__kmr_Latn":
            return item

        print("It is not Kurdish Kurmanji, dropping item")
        raise DropItem("Item is not Kurdish Kurmanji")
