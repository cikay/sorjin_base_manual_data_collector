from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst
from datetime import datetime


def round_float_3(value):
    return round(float(value), 3)


class DataItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

    word_count_in = MapCompose(int)
    lang_score_in = MapCompose(round_float_3)
