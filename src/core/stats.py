import asyncio
import json
import os
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import aiosqlite
import matplotlib.pyplot as plt

DB_PATH    = "data/crawl.db"
RAW_DIR    = Path("data/raw")
RESULTS    = Path("results")
RESULTS.mkdir(exist_ok=True)
PLOT_FILE  = RESULTS / "crawl_speed.png"
TXT_FILE   = RESULTS / "summary.txt"
JSON_FILE  = RESULTS / "summary.json"

async def column(db, sql, *params):
    rows = await db.execute_fetchall(sql, params or ())
    return [r[0] for r in rows]

async def main():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        total_pages = (await db.execute_fetchall("SELECT COUNT(*) FROM pages"))[0][0]

        status_rows = await db.execute_fetchall(
            "SELECT http_status, COUNT(*) FROM pages GROUP BY http_status"
        )
        status_break = {r[0]: r[1] for r in status_rows}
        ok_rate = status_break.get(200, 0) / total_pages if total_pages else 0

        ctype_rows = await db.execute_fetchall(
            "SELECT content_type, COUNT(*) FROM pages GROUP BY content_type"
        )
        ctype_break = {r[0]: r[1] for r in ctype_rows}

        kw_strings   = await column(db, "SELECT keywords FROM pages")
        kw_lists     = [k.split(",") if k else [] for k in kw_strings]
        flat_kws     = [k for lst in kw_lists for k in lst if k]
        unique_kw    = len(set(flat_kws))
        avg_kw_pp    = statistics.mean(len(lst) for lst in kw_lists) if kw_lists else 0
        pages_w_kw   = sum(1 for lst in kw_lists if lst)
        pages_wo_kw  = total_pages - pages_w_kw
        top10        = Counter(flat_kws).most_common(10)

        headings_col = await column(db, "SELECT headings FROM pages")
        avg_headings = statistics.mean(
            len(json.loads(h)) for h in headings_col if h
        ) if headings_col else 0

        links_col = await column(db, "SELECT outbound_links FROM pages")
        avg_links = statistics.mean(
            len(json.loads(l)) for l in links_col if l
        ) if links_col else 0

        domain_counts = Counter(
            urlparse(u).netloc for u in await column(db, "SELECT url FROM pages")
        ).most_common(5)

        sizes = [os.stat(RAW_DIR / f).st_size / 1024 for f in os.listdir(RAW_DIR)] if RAW_DIR.exists() else []
        avg_size = statistics.mean(sizes) if sizes else 0
        med_size = statistics.median(sizes) if sizes else 0
        min_size = min(sizes) if sizes else 0
        max_size = max(sizes) if sizes else 0

        failures = (await db.execute_fetchall("SELECT COUNT(*) FROM failures"))[0][0]
        fail_rows = await db.execute_fetchall(
            "SELECT error, COUNT(*) FROM failures GROUP BY error ORDER BY COUNT(*) DESC LIMIT 5"
        )
        top_fail = {r[0]: r[1] for r in fail_rows}

        timeline = await db.execute_fetchall("""
            SELECT
              substr(fetch_time, 1, 19) AS ts,           -- 'YYYY-MM-DD HH:MM'
              COUNT(*),
              SUM(length(keywords) > 0)
            FROM pages
            WHERE fetch_time IS NOT NULL AND fetch_time <> ''
            GROUP BY ts
            ORDER BY ts
        """)
        timeline = [row for row in timeline if row[0] is not None]
        ts, pages_pm, kw_pages_pm = zip(*timeline) if timeline else ([], [], [])
        avg_pages_pm = statistics.mean(pages_pm) if pages_pm else 0

    metrics = {
        "pages_total": total_pages,
        "http_200_rate": round(ok_rate, 4),
        "status_breakdown": status_break,
        "content_type_breakdown": ctype_break,
        "keywords_unique": unique_kw,
        "avg_keywords_per_page": round(avg_kw_pp, 2),
        "pages_with_keywords": pages_w_kw,
        "pages_without_keywords": pages_wo_kw,
        "avg_headings_per_page": round(avg_headings, 2),
        "avg_outbound_links_per_page": round(avg_links, 2),
        "top_keywords": top10,
        "top_domains": domain_counts,
        "html_size_avg_kib": round(avg_size, 1),
        "html_size_median_kib": round(med_size, 1),
        "html_size_min_max_kib": (round(min_size, 1), round(max_size, 1)),
        "failures_total": failures,
        "top_failures": top_fail,
        "avg_pages_per_minute": round(avg_pages_pm, 2),
    }

    # human-readable report
    lines = [
        "──────── Web-Archive Summary ────────",
        f"Pages crawled              : {metrics['pages_total']:,}",
        f"HTTP-200 success rate       : {metrics['http_200_rate']:.1%}",
        f"Content-types               : {metrics['content_type_breakdown']}",
        f"Unique keywords             : {metrics['keywords_unique']:,}",
        f"Avg keywords/page           : {metrics['avg_keywords_per_page']:.2f}",
        f"Pages w/ kw / w/o kw        : {metrics['pages_with_keywords']:,} / {metrics['pages_without_keywords']:,}",
        f"Avg headings/page           : {metrics['avg_headings_per_page']:.2f}",
        f"Avg outbound links/page     : {metrics['avg_outbound_links_per_page']:.2f}",
        f"Avg HTML size (KiB)         : {metrics['html_size_avg_kib']:.1f}  (median {metrics['html_size_median_kib']:.1f})",
        f"Min–Max HTML size (KiB)     : {metrics['html_size_min_max_kib']}",
        f"Failures total              : {metrics['failures_total']:,}",
        f"Top failures                : {metrics['top_failures']}",
        f"Average pages/min           : {metrics['avg_pages_per_minute']:.2f}",
        "",
        "Top-10 keywords:",
        *[f"  {kw:<15} {cnt:>5}" for kw, cnt in metrics["top_keywords"]],
        "",
        "Top-5 domains:",
        *[f"  {dom:<25} {cnt:>5}" for dom, cnt in metrics["top_domains"]],
    ]
    TXT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report saved → {TXT_FILE}")

    JSON_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"JSON saved   → {JSON_FILE}")

    if ts:
        plt.figure(figsize=(8, 4))
        plt.plot(ts, pages_pm,     label="Pages/min")
        plt.plot(ts, kw_pages_pm,  label="Pages w/ kw/min")
        plt.xticks(rotation=65, ha="right")
        plt.title("Crawl speed over time")
        plt.xlabel("Minute")
        plt.ylabel("Count")
        plt.legend()
        plt.tight_layout()
        plt.savefig(PLOT_FILE)
        print(f"Plot saved   → {PLOT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
