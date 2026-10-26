"""
LLM retrieval loop for Indian Paralegal Assistant.
Uses raw httpx for transparent data flow.
"""
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load env from backend/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")

import sys
sys.path.insert(0, str(Path(__file__).parent))
from search import search_laws


def build_system_prompt(sections):
    lines = [
        "You are an objective Indian Paralegal Assistant.",
        "Answer using ONLY the legal provisions provided below.",
        "Cite exact Act names and Section numbers from the context.",
        "If a provision references an older IPC/CrPC section, note the transition.",
        "Never invent sections or legal texts not present in the provided context.",
        "End every response with: 'Disclaimer: For informational and paralegal research purposes only; not formal legal counsel.'",
        "",
        "=== RETRIEVED BARE ACT SECTIONS ===",
    ]
    for s in sections:
        lines.append(
            f"\n[{s['domain'].upper()}] {s['act_name']} — Section {s['section_number']} '{s['section_title']}'\n"
        )
        content = s["content"][:3000]
        lines.append(content)
    return "\n".join(lines)


def generate_paralegal_response(user_query: str, domain: str | None = None) -> dict:
    sections = search_laws(user_query, domain=domain, top_k=4)
    system_text = build_system_prompt(sections)

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_query},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    try:
        url = f"{LLM_BASE_URL}/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LLM_API_KEY}"}
        resp = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "No response from LLM.")
    except Exception as e:
        answer = f"LLM call failed: {e}\n(Using retrieved context only — no generated text available.)"

    citations = [
        {
            "domain": s["domain"],
            "act_name": s["act_name"],
            "section_number": s["section_number"],
            "section_title": s["section_title"],
            "content": s["content"],
        }
        for s in sections
    ]

    return {"answer": answer, "citations": citations}


def cli_test():
    result = generate_paralegal_response("What is punishment for theft under BNS?", domain="criminal")
    print("Answer snippet:", result["answer"][:200])
    print("Citations:", len(result["citations"]))
    for c in result["citations"][:3]:
        print(" -", c["domain"], c["act_name"], "Sec", c["section_number"])


if __name__ == "__main__":
    cli_test()
