"""
FastAPI entry point with CORS for Expo Web + mobile.
Why allow_origins=["*"]? Cross-platform clients (iOS, Android, Web) connect
from different origins; strict CORS would block the React Native Expo
frontend during development.
"""
import base64
import mimetypes
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db import count_sections, get_connection
from llm import generate_paralegal_response
from parser import parse_file

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_ATTACHMENTS = 10
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

app = FastAPI(title="Indian Paralegal Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class AttachmentRef(BaseModel):
    id: str
    name: str


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=12000)
    domain: str | None = None
    attachments: list[AttachmentRef] = Field(default_factory=list)


def _safe_display_name(name: str) -> str:
    return Path(name.replace("\\", "/")).name[:200] or "attachment"


@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    if len(files) > MAX_ATTACHMENTS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_ATTACHMENTS} attachments allowed.")

    results = []
    saved_paths: list[Path] = []
    total_bytes = 0
    try:
        for upload in files:
            name = _safe_display_name(upload.filename or "attachment")
            suffix = Path(name).suffix.lower()
            if suffix not in ALLOWED_SUFFIXES:
                raise HTTPException(status_code=415, detail=f"Unsupported file type: {suffix or 'unknown'}")

            contents = await upload.read(MAX_UPLOAD_BYTES - total_bytes + 1)
            size = len(contents)
            total_bytes += size
            if total_bytes > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="Attachments exceed the 100 MB request limit.")

            attachment_id = str(uuid.uuid4())
            save_path = UPLOAD_DIR / f"{attachment_id}{suffix}"
            save_path.write_bytes(contents)
            saved_paths.append(save_path)

            is_image = suffix in IMAGE_SUFFIXES
            extracted_text = "" if is_image else parse_file(save_path)
            status = "ready" if is_image or extracted_text.strip() else "needs_ocr"
            results.append({
                "id": attachment_id,
                "name": name,
                "type": mimetypes.guess_type(name)[0] or "application/octet-stream",
                "size": size,
                "status": status,
                "preview": extracted_text.strip()[:180],
                "extracted_chars": len(extracted_text),
            })
    except Exception as exc:
        for path in saved_paths:
            path.unlink(missing_ok=True)
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=422, detail=f"Could not read attachment: {exc}") from exc

    return {"files": results}


def _load_attachments(references: list[AttachmentRef]) -> tuple[list[dict], list[dict]]:
    if len(references) > MAX_ATTACHMENTS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_ATTACHMENTS} attachments allowed.")

    documents: list[dict] = []
    images: list[dict] = []
    for reference in references:
        try:
            attachment_id = str(uuid.UUID(reference.id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid attachment reference.") from exc

        matches = list(UPLOAD_DIR.glob(f"{attachment_id}.*"))
        if not matches:
            raise HTTPException(status_code=404, detail=f"Attachment is missing: {_safe_display_name(reference.name)}")
        path = matches[0]
        name = _safe_display_name(reference.name)
        if path.suffix.lower() in IMAGE_SUFFIXES:
            mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            images.append({"name": name, "data_url": f"data:{mime_type};base64,{encoded}"})
        else:
            text = parse_file(path).strip()
            if not text:
                raise HTTPException(status_code=422, detail=f"No selectable text was found in {name}; OCR is needed.")
            documents.append({"name": name, "text": text})

    return documents, images

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
        documents, images = _load_attachments(req.attachments)
        return generate_paralegal_response(
            req.query,
            domain=req.domain,
            documents=documents,
            images=images,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Paralegal synthesis error: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

