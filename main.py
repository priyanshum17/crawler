import argparse
import asyncio
import json
import time
from pathlib import Path

import aiosqlite
from core.stats import run_all

from src.core.crawler import Crawler
from src.core.database import clear_directory
from src.core.settings import configuration as cfg

DB = cfg.DB_PATH
RES = Path("results")


async def run_crawl():
    start = time.perf_counter()
    await Crawler().start()
    elapsed = time.perf_counter() - start
    print(f"Crawler finished in {elapsed:.2f} seconds")


async def run_stats():
    await run_all()


async def show_recent(limit=10):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            f"SELECT * FROM pages ORDER BY publication_date DESC LIMIT {limit}"
        )
    for row in rows:
        print(json.dumps(dict(row), indent=2))


def main():
    parser = argparse.ArgumentParser(description="Crawler command line utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("crawl")
    subparsers.add_parser("stats")
    subparsers.add_parser("viz")

    recent_parser = subparsers.add_parser("recent")
    recent_parser.add_argument(
        "-n", type=int, default=10, help="Number of recent rows to display"
    )

    args = parser.parse_args()

    if args.command == "crawl":
        asyncio.run(run_crawl())
    elif args.command == "stats":
        asyncio.run(run_all())
    elif args.command == "recent":
        asyncio.run(show_recent(args.n))
    elif args.command == "clear":
        clear_directory()
        print("Cleared the data directory.")


if __name__ == "__main__":
    main()
