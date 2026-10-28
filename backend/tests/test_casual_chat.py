import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))
import llm


class CasualChatTests(unittest.TestCase):
    def test_standalone_hi_skips_retrieval_and_provider(self):
        with patch("llm.search_laws") as retrieval, patch("llm.httpx.post") as provider:
            result = llm.generate_paralegal_response("Hi!")

        self.assertEqual(result["response_type"], "casual")
        self.assertEqual(result["citations"], [])
        self.assertIn("Aarakshana", result["answer"])
        retrieval.assert_not_called()
        provider.assert_not_called()

    def test_legal_question_after_greeting_remains_grounded_and_cited(self):
        section = {
            "domain": "criminal",
            "act_name": "Bharatiya Nyaya Sanhita, 2023",
            "section_number": "303",
            "section_title": "Theft",
            "content": "Whoever commits theft shall be punished as provided by law.",
            "score": 1.0,
        }
        provider_response = httpx.Response(200, json={
            "model": llm.LLM_MODEL,
            "choices": [{"message": {"content": "Theft is addressed under Section 303 BNS."}}],
        })
        with patch("llm.search_laws", return_value=[section]) as retrieval:
            with patch("llm.httpx.post", return_value=provider_response) as provider:
                result = llm.generate_paralegal_response(
                    "Hi, what is the punishment for theft under BNS?"
                )

        self.assertEqual(result["response_type"], "legal")
        self.assertEqual(result["citations"][0]["section_number"], "303")
        retrieval.assert_called_once()
        system_prompt = provider.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertIn("Cite exact Act names and Section numbers", system_prompt)
        self.assertIn("Disclaimer:", system_prompt)

    def test_greeting_with_attachment_stays_on_document_pipeline(self):
        document = {"name": "brief.txt", "text": "Matter reference DKT-814."}
        provider_response = httpx.Response(200, json={
            "model": llm.LLM_MODEL,
            "choices": [{"message": {"content": "The document contains reference DKT-814."}}],
        })
        with patch("llm.search_laws", return_value=[]) as retrieval:
            with patch("llm.httpx.post", return_value=provider_response) as provider:
                result = llm.generate_paralegal_response("Hi", documents=[document])

        self.assertEqual(result["response_type"], "legal")
        retrieval.assert_called_once()
        system_prompt = provider.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertIn("Matter reference DKT-814", system_prompt)


if __name__ == "__main__":
    unittest.main()
