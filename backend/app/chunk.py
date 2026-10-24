"""Chunking layer for long legal documents — splits text into ~500-char chunks."""
import re
from pathlib import Path

def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    # Split by paragraphs first, then by sentences if needed
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 2 <= chunk_size:
            current += ("\n\n" if current else "") + p
        else:
            if current:
                chunks.append(current[:chunk_size])
            current = p[:chunk_size]
    if current:
        chunks.append(current[:chunk_size])
    return chunks[:8]  # Cap at 8 chunks to stay within LLM context
