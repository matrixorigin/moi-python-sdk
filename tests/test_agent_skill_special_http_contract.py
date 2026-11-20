import base64
from email import policy
from email.parser import BytesParser
import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentSkillSpecialHTTPContractTest(unittest.TestCase):
    def test_special_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "agent_skill_special_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                content_type = self.headers.get("Content-Type", "")
                observed.update(
                    method=self.command,
                    path=urllib.parse.urlsplit(self.path).path,
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    runtime_authorization=self.headers.get("X-MOI-Runtime-Authorization"),
                    accept=self.headers.get("Accept"),
                    content_type=content_type,
                    body=raw,
                    fields={},
                    filename=None,
                    file=None,
                )
                if content_type.startswith("multipart/"):
                    message = BytesParser(policy=policy.default).parsebytes(
                        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + raw
                    )
                    for part in message.iter_parts():
                        name = part.get_param("name", header="content-disposition")
                        content = part.get_payload(decode=True)
                        if name == "file":
                            observed["filename"] = part.get_filename()
                            observed["file"] = content
                        else:
                            observed["fields"][name] = content.decode("utf-8")
                if "response_base64" in scenario:
                    payload = base64.b64decode(scenario["response_base64"])
                elif "response_text" in scenario:
                    payload = scenario["response_text"].encode("utf-8")
                else:
                    payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                headers = dict(scenario.get("response_headers", {}))
                headers.setdefault("Content-Type", "application/json")
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_POST = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.agents("workspace-1")
        operation = scenario["operation"]
        file = base64.b64decode(scenario.get("file_base64", ""))
        stream = None
        if operation == "inspect_skill_package":
            result = service.inspect_skill_package(scenario["filename"], file)
        elif operation == "import_skill_package":
            kwargs = {key: scenario["input"][key] for key in ("name", "description", "category", "tags") if key in scenario["input"]}
            result = service.import_skill_package(scenario["filename"], file, **kwargs)
        elif operation == "polish_skill_stream":
            stream = service.polish_skill_stream(scenario["input"]["body"])
        else:
            self.fail(f"unknown operation {operation}")

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertIsNone(observed["runtime_authorization"])
        if operation in ("inspect_skill_package", "import_skill_package"):
            self.assertTrue(observed["content_type"].startswith("multipart/form-data; boundary="))
            self.assertEqual(observed["accept"], "application/json")
            self.assertEqual(observed["fields"], scenario["multipart_fields"])
            self.assertEqual(observed["filename"], scenario["filename"])
            self.assertEqual(observed["file"], file)
            self.assertEqual(result, scenario["response"]["data"])
        elif operation == "polish_skill_stream":
            self.assertEqual(observed["content_type"], "application/json")
            self.assertEqual(observed["accept"], "text/event-stream")
            self.assertEqual(json.loads(observed["body"]), scenario["request"])
        if stream is not None:
            try:
                if "response_base64" in scenario:
                    expected = base64.b64decode(scenario["response_base64"])
                else:
                    expected = scenario["response_text"].encode("utf-8")
                self.assertEqual(stream.status, scenario["status"])
                self.assertEqual(stream.read(), expected)
                for key, value in scenario.get("response_headers", {}).items():
                    self.assertEqual(stream.headers.get(key), value)
            finally:
                stream.close()


if __name__ == "__main__":
    unittest.main()
