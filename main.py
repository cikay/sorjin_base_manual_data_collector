import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from extractor.text_extractor import ArticleExtractor
from run_crawler import run_crawler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RecursiveSpider with output file."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path (supported: .csv, .json, .jsonl)",
    )
    parser.add_argument(
        "--log-file",
        default=f"logs/crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        help="Path to log file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def load_urls(domains_dir: Path) -> list[str]:
    domain_files = sorted(domains_dir.glob("*.json"))
    if not domain_files:
        raise FileNotFoundError(f"No domain files found in {domains_dir}/")

    seen: set[str] = set()
    urls: list[str] = []
    for domain_file in domain_files:
        for entry in json.loads(domain_file.read_text(encoding="utf-8")):
            if isinstance(entry, str):
                url = entry.strip().rstrip("/")
                if url and url not in seen:
                    seen.add(url)
                    urls.append(url)
    return urls


def configure_logging(log_file: str, log_level: str) -> None:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
        force=True,
    )


def main():
    args = parse_args()
    configure_logging(args.log_file, args.log_level)
    logger = logging.getLogger(__name__)

    def handle_uncaught(exc_type, exc_value, exc_traceback):
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_uncaught

    urls = load_urls(Path("domains"))
    logger.info(
        "Starting crawler for %d domain(s). Output: %s, log file: %s",
        len(urls),
        args.output,
        args.log_file,
    )
    try:
        run_crawler(
            output_path=args.output,
            content_extractor=ArticleExtractor(),
            urls=urls,
            log_file=args.log_file,
            log_level=args.log_level,
        )
    except Exception:
        logger.exception("Crawler run failed")
        raise
    logger.info("Crawler completed successfully")


if __name__ == "__main__":
    main()
