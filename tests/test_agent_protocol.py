import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk


_LOCALHOST_NO_PROXY = ("127.0.0.1", "localhost", "::1")


def _with_localhost_no_proxy(value):
    entries = []
    seen = set()
    for item in (value or "").split(","):
        item = item.strip()
        if item and item not in seen:
            entries.append(item)
            seen.add(item)
    for item in _LOCALHOST_NO_PROXY:
        if item not in seen:
            entries.append(item)
            seen.add(item)
    return ",".join(entries)


class _AgentProtocolHandler(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, format, *args):
        return

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.__class__.requests.append(
            {
                "path": self.path,
                "content_type": self.headers.get("Content-Type"),
                "accept": self.headers.get("Accept"),
                "workspace_id": self.headers.get("X-Workspace-ID"),
                "body": body,
            }
        )
        if self.path == "/newmoi/agents/a2a":
            payload = json.dumps({"jsonrpc": "2.0", "id": "request", "error": {"code": -32005, "message": "权限不足", "data": {"reason": "PLUGIN_SETUP_FORBIDDEN"}}}).encode("utf-8")
            self.send_response(403)
            self.send_header("X-Request-ID", "header-request")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/newmoi/workspaces/workspace%201/skills/polish/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b"event: done\ndata: {\"request_id\":\"r1\"}\n\n")
            return
        self._json({"code": "OK", "msg": "OK", "data": {"ok": True}})

    def do_GET(self):
        body = b""
        self.__class__.requests.append(
            {
                "path": self.path,
                "content_type": self.headers.get("Content-Type"),
                "accept": self.headers.get("Accept"),
                "workspace_id": self.headers.get("X-Workspace-ID"),
                "body": body,
            }
        )
        if self.path.startswith("/newmoi/workspaces/workspace%201/skills/skill%201/files/content"):
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown")
            self.end_headers()
            self.wfile.write(b"guide content")
            return
        self.send_error(404)

    def do_DELETE(self):
        self.__class__.requests.append(
            {
                "path": self.path,
                "content_type": self.headers.get("Content-Type"),
                "accept": self.headers.get("Accept"),
                "workspace_id": self.headers.get("X-Workspace-ID"),
                "body": b"",
            }
        )
        if self.path != "/newmoi/messages/message-1":
            self.send_error(404)
            return
        self._json({"code": "OK", "msg": "OK", "data": None})

    def _json(self, value):
        payload = json.dumps(value).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class AgentProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._no_proxy = os.environ.get("NO_PROXY")
        cls._no_proxy_lower = os.environ.get("no_proxy")
        os.environ["NO_PROXY"] = _with_localhost_no_proxy(cls._no_proxy)
        os.environ["no_proxy"] = _with_localhost_no_proxy(cls._no_proxy_lower)
        cls.server = HTTPServer(("127.0.0.1", 0), _AgentProtocolHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        if cls._no_proxy is None:
            os.environ.pop("NO_PROXY", None)
        else:
            os.environ["NO_PROXY"] = cls._no_proxy
        if cls._no_proxy_lower is None:
            os.environ.pop("no_proxy", None)
        else:
            os.environ["no_proxy"] = cls._no_proxy_lower

    def setUp(self):
        _AgentProtocolHandler.requests = []

    def test_a2a_http_error_preserves_owner_contract(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("test-key"))
        agent = client.agents("workspace 1")
        for method in (sdk.A2A_METHOD_SEND, sdk.A2A_METHOD_STREAM):
            with self.subTest(method=method), self.assertRaises(sdk.Error) as caught:
                request = sdk.AgentA2ARequest(sdk.AgentSelector(agent_id="agent"), sdk.A2ARequest(method, id_="request"))
                if method == sdk.A2A_METHOD_STREAM:
                    agent.a2a_stream(request)
                else:
                    agent.a2a(request)
            error = caught.exception
            self.assertEqual((error.code, error.message, error.status, error.request_id), ("-32005", "权限不足", 403, "header-request"))
            self.assertEqual(error.data, {"reason": "PLUGIN_SETUP_FORBIDDEN"})

    def test_agent_protocol_methods(self):
        client = sdk.Client(
            f"http://127.0.0.1:{self.server.server_port}/newmoi",
            sdk.with_api_key("user-key"),
        )
        agent = client.agents("workspace 1")

        self.assertEqual({"ok": True}, agent.load_agent_package(b"agent package"))
        self.assertEqual({"ok": True}, agent.upload_workspace_file("workspace.csv", b"workspace file"))
        self.assertEqual({"ok": True}, agent.inspect_skill_package("skill.zip", b"inspect skill"))
        self.assertEqual({"ok": True}, agent.import_skill_package("skill.zip", b"import skill"))
        file_stream = agent.get_skill_file("skill 1", "references/guide.md")
        self.addCleanup(file_stream.close)
        self.assertEqual(b"guide content", file_stream.read())
        stream = agent.polish_skill_stream({"name": "draft"})
        self.addCleanup(stream.close)
        self.assertEqual(b"event: done\ndata: {\"request_id\":\"r1\"}\n\n", stream.read())

        requests = _AgentProtocolHandler.requests
        self.assertEqual(6, len(requests))
        self.assertEqual("application/vnd.moi.agent+zip", requests[0]["content_type"])
        self.assertEqual(b"agent package", requests[0]["body"])
        self.assertEqual("workspace 1", requests[0]["workspace_id"])
        for index, filename, payload in (
            (1, "workspace.csv", b"workspace file"),
            (2, "skill.zip", b"inspect skill"),
            (3, "skill.zip", b"import skill"),
        ):
            request = requests[index]
            self.assertTrue(request["content_type"].startswith("multipart/form-data; boundary="))
            self.assertIn(f'filename="{filename}"'.encode("utf-8"), request["body"])
            self.assertIn(payload, request["body"])
            self.assertEqual("workspace 1", request["workspace_id"])
        self.assertTrue(requests[4]["path"].startswith("/newmoi/workspaces/workspace%201/skills/skill%201/files/content"))
        self.assertIn("path=references%2Fguide.md", requests[4]["path"])
        self.assertEqual("*/*", requests[4]["accept"])
        self.assertEqual("workspace 1", requests[4]["workspace_id"])
        self.assertEqual("application/json", requests[5]["content_type"])
        self.assertEqual("text/event-stream", requests[5]["accept"])
        self.assertEqual({"name": "draft"}, json.loads(requests[5]["body"]))
