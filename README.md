# Multi-Source Web Scraping & Data Consolidation Pipeline

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Code Style](https://img.shields.io/badge/code%20style-PEP%208-brightgreen.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Tests](https://img.shields.io/badge/tests-pytest%20(38%20passed)-success.svg)](tests/)

A robust, production-grade Python ETL pipeline that collects heterogeneous data from multiple public websites ([Books to Scrape](https://books.toscrape.com/) and [Quotes to Scrape](https://quotes.toscrape.com/)), standardizes and cleans the raw records, applies business validations, identifies and resolves duplicate entities via cryptographic fingerprinting, and consolidates the output into a unified dataset and JSON audit report.

---

## Table of Contents

1. [Assignment Overview](#assignment-overview)
2. [Architecture & Workflow](#architecture--workflow)
3. [Project Directory Structure](#project-directory-structure)
4. [Prerequisites & Python Version](#prerequisites--python-version)
5. [Installation & Setup](#installation--setup)
6. [How to Run the Pipeline](#how-to-run-the-pipeline)
7. [Source Analysis & Observations](#source-analysis--observations)
8. [Unified Data Model](#unified-data-model)
9. [Dynamic Pagination](#dynamic-pagination)
10. [Data Cleaning & Transformation](#data-cleaning--transformation)
11. [Validation Framework](#validation-framework)
12. [Duplicate Detection & Fingerprinting](#duplicate-detection--fingerprinting)
13. [Resilient Error Handling & Networking](#resilient-error-handling--networking)
14. [Output Artifacts & Summary Report](#output-artifacts--summary-report)
15. [Running Unit Tests](#running-unit-tests)
16. [Assumptions & Known Limitations](#assumptions--known-limitations)
17. [Interview Discussion Guide](#interview-discussion-guide)
18. [AI Usage Summary](#ai-usage-summary)

---

## 1. Assignment Overview

Real-world web data is noisy, unstructured, and fragmented across distinct domains. The objective of this assignment is to demonstrate practical engineering best practices for building an automated scraping and data consolidation pipeline:
- **Multi-Source Collection**: Extraction across distinct domains with heterogeneous HTML structures.
- **Dynamic Pagination**: Following relational `next` links dynamically across unknown page depths without hardcoded page counts.
- **Schema Harmonization**: Mapping diverse entity schemas into one standardized table layout.
- **Data Cleansing**: Normalizing whitespace, stripping quotation decorators, parsing foreign currency, standardizing textual ratings to numeric scales, and deduplicating tag taxonomies.
- **Quality Assurance**: Automated validation identifying corrupted records and cataloging exact failure reasons.
- **Entity Resolution**: Case-, punctuation-, and whitespace-insensitive hashing to detect duplicate records.
- **Fault-Tolerant Networking**: Exponential backoff retries on transient HTTP codes (429, 500, 502, 503, 504), per-record exception isolation, and graceful source recovery.

---

## 2. Architecture & Workflow

The pipeline is structured as a decoupled **ETL (Extract, Transform, Load)** pipeline where each layer has zero side effects on adjacent components:

```
┌─────────────────────────────────────────────────────────────┐
│                       EXTRACT PHASE                         │
│  Books to Scrape (50 pgs)        Quotes to Scrape (10 pgs)  │
│  [article.product_pod]           [div.quote]                │
│          │                                   │              │
│          ▼                                   ▼              │
│    BooksScraper                         QuotesScraper       │
│  (BaseScraper Session, Exponential Backoff, Rate Limiter)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Raw Records (Dicts)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      TRANSFORM PHASE                        │
│                                                             │
│  1. CLEANING (processing.cleaning)                          │
│     - Whitespace collapse & \xa0 normalization              │
│     - Currency extraction & float parsing (£51.77 -> 51.77) │
│     - Star rating mapping (Three -> 3)                      │
│     - Quote delimiter stripping (“...”)                     │
│     - Tag sorting & semicolon delimitation                  │
│                                                             │
│  2. VALIDATION (processing.validation)                      │
│     - Schema conformance & source verification              │
│     - URL protocol & syntax verification                    │
│     - Range & type checking (price >= 0, rating in 1..5)    │
│     - Rejected items logged with explicit failure reasons   │
│                                                             │
│  3. DEDUPLICATION (processing.deduplication)                │
│     - Normalized SHA-256 fingerprinting                     │
│     - Source-specific key generation                        │
│     - Duplicate dropping or flagging                        │
└──────────────────────────────┬──────────────────────────────┘
                               │ Consolidated Clean Records
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         LOAD PHASE                          │
│                                                             │
│  output/final_dataset.csv   output/summary_report.json      │
│  (Uniform UTF-8 CSV)         (Metrics & Reconciliation)     │
│                                                             │
│  logs/scraper.log (Detailed execution & audit trail)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Project Directory Structure

```
scraping_assignment/
├── scrapers/
│   ├── __init__.py           # Package exports for scraper classes
│   ├── base_scraper.py       # Resilient HTTP session, retries, timeout, delay
│   ├── books_scraper.py      # Books to Scrape selectors, pagination & extraction
│   └── quotes_scraper.py     # Quotes to Scrape selectors, pagination & extraction
├── processing/
│   ├── __init__.py           # Package exports for processing functions
│   ├── cleaning.py           # Pure transformation functions (text, price, rating, tags, URL)
│   ├── validation.py         # Business rule checks & failure diagnostics
│   └── deduplication.py      # SHA-256 fingerprinting & duplicate partitioning
├── tests/
│   ├── __init__.py
│   ├── test_cleaning.py      # 25 unit tests for cleaning functions
│   ├── test_validation.py    # 8 unit tests for validation rules
│   └── test_deduplication.py # 5 unit tests verifying duplicate edge cases
├── output/
│   ├── final_dataset.csv     # Consolidated, cleaned, and deduplicated CSV
│   └── summary_report.json   # Arithmetic reconciliation and execution metrics
├── logs/
│   └── scraper.log           # Time-stamped operational log file
├── main.py                   # CLI orchestrator and execution entry point
├── requirements.txt          # Pinned project dependencies
├── README.md                 # Complete system documentation
└── AI_USAGE.md               # Mandatory transparency disclosure on AI assistance
```

---

## 4. Prerequisites & Python Version

- **Python Version**: Python **3.10**, **3.11**, or **3.12** (Verified on Python `3.12.10`).
- **Operating System**: Platform-agnostic (Windows, macOS, Linux). Paths are constructed using `pathlib.Path`.
- **Dependencies**:
  - `requests >= 2.31.0`: HTTP client for downloading web content.
  - `beautifulsoup4 >= 4.12.0`: HTML parser and DOM traversal.
  - `lxml >= 5.0.0`: C-based, high-performance HTML engine utilized by BeautifulSoup.
  - `pytest >= 8.0.0`: Automated unit testing framework.

---

## 5. Installation & Setup

1. **Clone or extract** the repository into your desired workspace:
   ```bash
   cd scraping_assignment
   ```

2. **Create and activate a virtual environment**:
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows (Command Prompt / PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```

3. **Install the dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify the installation**:
   ```bash
   pytest
   ```
   *(Expected output: 38 passed in < 0.2s)*

---

## 6. How to Run the Pipeline

### Standard Execution
To run the full pipeline across all pages of both websites:
```bash
python main.py
```

### Command-Line Arguments & Options
The pipeline includes configurable CLI arguments for testing, debugging, rate limiting, and output customization:

| Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--max-pages-books` | `int` | `None` (All) | Scrape up to N pages of Books to Scrape (useful for quick testing). |
| `--max-pages-quotes`| `int` | `None` (All) | Scrape up to N pages of Quotes to Scrape. |
| `--delay` | `float` | `0.5` | Polite delay interval between HTTP requests (seconds). |
| `--flag-duplicates` | `flag` | `False` | Keep duplicates in output with an `is_duplicate` column instead of dropping them. |
| `--output-dir` | `str` | `output` | Directory path for saving CSV and JSON outputs. |
| `--log-dir` | `str` | `logs` | Directory path for writing log files. |

### Example CLI Usages:
- **Fast smoke test (2 pages per source)**:
  ```bash
  python main.py --max-pages-books 2 --max-pages-quotes 2
  ```
- **Retain duplicates with flag**:
  ```bash
  python main.py --flag-duplicates
  ```
- **Custom delay and output directory**:
  ```bash
  python main.py --delay 1.0 --output-dir custom_output
  ```

---

## 7. Source Analysis & Observations

Before building the scrapers, both target websites were inspected via Developer Tools to identify DOM selectors, data types, pagination mechanics, and edge cases:

| Dimension | Books to Scrape (`books.toscrape.com`) | Quotes to Scrape (`quotes.toscrape.com`) |
| :--- | :--- | :--- |
| **Domain Purpose** | Sandbox e-commerce catalog (~1,000 items) | Sandbox quote repository (~100 items) |
| **Pagination Volume**| 50 pages (20 books / page) | 10 pages (10 quotes / page) |
| **Record Container** | `article.product_pod` | `div.quote` |
| **Primary Text** | `h3 > a` (Visible text truncated; full title in `title` attr) | `span.text` (Wrapped in typographic curly quotes) |
| **Price** | `p.price_color` (Formatted as `£51.77` or `Â£51.77`) | Not applicable (`None`) |
| **Rating** | `p.star-rating` CSS classes (`["star-rating", "Three"]`) | Not applicable (`None`) |
| **Author** | Not applicable (`None`) | `small.author` |
| **Tags / Labels** | Not applicable on listing | `div.tags > a.tag` (0 or more tags) |
| **Relative Links** | `h3 > a[href]` (e.g. `catalogue/book_1000/index.html`) | `a[href*="/author/"]` (Author bio page) |
| **Pagination Link** | `li.next > a[href]` (`page-2.html` or `catalogue/page-2.html`) | `li.next > a[href]` (`/page/2/`) |

### Key Technical Observations & Mitigations
1. **Truncated Book Titles**: Visible inner text inside `<h3><a>` is truncated with ellipses (e.g., `"A Light in the ..."`). The complete, unabridged title is located in the anchor tag's `title` attribute. Our parser inspects `link.get("title")` first, falling back to inner text only if absent.
2. **Encoding & Currency Symbols**: Without explicitly forcing `response.encoding = "utf-8"`, the British Pound symbol `£` can decode into `Â£` due to Latin-1 misinterpretation. We explicitly set UTF-8 encoding on every response and implement regex cleaners resilient to both encodings.
3. **URL Resolution**: On Books to Scrape, the home page URL is `https://books.toscrape.com/`, which links to `catalogue/page-2.html`. On page 2, the next link is relative (`page-3.html`). Using `urllib.parse.urljoin(current_url, href)` dynamically and accurately constructs valid absolute URLs regardless of relative path nesting.

---

## 8. Unified Data Model

To merge disparate datasets into one unified CSV table without inventing artificial values, we define a common schema:

| Column Name | Books to Scrape | Quotes to Scrape | Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| `source` | `"Books to Scrape"` | `"Quotes to Scrape"` | `string` | Originating website name |
| `name_or_title` | Complete book title | Cleaned quote text | `string` | Identifying primary text |
| `category` | `""` (Empty) | `""` (Empty) | `string` / `None` | Product category (see assumptions) |
| `price` | E.g. `51.77` | `""` (Empty) | `float` / `None` | Numeric price in GBP |
| `rating` | Integer `1` to `5` | `""` (Empty) | `int` / `None` | 5-point star rating |
| `author` | `""` (Empty) | E.g. `"Albert Einstein"` | `string` / `None` | Quote author name |
| `tags` | `""` (Empty) | E.g. `"change;thinking"` | `string` / `None` | Semicolon-delimited, sorted tags |
| `description` | `""` (Empty) | `""` (Empty) | `string` / `None` | Extended item description |
| `source_url` | Book product URL | Author bio / page URL | `string` | Fully-qualified absolute URL |
| `scraped_at` | UTC ISO-8601 string | UTC ISO-8601 string | `string` | Extraction timestamp |

> **Design Decision**: Fields that do not exist for a source remain `None` in memory and render as empty cells in CSV output. We never synthesize arbitrary dummy values (e.g., quotes are not assigned a price of `0.0` or rating of `0`), preventing data skew during downstream analytics.

---

## 9. Dynamic Pagination

Hardcoding page counts (e.g. `for page in range(1, 51)`) is fragile: scrapers break when items are added or removed. 

Our scrapers implement dynamic pagination:
1. Fetch the current URL.
2. Parse all entities on the page.
3. Search for the next page link using CSS selector `li.next > a`.
4. If found, resolve the link against the current URL with `urljoin(current_url, next_link["href"])`, pause for the polite delay interval, and repeat.
5. If absent, terminate the pagination loop naturally.

---

## 10. Data Cleaning & Transformation

Cleaning logic resides in `processing/cleaning.py` as pure functions with no network or I/O side effects:
- **`clean_text(val)`**: Strips leading/trailing spaces, replaces non-breaking space bytes (`\xa0`) with ASCII spaces, and collapses internal consecutive whitespace (`" ".join(text.split())`).
- **`strip_quotes(val)`**: Strips typographic curly quotes (`“`, `”`, `‘`, `’`), guillemets (`«`, `»`), and straight quotes (`"`, `'`) from quote texts while preserving internal quotations.
- **`clean_price(val)`**: Uses regular expressions (`r"\d+(?:\.\d+)?"`) to extract decimal numbers, strips currency symbols (`£`, `$`, `€`), and parses valid floats rounded to 2 decimal places.
- **`clean_rating(val)`**: Maps rating strings (`"One"`..`"Five"` or `"star-rating Three"`) to canonical integers `1` to `5` using a dictionary lookup table (`RATING_MAP`).
- **`clean_tags(val)`**: Normalizes tag lists or delimited strings into lowercase, deduplicates entries, sorts alphabetically, and joins with semicolons (e.g., `"change;deep-thoughts;thinking"`).
- **`normalize_url(val)`**: Trims whitespace and ensures the URL starts with `http://` or `https://`.

---

## 11. Validation Framework

Located in `processing/validation.py`, records are screened against explicit quality rules before entering the final dataset:

| Failure Identifier | Rule Condition | Severity |
| :--- | :--- | :--- |
| `unknown_source` | `source` must be in `{"Books to Scrape", "Quotes to Scrape"}` | Critical / Reject |
| `missing_name` | `name_or_title` is missing, empty, or whitespace-only | Critical / Reject |
| `invalid_url` | `source_url` is missing or does not begin with `http://` or `https://` | Critical / Reject |
| `invalid_price` | `price` is present but `< 0` or non-numeric | Critical / Reject |
| `invalid_rating` | `rating` is present but not an integer in `{1, 2, 3, 4, 5}` | Critical / Reject |

The `validate_dataset` function partitions records into valid items and rejected items, logging a `WARNING` for every rejected record and compiling a tally of failure counts for the final JSON summary report.

---

## 12. Duplicate Detection & Fingerprinting

Identical records frequently arrive with minor formatting differences (e.g., `"Example Book Title"`, `" Example Book Title "`, `"EXAMPLE BOOK TITLE"`). Exact string equality fails on these cases.

### Fingerprinting Strategy
1. **Source-Specific Key Extraction**:
   - **Books to Scrape**: `source + name_or_title`
   - **Quotes to Scrape**: `source + author + name_or_title[:50]` *(First 50 characters prevents minor trailing discrepancies while uniquely identifying the quote)*
2. **Canonical Normalization**:
   - Convert to lowercase.
   - Remove punctuation and symbols (`re.sub(r"[^\w\s]", "", key)`).
   - Collapse multiple whitespace characters into single spaces.
3. **Cryptographic Hashing**:
   - Hash the normalized string with `hashlib.sha256()`.
   - Store fingerprints in a set to identify recurring records in $O(1)$ time.

### Removal vs. Flagging Strategy
- By default, duplicates are dropped from the final output dataset to produce a clean, ready-to-query dataset.
- Passing `--flag-duplicates` retains duplicate rows with an added boolean column `is_duplicate` (`True` or `False`), allowing reviewers to analyze data duplication patterns without discarding records.

---

## 13. Resilient Error Handling & Networking

1. **Exponential Backoff**: Configured via `urllib3.util.Retry(total=3, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504])`.
2. **Polite Request Throttling**: A configurable delay (default `0.5s`) pauses between requests to respect server capacity.
3. **Per-Record Isolation**: If an individual HTML element is malformed, exception handling logs the warning and continues extracting the remaining items on the page.
4. **Per-Source Isolation**: Books and Quotes scrapers run in isolated `try...except` blocks in `main.py`. A network failure in one source does not prevent the other source from completing.
5. **Comprehensive Logging**: Dual log outputs to console (stdout) and `logs/scraper.log` capture every request, page transition, warning, and fatal error.

---

## 14. Output Artifacts & Summary Report

Executing `python main.py` produces three files:

### 1. `output/final_dataset.csv`
Contains the consolidated, cleaned, and deduplicated records. Standard column headers:
`source,name_or_title,category,price,rating,author,tags,description,source_url,scraped_at`

### 2. `output/summary_report.json`
An audit report providing transparent metrics:
```json
{
    "pipeline_status": "SUCCESS",
    "start_time": "2026-10-06T16:35:10.123456+00:00",
    "end_time": "2026-10-06T16:36:25.654321+00:00",
    "duration_seconds": 75.53,
    "collected_per_source": {
        "Books to Scrape": 1000,
        "Quotes to Scrape": 100
    },
    "total_raw_collected": 1100,
    "cleaned_per_source": {
        "Books to Scrape": 1000,
        "Quotes to Scrape": 100
    },
    "total_cleaned": 1100,
    "validation_summary": {
        "valid_records": 1100,
        "rejected_records": 0,
        "rejected_by_reason": {
            "unknown_source": 0,
            "missing_name": 0,
            "invalid_url": 0,
            "invalid_price": 0,
            "invalid_rating": 0
        }
    },
    "duplicate_summary": {
        "duplicates_detected": 0,
        "strategy": "removed"
    },
    "final_record_count": 1100,
    "reconciliation_passed": true
}
```

### 3. `logs/scraper.log`
Full operational audit trail recording timestamps, log levels, fetched URLs, extracted record tallies, and warnings.

---

## 15. Running Unit Tests

The test suite contains **38 automated unit tests** in the `tests/` directory covering cleaning, validation, and deduplication edge cases without requiring an active internet connection.

Run all tests:
```bash
pytest -v
```

Test coverage includes:
- Whitespace stripping and non-breaking space replacement (`\xa0`).
- Typographic quote stripping (curly quotes, guillemets, straight quotes).
- Currency extraction across multiple formats and mojibake prevention (`Â£`).
- Word and numeric rating conversion (`"One"` -> `1`, `"star-rating Three"` -> `3`).
- Tag sorting, lowercasing, and delimitation.
- Business rule validations (missing titles, invalid URLs, negative prices, out-of-range ratings).
- Case- and space-insensitive duplicate detection with SHA-256 fingerprinting.

---

## 16. Assumptions & Known Limitations

1. **Book Listing vs. Product Detail Pages**:
   - The book catalog listing pages (`books.toscrape.com/catalogue/page-X.html`) provide Title, Price, Rating, In-Stock Availability, and Detail URL, but do **not** display Category or Description.
   - Fetching individual product detail pages for 1,000 books would generate 1,000 additional network requests. At a polite 0.5s rate limit, this would increase execution time by 8+ minutes and create unnecessary load on the practice server.
   - **Decision**: In alignment with the assignment guidelines (Stage 2), category and description remain empty (`None`) for book listing records. We strictly avoid guessing or fabricating values.
2. **Real-World Duplicate Discovery on Books to Scrape**:
   - Books to Scrape actually contains 1 real-world duplicate: the title **"The Star-Touched Queen"** appears on page 12 (item 764: `the-star-touched-queen_764/index.html`) and again on page 18 (item 642: `the-star-touched-queen_642/index.html`).
   - Our deduplication logic successfully detects this live duplicate and deduplicates it, bringing the final dataset from 1,100 raw records down to 1,099 unique records.
   - Additional synthetic duplicates (variations in case, punctuation, and whitespace) are thoroughly verified via `tests/test_deduplication.py`.
3. **Rate Limiting**:
   - A polite default delay of `0.5s` is applied between page requests (customizable via `--delay`). While lower delays execute faster, this rate respects server capacity.

---

## 17. Interview Discussion Guide

Be prepared to answer common technical questions about this implementation:

- **Q: Why choose Requests + BeautifulSoup over Playwright or Selenium?**  
  *A:* Both target websites are static, server-rendered HTML applications. Headless browser automation (Playwright/Selenium) introduces substantial CPU/memory overhead, requires browser binary installations, and runs orders of magnitude slower without providing any benefit since no JavaScript hydration or user interaction is required. `requests` + `BeautifulSoup` with `lxml` is lightweight, deterministic, fast, and dependency-minimal.

- **Q: How does dynamic pagination operate?**  
  *A:* Rather than iterating through a hardcoded range (`1..50`), our scraper inspects the DOM for `li.next > a`. If found, `urllib.parse.urljoin` computes the absolute URL from the relative `href`, allowing the scraper to seamlessly navigate varying relative directory depths (e.g., `/` to `catalogue/page-2.html` to `page-3.html`). When the selector returns `None`, the loop terminates naturally.

- **Q: How are network disruptions handled?**  
  *A:* Network resilience is layered:
  1. `urllib3.util.Retry` performs exponential backoff on HTTP 429, 500, 502, 503, and 504.
  2. A 10-second socket timeout prevents hung threads.
  3. Per-source try/except blocks ensure failure on one site does not crash the other.
  4. Per-record parsing try/except prevents single corrupted elements from aborting a page.

- **Q: How does your deduplication strategy prevent false negatives?**  
  *A:* Exact string matching fails on whitespace or case differences. We extract source-specific identifying fields, strip punctuation, convert to lowercase, collapse whitespace, and compute a SHA-256 fingerprint. For quotes, using author + first 50 characters prevents trailing differences while uniquely resolving the quote.

- **Q: What would you change for a production environment at scale?**  
  *A:*
  1. Distributed scraping with asynchronous I/O (`aiohttp` / `scrapy` / `celery`) and distributed queues (RabbitMQ/Redis).
  2. Rotating proxy pools with header randomization and TLS fingerprint management.
  3. Database storage (PostgreSQL with `ON CONFLICT DO NOTHING` or MongoDB) with incremental change detection (`If-Modified-Since` / ETag headers).
  4. Observability and alerting via Prometheus metrics and OpenTelemetry tracing.

---

## 18. AI Usage Summary

In accordance with Section 11 of the assignment specification, all AI tooling, prompts, architectural verifications, and corrected suggestions are documented in [AI_USAGE.md](AI_USAGE.md).
