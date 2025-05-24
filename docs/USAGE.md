# Command-Line Reference & Expected Runtimes

Every interaction happens through the package entry-point:

```bash
python -m crawler <command> [options]
````

---

## Commands

| Command  | Options                          | Description                                                                                                                                                                                   | Typical runtime          |
| -------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `crawl`  | `--max-pages INT` (override)     | Launches the asynchronous crawler. Spawns 10 workers by default, each maintaining its own `aiohttp` connection pool. Stops when either the frontier empties or the page cap is reached.       | 60 – 90 s for 1000 pages |
| `stats`  | *(none)*                         | Generates the full analytics suite: <br>• `results/summary.txt` – 17 metrics <br>• `results/urls_per_5s.png` – crawl throughput <br>• `results/links_per_5s.png` – link extraction throughput | 3 – 4 s                  |
| `viz`    | *(none)*                         | Alias for `stats`; kept for backwards compatibility.                                                                                                                                          | 3 – 4 s                  |
| `recent` | `-n / --number INT` (default=10) | Pretty-prints the *n* most recent rows from `pages`, ordered by `publication_date`. Useful sanity-check during long crawls.                                                                   | < 1 s                    |
| `clear`  | *(none)*                         | Recursively deletes `data/` (database + raw HTML) and empties `results/`. Safe to run multiple times.                                                                                         | ≤ 1 s                    |

---

## Environment Variables

| Variable            | Default                 | Purpose                                             |
| ------------------- | ----------------------- | --------------------------------------------------- |
| `CRAWL_MAX_PAGES`   | `1000`                  | Upper bound on pages to fetch (overrides CLI flag). |
| `CRAWL_CONCURRENCY` | `10`                    | Number of asynchronous workers.                     |
| `USER_AGENT`        | Modern Chrome UA string | Sent in the `User-Agent` header of every request.   |

---

## Exit Codes

| Code | Meaning                                                  |
| ---- | -------------------------------------------------------- |
| `0`  | Success                                                  |
| `2`  | CLI usage error (invalid flag/sub-command)               |
| `10` | Unexpected exception inside crawler (see console output) |

---

## Troubleshooting FAQ

| Symptom                          | Cause                                             | Fix                                                                                         |
| -------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: aiosqlite` | Dependencies not installed in active interpreter. | Activate venv and run `pip install -r requirements.txt`.                                    |
| Crawl exits after a few pages    | Default `MAX_PAGES` reached too quickly.          | Run `crawl --max-pages 5000` or set environment variable.                                   |
| PNG plots are empty              | Crawl didn’t fetch any pages.                     | Ensure network connectivity and that `SEED_URL` resolves.                                   |
| `SSL: CERTIFICATE_VERIFY_FAILED` | macOS lacks recent CA bundle.                     | Run `/Applications/Python*/Install Certificates.command` or `brew install ca-certificates`. |

---

## Performance Tips

* Increase concurrency cautiously – beyond \~32 workers, SQLite begins to throttle.
* Store DB on an SSD – WAL writes are fsync-heavy.
* Add a politeness delay (`await asyncio.sleep(0.5)`) when targeting remote servers to avoid bans.

---

> For further details see [`docs/architecture.md`](docs/architecture.md).
