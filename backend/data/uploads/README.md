# Indian Paralegal Assistant

Open-source, cross-platform AI paralegal assistant for Indian Law, focused on the new Bharatiya criminal statutes.

## Why these laws?

India replaced its colonial-era criminal codes with three Bare Acts in 2023:

- **Bharatiya Nyaya Sanhita, 2023 (BNS)** — replaces IPC (1860)
- **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)** — replaces CrPC (1973)
- **Bharatiya Sakshya Adhiniyam, 2023 (BSA)** — replaces Indian Evidence Act (1872)

This project builds a transparent, scratch-built RAG pipeline so students and practitioners can ask plain-English questions and receive ground-truth citations from the actual Bare Act text — not black-box hallucinations.

## Architecture

```
React Native Expo (frontend)
    ↓ HTTP
FastAPI + Pydantic v2 (backend/app/main.py)
    ↓ SQLite FTS5 BM25
sqlite3 backend/data/indian_law.db
    ↓ PyMuPDF parsing
backend/data/raw_laws/*.pdf
```

**Data flow:** PDF → `fitz` text blocks → regex section splitting → `sections_fts` virtual table → `search_laws()` BM25 ranking → `generate_paralegal_response()` system prompt injection → `httpx` LLM call.

No LangChain, LlamaIndex, or heavy agent frameworks. Every step is readable Python.

## Setup

### Backend (Python 3.11+)

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\python -m pip install -r requirements.txt
# macOS/Linux:
source venv/bin/activate && pip install -r requirements.txt

# Initialize DB and ingest BNS
venv\Scripts\python app/ingest_bns.py

# Start server
venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```

Add `backend/.env` (never commit):

```bash
LLM_API_KEY=your-key
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
```

### Frontend (Expo + pnpm)

```bash
pnpm install
pnpm run web   # or android / ios
```

The API helper (`frontend/src/services/api.ts`) points to `http://localhost:8000`. For mobile on the same LAN, replace with your machine's IP (e.g., `http://192.168.1.42:8000`).

## Adding more Bare Acts

To extend `indian_law.db` with BNSS, BSA, or future amendments:

1. Place the official PDF in `backend/data/raw_laws/` (e.g., `BNSS_2023.pdf`).
2. Create `backend/app/ingest_bnss.py` modeled on `ingest_bns.py`; adjust regex and page ranges for BNSS's section structure.
3. Run ingestion; `sections_fts` auto-accepts new rows.
4. Update `.env`/`LLM_MODEL` if needed, then test via `/api/chat`.

## Project rules

- Minimal dependencies (no bloated UI libraries)
- Pedagogical code comments explaining *why* choices are made (FTS5 BM25, font-block chunking, raw `httpx`)
- Incremental execution — never dump the full repo in one turn
- `.gitignore` excludes `backend/venv/`, `backend/data/raw_laws/*.pdf`, `backend/data/indian_law.db`, `.env`

## License

Open source — for educational and paralegal research purposes.
