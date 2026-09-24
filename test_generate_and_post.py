import json
import os
import unittest
from unittest.mock import patch


os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "test-chat")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import generate_and_post


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "Готово"}]}}]}
        ).encode("utf-8")


class RecipeMenuTests(unittest.TestCase):
    def test_gemini_request_enables_google_search_grounding(self):
        with patch("generate_and_post.urlopen", return_value=FakeResponse()) as urlopen:
            result = generate_and_post.ask_gemini("Знайди рецепт", timeout=1)

        self.assertEqual(result, "Готово")
        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertIn("key=test-key", request.full_url)
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
