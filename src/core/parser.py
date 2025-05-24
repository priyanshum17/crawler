from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import re
from collections import Counter
from datetime import datetime

def parse_html(base_url, html_bytes):
    soup = BeautifulSoup(html_bytes, "html.parser")

    title = soup.title.string.strip() if (soup.title and soup.title.string) else ""

    meta_description = ""
    meta_keywords = ""
    robots_meta = ""
    publication_date = ""

    for tag in soup.find_all("meta"):
        name = tag.get("name", "").lower()
        if name == "description":
            meta_description = tag.get("content", "")
        elif name == "keywords":
            meta_keywords = tag.get("content", "")
        elif name == "robots":
            robots_meta = tag.get("content", "")
        elif name == "publication_date":
            publication_date = tag.get("content", "")

    text_content = soup.get_text(separator=" ", strip=True)

    headings = [
        h.get_text(strip=True)
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    ]

    keywords = _extract_keywords(base_url, title, meta_keywords, headings)

    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        links.add(full_url)

    rec = {
        "url": base_url,
        "http_status": 200,  # you can override later
        "fetch_time": "",  # you can override later
        "content_type": "text/html",  # override later
        "title": title,
        "meta_description": meta_description,
        "meta_keywords": meta_keywords,
        "text_content": text_content,
        "headings": json.dumps(headings),
        "outbound_links": json.dumps(list(links)),
        "keywords": keywords,
        "robots_meta": robots_meta,
        "publication_date": datetime.now().isoformat(),
    }
    return rec


_STOP = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "http",
    "https",
    "www",
    "com",
    "edu",
    "org",
    "gatech",
}


def _extract_keywords(url: str, title: str, meta_kw: str, headings: list[str]) -> str:
    """
    Choose up to 5 keywords (comma-separated) that summarise the page.

    Priority:
      1. If <meta name="keywords"> exists, just use that.
      2. Otherwise – take words from title + H1/H2 + URL path, strip
         stop-words, rank by frequency, return the top 5.
    """
    if meta_kw:
        kws = {k.strip().lower() for k in meta_kw.split(",") if k.strip()}
        return ",".join(kws)

    corpus = " ".join([title] + headings + url.split("/"))
    words = re.findall(r"[a-zA-Z]{3,}", corpus.lower())
    words = [w for w in words if w not in _STOP]

    most_common = [w for w, _ in Counter(words).most_common(5)]
    return ",".join(most_common)