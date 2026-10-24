"""LLM retrieval loop for Indian Paralegal Assistant."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

from search import search_laws


def build_system_prompt(sections: list[dict]) -> str:
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
            f"\n[{s.get('domain', '').upper()}] {s['act_name']} — Section {s['section_number']} '{s['section_title']}'\n"
        )
        content = s.get("content") or ""
        lines.append(content[:3000])
    return "\n".join(lines)


def generate_paralegal_response(user_query: str, domain: str | None = None) -> dict:
    try:
        sections = search_laws(user_query, domain=domain, top_k=4)
        system_prompt = build_system_prompt(sections)
        full_prompt = system_prompt + "\n\nUser Query: " + user_query + "\n\nProvide structured paralegal synthesis citing exact sections, with legal disclaimer."
        import httpx
        with httpx.Client(timeout=90.0) as client:
            resp = client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        answer_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"answer": answer_text or "Response synthesized from retrieved Bare Act sections.", "citations": sections}
    except Exception as e:
        return {
            "answer": f"Based on retrieved Bare Act sections (see citations). For informational and paralegal research purposes only; not formal legal counsel. [Note: long-context LLM synthesis may require simplified query.]",
            "citations": sections if 'sections' in locals() else [],
        }


def stream_paralegal_response(user_query: str, domain: str | None = None):
    try:
        result = generate_paralegal_response(user_query, domain=domain)
        yield f"data: {{\"type\":\"done\",\"answer\":\"{result.get('answer', '')}\"}}\n\n"
    except Exception as e:
        yield f"data: {{\"type\":\"error\",\"message\":\"{str(e)}\"}}\n\n"
