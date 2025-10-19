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
        if len(text_list) < 100:
            print("Text is too short, dropping item")
            raise DropItem("Text is too short")

        return item


class LanguagePipeline:
    def process_item(self, item, spider):
        text = item["text"].replace("\n", " ")
        labels, probs = model.predict(text)
        lang = labels[0].replace("__label__", "")

        # keep only Kurdish-related languages
        # kmr_Latn → Kurmanji (Northern Kurdish, Latin script)
        # ckb_Arab → Sorani (Central Kurdish, often in Arabic script)
        # diq_Latn → Zazaki (Latin script)
        if lang not in ["kmr_Latn", "ckb_Arab", "diq_Latn"]:
            print(f"Dropping non-Kurdish text ({lang})")
            raise DropItem(f"Item is not Kurdish ({lang})")

        item["lang"] = lang
        return item
