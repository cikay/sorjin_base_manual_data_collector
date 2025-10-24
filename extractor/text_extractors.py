from parsel import Selector


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
        title = (response.css(".entry-header .jeg_post_title ::text").get() or "").strip()
        text_list = response.css(".content-inner ::text").getall()
        return {
            "title": title,
            "text": "\n".join(
                [
                    text_item.strip()
                    for text_item in text_list
                    if text_item and text_item.strip()
                ]
            ),
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


class LotikxaneExtractor:

    def extract(self, response):
        title = response.css(".entry-header-details h1.entry-title ::text").get()
        html = response.text
        sel = Selector(text=html)
        # Select all nodes before <h3.awpa-title> inside the .entry-content-wrap.read-single
        nodes = sel.css(".entry-content.read-details > *").getall()

        text_until_h3 = []
        for node in nodes:
            # Stop when reaching the h3.awpa-title
            if "<h3" in node and "awpa-title" in node:
                break
            text_until_h3.append(node)
        
        parts = []
        for node in text_until_h3:
            node_text = Selector(text=node).xpath("normalize-space(string())").get().strip()
            if node_text:
                parts.append(node_text)

        # Join with newline between paragraphs
        clean_text = "\n".join(parts)

        return {
            "title": title,
            "text": clean_text,
            "url": response.url,
        }


class RojevaKurdExtractor:
    def extract(self, response):
        title = (response.css("h1.post-title.entry-title ::text").get() or "").strip()

        texts = response.css(".entry-content.entry.clearfix ::text").getall()
        text = "\n".join(
            text_item.strip() for text_item in texts if text_item and text_item.strip()
        )

        return {
            "title": title,
            "text": text,
            "url": response.url,
        }
