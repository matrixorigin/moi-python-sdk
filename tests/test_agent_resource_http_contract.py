import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentResourceHTTPContractTest(unittest.TestCase):
    def test_knowledge_base_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_knowledge_bases_http_contract.json")

    def test_task_template_workflow_binding_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_task_template_workflow_binding_http_contract.json")

    def test_definition_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_definition_http_contract.json")

    def test_version_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_version_http_contract.json")

    def test_skill_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_skill_http_contract.json")

    def test_tool_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_tool_http_contract.json")

    def test_tool_connection_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_tool_connection_http_contract.json")

    def test_automation_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_automation_http_contract.json")

    def test_artifact_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_artifact_http_contract.json")

    def test_runtime_read_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_runtime_read_http_contract.json")

    def test_runtime_action_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_runtime_action_http_contract.json")

    def test_builder_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_builder_http_contract.json")

    def test_conversation_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_conversation_http_contract.json")

    def test_workspace_extensions_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_workspace_extensions_http_contract.json")

    def _run_fixture(self, fixture_name):
        fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / fixture_name
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
            do_PUT = _handle
            do_PATCH = _handle
            do_DELETE = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.agents("workspace-1")
        query = tuple(
            sdk.with_query_values(key, *values)
            for key, values in sorted(scenario.get("query", {}).items())
        )
        body = scenario["input"].get("body")
        try:
            result = service.resource_any(
                scenario["method"], scenario["resource"], scenario["tail_path"], body, *query,
            )
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            self.assertEqual(error.code, str(scenario["response"]["code"]))
            self.assertEqual(error.message, scenario["response"].get("msg", scenario["response"].get("message")))
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            self.assertLess(scenario["status"], 400)
            expected = scenario["response"] if scenario.get("raw_response") else scenario["response"]["data"]
            self.assertEqual(expected, result)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["body"], scenario["request"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])


if __name__ == "__main__":
    unittest.main()
