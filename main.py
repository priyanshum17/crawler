import asyncio
import time

from src.core.crawler import Crawler

if __name__ == "__main__":
    t0 = time.perf_counter()
    asyncio.run(Crawler().start())
    elapsed = time.perf_counter() - t0
    print(f"\nCrawler finished in {elapsed:.2f} s")
