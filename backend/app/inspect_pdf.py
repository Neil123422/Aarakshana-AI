"""
Phase 1 diagnostic: inspect BNS_2023.pdf structure.
Why font blocks instead of raw get_text()? Bare Act PDFs embed headings
with different font weights / sizes and marginal notes in separate
blocks. Blind string splitting would cut legal provisions in half.
"""
import fitz  # PyMuPDF; AGENTS.md uses pymupdf but import as fitz

PDF_PATH = "backend/data/raw_laws/BNS_2023.pdf"

# Pages where Chapter I / Section 1 begin (after preamble) and where
# substantive offenses (theft etc.) appear.
PAGES_CH1 = list(range(7, 15))   # 7 to 14 inclusive
PAGES_OFFENSES = list(range(50, 56))  # 50 to 55 inclusive

HEADER_FOOTER_KEYWORDS = [
    "THE GAZETTE OF INDIA", "Gazette of India", "OFFICE OF THE",
    "EXTRAORDINARY", "PART III", "SECTION 1",  # running header patterns
]


def is_header_footer(text_block):
    txt = text_block[4]  # text content is 5th element in dict format
    # Filter out running headers/footers by keyword match and very short lines
    if len(txt) < 3:
        return True
    for kw in HEADER_FOOTER_KEYWORDS:
        if kw in txt:
            return True
    # Page numbers alone (e.g., "39" or "12")
    if txt.strip().isdigit() and len(txt.strip()) <= 4:
        return True
    return False


def inspect_page(doc, pno):
    page = doc.load_page(pno - 1)  # 0-indexed
    # get_text("blocks") yields (x0, y0, x1, y1, text, block_no, block_type)
    # We use dicts to also capture font flags via get_text("dict").
    blocks = page.get_text("blocks")
    # Also get structured dict to see font info per block
    blocks_dict = page.get_text("dict")["blocks"]

    print(f"\n=== PAGE {pno} ===")
    for b in blocks:
        x0, y0, x1, y1, text, block_no, block_type = b
        # Filter running headers / footers
        if is_header_footer(b):
            continue
        # Show raw block with flags (we approximate bold by checking dict)
        # Find matching block_dict for font info
        for d in blocks_dict:
            if d.get("number") == block_no or d.get("bbox") == (x0, y0, x1, y1):
                # Print block with line-break preservation
                lines = text.splitlines()
                flag_str = ""
                # Check first span for bold/italic flags
                spans = d.get("lines", [{}])[0].get("spans", [{}]) if d.get("lines") else [{}]
                if spans and spans[0].get("flags") is not None:
                    flags = spans[0]["flags"]
                    if flags & 2**4:  # bold flag (approx)
                        flag_str += "[BOLD]"
                    if flags & 2**0:  # italic flag
                        flag_str += "[ITALIC]"
                print(f"  BLOCK {block_no} (bbox {x0:.1f},{y0:.1f}-{x1:.1f},{y1:.1f}) {flag_str}")
                for line in lines:
                    # Trim very long whitespace; preserve line breaks
                    trimmed = line.strip()
                    if trimmed:
                        print("     | " + trimmed)
                break


def main():
    doc = fitz.open(PDF_PATH)
    total = doc.page_count
    print(f"PDF: {PDF_PATH}")
    print(f"Total pages: {total}")
    print(f"Pages requested (Chapter I): {PAGES_CH1}")
    print(f"Pages requested (Offenses): {PAGES_OFFENSES}")

    for p in PAGES_CH1 + PAGES_OFFENSES:
        if 1 <= p <= total:
            inspect_page(doc, p)
        else:
            print(f"Page {p} out of range (max {total})")

    doc.close()
    print("\n--- Diagnostic complete ---")


if __name__ == "__main__":
    main()
