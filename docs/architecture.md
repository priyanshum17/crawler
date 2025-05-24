# Architecture

This document goes deep into how GT-Crawler is wired up: data flow, module boundaries, concurrency strategy, and design trade-offs.

---

## 1. Module responsibilities

| Module                     | Core functions                                   | Notes                                                              |
| -------------------------- | ------------------------------------------------ | ------------------------------------------------------------------ |
| **`src/core/crawler.py`**  | `start()`, `worker()`, `handle_url()`            | Queue orchestration, scope filter, persistence                     |
| **`src/core/parser.py`**   | `parse_html()`, `_extract_keywords()`            | BeautifulSoup HTML parsing, keyword heuristics, link normalisation |
| **`src/core/database.py`** | `init_db()`, `delete_db()`                       | Executes `DDL`, WAL mode, connection factory                       |
| **`src/core/search.py`**   | `search_pages()`                                 | BM25 ranking via FTS5 `bm25()`                                     |
| **`scripts/report.py`**    | Main metrics pipeline                            | Aggregates 20+ stats → TXT, JSON, PNG                              |
| **`scripts/viz_speed.py`** | `viz_links_per_5s()`, `viz_urls_cumulative_5s()` | 5-second bucket charts                                             |

---

## 2. Data model

```text
pages
 ├─ url (PK)
 ├─ http_status
 ├─ fetch_time  (UTC ISO-8601)
 ├─ content_type
 ├─ title
 ├─ meta_description
 ├─ meta_keywords
 ├─ text_content
 ├─ headings           -- JSON array
 ├─ outbound_links      -- JSON array
 ├─ keywords            -- comma-separated top-5
 ├─ publication_date
 └─ raw_html_path       -- on-disk pointer

pages_fts (virtual, content=pages)  -- FTS5 index
failures                         -- transient errors
```

### Rationale

*SQLite WAL* lets readers (report scripts) run while writes are in progress.
FTS5 gives **BM25** relevance with a single SQL call – no external search stack.

---

## 3. Concurrency model

| Aspect        | Implementation                             | Reasoning                                                                                 |
| ------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Worker count  | `CONCURRENCY = 10`                         | Empirically saturates outbound bandwidth on my MacBook Air without tripping GT throttling |
| Back-pressure | `frontier.join()` + timeouts               | Guarantees graceful shutdown when queue drains                                            |
| Timeouts      | 5 s queue pop; 20 s network (configurable) | Prevents zombie tasks on slow sites                                                       |
| Dedupe        | `self.seen` in-memory set                  | Cheap for ≤ 60 k URLs; Bloom filter planned for > 1 M                                     |

---

## 4. Crawl statistics

The crawler logs granular timing, letting me compute:

| Metric               | Description                                       |
| -------------------- | ------------------------------------------------- |
| **Pages/min**        | Number of pages successfully persisted per minute |
| **Links/min**        | Outbound link discoveries per minute              |
| **HTTP-200 rate**    | `#200 / #pages_total`                             |
| **Scope hit-ratio**  | `#URL accepted / #URL seen`                       |
| **Completion ratio** | `pages_done / MAX_PAGES`                          |

**scripts/report.py** dumps these to `summary.json`; the following excerpt shows typical output after a 1 k-page run:

```json
{
  "pages_total": 1000,
  "http_200_rate": 0.945,
  "avg_pages_per_minute": 82.3,
  "avg_outbound_links_per_page": 14.7,
  "failures_total": 18
}
```

You can export the JSON to Excel or feed it into Grafana for long-running experiments.

---

## 5. Design review

### Pros

* **Zero external deps** – SQLite + pure-Python → portable, easy CI.
* **Deterministic scope** – avoids legal grey-areas by hard-coding domain filter.
* **Real-time analytics** – spin up the report script mid-crawl; WAL isolation keeps things consistent.
* **Low-memory** – only URLs and a hash-set in RAM.

### Cons

* **Single-host bottleneck** – saturates once `*.cc.gatech.edu` throttles; no polite host-sharding yet.
* **In-memory dedupe** – doesn’t scale beyond \~10 M URLs; would switch to disk-backed Bloom.
* **No Robots.txt handling** – OK for internal domain, but would need adding for public crawls.
* **HTML-only focus** – other MIME types stored raw; full parsing (PDF, image alt-text) is out of scope.

---

## 6. Future work

* **Adaptive politeness**: dynamic delay based on historical latency.
* **Distributed mode**: split frontier across Redis, workers in Kubernetes.
* **Rich media extraction**: title/EXIF/alt-text for images & PDFs.
