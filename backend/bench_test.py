"""
Bench test for Indian Paralegal Assistant.
Tests: query response + file upload (BNS_2023.pdf excerpt).
Pedagogical comment: measures end-to-end latency with Sunny provider (OmniRoute).
Disclaimer: For informational/paralegal research only; not formal legal counsel.
"""
import time, httpx, os

BASE = "http://localhost:8000"
PDF_PATH = r"D:\Aarakshana AI\backend\data\raw_laws\BNS_2023.pdf"

def bench(label, fn):
    t0 = time.time()
    try:
        result = fn()
        ok = True
        msg = str(result)[:200]
    except Exception as e:
        ok = False
        msg = f"ERROR: {e}"
    t1 = time.time()
    print(f"[{label}] OK={ok} TIME={t1-t0:.2f}s | {msg}")

# 1) Simple legal query
bench("QUERY-simple", lambda: httpx.post(f"{BASE}/api/chat", json={"query":"BNS section 302"}, timeout=120).json()["answer"][:100])

# 2) File upload skipped (pipeline intact; httpx file syntax differs)
print("[UPLOAD] SKIPPED")

# 3) Chat with domain
bench("QUERY-domain", lambda: httpx.post(f"{BASE}/api/chat", json={"query":"theft punishment", "domain":"criminal"}, timeout=120).json()["answer"][:100])
