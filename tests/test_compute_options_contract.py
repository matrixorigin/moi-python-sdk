import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class ComputeOptionsContractTest(unittest.TestCase):
    def test_requests_and_responses_match_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "compute_options_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        current = {}
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def receive(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                target = urlsplit(self.path)
                requests.append({
                    "method": self.command, "path": target.path,
                    "query": parse_qs(target.query, keep_blank_values=True),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "body_present": bool(raw), "body": json.loads(raw) if raw else None,
                })
                data = json.dumps({"code": "OK", "data": current["response"]}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = receive
            do_POST = receive
            do_PUT = receive

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        compute = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key")).compute("workspace-1")

        def options(values, prefix, excluded=()):
            result = []
            for field, value in values.items():
                if field in excluded:
                    continue
                factory = getattr(sdk, prefix + field)
                if field == "worker_images":
                    result.append(factory(*(sdk.WorkerImageSelection(**image) for image in value)))
                else:
                    result.append(factory(value))
            return result

        spec_required = ("kind", "family", "family_name", "family_name_en", "cpu_milli", "memory_mib")
        resource_required = ("name", "spec_id", "cpu", "memory_gib")
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                values = case["input"]
                command = case["command"]
                if command == "create-spec":
                    result = compute.create_spec(case["id"], *(values[field] for field in spec_required), *options(values, "with_compute_spec_", spec_required))
                elif command == "update-spec":
                    opts = []
                    for field, value in values.items():
                        prefix = "with_compute_spec_update_" if field in spec_required else "with_compute_spec_"
                        opts.append(getattr(sdk, prefix + field)(value))
                    result = compute.update_spec(case["id"], *opts)
                elif command == "create":
                    result = compute.create(*(values[field] for field in resource_required), *options(values, "with_compute_", resource_required))
                elif command in ("update", "admin-update"):
                    operation = compute.update if command == "update" else compute.admin_update
                    result = operation(case["id"], *options(values, "with_compute_update_"))
                elif command == "get":
                    result = compute.get(case["id"])
                    self.assertIsInstance(result.py_deps, sdk.ComputeResourcePyDeps)
                elif command == "admin-list":
                    result = compute.admin_list(*(sdk.with_query_values(key, *value) for key, value in case.get("query", {}).items()))
                else:
                    self.fail(f"Unknown fixture operation: {command}")
                expected_request = [{
                    "method": case["method"], "path": "/newmoi" + case["path"],
                    "query": case.get("query", {}), "workspace": "workspace-1", "api_key": "synthetic-key",
                    "body_present": case["request"] is not None, "body": case["request"],
                }]
                # JSON comparison keeps booleans distinct from numeric zero.
                self.assertEqual(json.dumps(requests, sort_keys=True), json.dumps(expected_request, sort_keys=True))
                expected = json_format.ParseDict(case["response"], type(result)())
                self.assertEqual(result, expected)
