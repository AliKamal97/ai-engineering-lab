"""Exercise the real scraper and SDK against a local HTTP server, without API costs."""

import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import summarizer
from scraper import fetch_website_contents

PAGE = """<!doctype html><html><head><title>Cedar Trails</title>
<style>hidden-style</style></head><body><nav>navigation-noise</nav>
<h1>Weekend hikes</h1><p>Beginner hikes in northern Italy cost €35.</p>
<script>hidden-script</script><footer>footer-noise</footer></body></html>"""
TEST_ANSWER = "## Purpose\n\nLocal integration-test response.\n"


class Endpoint(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.downloads += 1
        if self.path == "/blocked":
            self.send_error(403)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE.encode("utf-8"))

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        self.server.submissions.append((self.path, self.headers.get("Authorization"), json.loads(body)))
        self.send_response(self.server.reply_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.server.reply_status != 200:
            result = {"error": {"message": "Local test quota", "type": "rate_limit_error"}}
        else:
            result = {
                "id": "local-test-response", "object": "chat.completion", "created": 0,
                "model": "local-test-model",
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": TEST_ANSWER}}],
            }
        self.wfile.write(json.dumps(result).encode("utf-8"))


class Day1IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Endpoint)
        self.server.downloads = 0
        self.server.submissions = []
        self.server.reply_status = 200
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.temp = tempfile.TemporaryDirectory()
        self.settings = patch.multiple(
            summarizer, PROJECT_ROOT=Path(self.temp.name),
            GEMINI_BASE_URL=self.base + "/v1beta/openai/",
        )
        self.settings.start()
        self.environment = patch.dict(os.environ, {
            "GEMINI_API_KEY": "local-test-key-not-a-real-credential",
            "GEMINI_MODEL": "local-test-model",
            "HTTP_PROXY": "", "HTTPS_PROXY": "", "ALL_PROXY": "",
            "http_proxy": "", "https_proxy": "", "all_proxy": "",
            "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost",
        })
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.settings.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def test_extracts_readable_unicode_and_removes_page_noise(self):
        text = fetch_website_contents(self.base + "/page")
        self.assertIn("Cedar Trails", text)
        self.assertIn("€35", text)
        for noise in ["navigation-noise", "hidden-script", "hidden-style", "footer-noise"]:
            self.assertNotIn(noise, text)
        with self.assertRaises(ValueError):
            fetch_website_contents("file:///private.txt")

    def test_cli_sends_real_sdk_request_and_saves_markdown(self):
        destination = Path(self.temp.name) / "reports" / "briefing.md"
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            status = summarizer.main([self.base + "/page", "--output", str(destination)])
        self.assertEqual(status, 0)
        self.assertIn(TEST_ANSWER.strip(), output.getvalue())
        report = destination.read_text(encoding="utf-8")
        self.assertIn("Source: " + self.base + "/page", report)
        self.assertIn(TEST_ANSWER, report)
        path, authorization, payload = self.server.submissions[0]
        self.assertEqual(path, "/v1beta/openai/chat/completions")
        self.assertEqual(authorization, "Bearer local-test-key-not-a-real-credential")
        self.assertEqual(payload["model"], "local-test-model")
        self.assertEqual([m["role"] for m in payload["messages"]], ["system", "user"])
        self.assertIn("€35", payload["messages"][1]["content"])
        self.assertNotIn("reasoning_effort", payload)

    def test_missing_key_is_clear_and_preview_still_works(self):
        os.environ.pop("GEMINI_API_KEY", None)
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            status = summarizer.main([self.base + "/page"])
        self.assertEqual(status, 1)
        self.assertIn("Set GEMINI_API_KEY", errors.getvalue())
        self.assertEqual(self.server.downloads, 0)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = summarizer.main([self.base + "/page", "--preview"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output.getvalue())[0]["role"], "system")
        self.assertEqual(self.server.submissions, [])

    def test_http_failures_do_not_create_summary_files(self):
        destination = Path(self.temp.name) / "failed.md"
        for url, reply_status, expected in [
            ("/blocked", 200, "Website download failed (HTTP 403)"),
            ("/page", 429, "quota or rate limit"),
        ]:
            with self.subTest(url=url):
                self.server.reply_status = reply_status
                errors = io.StringIO()
                with contextlib.redirect_stderr(errors):
                    status = summarizer.main([self.base + url, "--output", str(destination)])
                self.assertEqual(status, 1)
                self.assertIn(expected, errors.getvalue())
                self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
