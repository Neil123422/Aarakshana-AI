"""
SQLite FTS5 database layer for Indian Bare Acts.
Why FTS5? Built-in BM25 ranking, no extra dependencies, fast full-text search
over legal sections. Virtual table stores denormalized rows so each query
returns the exact verbatim section text for LLM context injection.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "indian_law.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Open a SQLite connection with FTS5 enabled (standard in Python's sqlite3)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the FTS5 virtual table if it doesn't exist."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
                domain,              -- "criminal", "procedure", "evidence"
                act_name,            -- e.g., "Bharatiya Nyaya Sanhita, 2023"
                section_number,      -- e.g., "1", "303", "358"
                section_title,       -- e.g., "Theft", "Hurt"
                content,             -- full verbatim section text (sub-clauses, explanations, illustrations)
                old_ipc_reference,   -- optional: corresponding IPC/CrPC section for transition reference
                tokenize="porter unicode61"  -- stemming + unicode for Hindi/English terms
            );
        """)
        conn.commit()
        print(f"FTS5 table 'sections_fts' ready at {DB_PATH}")
    finally:
        conn.close()


def insert_section(domain: str, act_name: str, section_number: str,
                   section_title: str, content: str, old_ipc_reference: str | None = None):
    """Insert one parsed section into the FTS5 table."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sections_fts (domain, act_name, section_number, section_title, content, old_ipc_reference) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (domain, act_name, section_number, section_title, content, old_ipc_reference)
        )
        conn.commit()
    finally:
        conn.close()


def count_sections():
    """Return total row count in sections_fts."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM sections_fts").fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def search_sections(query: str, limit: int = 5):
    """
    BM25-ranked search over section content.
    Returns list of dicts with all columns + rank.
    """
    conn = get_connection()
    try:
        # FTS5 bm25() returns lower score = better match; we sort ASC
        rows = conn.execute(
            "SELECT domain, act_name, section_number, section_title, content, old_ipc_reference, "
            "bm25(sections_fts) AS rank "
            "FROM sections_fts "
            "WHERE sections_fts MATCH ? "
            "ORDER BY rank ASC "
            "LIMIT ?",
            (query, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Total sections in DB: {count_sections()}")