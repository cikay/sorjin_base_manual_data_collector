from parsel import Selector


class BaseExtractor:
    def normalize_title(self, title):
        return (title or "").strip()

    def normalize_text(self, text_list):
        return "\n".join(
            stripped
            for text in (text_list or [])
            if text and (stripped := text.strip())
        )


class JinnewsExtractor(BaseExtractor):

    def extract(self, response):
        title = response.css(".post-entry.single-post-box h2::text").get()
        text_list = response.css(".post-entry.single-post-box .body ::text").getall()

        return {
            "title": title,
            "text": "\n".join([text.strip() for text in text_list if text.strip()]),
            "url": response.url,
        }


class AjansawelatExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css("div.jeg_inner_content h1.jeg_post_title ::text").get()

        content_selectors = response.css("div.jeg_inner_content div.content-inner")
        if not content_selectors:
            return {
                "title":"",
                "text": "",
                "url": response.url
            }

        content_selector = content_selectors[0]

        # If there is a jeg_post_tags div, select nodes that have that div as a following-sibling
        has_tags = bool(content_selector.xpath('.//div[contains(concat(" ", normalize-space(@class), " "), " jeg_post_tags ")]'))
        if has_tags:
            # get text from all child nodes that are BEFORE the jeg_post_tags div
            texts = content_selector.xpath(
                './node()[following-sibling::div[contains(concat(" ", normalize-space(@class), " "), " jeg_post_tags ")]]//text()'
            ).getall()
        else:
            # fallback: get all text if no tags div present
            texts = content_selector.xpath(".//text()").getall()

        text = "\n".join([t.strip() for t in texts if t and t.strip()])
        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(texts),
            "url": response.url,
        }


class NuhevExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css(".entry-header .jeg_post_title ::text").get()
        text_list = response.css(".content-inner ::text").getall()
        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class XwebunExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css("h1.tdb-title-text ::text").get()

        texts = response.css(
            ".td_block_wrap.tdb_single_content.tdi_96.td-pb-border-top.td_block_template_1.td-post-content.tagdiv-type .tdb-block-inner.td-fix-index ::text"
        ).getall()


        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(texts),
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


class RojevaKurdExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css("h1.post-title.entry-title ::text").get()
        texts = response.css(".entry-content.entry.clearfix ::text").getall()

        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(texts),
            "url": response.url,
        }


class BianetExtractor:
    def extract(self, response):
        title = (response.css(".top-part .txt-wrapper h1.headline::text").get() or "").strip()

        first = response.css(".top-part .txt-wrapper .desc::text").get()

        paragraphs = response.css(".bottom-part .content ::text").getall()

        text = "\n".join(
            p.strip() for p in [first, *paragraphs] if p and p.strip()
        )

        return {
            "title": title,
            "text": text,
            "url": response.url,
        }
