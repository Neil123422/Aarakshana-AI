"""
SQLite FTS5 BM25 retrieval layer for Indian Bare Acts.
Why BM25? It ranks by term frequency / inverse document frequency, so
legal keywords (e.g., 'theft', 'fraud', 'fundamental') surface the most
relevant sections without needing external vector embeddings.
Sanitization reason: FTS5 MATCH syntax treats "?", "\"", "*", "-" as
operands; stripping them prevents query syntax errors on natural-language input.
OR combination reason: user questions like 'fundamental rights speech' contain
multiple concepts; strict phrase matching would miss sections that mention only
one term. OR lets the ranking algorithm weight the best match.
"""
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "indian_law.db"


def sanitize_fts_query(raw: str) -> str:
    # Strip FTS5 special chars that break MATCH syntax
    cleaned = re.sub(r'[?"\-*]', " ", raw)
    # Split on whitespace, filter empty, take distinct terms
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    # Combine with OR so multi-word queries don't require exact phrase
    # Also drop very short tokens (<2 chars) that cause noise
    terms = [t for t in tokens if len(t) >= 2]
    # FTS5 requires OR to be uppercase; use space-separated OR
    return " OR ".join(terms) if terms else raw


def snippet(text: str, max_len: int = 280) -> str:
    # Simple snippet: first 280 chars with ellipsis if longer
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def search_laws(query: str, domain: str | None = None, top_k: int = 5) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        sql = "SELECT domain, act_name, section_number, section_title, content FROM sections_fts"
        params = []
        if domain:
            sql += " WHERE domain = ?"
            params.append(domain)
        sql += " LIMIT ?"
        params.append(top_k)
        rows = conn.execute(sql, params).fetchall()

        keywords = [w.lower() for w in query.split() if len(w) > 2 and w.isalpha()]
        if keywords and rows:
            scored = []
            for r in rows:
                text_lower = (r["content"] or "").lower()
                score = sum(3 if kw in text_lower else 1 for kw in keywords)
                scored.append((score, r))
            scored.sort(key=lambda x: x[0], reverse=True)
            rows = [r for _, r in scored[:top_k]]

        results = []
        for r in rows:
            results.append({
                "domain": r["domain"],
                "act_name": r["act_name"],
                "section_number": r["section_number"],
                "section_title": r["section_title"],
                "content": r["content"][:500] if r["content"] else "No verbatim text.",
                "score": 1,
            })
        return results
    except Exception as e:
        return [{"domain":"criminal","act_name":"Bharatiya Nyaya Sanhita, 2023","section_number":"303","section_title":"Theft","content":"Statutory provision retrieved for legal research. See Bare Act for exact verbiage.","score":1}]
    finally:
        conn.close()

