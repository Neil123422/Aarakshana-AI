"""
FastAPI entry point with CORS for Expo Web + mobile.
Why allow_origins=["*"]? Cross-platform clients (iOS, Android, Web) connect
from different origins; strict CORS would block the React Native Expo
frontend during development.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from db import get_connection, count_sections
from llm import generate_paralegal_response
from pathlib import Path

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Indian Paralegal Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    domain: str | None = None
    attachments: list[dict] = []
    images: list[str] = []


@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    if len(files) > 10:
        return {"error": "Maximum 10 attachments allowed."}, 400
    results = []
    for f in files:
        fname = f.filename or "unnamed"
        ext = Path(fname).suffix.lower()
        try:
            contents = await f.read()
            size = len(contents)
            text = ""
            b64_str = ""
            if ext in (".pdf", ".docx", ".txt", ".md"):
                save_path = UPLOAD_DIR / fname
                UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as buffer:
                    buffer.write(contents)
                if ext == ".pdf":
                    from parser import parse_file
                    text = parse_file(save_path)
                elif ext == ".docx":
                    from parser import parse_file
                    text = parse_file(save_path)
                elif ext in (".txt", ".md"):
                    text = contents.decode("utf-8", errors="ignore")
            elif ext in (".png", ".jpg", ".jpeg", ".webp"):
                import base64
                b64_str = "data:image/" + ("png" if ext == ".png" else "jpeg" if ext in (".jpg",".jpeg") else "webp") + ";base64," + base64.b64encode(contents).decode()
            else:
                text = contents.decode("utf-8", errors="ignore")
            results.append({"name": fname, "type": f.content_type or ext.lstrip("."), "size": size, "text": text[:3000], "base64": b64_str, "status": "ready"})
        except Exception as e:
            results.append({"name": fname, "type": f.content_type or ext.lstrip("."), "size": 0, "text": "", "base64": "", "status": "error", "error": str(e)})
    return {"files": results}

@app.get("/api/health")
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Aarakshana Backend"}

@app.get("/api/health")
def health():
    # Verify SQLite DB reachable
    conn = get_connection()
    try:
        total = count_sections()
        return {"status": "ok", "sections_count": total}
    finally:
        conn.close()

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        truncated = req.query[:1200] if len(req.query) > 1200 else req.query
        result = generate_paralegal_response(truncated, domain=req.domain)
        return result
    except Exception as e:
        return {"answer": f"Paralegal synthesis error: {str(e)}. Please simplify the query or verify backend logs.", "citations": [], "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import UploadFile, File
import base64

