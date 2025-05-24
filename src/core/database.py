import aiosqlite
import os
import shutil

from src.core.settings import configuration

DDL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS pages (
  url TEXT PRIMARY KEY,
  http_status INTEGER,
  fetch_time TEXT,
  content_type TEXT,
  title TEXT,
  meta_description TEXT,
  meta_keywords TEXT,
  text_content TEXT,
  headings TEXT,
  outbound_links TEXT,
  media TEXT,
  canonical_url TEXT,
  robots_meta TEXT,
  keywords TEXT,              
  publication_date TEXT,
  raw_html_path TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts
USING fts5(title, text_content, meta_description, content='pages', content_rowid='rowid');

CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages
BEGIN
  INSERT INTO pages_fts(rowid, title, text_content, meta_description)
  VALUES (new.rowid, new.title, new.text_content, new.meta_description);
END;

CREATE TABLE IF NOT EXISTS failures (
  url TEXT PRIMARY KEY,
  error TEXT,
  fail_time TEXT
);
"""


def delete_db():
    """Delete the existing database file if it exists."""
    if os.path.exists(configuration.DB_PATH):
        os.remove(configuration.DB_PATH)


async def init_db():
    clear_directory()
    db = await aiosqlite.connect(configuration.DB_PATH)
    await db.executescript(DDL)
    await db.commit()
    return db


def clear_directory(dir_path="data"):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
