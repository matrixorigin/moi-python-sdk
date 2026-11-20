import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class ResourceTagsHTTPContractTest(unittest.TestCase):
    def test_requests_and_results_match_shared_go_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/resource_tags_http_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def record(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), json.loads(raw) if raw else None))
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(current["response"]).encode())

            do_POST = record
            do_GET = record
            do_PATCH = record
            do_DELETE = record

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        service = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key")).resource_tags("workspace-1")
        types = {
            "create": (sdk.ResourceTagCreateRequest, sdk.ResourceTag),
            "list": (sdk.ResourceTagListRequest, sdk.ResourceTagList),
            "update": (sdk.ResourceTagUpdateRequest, sdk.ResourceTag),
            "delete": (None, None),
            "create-value": (sdk.ResourceTagValueRequest, sdk.ResourceTagValue),
            "list-values": (sdk.ResourceTagListRequest, sdk.ResourceTagValueList),
            "update-value": (sdk.ResourceTagValueRequest, sdk.ResourceTagValue),
            "delete-value": (None, None),
            "update-relations": (sdk.ResourceTagRelationsRequest, None),
            "groups": (sdk.ResourceTagQueryRequest, sdk.ResourceTagGroupList),
            "resources": (sdk.ResourceTagQueryRequest, sdk.ResourceTagResourceList),
            "assignments": (sdk.ResourceTagAssignmentsRequest, sdk.ResourceTagAssignmentsList),
        }
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                request_type, response_type = types[case["operation"]]
                args = []
                for field in ("tag_id", "value_id"):
                    if field in case:
                        args.append(case[field])
                if request_type is not None:
                    args.append(json_format.ParseDict(case["input"], request_type()))
                method = getattr(service, case["operation"].replace("-", "_"))
                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as raised:
                        method(*args)
                    self.assertEqual((raised.exception.code, raised.exception.message, raised.exception.status), (case["response"]["code"], case["response"]["msg"], case["status"]))
                else:
                    actual = method(*args)
                    if response_type is None:
                        self.assertIsNone(actual)
                    else:
                        self.assertEqual(actual, json_format.ParseDict(case["response"]["data"], response_type()))
                self.assertEqual(len(requests), 1)
                method_name, raw_path, key, workspace, body = requests[0]
                path = urllib.parse.urlsplit(raw_path)
                self.assertEqual((method_name, path.path, key, workspace), (case["method"], case["path"], "synthetic-key", "workspace-1"))
                self.assertEqual(urllib.parse.parse_qs(path.query, keep_blank_values=True), {name: [value] for name, value in case["query"].items()})
                self.assertEqual(json.dumps(body, sort_keys=True), json.dumps(case["request"], sort_keys=True))
