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


def normalize_domains(domains: list) -> set[str]:
    return {
        domain.strip().rstrip("/")
        for domain in domains
        if isinstance(domain, str) and domain.strip()
    }


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

    domains_dir = Path("domains")
    domain_files = sorted(domains_dir.glob("*.json"))
    if not domain_files:
        raise FileNotFoundError(f"No domains files found in {domains_dir}/")
    urls_to_crawl: set[str] = set()
    for domain_file in domain_files:
        urls = json.loads(domain_file.read_text(encoding="utf-8"))
        urls_to_crawl |= normalize_domains(urls)
    logger.info(
        "Starting crawler for %d domain(s) from %d file(s). Output: %s, log file: %s",
        len(urls_to_crawl),
        len(domain_files),
        args.output,
        args.log_file,
    )
    try:
        run_crawler(
            output_path=args.output,
            content_extractor=ArticleExtractor(),
            urls_to_crawl=urls_to_crawl,
            log_file=args.log_file,
            log_level=args.log_level,
        )
    except Exception:
        logger.exception("Crawler run failed")
        raise
    logger.info("Crawler completed successfully")


if __name__ == "__main__":
    main()
