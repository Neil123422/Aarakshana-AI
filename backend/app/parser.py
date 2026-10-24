"""Parse uploaded docs (PDF, DOCX, TXT/MD) into plain text."""
import os
from pathlib import Path
from pypdf import PdfReader
from docx import Document

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def parse_file(file_path: Path) -> str:
    try:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == ".docx":
            doc = Document(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs)
        elif ext in (".txt", ".md"):
            return file_path.read_text(encoding="utf-8", errors="ignore")
        else:
            return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except:
            return f"[Unreadable file: {file_path.name}]"
