"""Extract searchable text from supported legal-document uploads."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree


def parse_file(file_path: Path) -> str:
    """Parse documents without silently treating binary files as UTF-8 text."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        import pymupdf

        with pymupdf.open(str(file_path)) as document:
            return "\n".join(page.get_text("text") or "" for page in document)

    if suffix == ".docx":
        with ZipFile(file_path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs = []
        for paragraph in root.iter(f"{namespace}p"):
            text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
            if text.strip():
                paragraphs.append(text)
        return "\n".join(paragraphs)

    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8-sig", errors="replace")

    raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")
