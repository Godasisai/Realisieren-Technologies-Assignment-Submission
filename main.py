"""Main execution pipeline for Multi-Source Web Scraping & Data Consolidation.

Orchestrates scraping, cleaning, validation, deduplication, and export.
"""

import argparse
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper
from processing.cleaning import clean_record
from processing.validation import validate_dataset
from processing.deduplication import find_duplicates

DEFAULT_OUTPUT_COLUMNS = [
    "source",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "source_url",
    "scraped_at",
]


def setup_logging(log_dir: Path) -> logging.Logger:
    """Configure unified logging to file and console.

    Args:
        log_dir: Directory where log files are stored.

    Returns:
        Root logger instance.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "scraper.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers if re-initializing
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def write_csv_dataset(
    records: List[Dict[str, Any]],
    output_path: Path,
    fieldnames: List[str],
) -> None:
    """Write cleaned records to a CSV file with standardized column ordering.

    Args:
        records: List of record dictionaries.
        output_path: Target CSV file path.
        fieldnames: Ordered list of column headers.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            # Map None values to empty strings for clean CSV representation
            row = {k: ("" if rec.get(k) is None else rec.get(k)) for k in fieldnames}
            writer.writerow(row)


def write_summary_report(stats: Dict[str, Any], output_path: Path) -> None:
    """Write pipeline execution statistics to a JSON report.

    Args:
        stats: Dictionary containing pipeline metrics.
        output_path: Target JSON file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)


def run_pipeline(
    max_pages_books: int = None,
    max_pages_quotes: int = None,
    delay_seconds: float = 0.5,
    flag_duplicates: bool = False,
    output_dir: Path = Path("output"),
    log_dir: Path = Path("logs"),
) -> Dict[str, Any]:
    """Execute the complete ETL scraping and processing pipeline.

    Args:
        max_pages_books: Optional max pages for Books to Scrape.
        max_pages_quotes: Optional max pages for Quotes to Scrape.
        delay_seconds: Polite delay between HTTP requests.
        flag_duplicates: If True, keep duplicates with 'is_duplicate' flag.
        output_dir: Output folder path.
        log_dir: Log folder path.

    Returns:
        Summary statistics dictionary.
    """
    logger = setup_logging(log_dir)
    logger.info("=" * 60)
    logger.info("Starting Multi-Source Web Scraping & Consolidation Pipeline")
    logger.info("=" * 60)

    start_wall_time = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()

    # Step 1: Scrape Books to Scrape
    books_records: List[Dict[str, Any]] = []
    try:
        books_scraper = BooksScraper(delay_seconds=delay_seconds)
        books_records = books_scraper.scrape(max_pages=max_pages_books)
    except Exception as exc:
        logger.error("Critical error scraping Books to Scrape: %s", exc, exc_info=True)

    # Step 2: Scrape Quotes to Scrape
    quotes_records: List[Dict[str, Any]] = []
    try:
        quotes_scraper = QuotesScraper(delay_seconds=delay_seconds)
        quotes_records = quotes_scraper.scrape(max_pages=max_pages_quotes)
    except Exception as exc:
        logger.error("Critical error scraping Quotes to Scrape: %s", exc, exc_info=True)

    raw_total = len(books_records) + len(quotes_records)
    logger.info("Scraping completed. Books: %d, Quotes: %d, Total: %d",
                len(books_records), len(quotes_records), raw_total)

    # Step 3: Clean and Standardize Data
    logger.info("Starting data cleaning and standardization...")
    cleaned_books = [clean_record(r) for r in books_records]
    cleaned_quotes = [clean_record(r) for r in quotes_records]
    all_cleaned = cleaned_books + cleaned_quotes

    # Step 4: Validate Data
    logger.info("Validating %d cleaned records...", len(all_cleaned))
    valid_records, rejected_items, reason_counts = validate_dataset(all_cleaned)

    for item, reasons in rejected_items:
        logger.warning("Record rejected: %s | Reasons: %s", item.get("name_or_title"), reasons)

    # Step 5: Duplicate Detection
    logger.info("Running duplicate detection on %d valid records...", len(valid_records))
    final_records, duplicate_records = find_duplicates(
        valid_records, flag_only=flag_duplicates
    )
    logger.info("Duplicates detected: %d", len(duplicate_records))
    for dupe in duplicate_records:
        logger.info(
            "Duplicate identified and %s: '%s' (Source: %s, URL: %s)",
            "flagged" if flag_duplicates else "removed",
            dupe.get("name_or_title"),
            dupe.get("source"),
            dupe.get("source_url"),
        )

    # Step 6: Generate Output Datasets
    final_csv_path = output_dir / "final_dataset.csv"
    summary_json_path = output_dir / "summary_report.json"

    columns = list(DEFAULT_OUTPUT_COLUMNS)
    if flag_duplicates:
        columns.append("is_duplicate")

    write_csv_dataset(final_records, final_csv_path, columns)
    logger.info("Exported consolidated dataset to %s (%d rows)", final_csv_path, len(final_records))

    # Calculate execution metrics
    end_wall_time = time.time()
    end_iso = datetime.now(timezone.utc).isoformat()
    duration = round(end_wall_time - start_wall_time, 2)

    # Arithmetic reconciliation
    # If flag_duplicates is False: final_record_count == raw_total - rejected_count - duplicates_detected
    reconciliation_ok = (
        len(final_records) == (raw_total - len(rejected_items) - (0 if flag_duplicates else len(duplicate_records)))
    )

    summary_stats = {
        "pipeline_status": "SUCCESS",
        "start_time": start_iso,
        "end_time": end_iso,
        "duration_seconds": duration,
        "collected_per_source": {
            "Books to Scrape": len(books_records),
            "Quotes to Scrape": len(quotes_records),
        },
        "total_raw_collected": raw_total,
        "cleaned_per_source": {
            "Books to Scrape": len(cleaned_books),
            "Quotes to Scrape": len(cleaned_quotes),
        },
        "total_cleaned": len(all_cleaned),
        "validation_summary": {
            "valid_records": len(valid_records),
            "rejected_records": len(rejected_items),
            "rejected_by_reason": reason_counts,
        },
        "duplicate_summary": {
            "duplicates_detected": len(duplicate_records),
            "strategy": "flagged" if flag_duplicates else "removed",
        },
        "final_record_count": len(final_records),
        "reconciliation_passed": reconciliation_ok,
    }

    write_summary_report(summary_stats, summary_json_path)
    logger.info("Exported summary report to %s", summary_json_path)

    logger.info("=" * 60)
    logger.info("Pipeline Execution Summary:")
    logger.info("  Raw Records Scraped : %d", raw_total)
    logger.info("  Validation Rejections: %d", len(rejected_items))
    logger.info("  Duplicates Found    : %d (%s)", len(duplicate_records), "flagged" if flag_duplicates else "removed")
    logger.info("  Final Dataset Rows  : %d", len(final_records))
    logger.info("  Execution Duration  : %.2f seconds", duration)
    logger.info("  Reconciliation Check: %s", "PASSED" if reconciliation_ok else "FAILED")
    logger.info("=" * 60)

    return summary_stats


def main() -> None:
    """CLI entry point for the web scraping pipeline."""
    parser = argparse.ArgumentParser(
        description="Multi-Source Web Scraping & Data Consolidation Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--max-pages-books",
        type=int,
        default=None,
        help="Maximum pages to scrape for Books to Scrape (default: all pages)",
    )
    parser.add_argument(
        "--max-pages-quotes",
        type=int,
        default=None,
        help="Maximum pages to scrape for Quotes to Scrape (default: all pages)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Polite request delay in seconds",
    )
    parser.add_argument(
        "--flag-duplicates",
        action="store_true",
        help="Flag duplicates with 'is_duplicate' column instead of removing them",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save generated datasets and summary",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory to save log files",
    )

    args = parser.parse_args()

    run_pipeline(
        max_pages_books=args.max_pages_books,
        max_pages_quotes=args.max_pages_quotes,
        delay_seconds=args.delay,
        flag_duplicates=args.flag_duplicates,
        output_dir=Path(args.output_dir),
        log_dir=Path(args.log_dir),
    )


if __name__ == "__main__":
    main()
