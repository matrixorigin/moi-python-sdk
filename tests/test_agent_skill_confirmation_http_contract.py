import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentSkillConfirmationHTTPContractTest(unittest.TestCase):
    def test_shared_typed_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk/testdata/agent_skill_confirmation_http_contract.json"
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
                parsed = urllib.parse.urlsplit(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    body=json.loads(raw) if raw else None,
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                )
                payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = _handle
            do_POST = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.agents("workspace 1")
        input_value = scenario["input"]
        try:
            if scenario["operation"] == "get-skill-candidate-confirmation":
                result = service.get_skill_candidate_confirmation(
                    input_value["task_id"], input_value["call_id"], input_value["source_digest"],
                )
                response_type = sdk.SkillCandidateConfirmationResult
            elif scenario["operation"] == "confirm-skill-candidate":
                request = json_format.ParseDict(input_value["body"], sdk.ConfirmSkillCandidateRequest())
                result = service.confirm_skill_candidate(input_value["task_id"], request)
                response_type = sdk.ConfirmSkillCandidateResult
            else:
                self.fail(f"unknown operation {scenario['operation']}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            response = scenario["response"]
            self.assertEqual(error.code, str(response["code"]))
            self.assertEqual(error.message, response.get("msg", response.get("message")))
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
            self.assertEqual(error.details, response.get("details", {}))
        else:
            self.assertLess(scenario["status"], 400)
            expected = json_format.ParseDict(scenario["response"]["data"], response_type())
            self.assertEqual(result, expected)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["body"], scenario["request"])
        self.assertEqual(observed["workspace"], "workspace 1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])


if __name__ == "__main__":
    unittest.main()
