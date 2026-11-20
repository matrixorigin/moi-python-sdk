import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class ConversationHTTPContractTest(unittest.TestCase):
    def test_requests_and_results_match_shared_go_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/conversation_http_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def record(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), self.headers.get("Content-Type"), json.loads(raw) if raw else None))
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if current["status"] != 204:
                    self.wfile.write(json.dumps(current["response"]).encode())

            do_POST = record
            do_PUT = record
            do_GET = record
            do_DELETE = record

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        service = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key")).conversations("workspace-1")
        types = {
            "create-ui-session": (sdk.ConversationUISessionRequest, sdk.ConversationSession),
            "update-ui-session": (sdk.ConversationUISessionRequest, sdk.ConversationSession),
            "get-ui-session": (None, sdk.ConversationSession),
            "delete-ui-session": (None, sdk.ConversationMutation),
            "pin-ui-session": (None, sdk.ConversationMutation),
            "unpin-ui-session": (None, sdk.ConversationMutation),
            "list-ui-sessions": (sdk.ConversationUISessionListRequest, sdk.ConversationSessionList),
            "list-pinned-ui-sessions": (sdk.ConversationUISessionListRequest, sdk.ConversationSessionList),
            "list-unpinned-ui-sessions": (sdk.ConversationUISessionListRequest, sdk.ConversationSessionList),
            "list-ui-messages": (sdk.ConversationUIMessageListRequest, sdk.ConversationUIMessage),
            "get-ui-message": (None, sdk.ConversationUIMessage),
            "like-ui-message": (None, sdk.ConversationUIMessage),
            "dislike-ui-message": (None, sdk.ConversationUIMessage),
            "latest-ui-message-id": (None, sdk.ConversationLatestMessageID),
            "create-session": (sdk.ConversationWorkspaceSessionRequest, sdk.ConversationSession),
            "update-session": (sdk.ConversationWorkspaceSessionRequest, sdk.ConversationSession),
            "create-message": (sdk.ConversationWorkspaceMessageRequest, sdk.ConversationWorkspaceMessage),
            "create-tag": (sdk.ConversationTagRequest, sdk.ConversationTag),
            "add-session-tag": (sdk.ConversationTagRequest, None),
            "add-message-tag": (sdk.ConversationTagRequest, None),
        }
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                request_type, response_type = types[case["operation"]]
                args = [] if request_type is None else [json_format.ParseDict(case["input"], request_type())]
                if "session_id" in case:
                    args.insert(0, case["session_id"])
                if "message_id" in case:
                    args.insert(0, case["message_id"])
                method = getattr(service, case["operation"].replace("-", "_"))
                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as raised:
                        method(*args)
                    self.assertEqual((raised.exception.code, raised.exception.message, raised.exception.status), (case["response"]["code"], case["response"]["msg"], case["status"]))
                else:
                    actual = method(*args)
                    expected = case["response"]["data"]
                    if case["operation"] == "list-ui-messages":
                        self.assertEqual(actual, [json_format.ParseDict(item, response_type()) for item in expected])
                    elif response_type is not None:
                        self.assertEqual(actual, json_format.ParseDict(expected, response_type()))
                    else:
                        self.assertIsNone(actual)
                self.assertEqual(len(requests), 1)
                method_name, path, key, workspace, content_type, body = requests[0]
                expected_content_type = "application/json" if "input" in case else None
                self.assertEqual((method_name, path, key, workspace, content_type), (case["method"], case["path"], "synthetic-key", "workspace-1", expected_content_type))
                self.assertEqual(json.dumps(body, sort_keys=True), json.dumps(case["request"], sort_keys=True))
