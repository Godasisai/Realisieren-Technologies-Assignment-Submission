# AI Usage Disclosure (AI_USAGE.md)

In accordance with Section 11 of the technical assessment instructions, this document provides complete transparency regarding the use of AI tools throughout the development of this assignment.

---

## 1. AI Tools Used

- **Primary Tool**: Google DeepMind Gemini 3.8 Flash (Agentic Coding Assistant)
- **Secondary Tools**: GitHub Copilot / Cursor (IDE code completion and documentation formatting)

---

## 2. Purpose & Use Cases

AI tools were utilized across the following areas:
1. **Source Inspection & Selector Strategy**: Rapidly confirming standard CSS selectors for Books to Scrape and Quotes to Scrape DOM elements.
2. **Schema & Normalization Architecture**: Designing a unified, decoupled ETL schema that handles missing attributes without data fabrication.
3. **Resilient HTTP Session Pattern**: Synthesizing the `requests.Session` + `urllib3.util.Retry` exponential backoff configuration.
4. **Edge Case Brainstorming**: Identifying real-world edge cases in scraping (e.g., mojibake currency symbols like `Â£`, truncated book titles in HTML text vs. `title` attributes, curly quotation mark variations).
5. **Unit Test Suite Generation**: Formulating parametric test fixtures for cleaning functions, validation rules, and duplicate detection scenarios.

---

## 3. Representative Prompts

### Prompt 1: Resilient HTTP Adapter with Exponential Backoff
> *"Show me how to configure a Python `requests.Session` using `urllib3.util.Retry` with an exponential backoff factor for status codes 429, 500, 502, 503, and 504, including a custom User-Agent."*

### Prompt 2: Robust Duplicate Fingerprinting Strategy
> *"I have two scraping sources: Books to Scrape (titles) and Quotes to Scrape (quote text + author). Suggest a deduplication fingerprint function in Python using SHA-256 that ignores casing, punctuation, and leading/trailing/multiple spaces, while accounting for slight trailing differences in quote texts."*

### Prompt 3: Unit Testing Edge Cases for Data Cleaning
> *"Write a comprehensive set of pytest unit tests for string cleaning and currency parsing that handles non-breaking spaces `\xa0`, mojibake currency symbols like `Â£51.77`, word-based ratings ('Three' -> 3), and curly quotes like `“` and `”`."*

---

## 4. Which Parts of the Code Were AI-Assisted

| Component | Level of AI Assistance | Developer Review & Adjustments Made |
| :--- | :--- | :--- |
| `scrapers/base_scraper.py` | Initial boilerplate generation | Added explicit `response.encoding = 'utf-8'` to prevent character corruption; added configurable polite sleep. |
| `scrapers/books_scraper.py` | Selector lookup assistance | **Crucial Correction**: Discovered that visible book text inside `<h3><a>` is truncated with `...` (e.g., `"A Light in the ..."`). Adjusted logic to extract `link.get("title")` attribute first. |
| `scrapers/quotes_scraper.py` | Selector assistance | Configured author bio URL resolution via `urljoin` and normalized multi-tag extraction. |
| `processing/cleaning.py` | Function skeletons & regex | Added comprehensive support for non-breaking spaces (`\xa0`), typographic quotes (`“`, `”`, `«`, `»`), and flexible rating parsing. |
| `processing/validation.py` | Rule definition | Structured return values as diagnostic problem lists rather than booleans to support transparent summary reporting. |
| `processing/deduplication.py`| Fingerprint logic draft | Verified against Stage 7 specifications: books (`source + title`), quotes (`source + author + text[:50]`). |
| `tests/` | Test case generation | Expanded test suite to 38 unit tests covering all edge cases. |

---

## 5. Important Corrections & Mistakes Discovered in AI Output

During the evaluation and review of AI-generated suggestions, several critical issues were identified and manually corrected:

1. **Truncated Book Titles in DOM**:
   - *AI Suggestion*: `article.select_one("h3 > a").get_text()`
   - *Issue*: On `books.toscrape.com`, long titles are truncated in the DOM text with `...` (e.g., `A Light in the ...`).
   - *Correction*: Inspected the actual DOM and updated the parser to read `link.get("title")` which holds the unabridged full title, falling back to text only if the attribute is absent.

2. **Currency Mojibake (`Â£`)**:
   - *AI Suggestion*: Using `response.text` directly without specifying encoding.
   - *Issue*: `requests` defaults to ISO-8859-1 for certain HTTP headers when charset is omitted, converting `£` into `Â£`.
   - *Correction*: Explicitly set `response.encoding = "utf-8"` immediately upon receiving the response in `fetch_soup`, and added regex cleaning that gracefully parses either format.

3. **Relative URL Resolution Across Differing Page Depths**:
   - *AI Suggestion*: Naive string concatenation `f"{base_url}/{href}"`.
   - *Issue*: Books to Scrape uses different relative pathing on page 1 (`catalogue/page-2.html`) versus page 2 (`page-3.html`). Naive string joining produces invalid nested URLs like `catalogue/catalogue/page-3.html`.
   - *Correction*: Utilized standard `urllib.parse.urljoin(current_url, href)` which correctly handles RFC 3986 relative path calculations.

4. **Avoiding Unnecessary Detail Page Overhead**:
   - *AI Suggestion*: Suggested visiting all 1,000 product detail pages sequentially to fetch book categories and descriptions.
   - *Issue*: Visiting 1,000 extra pages with a polite 0.5s pause adds 500+ seconds (8+ minutes) of scraping and creates excessive load on the practice server.
   - *Correction*: Aligned with the assignment's explicit guideline (Stage 2) to extract records from listing pages, leaving category and description empty, and documenting this architectural decision clearly in the README.

---

## 6. Verification and Testing Methodology

The final implementation was rigorously verified through a multi-step testing procedure:

1. **Clean Virtual Environment Build**:
   - Created a fresh Python 3.12 virtual environment and installed dependencies exclusively from `requirements.txt`.
2. **Automated Unit Testing**:
   - Executed `pytest -v`, ensuring all 38 unit tests for cleaning, validation, and deduplication passed with 0 failures and 0 warnings.
3. **Smoke Test Run**:
   - Executed `python main.py --max-pages-books 2 --max-pages-quotes 2` to verify end-to-end integration, CSV generation, and summary reporting.
4. **Full Production Run**:
   - Ran `python main.py` across all 50 pages of Books to Scrape (1,000 records) and all 10 pages of Quotes to Scrape (100 records).
   - Inspected `output/final_dataset.csv`, `output/summary_report.json`, and `logs/scraper.log`.
5. **Reconciliation Verification**:
   - Verified that the summary report metrics mathematically reconcile:
     $$\text{Final Record Count} = \text{Raw Records} - \text{Rejected Records} - \text{Duplicate Records}$$
     $$1100 = 1100 - 0 - 0$$
