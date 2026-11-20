import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentDiscoveryHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_discovery_http_contract.json")

    def test_catalog_and_home_guide_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_catalog_home_http_contract.json")

    def test_workspace_protocol_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("agent_workspace_protocol_http_contract.json")

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
        try:
            if scenario["operation"] == "list":
                result = service.list(*query)
            elif scenario["operation"] == "agent-card":
                result = service.agent_card(*query)
            elif scenario["operation"] == "list-agent-catalog-cards":
                result = service.list_agent_catalog_cards(*query)
            elif scenario["operation"] == "agent-home-guide-sample-locale":
                result = service.resource_get("agent-home-guide", "/sample-locale")
            elif scenario["operation"] == "workspace-agent-card":
                result = service.resource_get("agents", "/agent-1/.well-known/agent-card.json", *query)
            elif scenario["operation"] == "workspace-a2a":
                result = service.resource_post("agents", "/agent-1/a2a", scenario["input"]["body"], *query)
            elif scenario["operation"] == "workspace-mcp":
                request = json_format.ParseDict(scenario["input"]["body"], sdk.RuntimeRPCRequest())
                result = service.workspace_mcp(scenario["input"]["agent_id"], request)
            elif scenario["operation"] == "a2a":
                body = scenario["input"]["body"]
                selector = sdk.AgentSelector(
                    agent_code=body.get("agent_code", ""),
                    agent_id=body.get("agent_id", ""),
                    agent_workspace_id=body.get("agent_workspace_id", ""),
                )
                request = sdk.A2ARequest(
                    body["method"], id_=body.get("id"), params=body.get("params"),
                    jsonrpc=body.get("jsonrpc", "2.0"), model=body.get("model", ""), no_wait=True,
                )
                result = service.a2a(sdk.AgentA2ARequest(selector, request))
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
            if scenario["operation"] in ("list", "agent-home-guide-sample-locale", "workspace-agent-card", "workspace-a2a"):
                self.assertEqual(result, scenario["response"] if scenario["operation"].startswith("workspace-") else scenario["response"]["data"])
            elif scenario["operation"] == "workspace-mcp":
                expected = json_format.ParseDict(scenario["response"], sdk.RuntimeRPCResponse())
                self.assertEqual(result, expected)
            elif scenario["operation"] == "agent-card":
                self.assertEqual(json.loads(result.json), scenario["response"].get("data", scenario["response"]))
            elif scenario["operation"] == "list-agent-catalog-cards":
                expected = json_format.ParseDict(scenario["response"]["data"], sdk.AgentCatalogCardListResult())
                self.assertEqual(result, expected)
            else:
                self.assertEqual(json.loads(result.json), scenario["response"])

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
