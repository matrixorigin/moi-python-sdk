import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class WorkflowWorkerTaskHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk/testdata/workflow_worker_task_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observations = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                observations.append({
                    "method": self.command,
                    "path": self.path,
                    "body": self.rfile.read(int(self.headers.get("Content-Length", "0"))),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "authorization": self.headers.get("Authorization"),
                    "cookie": self.headers.get("Cookie"),
                    "runtime_authorization": self.headers.get("X-MOI-Runtime-Authorization"),
                })
                payload = json.dumps(scenario["response"]).encode("utf-8")
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        request = json_format.ParseDict(scenario["input"], sdk.WorkflowWorkerTaskCreateRequest())
        try:
            result = client.workflows("workspace-1").create_worker_task(request)
        except sdk.Error as error:
            if "error_code" in scenario:
                self.assertEqual(error.code, scenario["error_code"])
            else:
                self.assertEqual(error.status, scenario["status"])
                self.assertEqual(error.code, scenario["response"]["code"])
                self.assertEqual(error.message, scenario["response"]["msg"])
                self.assertEqual(error.request_id, scenario["response_headers"]["X-Request-ID"])
        else:
            self.assertNotIn("error_code", scenario)
            self.assertLess(scenario["status"], 400)
            expected = json_format.ParseDict(scenario["response"]["task"], sdk.WorkflowWorkerTask())
            self.assertEqual(result, expected)

        self.assertEqual(len(observations), 1)
        observed = observations[0]
        self.assertEqual(observed["method"], "POST")
        self.assertEqual(observed["path"], "/newmoi/workspaces/workspace-1/tasks")
        self.assertEqual(json.loads(observed["body"]), scenario["request"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertIsNone(observed["runtime_authorization"])


if __name__ == "__main__":
    unittest.main()
