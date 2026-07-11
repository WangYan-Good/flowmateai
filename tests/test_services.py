import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.config import Settings
from backend.models.schemas import Email
from backend.services.email_service import MockEmailProvider
from backend.services.llm_service import LLMService


class SettingsTests(unittest.TestCase):
    def test_llm_url_accepts_root_or_v1(self):
        self.assertEqual(
            Settings(llm_base_url="http://model:8001").llm_chat_completions_url,
            "http://model:8001/v1/chat/completions",
        )
        self.assertEqual(
            Settings(llm_base_url="http://model:8001/v1/").llm_chat_completions_url,
            "http://model:8001/v1/chat/completions",
        )

    def test_provider_and_model_are_visible(self):
        settings = Settings(llm_provider="deepseek", llm_model="deepseek-v4-flash")
        self.assertEqual(settings.llm_display_name, "deepseek/deepseek-v4-flash")


class EmailProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_provider_loads_alias(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "emails.json"
            path.write_text(
                json.dumps([{"id": "1", "from": "a@b.test", "subject": "S", "body": "B"}]),
                encoding="utf-8",
            )
            emails = await MockEmailProvider(path).get_unread_emails()
            self.assertEqual(emails[0].sender, "a@b.test")


class LLMParsingTests(unittest.TestCase):
    def test_parses_fenced_json(self):
        parsed = LLMService._parse_json('```json\n{"important": [], "normal": []}\n```')
        self.assertEqual(parsed["important"], [])


class _MockLLMHandler(BaseHTTPRequestHandler):
    request_path = ""

    def do_POST(self):
        type(self).request_path = self.path
        length = int(self.headers.get("Content-Length", "0"))
        json.loads(self.rfile.read(length))
        body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "important": [
                                        {
                                            "subject": "Delivery",
                                            "summary": "Timeline changed.",
                                            "action": "Review the plan.",
                                        }
                                    ],
                                    "normal": [],
                                }
                            )
                        }
                    }
                ]
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


class LLMHttpTests(unittest.IsolatedAsyncioTestCase):
    async def test_calls_openai_compatible_endpoint(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _MockLLMHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            service = LLMService(
                Settings(llm_base_url=f"http://127.0.0.1:{server.server_port}/v1")
            )
            result = await service.summarize_emails(
                [Email(id="1", **{"from": "a@b.test"}, subject="Delivery", body="Changed")]
            )
            self.assertEqual(_MockLLMHandler.request_path, "/v1/chat/completions")
            self.assertEqual(result.important[0].action, "Review the plan.")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
