import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))
import llm


class ModelFallbackTests(unittest.TestCase):
    def response(self, status, body, headers=None):
        return httpx.Response(status, json=body, headers=headers or {})

    def test_402_credit_exhaustion_stops_before_fallback(self):
        blocked = self.response(402, {
            "error": {
                "code": 402,
                "message": "Insufficient credits",
                "metadata": {"limit_source": "openrouter_credits"},
            }
        })
        with patch("llm.httpx.post", return_value=blocked) as post:
            with self.assertRaisesRegex(llm.LLMProviderError, "switching models will not help"):
                llm.generate_paralegal_response("Plain text test")
        self.assertEqual(post.call_count, 1)

    def test_invalid_credentials_stop_before_fallback(self):
        blocked = self.response(401, {"error": {"message": "Invalid API key"}})
        with patch("llm.httpx.post", return_value=blocked) as post:
            with self.assertRaisesRegex(llm.LLMProviderError, "rejected the configured API key"):
                llm.generate_paralegal_response("Plain text test")
        self.assertEqual(post.call_count, 1)

    def test_shared_429_does_not_try_another_model(self):
        blocked = self.response(
            429,
            {"error": {"message": "Rate limit exceeded", "metadata": {"error_type": "rate_limit_exceeded"}}},
            {"X-RateLimit-Limit": "10", "X-RateLimit-Remaining": "0", "Retry-After": "30"},
        )
        with patch("llm.httpx.post", return_value=blocked) as post:
            with self.assertRaisesRegex(llm.LLMProviderError, "shared platform/account rate limit"):
                llm.generate_paralegal_response("Plain text test")
        self.assertEqual(post.call_count, 1)

    def test_upstream_429_tries_configured_fallback(self):
        limited = self.response(429, {
            "error": {"message": "provider overloaded", "metadata": {"provider_code": "429"}}
        })
        success = self.response(200, {
            "model": "anthropic/claude-sonnet-5",
            "choices": [{"message": {"content": "Recovered from upstream rate limit"}}],
        })
        with patch("llm.httpx.post", side_effect=[limited, success]) as post:
            result = llm.generate_paralegal_response("Plain text test")
        self.assertEqual(result["answer"], "Recovered from upstream rate limit")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(post.call_count, 2)

    def test_fallback_keeps_document_and_image_context(self):
        failure = self.response(503, {"error": {"message": "No provider available"}})
        success = self.response(200, {
            "model": "anthropic/claude-sonnet-5",
            "choices": [{"message": {"content": "Grounded test response"}}],
        })
        document = {"name": "fixture.md", "text": "Reference marker TEST-MD-6412."}
        image = {"name": "fixture.png", "data_url": "data:image/png;base64,dGVzdA=="}
        with patch("llm.httpx.post", side_effect=[failure, success]) as post:
            result = llm.generate_paralegal_response(
                "Find the reference marker", documents=[document], images=[image]
            )
        self.assertEqual(result["answer"], "Grounded test response")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["model"], "anthropic/claude-sonnet-5")
        first, second = [call.kwargs["json"] for call in post.call_args_list]
        self.assertEqual(first["model"], llm.LLM_MODEL)
        self.assertEqual(second["model"], "anthropic/claude-sonnet-5")
        self.assertEqual(first["provider"], {"only": ["anthropic"], "allow_fallbacks": False})
        self.assertIn("TEST-MD-6412", first["messages"][0]["content"])
        self.assertEqual(first["messages"], second["messages"])
        self.assertIn("image_url", [part["type"] for part in first["messages"][1]["content"]])

    def test_empty_primary_answer_tries_fallback(self):
        empty = self.response(200, {"choices": [{"message": {"content": ""}}]})
        success = self.response(200, {
            "model": "anthropic/claude-sonnet-5",
            "choices": [{"message": {"content": "Recovered answer"}}],
        })
        with patch("llm.httpx.post", side_effect=[empty, success]) as post:
            result = llm.generate_paralegal_response("Explain BNS Section 106")
        self.assertEqual(result["answer"], "Recovered answer")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(post.call_count, 2)

    def test_cross_publisher_fallback_is_rejected_before_send(self):
        with patch.dict("os.environ", {"LLM_FALLBACK_MODELS": "openai/gpt-5-mini"}):
            with self.assertRaisesRegex(llm.LLMProviderError, "cross-publisher"):
                llm._models_for_request()


if __name__ == "__main__":
    unittest.main()
