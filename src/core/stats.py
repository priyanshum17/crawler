import asyncio
import json
import os
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from statistics import mean, median

import aiosqlite
import matplotlib.pyplot as plt

DB = "data/crawl.db"
RAW_DIR = Path("data/raw")
RES = Path("results")
RES.mkdir(exist_ok=True)
INC = 5
TXT_FILE = RES / "summary.txt"

def _snap(dt: datetime) -> datetime:
    return dt - timedelta(seconds=dt.second % INC, microseconds=dt.microsecond)

async def _series(sql: str):
    async with aiosqlite.connect(DB) as db:
        rows = await db.execute_fetchall(sql)

    buckets = {}
    for (ts,) in rows:
        if not ts:
            continue
        try:
            key = _snap(datetime.fromisoformat(ts.replace("Z", "+00:00")))
        except ValueError:
            continue
        buckets[key] = buckets.get(key, 0) + 1

    if not buckets:
        return [], []

    t = min(buckets)
    end = max(buckets)
    x, y = [], []
    while t <= end:
        x.append(t)
        y.append(buckets.get(t, 0))
        t += timedelta(seconds=INC)
    return x, y

async def viz_links():
    sql = """
        SELECT p.publication_date
        FROM pages p, json_each(p.outbound_links)
        WHERE p.publication_date <> ''
    """
    x, y = await _series(sql)
    if not x:
        return
    total = 0
    y_cum = []
    for v in y:
        total += v
        y_cum.append(total)
    plt.figure(figsize=(10, 4))
    plt.plot(x, y_cum, color="tab:orange")
    plt.title("Cumulative links extracted (5-s buckets)")
    plt.tight_layout()
    out = RES / "links_per_5s.png"
    plt.savefig(out)
    plt.close()
    print("Saved", out)

async def viz_urls():
    x, y = await _series("SELECT publication_date FROM pages WHERE publication_date <> ''")
    if not x:
        return
    total = 0
    y_cum = []
    for v in y:
        total += v
        y_cum.append(total)
    plt.figure(figsize=(10, 4))
    plt.plot(x, y_cum, color="tab:green")
    plt.title("Cumulative URLs scraped (5-s buckets)")
    plt.tight_layout()
    out = RES / "urls_per_5s.png"
    plt.savefig(out)
    plt.close()
    print("Saved", out)

async def summary():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row

        total_pages = (await db.execute_fetchall("SELECT COUNT(*) FROM pages"))[0][0]

        status_break = dict(await db.execute_fetchall("SELECT http_status, COUNT(*) FROM pages GROUP BY http_status"))
        ok_rate = status_break.get(200, 0) / total_pages if total_pages else 0

        ctype_break = dict(await db.execute_fetchall("SELECT content_type, COUNT(*) FROM pages GROUP BY content_type"))

        kw_strings = [r[0] for r in await db.execute_fetchall("SELECT keywords FROM pages")]
        kw_lists = [k.split(",") if k else [] for k in kw_strings]
        flat_kws = [k for sub in kw_lists for k in sub if k]
        unique_kw = len(set(flat_kws))
        avg_kw_pp = mean(len(lst) for lst in kw_lists) if kw_lists else 0
        pages_w_kw = sum(1 for lst in kw_lists if lst)
        pages_wo_kw = total_pages - pages_w_kw
        top10 = Counter(flat_kws).most_common(10)

        headings_col = [r[0] for r in await db.execute_fetchall("SELECT headings FROM pages")]
        avg_headings = mean(len(json.loads(h)) for h in headings_col if h) if headings_col else 0

        links_col = [r[0] for r in await db.execute_fetchall("SELECT outbound_links FROM pages")]
        avg_links = mean(len(json.loads(l)) for l in links_col if l) if links_col else 0

        domain_counts = Counter(urlparse(u).netloc for u, in await db.execute_fetchall("SELECT url FROM pages")).most_common(5)

        sizes = [os.stat(RAW_DIR / f).st_size / 1024 for f in os.listdir(RAW_DIR)] if RAW_DIR.exists() else []
        avg_size = mean(sizes) if sizes else 0
        med_size = median(sizes) if sizes else 0
        min_size = min(sizes) if sizes else 0
        max_size = max(sizes) if sizes else 0

        failures = (await db.execute_fetchall("SELECT COUNT(*) FROM failures"))[0][0]
        top_fail = dict(await db.execute_fetchall("SELECT error, COUNT(*) FROM failures GROUP BY error ORDER BY COUNT(*) DESC LIMIT 5"))

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
        "html_size_avg_kib": round(avg_size, 1),
        "html_size_median_kib": round(med_size, 1),
        "html_size_min_max_kib": (round(min_size, 1), round(max_size, 1)),
        "failures_total": failures,
        "top_failures": top_fail,
        "top_keywords": top10,
        "top_domains": domain_counts,
    }

    lines = [
        "──────── Web-Archive Summary ────────",
        f"Pages crawled             : {metrics['pages_total']:,}",
        f"HTTP-200 success rate      : {metrics['http_200_rate']:.1%}",
        f"Content-types              : {metrics['content_type_breakdown']}",
        f"Unique keywords            : {metrics['keywords_unique']:,}",
        f"Avg keywords/page          : {metrics['avg_keywords_per_page']:.2f}",
        f"Pages w/kw / w/o kw        : {metrics['pages_with_keywords']:,} / {metrics['pages_without_keywords']:,}",
        f"Avg headings/page          : {metrics['avg_headings_per_page']:.2f}",
        f"Avg outbound links/page    : {metrics['avg_outbound_links_per_page']:.2f}",
        f"Avg HTML size KiB          : {metrics['html_size_avg_kib']:.1f} (median {metrics['html_size_median_kib']:.1f})",
        f"Min–Max HTML size KiB      : {metrics['html_size_min_max_kib']}",
        f"Failures total             : {metrics['failures_total']:,}",
        f"Top failures               : {metrics['top_failures']}",
        "",
        "Top-10 keywords:",
        *[f"  {k:<15} {c:>5}" for k, c in metrics["top_keywords"]],
        "",
        "Top-5 domains:",
        *[f"  {d:<25} {c:>5}" for d, c in metrics["top_domains"]],
    ]

    TXT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print("Report saved →", TXT_FILE)

async def run_all():
    await summary()
    await viz_links()
    await viz_urls()