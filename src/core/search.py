import aiosqlite
from typing import List, Dict, Any

from src.core.settings import configuration


async def search_pages(
    query: str,
    top_n: int = 10,
    db_path: str = configuration.DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Return up to `top_n` pages ranked by bm25() that match `query`.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        sql = """
        WITH ranked AS (
            SELECT
                rowid,
                bm25(pages_fts) AS rank
            FROM pages_fts
            WHERE pages_fts MATCH :query
            ORDER BY rank
            LIMIT :top
        )
        SELECT
            p.url,
            p.title,
            p.meta_description,
            snippet(pages_fts, -1, '[', ']', '…', 10) AS snippet,
            r.rank
        FROM ranked   AS r
        JOIN pages_fts AS pf ON pf.rowid = r.rowid
        JOIN pages     AS p  ON p.rowid  = r.rowid
        ORDER BY r.rank;
        """

        rows = await db.execute_fetchall(sql, {"query": query, "top": top_n})
        return [dict(r) for r in rows]
