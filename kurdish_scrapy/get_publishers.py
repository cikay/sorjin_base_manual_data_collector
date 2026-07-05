"""Extract candidate publisher domains from CulturaX for each target language.

For every configured low-resource language this loads the matching CulturaX
split, counts how often each domain appears, and writes the domains that occur
more than 100 times to ``domains.json``. Those domains are a starting point for
curating the crawl target lists.
"""

import json
import os
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv()

# CulturaX is a gated dataset on the Hugging Face Hub, so a token is required.
# Request access at https://huggingface.co/datasets/uonlp/CulturaX and set HF_TOKEN
# in your .env file.
HF_TOKEN = os.getenv("HF_TOKEN")

# CulturaX language code -> human-readable name.
# ku → Kurdish, cy → Welsh, hr → Croatian.
LANGUAGES = {
    "ku": "Kurdish",
}

OUTPUT_PATH = Path("domains.json")

# Only keep domains that appear more than this many times in the dataset.
MIN_COUNT = 100


def extract_domain(url: str) -> str | None:
    """Return the domain of a URL with an ``https://`` prefix, or None on failure.

    Strips a leading ``www.`` so ``www.example.com`` and ``example.com`` collapse
    to the same domain.
    """
    try:
        netloc = urlparse(url).netloc
    except Exception:
        return None
    if not netloc:
        return None
    netloc = netloc.removeprefix("www.")
    return f"https://{netloc}"


def count_domains_for_language(lang: str, counter: Counter) -> None:
    """Load a CulturaX language split and accumulate domain counts into ``counter``."""
    dataset = load_dataset("uonlp/CulturaX", lang, split="train", token=HF_TOKEN)
    dataset = dataset.map(
        lambda x: {"domain": extract_domain(x["url"])}, num_proc=4
    )

    for domain in dataset["domain"]:
        if domain is not None:
            counter[domain] += 1


def main() -> None:
    if not HF_TOKEN:
        raise SystemExit(
            "HF_TOKEN is not set. CulturaX is gated; request access at "
            "https://huggingface.co/datasets/uonlp/CulturaX and add HF_TOKEN to your .env file."
        )

    counter: Counter = Counter()

    for lang, name in LANGUAGES.items():
        print(f"Processing {name} ({lang})...")
        count_domains_for_language(lang, counter)

    # Keep only domains that occur more than MIN_COUNT times, ranked by
    # frequency. A set guards against any duplicate entries in the output.
    seen: set[str] = set()
    domains = []
    for domain, count in counter.most_common():
        if count > MIN_COUNT and domain not in seen:
            seen.add(domain)
            domains.append(domain)

    OUTPUT_PATH.write_text(
        json.dumps(domains, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"✅ Saved {len(domains)} domains (>{MIN_COUNT} entries) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
