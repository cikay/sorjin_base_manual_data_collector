# Sorjin Scrapy

A [Scrapy](https://www.scrapy.org/) package based web scraper for collecting text data in low-resource languages from websites. The tool recursively crawls specified domains, extracts article content using [Trafilatura](https://trafilatura.readthedocs.io/), and filters results by language using Facebook's [FastText language identification model](https://huggingface.co/facebook/fasttext-language-identification).

## Features

- **Recursive crawling** - Crawls entire websites following internal links
- **Language detection** - Filters content by the configured language variants (FLORES-200 codes):
  - `kmr_Latn` - Kurmanji (Northern Kurdish, Latin script)
  - `ckb_Arab` - Sorani (Central Kurdish, Arabic script)
  - `diq_Latn` - Zazaki (Latin script)
  - `cym_Latn` - Welsh (Latin script)
  - `hrv_Latn` - Croatian (Latin script)
- **Content extraction** - Extracts clean article text, title, and metadata using Trafilatura
- **Smart filtering** - Skips media files, non-HTML content, and short texts
- **Anti-bot protection** - Rotates user agents via ScrapeOps
- **Duplicate handling** - Built-in URL deduplication

## Prerequisites

- Python 3.10
- [Pipenv](https://pipenv.pypa.io/en/latest/)
- [ScrapeOps API key](https://scrapeops.io/app/headers) (optional, free tier available)

## Installation

1. Clone the repository:
```bash
git clone git@github.com:cikay/sorjin_scrapy.git
cd sorjin_scrapy
```

2. Create and activate virtual environment:
```bash
pipenv --python 3.10
pipenv shell
```

3. Install dependencies:
```bash
pipenv install
```

4. Create a `.env` file with your configuration:
```bash
ALLOWED_LANGS="kmr_Latn,ckb_Arab,diq_Latn,cym_Latn,hrv_Latn"
TEXT_MIN_WORD_COUNT=100
# Optional
# SCRAPEOPS_API_KEY="your_api_key_here"
```

## Configuration

| Variable | Description | Default |
|----------|-------------|--------|
| `SCRAPEOPS_API_KEY` | API key for ScrapeOps user agent rotation | Optional |
| `ALLOWED_LANGS` | Comma-separated language codes to collect | `kmr_Latn,ckb_Arab,diq_Latn,cym_Latn,hrv_Latn` |
| `TEXT_MIN_WORD_COUNT` | Minimum word count for collected texts | `100` |

Note: `SCRAPEOPS_API_KEY` is currently optional and scraping may still work without it. If this changes in the future and requests start failing, either:
- obtain a valid ScrapeOps API key, or
- remove `sorjin_scrapy.middlewares.ScrapeOpsFakeUserAgentMiddleware` from `DOWNLOADER_MIDDLEWARES` in `sorjin_scrapy/settings.py`.

## Usage

### Configure target domains

Target domains are kept in `domains.json`, a single flat list of URLs to crawl:

```json
[
    "https://www.nuhev.com/",
    "https://ajansawelat.com/"
]
```

To discover candidate domains for a language, run `python get_publishers.py`, which
pulls the matching CulturaX splits and writes ranked domain lists to `publishers/<lang>.csv`.

### Run the app

```bash
python main.py --output output.csv
```

For production/server runs, write logs to a file so crashes are preserved:

```bash
python main.py --output output.csv --log-file logs/crawler.log --log-level INFO
```

`main.py` reads `domains.json` and passes the domains to `run_crawler.py`.
For each domain, the runner tries `SitemapSpider` first (using `robots.txt` and common sitemap paths). If no sitemap is found, it falls back to `RecursiveSpider`.

Supported output formats: `.csv`, `.json`, `.jsonl`

### Run with Docker

The crawler is packaged so it runs without a local Python/Pipenv setup. The
image bakes in the dependencies; the GlotLID language model is downloaded on the
first run into `/hf-cache` (set `HF_TOKEN` for a faster authenticated download)
and reused afterwards. Crawl output and logs are written to `/data`. Mount
volumes on both paths so the model and results survive container restarts and
removals.

Build the image:

```bash
docker build -t sorjin-crawler .
```

#### With docker compose (recommended)

`docker-compose.yml` defines a named volume `crawler-data` mounted at `/data`
and loads `.env` for configuration. Run:

```bash
docker compose run --rm crawler
```

By default this writes `/data/output.csv` and `/data/logs/crawler.log` inside the
`crawler-data` volume. Override the command to change format/paths or verbosity:

```bash
docker compose run --rm crawler \
  --output /data/output.jsonl --log-file /data/logs/crawler.log --log-level DEBUG
```

`docker compose up -d` runs the service detached but leaves a stopped container
behind on exit (Compose has no auto-remove); clean it up with `docker compose
down`. For a detached run that deletes itself when the crawl finishes, use plain
`docker run -d --rm` (see below).

#### With plain docker

Mount a host directory (or named volume) at `/data`, plus a volume at `/hf-cache`
so the language model is downloaded only once:

```bash
# persist to ./real_data on the host
docker run --rm --env-file .env \
  -v "$(pwd)/real_data:/data" -v hf-cache:/hf-cache sorjin-crawler

# or to named volumes
docker run --rm --env-file .env \
  -v crawler-data:/data -v hf-cache:/hf-cache sorjin-crawler
```

Run detached and have the container delete itself when the crawl finishes
(`docker run` honors `--rm` together with `-d`, unlike `docker compose`). Reuse
the Compose-created volumes by their project-prefixed names so the cached model
and prior output carry over:

```bash
docker run -d --rm --name sorjin-crawler --env-file .env \
  -v sorjin_scrapy_crawler-data:/data -v sorjin_scrapy_hf-cache:/hf-cache \
  sorjin-crawler

docker logs -f sorjin-crawler   # follow progress
```

Inspect the results in a named volume:

```bash
docker run --rm -v crawler-data:/data alpine ls -la /data /data/logs
```

Notes:

- The default `ENTRYPOINT` is `python main.py`; anything after the image name is
  passed as CLI args (`--output`, `--log-file`, `--log-level`). Keep paths under
  `/data` so they land in the volume.
- `domains.json` is copied into the image at build time. To crawl a different
  list without rebuilding, mount it: `-v "$(pwd)/domains.json:/app/domains.json"`.
- `.env` is excluded from the image (see `.dockerignore`); pass configuration at
  run time via `--env-file .env` or compose's `env_file`.

### Check collected data statistics

```bash
python rows_count.py --file-name output.csv
```

This displays:
- Total row count
- Unique titles, URLs, and texts count

### Run benchmark mode

Use `bencmark.py` to benchmark one domain by running both spiders sequentially (`SitemapSpider` first, then `RecursiveSpider`) and writing timing logs.

Arguments:
- `--domain`: Required start URL/domain to crawl (use full URL, e.g. `https://www.nuhev.com`)
- `--sitemap`: Output file for sitemap crawl (`.csv`, `.json`, or `.jsonl`)
- `--recursive`: Output file for recursive crawl (`.csv`, `.json`, or `.jsonl`)
- `--benchmark-log` (optional): Log file path for timing details (default: `benchmark.log`)

Example with default log path:

```bash
python bencmark.py --domain https://www.nuhev.com --sitemap sitemap_output.csv --recursive recursive_output.csv
```

## Output Format

The spider outputs the following fields:

| Field | Description |
|-------|-------------|
| `text` | Extracted article content |
| `title` | Article title |
| `url` | Source URL |
| `publisher` | Website/publisher name |
| `word_count` | Word count (calculated by whitespace splitting) |
| `lang` | Detected language code |
| `lang_score` | Language detection confidence score |
| `source_type` | Content type (default: `news`) |

## Project Structure

```
├── sorjin_scrapy/
│   ├── spiders/
│   │   ├── sitemap.py        # Sitemap-based spider
│   │   ├── recursive.py      # Recursive fallback spider
│   │   └── base.py           # Shared spider base class
│   ├── items.py              # Data item schema
│   ├── middlewares.py        # User agent rotation & URL filtering
│   ├── pipelines.py          # Language & length filtering
│   ├── settings.py           # Scrapy configuration
│   └── lang_model.py         # FastText language model loader
├── extractor/
│   ├── text_extractor.py     # Trafilatura-based content extraction
│   ├── url_extractor.py      # URL parsing and filtering
│   └── protocol.py           # Extractor protocol interface
├── run_crawler.py            # Spider selection + feed setup
├── main.py                   # CLI entrypoint
├── domains.json              # Flat list of crawl target URLs
├── publishers/               # Candidate domains discovered from CulturaX per language
├── get_publishers.py         # Build publishers/<lang>.csv from CulturaX
├── bencmark.py               # Sitemap vs recursive benchmark runner
├── rows_count.py             # Utility for data statistics
├── Pipfile                   # Dependencies
├── Dockerfile                # Container build (deps + GlotLID model baked in)
├── docker-compose.yml        # Compose service with a /data output volume
├── .dockerignore             # Build-context excludes (.git, real_data, .env, …)
└── .env                      # Environment variables (create this)
```
