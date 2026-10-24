"""
Stream KanonGPT Indian Legal Documents via HF datasets.
Why streaming=True? Avoids downloading the full dataset locally;
we only process what matches our 4 Central Acts.
Filter key: document_title contains the act name.
Chunking: each dataset row is treated as one section (up to 120 per act).
Domain mapping is hard-coded based on AGENTS.md categories.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from db import init_db, insert_section, count_sections

from datasets import load_dataset

DATASET = "KanoonGPT/indian-legal-documents"
SPLIT = "train"

ACT_FILTERS = {
    "constitutional": ("Constitution of India", "constitutional"),
    "commercial": ("Indian Contract Act, 1872", "commercial"),
    "civil": ("Code of Civil Procedure, 1908", "civil"),
    "cyber": ("Information Technology Act, 2000", "cyber"),
}

MAX_PER_ACT = 120


def main():
    init_db()
    print(f"Streaming {DATASET} split={SPLIT} ...")
    ds = load_dataset(DATASET, split=SPLIT, streaming=True)

    counts = {k: 0 for k in ACT_FILTERS}

    for row in ds:
        title = row.get("document_title", "") or ""
        text = row.get("text", "") or ""

        for domain, (keyword, _) in ACT_FILTERS.items():
            if counts[domain] >= MAX_PER_ACT:
                continue
            # Case-insensitive keyword match in title
            if keyword.lower() in title.lower():
                # Derive section number / title from text if possible; else use doc_title
                # For streaming simplicity, treat each row as one section
                section_number = str(counts[domain] + 1)  # sequential index
                section_title = title.split("-")[-1].strip() if "-" in title else title[:120]

                insert_section(
                    domain=domain,
                    act_name=title,
                    section_number=section_number,
                    section_title=section_title,
                    content=text[:8000],  # cap content length for DB performance
                    old_ipc_reference=None,
                )
                counts[domain] += 1
                if counts[domain] % 30 == 0:
                    print(f"  {domain}: {counts[domain]} inserted")

    print("Ingest complete.")
    for k, v in counts.items():
        print(f"  {k}: {v} sections")
    total = count_sections()
    print(f"Updated total sections in DB: {total}")


if __name__ == "__main__":
    main()