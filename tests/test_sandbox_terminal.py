import base64
import hashlib
import json
import socket
import struct
import threading
import time
import unittest
import urllib.parse

import moi_product_sdk as sdk

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
    opcode = first & 0x0F
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", _read_exact(connection, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _read_exact(connection, 8))[0]
    mask = _read_exact(connection, 4) if second & 0x80 else None
    payload = _read_exact(connection, length)
    if mask:
        payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return opcode, payload


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


class _TerminalServer:
    def __init__(self, acknowledge_close=True):
        self.acknowledge_close = acknowledge_close
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.frames = []
        self.handshake = None
        self.errors = []
        self.release = threading.Event()
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
            connection.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + accept + "\r\n\r\n").encode())
            while True:
                opcode, payload = _read_frame(connection)
                if opcode == 8:
                    if self.acknowledge_close:
                        _send_frame(connection, 8, payload[:2])
                    else:
                        self.release.wait(5)
                    break
                self.frames.append((opcode, payload))
                if opcode == 2:
                    _send_frame(connection, 2, b"\x00\x01\xff")
                elif opcode == 1:
                    _send_frame(connection, 1, b'{"type":"exit","code":0}')
        except (EOFError, ConnectionError, OSError) as error:
            if self.frames or self.acknowledge_close:
                self.errors.append(error)
        except Exception as error:
            self.errors.append(error)
        finally:
            if connection is not None:
                connection.close()
            self.listener.close()

    def close(self):
        self.release.set()
        self.listener.close()
        self.thread.join(timeout=6)
        self.assert_no_errors()

    def assert_no_errors(self):
        if self.errors:
            raise AssertionError(self.errors)


class SandboxTerminalProtocolTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_frames_receive_and_close(self):
        server = _TerminalServer()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.port}/newmoi", sdk.with_api_key("synthetic-key"))
            terminal = client.sandboxes("workspace-1").connect_terminal("sandbox-1", "signed token", cols=100, rows=30)
            terminal.write_input(b"\x00\x02\xfe")
            terminal.resize(120, 40)
            self.assertEqual(terminal.receive(), b"\x00\x01\xff")
            self.assertEqual(terminal.receive(), b'{"type":"exit","code":0}')
            terminal.close()
            deadline = time.monotonic() + 2
            while len(server.frames) < 2 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(server.frames[0], (2, b"\x00\x02\xfe"))
            self.assertEqual(server.frames[1][0], 1)
            self.assertEqual(json.loads(server.frames[1][1]), {"type": "resize", "cols": 120, "rows": 40})
            request, headers = server.handshake
            parsed = urllib.parse.urlsplit(request.split(" ")[1])
            self.assertEqual(parsed.path, "/newmoi/agent-sandboxes/sandbox-1/terminal/ws")
            self.assertEqual(urllib.parse.parse_qs(parsed.query), {"token": ["signed token"], "cols": ["100"], "rows": ["30"]})
            self.assertEqual(headers["origin"], f"http://127.0.0.1:{server.port}")
        finally:
            server.close()

    def test_close_does_not_wait_for_peer_acknowledgement(self):
        server = _TerminalServer(acknowledge_close=False)
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.port}/newmoi", sdk.with_api_key("synthetic-key"))
            terminal = client.sandboxes("workspace-1").connect_terminal("sandbox-1", "signed-token")
            started = time.monotonic()
            terminal.close()
            self.assertLess(time.monotonic() - started, 1.0, "close waited for a peer close frame")
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
