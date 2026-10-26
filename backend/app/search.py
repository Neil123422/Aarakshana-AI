"""
SQLite FTS5 BM25 retrieval layer for Indian Bare Acts.
"""
from db import build_fts_query, search_sections


def sanitize_fts_query(raw: str) -> str:
    """Return a safe FTS5 expression for free-form user text."""
    return build_fts_query(raw)


def snippet(text: str, max_len: int = 280) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def search_laws(query: str, domain: str | None = None, top_k: int = 5) -> list[dict]:
    rows = search_sections(query, limit=top_k, domain=domain)
    return [
        {
            "domain": row["domain"],
            "act_name": row["act_name"],
            "section_number": row["section_number"],
            "section_title": row["section_title"],
            "content": row["content"][:500] if row["content"] else "No verbatim text.",
            "score": row.get("rank", 0),
        }
        for row in rows
    ]
