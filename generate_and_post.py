import os
import sys
import types
import unittest
from unittest.mock import patch


os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "test-chat")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(
        post=None,
        RequestException=Exception,
    )

import generate_and_post


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": "Готово"}]}}]}


class RecipeMenuTests(unittest.TestCase):
    def test_gemini_request_enables_google_search_grounding(self):
        with patch("generate_and_post.requests.post", return_value=FakeResponse()) as post:
            result = generate_and_post.ask_gemini("Знайди рецепт", timeout=1)

        self.assertEqual(result, "Готово")
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["tools"], [{"google_search": {}}])
        self.assertEqual(body["generationConfig"]["temperature"], 0.2)

    def test_menu_prompt_requires_sources_and_timed_steps(self):
        with patch("generate_and_post.ask_gemini", return_value="menu") as ask:
            self.assertEqual(generate_and_post.generate_menu(), "menu")

        prompt = ask.call_args.args[0]
        self.assertIn("одній повноцінній\nстраві", prompt)
        self.assertIn("пряме URL-посилання", prompt)
        self.assertIn("кожен з тривалістю", prompt)
        self.assertIn("Не вигадуй посилань", prompt)

    def test_split_text_preserves_all_content(self):
        text = "Перший абзац.\n\nДругий абзац.\n\nТретій абзац."
        parts = generate_and_post.split_text(text, limit=20)

        self.assertTrue(all(len(part) <= 20 for part in parts))
        self.assertEqual(parts, ["Перший абзац.", "Другий абзац.", "Третій абзац."])


if __name__ == "__main__":
    unittest.main()
