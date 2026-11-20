import base64
import hashlib
import json
import socket
import threading
import unittest
from unittest.mock import patch
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from websockets.sync.server import serve

import moi_product_sdk as sdk
from moi_product_sdk import Client, with_token
from loopback_http import loopback_proxy_environment
from test_sandbox_terminal import _read_frame, _send_frame


class _BrowserServer:
    def __init__(self):
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.frames = []
        self.handshake = None
        self.errors = []
        self.closed = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        connection = None
        try:
            connection, _ = self.listener.accept()
            connection.settimeout(5)
            raw = bytearray()
            while b"\r\n\r\n" not in raw:
                chunk = connection.recv(4096)
                if not chunk:
                    raise EOFError("websocket handshake ended")
                raw.extend(chunk)
            head = bytes(raw).split(b"\r\n\r\n", 1)[0].decode("ascii")
            lines = head.split("\r\n")
            headers = {key.lower(): value.strip() for key, value in (line.split(":", 1) for line in lines[1:])}
            self.handshake = (lines[0], headers)
            accept = base64.b64encode(hashlib.sha1((headers["sec-websocket-key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            connection.sendall((
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Accept: " + accept + "\r\n"
                "Sec-WebSocket-Protocol: moi-browser.v1\r\n\r\n"
            ).encode())
            opcode, payload = _read_frame(connection)
            self.frames.append((opcode, payload))
            _send_frame(connection, 1, b'{"type":"frame","seq":9007199254740993,"metadata":{"deviceWidth":0}}')
            _send_frame(connection, 2, b"\x00\x01\xff\xfe")
            while True:
                opcode, payload = _read_frame(connection)
                if opcode == 8:
                    self.closed.set()
                    _send_frame(connection, 8, payload[:2])
                    break
                self.frames.append((opcode, payload))
        except (EOFError, ConnectionError, OSError) as error:
            if not self.closed.is_set():
                self.errors.append(error)
        except Exception as error:
            self.errors.append(error)
        finally:
            if connection is not None:
                connection.close()
            self.listener.close()

    def close(self):
        self.listener.close()
        self.thread.join(timeout=6)
        if self.thread.is_alive():
            raise AssertionError("browser server did not stop")
        if self.errors:
            raise AssertionError(self.errors)


class AgentBrowserContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_token_http_contract(self):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                observed["method"] = self.command
                observed["path"] = self.path
                observed["headers"] = self.headers
                observed["body"] = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                payload = json.dumps({"code": "OK", "data": {"token": "moi-browser-token-v1.signed", "expires_at": "2026-11-10T12:00:00Z"}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
            result = client.agents("workspace /1").runtime_browser_token("task/1 ?")
            self.assertEqual(result.token, "moi-browser-token-v1.signed")
            self.assertEqual(result.expires_at, "2026-11-10T12:00:00Z")
            self.assertEqual(observed["method"], "POST")
            self.assertEqual(observed["path"], "/newmoi/workspaces/workspace%20%2F1/agent-runtime-tasks/task%2F1%20%3F/browser/token")
            self.assertEqual(observed["body"], b"{}")
            headers = observed["headers"]
            self.assertEqual(headers["X-API-Key"], "synthetic-key")
            self.assertEqual(headers["X-Workspace-ID"], "workspace /1")
            self.assertIsNone(headers["Authorization"])
            self.assertIsNone(headers["Cookie"])
            self.assertIsNone(headers["X-MOI-Runtime-Authorization"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_websocket_frames_and_handshake(self):
        server = _BrowserServer()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.port}/newmoi", sdk.with_api_key("synthetic-key"))
            browser = client.agents("workspace /1").connect_runtime_browser(
                "task/1 ?", "moi-browser-token-v1.signed", "https://console.example.com"
            )
            event = {"type": "input_keyboard", "eventType": "keyDown", "key": "", "modifiers": 0, "enabled": False, "optional": None}
            browser.write_input(event)
            metadata = browser.receive(timeout=1)
            self.assertIsInstance(metadata, sdk.RuntimeBrowserFrame)
            self.assertTrue(metadata.text)
            self.assertEqual(metadata.data, b'{"type":"frame","seq":9007199254740993,"metadata":{"deviceWidth":0}}')
            image = browser.receive(timeout=1)
            self.assertFalse(image.text)
            self.assertEqual(image.data, b"\x00\x01\xff\xfe")
            browser.close()
            self.assertTrue(server.closed.wait(2), "server did not observe browser close")

            request, headers = server.handshake
            target = urllib.parse.urlsplit(request.split(" ")[1])
            self.assertEqual(target.path, "/newmoi/workspaces/workspace%20%2F1/agent-runtime-tasks/task%2F1%20%3F/browser/stream")
            self.assertEqual(target.query, "")
            self.assertEqual(headers["origin"], "https://console.example.com")
            self.assertEqual([value.strip() for value in headers["sec-websocket-protocol"].split(",")], ["moi-browser.v1", "moi-browser-token-v1.signed"])
            for name in ("x-api-key", "x-workspace-id", "authorization", "cookie", "x-moi-runtime-authorization"):
                self.assertNotIn(name, headers)
            self.assertEqual(len(server.frames), 1)
            opcode, payload = server.frames[0]
            self.assertEqual(opcode, 1)
            self.assertEqual(json.loads(payload), event)
        finally:
            server.close()

    def test_websocket_requires_token_and_origin(self):
        client = sdk.Client("http://127.0.0.1:1/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.agents("workspace-1")
        with self.assertRaises(sdk.Error) as caught:
            service.connect_runtime_browser("task-1", "", "https://console.example.com")
        self.assertIs(caught.exception, sdk.ErrTokenRequired)
        with self.assertRaises(sdk.Error) as caught:
            service.connect_runtime_browser("task-1", "moi-browser-token-v1.signed", "")
        self.assertIs(caught.exception, sdk.ErrOriginRequired)


if __name__ == "__main__":
    unittest.main()


class AgentBrowserTest(unittest.TestCase):
    def test_browser_transport(self):
        self.enterContext(loopback_proxy_environment())
        for compression, view in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(compression=compression, view=view):
                path = "/newmoi/workspaces/ws/agent-runtime-tasks/task/browser"
                proof = "moi-browser-token-v1.test"

                def process_request(connection, request):
                    target = path + "/stream" + ("?mode=view" if view else "")
                    if request.path != target or proof not in request.headers.get("Sec-WebSocket-Protocol", ""):
                        return connection.respond(401, "task proof missing")

                def handle(connection):
                    connection.send(json.dumps({"type": "frame", "seq": 7}))
                    connection.send(b"image\x00\xff")
                    ack = json.loads(connection.recv())
                    if ack != {"type": "ack", "seq": 7}:
                        return
                    connection.send(json.dumps({"type": "frame", "seq": 8}))
                    connection.send(b"next-image")
                    event = json.loads(connection.recv())
                    if not view:
                        connection.send(json.dumps({"type": "input_echo", "event": event}))
                        event = json.loads(connection.recv())
                    if event == {"type": "release"}:
                        connection.send(json.dumps({"type": "released"}))

                with serve(handle, "127.0.0.1", 0, subprotocols=["moi-browser.v1"], process_request=process_request) as server:
                    thread = threading.Thread(target=server.serve_forever)
                    thread.start()
                    try:
                        client = Client(f"http://127.0.0.1:{server.socket.getsockname()[1]}/newmoi", with_token("product-identity"))
                        with patch.object(client, "_request", return_value={"token": proof}) as token_request:
                            agents = client.agents("ws")
                            connect = agents.watch_browser if view else agents.connect_browser
                            browser = connect("task", compression)
                        self.assertEqual(token_request.call_args.args[:4], ("POST", "/workspaces/ws/agent-runtime-tasks/task/browser/token", "ws", {}))
                        try:
                            self.assertEqual(browser.compression_enabled(), compression)
                            self.assertEqual(browser.receive(), ({"type": "frame", "seq": 7}, b"image\x00\xff"))
                            browser.acknowledge(7)
                            self.assertEqual(browser.receive(), ({"type": "frame", "seq": 8}, b"next-image"))
                            if not view:
                                browser.input_keyboard("char", "验收 input")
                                self.assertEqual(browser.receive(), ({"type": "input_echo", "event": {"type": "input_keyboard", "eventType": "char", "text": "验收 input"}}, None))
                            browser.release()
                            self.assertEqual(browser.receive(), ({"type": "released"}, None))
                        finally:
                            browser.close()
                    finally:
                        server.shutdown()
                        thread.join(timeout=5)
