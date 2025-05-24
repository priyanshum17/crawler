# GT-Crawler

A focused, asynchronous web crawler that archives **cc.gatech.edu** pages, extracts structured metadata, and produces analytics & visualisations – all in under a thousand lines of Python.

> *Built for CS-6675 Summer 2025 – Priyanshu Mehta*

## Why I built it
I wanted a lightweight, easily-extensible crawler that could:
- respect concurrency & politeness without external services,
- store pages in a single SQLite file with FTS5 search,
- give me instant insight into crawl speed, failures, and keyword coverage.

## Key features
| Feature | Notes |
|---------|-------|
| Async I/O | `aiohttp` + `asyncio` worker pool (configurable concurrency) |
| In-scope filtering | Only crawls `*.cc.gatech.edu` – no surprises |
| WAL-backed SQLite | Durable, zero-setup DB with FTS5 for BM25 ranking |
| Raw HTML archive | Deduped by SHA-256; stored under `data/raw/` |
| Analytics scripts | Generate JSON report + PNG charts in `results/` |

## Quick start
```bash
git clone https://github.com/<you>/crawler.git
cd crawler
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py         
python scripts/report.py  
