"""Extract candidate publisher domains from CulturaX for each target language.

For every configured low-resource language this loads the matching CulturaX
split, counts how often each domain appears, and writes a ranked CSV to
``publishers/<lang>.csv``. Those domains are a starting point for curating the
crawl target lists in ``domains/<lang>.json``.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
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
    "cy": "Welsh",
    "hr": "Croatian",
}

OUTPUT_DIR = Path("publishers")


def extract_domain(url: str) -> str | None:
    """Return the network location (domain) of a URL, or None on failure."""
    try:
        return urlparse(url).netloc
    except Exception:
        return None


def domain_counts_for_language(lang: str) -> pd.DataFrame:
    """Load a CulturaX language split and count documents per domain."""
    dataset = load_dataset("uonlp/CulturaX", lang, split="train", token=HF_TOKEN)
    dataset = dataset.map(
        lambda x: {"domain": extract_domain(x["url"])}, num_proc=4
    )

    df = pd.DataFrame({"domain": list(dataset["domain"])}).dropna()

    counts = df.value_counts().reset_index()
    counts.columns = ["domain", "count"]
    return counts.sort_values(by="count", ascending=False).reset_index(drop=True)


def main() -> None:
    if not HF_TOKEN:
        raise SystemExit(
            "HF_TOKEN is not set. CulturaX is gated; request access at "
            "https://huggingface.co/datasets/uonlp/CulturaX and add HF_TOKEN to your .env file."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for lang, name in LANGUAGES.items():
        print(f"Processing {name} ({lang})...")
        counts = domain_counts_for_language(lang)

        output_path = OUTPUT_DIR / f"{lang}.csv"
        counts.to_csv(output_path, index=False)

        print(f"✅ Saved {len(counts)} {name} domains to {output_path}")
        print(counts.head(10))


if __name__ == "__main__":
    main()
