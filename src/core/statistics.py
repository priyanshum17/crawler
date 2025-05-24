import asyncio, aiosqlite, matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path

DB = "data/crawl.db"
RES = Path("results"); RES.mkdir(exist_ok=True)
INC = 5

def _snap(dt): return dt - timedelta(seconds=dt.second % INC, microseconds=dt.microsecond)

async def _series(sql):
    async with aiosqlite.connect(DB) as db:
        rows = await db.execute_fetchall(sql)
    c = {}
    for ts, in rows:
        if not ts: continue
        try: k = _snap(datetime.fromisoformat(ts.replace("Z", "+00:00")))
        except ValueError: continue
        c[k] = c.get(k, 0) + 1
    if not c: return [], []
    t0, t1 = min(c), max(c)
    x, y = [], []
    while t0 <= t1:
        x.append(t0); y.append(c.get(t0, 0)); t0 += timedelta(seconds=INC)
    return x, y

async def viz_links_per_5s():
    sql = """
        SELECT p.publication_date
        FROM pages p, json_each(p.outbound_links)
        WHERE p.publication_date <> ''
    """
    x, y = await _series(sql)
    if not x: return
    total = 0
    y_cum = []
    for v in y:
        total += v
        y_cum.append(total)
    plt.figure(figsize=(10,4))
    plt.plot(x, y_cum, color="tab:orange")
    plt.title(f"Cumulative links extracted (5-s buckets)")
    plt.tight_layout()
    out = RES / "links_per_5s.png"
    plt.savefig(out)
    plt.close()
    print("Saved", out)


async def viz_urls_cumulative_5s():
    x, y = await _series(
        "SELECT publication_date FROM pages WHERE publication_date <> ''"
    )
    if not x:
        return
    c = 0
    ycum = []
    for v in y:
        c += v
        ycum.append(c)
    plt.figure(figsize=(10, 4))
    plt.plot(x, ycum, color="tab:green")
    plt.title(f"Cumulative URLs scraped (5-s buckets)")
    plt.tight_layout()
    out = RES / "urls_cumulative_5s.png"
    plt.savefig(out)
    plt.close()
    print("Saved", out)


if __name__ == "__main__":
    asyncio.run(viz_links_per_5s()); asyncio.run(viz_urls_cumulative_5s())
