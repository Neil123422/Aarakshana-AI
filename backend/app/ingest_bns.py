"""
Ingest BNS_2023.pdf into sections_fts.
Chunking logic (observed from inspect_pdf.py):
- Section headings: bold blocks like "303. Theft.", "114. Hurt."
- Sub-clauses / explanations / illustrations: non-bold blocks following until next heading
- Skip preamble pages (1-6); start at page 7 (Chapter I / Section 1)
Why regex on bold blocks? Because headings carry font weight flags ([BOLD])
so they separate cleanly from body clauses that follow.
"""
import re
import fitz
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import init_db, insert_section, count_sections

PDF_PATH = Path(__file__).parent.parent / "data" / "raw_laws" / "BNS_2023.pdf"

# Regex: number, period, optional space, then title starting with capital letter
SECTION_START_RE = re.compile(r"^(\d+)\.\s+([A-Z][A-Z\s.,;()-]+)")
# More flexible version for sections like "303. Theft." or complex titles
SECTION_START_LOOSE = re.compile(r"^(\d+)\.\s+(.+?)\.")


def is_heading_block(block_text: str) -> tuple[bool, str, str]:
    """Check if a text block is a section heading. Return (is_heading, number, title)."""
    # Clean whitespace/newlines from block text for regex
    cleaned = block_text.replace("\n", " ").strip()
    # Try loose match: number followed by period and title ending with period
    m = SECTION_START_LOOSE.match(cleaned)
    if m:
        num_str = m.group(1)
        title = m.group(2).strip()
        # Section numbers in BNS go up to ~358; avoid matching years like 2023.
        num_int = int(num_str)
        if num_int > 0 and num_int < 1000:
            # Confirm this is a heading by checking the original block has [BOLD] flag
            return True, num_str, title
    return False, "", ""


def extract_bns_sections():
    doc = fitz.open(PDF_PATH)
    total_pages = doc.page_count
    print(f"BNS_2023.pdf loaded: {total_pages} pages")

    # Accumulate text blocks across pages; we start from page 7 (index 6) to skip preamble
    sections = {}
    current_number = None
    current_title = ""
    current_content_lines = []

    # Start collecting from page index 6 (page 7) to skip preamble
    for page_index in range(6, total_pages):
        page = doc.load_page(page_index)
        blocks = page.get_text("blocks")
        # Also get dict blocks for font flags
        dict_blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            # Filter empty blocks and pure page numbers
            if not text or not text.strip():
                continue
            # Filter out running footer "IndiaCode" (bold footer block)
            if text.strip() == "IndiaCode":
                continue
            # Filter out "THE GAZETTE OF INDIA" headers (not present but safe)
            if "GAZETTE" in text or (text.strip().isdigit() and len(text.strip()) <= 4):
                continue

            # Check if this block is a heading by matching number + title
            # We approximate bold by looking for bold flag in dict_blocks
            bold_flag = False
            for d in dict_blocks:
                if d.get("bbox") == (x0, y0, x1, y1) and d.get("number") == block_no:
                    spans = d.get("lines", [{}])[0].get("spans", [{}]) if d.get("lines") else [{}]
                    if spans:
                        flags = spans[0].get("flags", 0)
                        # Bold flag in PyMuPDF is usually bit 4 (16)
                        if flags & 16:
                            bold_flag = True

            # Try heading detection regardless of bold for loose sections
            is_heading, sec_num, sec_title = is_heading_block(text)
            # For some headings, the bold flag confirms; for others, regex alone is enough
            if is_heading:
                # Save previous section if there was one
                if current_number is not None and current_content_lines:
                    full_content = "\n".join(current_content_lines).strip()
                    sections[current_number] = {
                        "number": current_number,
                        "title": current_title,
                        "content": full_content,
                    }
                # Start new section
                current_number = sec_num
                current_title = sec_title
                current_content_lines = []
            else:
                # This is body content for the current section
                if current_number is not None:
                    lines = text.splitlines()
                    for line in lines:
                        line = line.strip()
                        if line:
                            current_content_lines.append(line)

        # End of page: option to flush, but we'll accumulate across pages

    # Flush final section
    if current_number is not None and current_content_lines:
        full_content = "\n".join(current_content_lines).strip()
        sections[current_number] = {
            "number": current_number,
            "title": current_title,
            "content": full_content,
        }

    doc.close()
    return sections


def main():
    init_db()
    print("Parsing BNS_2023.pdf sections...")
    sections = extract_bns_sections()
    print(f"Parsed sections: {len(sections)}")
    print(f"Section number range: {min(sections.keys(), key=lambda k: int(k))} to {max(sections.keys(), key=lambda k: int(k))}")

    # Insert all parsed sections
    inserted = 0
    for sec in sorted(sections.values(), key=lambda s: int(s["number"])):
        insert_section(
            domain="criminal",
            act_name="Bharatiya Nyaya Sanhita, 2023",
            section_number=sec["number"],
            section_title=sec["title"],
            content=sec["content"],
            old_ipc_reference=None  # can be mapped later
        )
        inserted += 1

    print(f"Inserted {inserted} sections into FTS5.")
    print(f"Total rows in DB: {count_sections()}")

    # Verify a known section exists
    test_sections = ["1", "303", "358"]
    import db as db_mod
    conn = db_mod.get_connection()
    try:
        for s_num in test_sections:
            row = conn.execute(
                "SELECT section_number, section_title FROM sections_fts WHERE section_number = ?",
                (s_num,)
            ).fetchone()
            if row:
                print(f"Verified section {s_num}: '{row['section_title']}'")
            else:
                print(f"WARNING: Section {s_num} not found!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()