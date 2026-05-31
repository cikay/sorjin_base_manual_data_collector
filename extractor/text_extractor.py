"""Extract article content using Trafilatura."""

from typing import Optional
import json

import trafilatura

from sorjin_scrapy.lang_model import language_model
from sorjin_scrapy.items import DataItem
from sorjin_scrapy.loaders import DataItemLoader


class ArticleExtractor:
    """Extract article content from individual URLs using Trafilatura."""

    def __init__(
        self,
        include_comments: bool = False,
        include_tables: bool = True,
        favor_precision: bool = True,
        with_metadata: bool = True,
    ):
        """Initialize the article extractor.

        Args:
            include_comments: Whether to include comments in extraction.
            include_tables: Whether to include tables in extraction.
            favor_precision: Favor precision over recall in extraction.
        """
        self.include_comments = include_comments
        self.include_tables = include_tables
        self.favor_precision = favor_precision
        self.with_metadata = with_metadata

    def extract(
        self,
        html: str,
        url: str,
    ) -> Optional[dict]:
        """Extract article content from a URL.

        Args:
            url: The URL of the article.
            html: Pre-fetched HTML content.

        Returns:
            Dict with article data, or None if extraction failed.
        """
        # Single call to get text + metadata
        json_output = trafilatura.extract(
            html,
            url=url,
            output_format="json",
            include_comments=self.include_comments,
            include_tables=self.include_tables,
            favor_precision=self.favor_precision,
            with_metadata=self.with_metadata,
        )

        if json_output is None:
            return

        output = json.loads(json_output)

        text = output.get("text") or ""
        word_count = len(text.split())

        labels, probs = language_model.predict(text.replace("\n", " "))
        lang = labels[0].replace("__label__", "")
        lang_score = probs[0]

        loader = DataItemLoader(item=DataItem())

        loader.add_value("text", text)
        loader.add_value("title", output.get("title"))
        loader.add_value("url", url)
        loader.add_value("publisher", output.get("hostname"))
        loader.add_value("word_count", word_count)
        loader.add_value("lang", lang)
        loader.add_value("lang_score", lang_score)

        loader.add_value("source_type", "news")

        return loader.load_item()
