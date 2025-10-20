class JinnewsExtractor:

    def extract(self, response):
        title = response.css(".post-entry.single-post-box h2::text").get()
        text_list = response.css(".post-entry.single-post-box .body ::text").getall()

        return {
            "title": title,
            "text": "\n".join([text.strip() for text in text_list if text.strip()]),
            "url": response.url,
        }


class AjansawelatExtractor:
    def parse(self, response):
        pass


class NuhevExtractor:
    def extract(self, response):
        title = response.css(".entry-header .jeg_post_title ::text").get()
        text_list = response.css(".content-inner ::text").getall()
        return {
            "title": title,
            "text": "\n".join([text.strip() for text in text_list if text.strip()]),
            "url": response.url,
        }


class XwebunExtractor:
    def extract(self, response):
        title = response.css("h1.tdb-title-text ::text").get()

        texts = texts = response.css(
            ".td_block_wrap.tdb_single_content.tdi_96.td-pb-border-top.td_block_template_1.td-post-content.tagdiv-type .tdb-block-inner.td-fix-index ::text"
        ).getall()
        text = "\n".join(texts)

        return {
            "title": title,
            "text": text,
            "url": response.url,
        }
