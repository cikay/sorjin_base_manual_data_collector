class JinnewsExtractor:
    def parse(self, response):
        title = response.css(".post-entry.single-post-box h2::text").get()
        text_array = response.css(".post-entry.single-post-box .body ::text").getall()

        return {
            "title": title,
            "text": "\n".join([text.strip() for text in text_array if text.strip()]),
            "url": response.url,
        }


class AjansawelatExtractor:
    def parse(self, response):
        pass


class NuhevaExtractor:
    def parse(self, response):
        pass

