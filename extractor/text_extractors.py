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
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
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


class AnfKurmanciExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css("div.container div.post-content h2.entry-title ::text").get()
        first_text = response.css(
            "div.container div.post-content p.entry-lead ::text"
        ).get()
        text_list = response.css(
            "article.post.pt-0.mt-0.post-neg.bg-transparent div.post-content div.entry-content ::text"
        ).getall()
        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text([first_text, *text_list]),
            "url": response.url,
        }


class MezopotamyaExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css(
            "div.rs-blog-post-wrapper h1.rs-blog-post-title ::text"
        ).get()
        text_list = response.css(
            "div.container div.rs-postbox-details-content ::text"
        ).getall()
        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class DengeEmerikaExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css(
            "div.col-title.col-xs-12.col-md-10.pull-right h1.title.pg-title ::text"
        ).get()
        text_list = response.css("div#article-content ::text").getall()
        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class RupelanuExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css(
            "article.news-detail.clearfix div.content-heading h1.content-title ::text"
        ).get()
        text_list = response.css(
            "article.news-detail.clearfix div.text-content ::text"
        ).getall()
        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class SemakurdExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css("div#container h1[property='dc:title'] ::text").get()
        text_list = response.css(
            "div#op-content div.body-content div[property='dc:description'] ::text"
        ).getall()
        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class CandnameExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css(
            "div.post-inner h1.name.post-title.entry-title ::text"
        ).get()
        text_list = response.xpath(
            "//div[@class='post-inner']//div[@class='entry']"
            "//text()[not(ancestor::div[contains(@class,'share-post')])]"
        ).getall()

        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class RojnewsExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css(
            "div.post-header.post-tp-1-header h1.single-post-title span.post-title::text"
        ).get()

        text_list = response.css(
            "div.entry-content.clearfix.single-post-content ::text"
        ).getall()

        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class XebatExtractor(BaseExtractor):
    def extract(self, response):
        title_parts = response.css("h1.post-title.entry-title ::text").getall()

        text_list = response.css("div.bdaia-post-content ::text").getall()

        return {
            "title": self.normalize_text(title_parts),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class DiyarnameExtractor(BaseExtractor):
    def extract(self, response):
        title_parts = response.css("h2.title-semibold-dark.size-c30 ::text").getall()

        text_list = response.css(
            "div.container div.news-details-layout1 div.content ::text"
        ).getall()

        return {
            "title": self.normalize_text(title_parts),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class PortalNeteweExtractor(BaseExtractor):
    def extract(self, response):
        title_parts = response.css("header.entry-header h1.entry-title ::text").getall()

        all_texts = response.css(
            "div#primary main#main div.entry-content ::text"
        ).getall()

        excluded = response.css(
            "div.row.gutter-parent-14.post-wrap div.entry-content ::text"
        ).getall()

        text_list = [t for t in all_texts if t not in excluded]
        return {
            "title": self.normalize_text(title_parts),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class KurdYekitiExtractor(BaseExtractor):
    def extract(self, response):
        title_parts = response.css(
            "article#the-post h1.post-title.entry-title ::text"
        ).getall()

        text_list = response.css(
            "article#the-post div.entry-content.entry.clearfix ::text"
        ).getall()

        return {
            "title": self.normalize_text(title_parts),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class KurdistanMediaExtractor(BaseExtractor):
    def extract(self, response):
        title_parts = response.css(
            "div.card-img-overlay.text-white h3.card-title ::text"
        ).getall()

        text_list = response.css(
            "div.card div.card-body.overflow-hidden div.card-text ::text"
        ).getall()

        return {
            "title": self.normalize_text(title_parts),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class NlkNetMediaExtractor(BaseExtractor):
    def extract(self, response):
        title_parts = response.css("div.entry-header h1.jeg_post_title ::text").getall()

        text_list = response.css(
            "div.jeg_inner_content div.content-inner.jeg_link_underline ::text"
        ).getall()

        return {
            "title": self.normalize_text(title_parts),
            "text": self.normalize_text(text_list),
            "url": response.url,
        }


class JinhaMediaExtractor(BaseExtractor):
    def extract(self, response):
        title_parts = response.css(
            "article.post div.post-content h2.entry-title ::text"
        ).getall()

        text_list = response.css(
            "article.post div.post-content div.entry-content.row ::text"
        ).getall()

        return {
            "title": self.normalize_text(title_parts),
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


class BianetExtractor(BaseExtractor):
    def extract(self, response):
        title = response.css(".top-part .txt-wrapper h1.headline::text").get()

        first = response.css(".top-part .txt-wrapper .desc::text").get()

        paragraphs = response.css(".bottom-part .content ::text").getall()

        return {
            "title": self.normalize_title(title),
            "text": self.normalize_text([first, *paragraphs]),
            "url": response.url,
        }
