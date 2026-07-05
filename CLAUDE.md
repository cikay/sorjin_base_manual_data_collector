# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Scrapy-based crawler that collects article text in low-resource languages (currently Kurdish variants: `kmr_Latn`, `ckb_Arab`, `diq_Latn`) from a curated list of news domains. Content is extracted with Trafilatura and filtered by language using a FastText model.

## Commands

Environment uses Pipenv with Python 3.10:

```bash
pipenv --python 3.10 && pipenv shell
pipenv install
```

Run the crawler (reads `domains.json`):

```bash
python main.py --output output.csv                                      # output: .csv | .json | .jsonl
python main.py --output output.csv --log-file logs/crawler.log --log-level INFO
```

Other entrypoints:

```bash
python rows_count.py --file-name output.csv                             # row/unique-field counts
python bencmark.py --domain https://www.nuhev.com --sitemap s.csv --recursive r.csv   # sitemap vs recursive timing
python get_publishers.py                                                # discover candidate domains from CulturaX (needs HF_TOKEN)
```

There is no test suite, linter, or build step. `.env` (loaded by `kurdish_scrapy/settings.py`) holds `SCRAPEOPS_API_KEY` (optional), `TEXT_MIN_WORD_COUNT`, and `HF_TOKEN` (for `get_publishers.py` only).

## Architecture

The flow is **not** the standard `scrapy crawl` CLI. `main.py` → `run_crawler.py` drives a `CrawlerProcess` programmatically, scheduling one spider per domain.

**Per-domain spider selection (`run_crawler.py`):**
1. `_build_url_filter_for_domain` probes the homepage (`extractor/lang_url_filter.py`) to find language-section URL prefixes (via `<link hreflang>`, anchor `hreflang`, lang-menu containers, then a path-segment scan). Three outcomes:
   - **Prefixes found** → a compiled regex `url_filter` restricts crawling to those sections.
   - **No prefix, homepage unreachable** → skip the domain.
   - **No prefix, reachable** → fetch the root page, detect its language; crawl the whole site only if it's a target language, else skip.
2. If a sitemap is discoverable (`sitemap_discovery.py`: robots.txt first, then `SITEMAP_PATTERNS`), use `SitemapSpider`; otherwise fall back to `RecursiveSpider`.

**Spiders (`kurdish_scrapy/spiders/`):** Both extract via `content_extractor` and yield items. `SitemapSpider` wraps the `url_filter` regex into `sitemap_rules` (must be set before `super().__init__`). `RecursiveSpider` follows in-domain links matching `url_filter`; when there's no filter it self-terminates by only following links from pages already detected as a target language.

**Extraction (`extractor/`):** `ArticleExtractor.extract` runs Trafilatura once (`output_format="json"`), runs the FastText model on the text, and populates a `DataItem` via the item loader. `UrlExtractor` handles link extraction plus media/non-HTML filtering (also used by `MediaFilterMiddleware`). `protocol.py` defines `ContentExtractorProtocol` — the seam that lets `run_crawler`/spiders stay decoupled from Trafilatura.

**Filtering pipelines (`pipelines.py`):** `LenPipeline` drops items below `TEXT_MIN_WORD_COUNT`; `LanguagePipeline` drops items whose detected `lang` is not in `ALLOWED_LANGS`. So language filtering happens twice — once to steer crawling, once to reject collected items.

**Language model (`lang_model.py`):** loads `cis-lmu/glotlid` (`model_v3.bin`) from the HF Hub at import time. Returns FLORES-200 codes (e.g. `kmr_Latn`). Despite the README naming Facebook's model, this is the model actually used.

## Key config points

- **Target languages** are hardcoded in `ALLOWED_LANGS` in `kurdish_scrapy/settings.py` (not env-driven, despite the README's `ALLOWED_LANGS` env var). Changing the set of collected languages means editing this list and usually `HREFLANG` in `extractor/lang_url_filter.py` (the set of language keywords matched in URLs/menus).
- Crawl politeness: `CONCURRENT_REQUESTS_PER_DOMAIN = 1`, `DOWNLOAD_DELAY = 1`, `ROBOTSTXT_OBEY = True`.
- `ScrapeOpsFakeUserAgentMiddleware` rotates user agents; it self-disables if `SCRAPEOPS_API_KEY` is unset. Remove it from `DOWNLOADER_MIDDLEWARES` if it ever blocks runs.
- Feeds use `overwrite: False`, so reusing an output file appends to it.

Note: `get_publishers.py` writes its discovered domains to `domains.json` (the README's mention of `publishers/<lang>.csv` is stale); review before overwriting the curated `domains.json`.
