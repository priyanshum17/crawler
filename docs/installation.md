# Installation & Setup

## 1 — Prerequisites
- **Python ≥ 3.11**  
- macOS / Linux (paths are POSIX-style; Windows works with minor tweaks)  
- A sensible `ulimit -n` (≥ 1024) to avoid hitting the open-file ceiling

## 2 — Clone & create a virtual-env
```bash
git clone https://github.com/<your-gh-handle>/crawler.git
cd crawler
python -m venv .venv
source .venv/bin/activate
````

## 3 — Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

<details>
<summary>Optional dev tools</summary>

```bash
pip install ruff   # import-sort & lint
pip install black  # automatic formatting
```

</details>

## 4 — Configure paths (optional)

`config.json` overrides default locations:

```jsonc
{
  "DB_PATH": "data/crawl.db",
  "DB_LOCATION": "data/"
}
```

## 5 — Run the crawler

```bash
python main.py          # begins crawl
```

Live output is terse; open the `results/` folder afterwards for summaries and plots.

## 6 — Generate detailed reports

```bash
python scripts/report.py
python scripts/viz_speed.py
```

The scripts export:

* `summary.json` – consumable by pandas/Excel
* `crawl_speed.png`, `links_per_5s.png`, `urls_cumulative_5s.png` – ready for slide decks

---

### Export to Excel

```python
import pandas as pd, json
with open("results/summary.json") as f:
    df = pd.json_normalize(json.load(f))
df.to_excel("results/summary.xlsx", index=False)
```

Happy crawling!

