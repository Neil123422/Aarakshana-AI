# AGENTS.md — Open-Source Indian Paralegal Assistant

## 1. Project Overview & Core Philosophy
We are building an open-source, cross-platform (iOS, Android, Web) AI Paralegal Assistant tailored specifically to Indian Law (Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, and Bharatiya Sakshya Adhiniyam).

### Strict Anti-Slop & Mentorship Rules (MANDATORY)
- **Developer Profile:** The human developer is an engineering fresher building this for an open-source portfolio to learn full-stack and AI engineering from the ground up.
- **NO Black-Box AI Frameworks:** Strictly DO NOT use LangChain, LlamaIndex, CrewAI, or heavy agent wrappers. Build the PDF parsing, chunking, SQLite retrieval, and LLM API calls in raw, readable Python so the data flow is 100% transparent.
- **Incremental Execution:** Never scaffold or dump the entire repository in one turn. Work strictly one phase at a time. Write 1–2 files, explain the core mechanism in plain English, and ask the developer to run and test it before moving to the next step.
- **Pedagogical Code Comments:** Add concise comments explaining *why* specific engineering choices are made (e.g., how regex splits legal sections, how SQLite FTS5 ranks results, or how FastAPI handles CORS).
- **Minimal Dependencies:** Do not install bloated UI libraries or unnecessary npm/pip packages. Use standard library tools wherever practical.

---

## 2. Architecture & Tech Stack

### Backend (`/backend`)
- **Language & Framework:** Python 3.11+ with **FastAPI** and **Pydantic v2**.
- **PDF Ingestion:** Use `PyMuPDF` (`fitz`) to extract text from official Bare Act PDFs stored in `backend/data/raw_laws/` (`BNS_2023.pdf`, `BNSS_2023.pdf`, `BSA_2023.pdf`).
- **Database & Retrieval (Scratch-Built RAG):**
  - Use **SQLite** (`backend/data/indian_law.db`) with the built-in **FTS5 (Full-Text Search)** extension using BM25 ranking (and optional lightweight vector embeddings later).
  - Chunk the Bare Acts logically by **Act Name + Section Number + Section Title** rather than arbitrary character counts so legal provisions are never cut in half.
- **LLM Engine:**
  - Use a clean, provider-agnostic HTTP/OpenAI-compatible client (`httpx` or `openai` SDK) configured via `.env` (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`) so it works seamlessly with Mistral AI, OpenRouter, or local Ollama models.
  - Use a tool-calling / retrieval loop:
    1. Extract search keywords from the user's plain-English query.
    2. Query the local SQLite database for the top 5 relevant sections across BNS, BNSS, and BSA.
    3. Inject those exact verbatim sections into the LLM system prompt.
    4. Require the LLM to cite exact Act and Section numbers, highlight the transition from old IPC/CrPC sections where helpful, and include a clear legal disclaimer ("For informational and paralegal research purposes only; not formal legal counsel").

### Frontend (`/frontend`)
- **Framework:** **React Native with Expo** (TypeScript) targeting iOS, Android, and Web from a single codebase.
- **Package Manager:** Always use `pnpm` for frontend dependencies.
- **UI Design:** Clean, minimalist, high-contrast legal assistant interface built with core React Native primitives (`FlatList`, `TextInput`, `Pressable`, `SafeAreaView`, `StyleSheet`).
- **Features:**
  - Chat stream showing the user's question and the AI's structured response.
  - Collapsible "Referenced Bare Act Sections" cards inside each response so the user can read the verbatim law retrieved from SQLite alongside the AI summary.

---

## 3. Repository Structure
```text
indian-paralegal-ai/
├── AGENTS.md
├── README.md
├── backend/
│   ├── .env                  # API keys (never commit)
│   ├── .env.example
│   ├── requirements.txt
│   ├── data/
│   │   ├── raw_laws/         # Official BNS_2023.pdf, BNSS_2023.pdf, BSA_2023.pdf
│   │   └── indian_law.db     # Generated SQLite FTS5 database
│   └── app/
│       ├── main.py           # FastAPI entry point & CORS config
│       ├── ingest.py         # Script to parse PDFs into SQLite sections
│       ├── search.py         # SQLite FTS5 query logic
│       └── llm.py            # Prompt construction & LLM API call
└── frontend/                 # Expo (React Native + Web) app