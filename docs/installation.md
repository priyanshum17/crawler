# Installation & Setup

## 1 — Prerequisites
- **Python ≥ 3.11**  
- macOS / Linux (paths are POSIX-style; Windows works with minor tweaks)  
- A sensible `ulimit -n` (≥ 1024) to avoid hitting the open-file ceiling

## 2 — Clone & create a virtual-env
```bash
git clone https://github.com/priyanshum17crawler.git
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