import base64
import hashlib
import json
import socket
import struct
import threading
import unittest
import urllib.parse

import moi_product_sdk as sdk
import websocket

from loopback_http import loopback_proxy_environment


def _read_exact(connection, length):
    data = bytearray()
    while len(data) < length:
        chunk = connection.recv(length - len(data))
        if not chunk:
            raise EOFError("websocket peer closed")
        data.extend(chunk)
    return bytes(data)


def _read_frame(connection):
    first, second = _read_exact(connection, 2)
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", _read_exact(connection, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _read_exact(connection, 8))[0]
    mask = _read_exact(connection, 4) if second & 0x80 else None
    payload = _read_exact(connection, length)
    if mask:
        payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return first & 0x0F, payload


def _send_frame(connection, opcode, payload=b""):
    length = len(payload)
    header = bytes([0x80 | opcode])
    if length < 126:
        header += bytes([length])
    elif length <= 0xFFFF:
        header += bytes([126]) + struct.pack("!H", length)
    else:
        header += bytes([127]) + struct.pack("!Q", length)
    connection.sendall(header + payload)


class _SQLWebSocketServer:
    def __init__(self):
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.frames = []
        self.handshake = None
        self.errors = []
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        connection = None
        try:
            connection, _ = self.listener.accept()
            connection.settimeout(5)
            raw = bytearray()
            while b"\r\n\r\n" not in raw:
                raw.extend(connection.recv(4096))
            head = bytes(raw).split(b"\r\n\r\n", 1)[0].decode("ascii")
            lines = head.split("\r\n")
            headers = {key.lower(): value.strip() for key, value in (line.split(":", 1) for line in lines[1:])}
            self.handshake = (lines[0], headers)
            accept = base64.b64encode(hashlib.sha1((headers["sec-websocket-key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            connection.sendall(
                (
                    "HTTP/1.1 101 Switching Protocols\r\n"
                    "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                    f"Sec-WebSocket-Accept: {accept}\r\n"
                    "Sec-WebSocket-Protocol: moi-api-key\r\n\r\n"
                ).encode()
            )
            while True:
                opcode, payload = _read_frame(connection)
                if opcode == 8:
                    _send_frame(connection, 8, payload[:2])
                    break
                message = json.loads(payload)
                self.frames.append((opcode, message))
                message_id = message["id"]
                if message["message_type"] == "ping":
                    response = {"id": message_id, "message_type": "pong"}
                    _send_frame(connection, 1, json.dumps(response).encode())
                elif message["message_type"] == "query_execute":
                    started = {"id": message_id, "message_type": "query_id", "data": {"query_id": "query/1"}}
                    finished = {
                        "id": message_id,
                        "message_type": "query_result",
                        "data": {"query_id": "query/1", "status": "success", "total": 1, "nullable": None},
                    }
                    _send_frame(connection, 1, json.dumps(started).encode())
                    _send_frame(connection, 1, json.dumps(finished).encode())
                elif message["message_type"] == "query_kill":
                    response = {"id": message_id, "message_type": "query_kill"}
                    _send_frame(connection, 1, json.dumps(response).encode())
        except (EOFError, ConnectionError, OSError) as error:
            if len(self.frames) != 3:
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
            raise AssertionError("SQL WebSocket server did not stop")
        if self.errors:
            raise AssertionError(self.errors)


class SQLQueryWebSocketContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_protocol_timeout_and_close(self):
        secret = "synthetic-key"
        server = _SQLWebSocketServer()
        session = None
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.port}/newmoi", sdk.with_api_key(secret))
            session = client.sql("workspace-1").connect_query_web_socket()
            self.assertEqual(session.protocols(), ["moi-api-key"])
            with self.assertRaises(websocket.WebSocketTimeoutException):
                session.receive(timeout=0.02)
            session.ping("ping-1")
            pong = session.receive(timeout=1)
            self.assertEqual((pong.id, pong.message_type), ("ping-1", sdk.SQLQueryWebSocketMessage.pong))
            session.execute_query(
                "execute-1",
                "SELECT 1",
                sdk.with_sql_query_db_name("db/1"),
                sdk.with_sql_query_type("sql"),
                sdk.with_sql_query_offset(0),
                sdk.with_sql_query_limit(0),
            )
            started = session.receive(timeout=1)
            self.assertEqual(started.message_type, sdk.SQLQueryWebSocketMessage.query_id)
            self.assertEqual(started.data["query_id"], "query/1")
            finished = session.receive(timeout=1)
            self.assertEqual(finished.message_type, sdk.SQLQueryWebSocketMessage.query_result)
            self.assertEqual(finished.data["status"], "success")
            self.assertEqual(finished.data["total"], 1)
            self.assertIsNone(finished.data["nullable"])
            session.kill_query("kill-1", "query/1")
            killed = session.receive(timeout=1)
            self.assertEqual((killed.id, killed.message_type), ("kill-1", sdk.SQLQueryWebSocketMessage.query_kill))
            session.close()
            session = None
            server.thread.join(timeout=2)
            request_line, headers = server.handshake
            target = request_line.split(" ")[1]
            parsed = urllib.parse.urlparse(target)
            self.assertEqual(parsed.path, "/newmoi/query/ws")
            self.assertEqual(urllib.parse.parse_qs(parsed.query), {"workspace_id": ["workspace-1"]})
            self.assertEqual(headers["x-api-key"], secret)
            self.assertEqual(headers["x-workspace-id"], "workspace-1")
            self.assertIn("moi-api-key." + secret, headers["sec-websocket-protocol"])
            expected = [
                {"id": "ping-1", "message_type": "ping"},
                {
                    "id": "execute-1",
                    "message_type": "query_execute",
                    "data": {"query": "SELECT 1", "db_name": "db/1", "sql_type": "sql", "offset": 0, "limit": 0},
                },
                {"id": "kill-1", "message_type": "query_kill", "data": {"query_id": "query/1"}},
            ]
            self.assertEqual(server.frames, [(1, message) for message in expected])
        finally:
            if session is not None:
                session.close()
            server.close()


if __name__ == "__main__":
    unittest.main()
