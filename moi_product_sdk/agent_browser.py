from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from .errors import Error


@dataclass(frozen=True)
class RuntimeBrowserFrame:
    """One browser frame, preserving text metadata versus binary image data."""

    text: bool
    data: bytes


class RuntimeBrowser:
    def __init__(self, connection: Any):
        self._connection = connection

    def close(self) -> None:
        # Do not wait for a peer that may already have stopped reading.
        self._connection.close(timeout=0)

    def write_input(self, event: Any) -> None:
        self._connection.send(json.dumps(event, ensure_ascii=False, separators=(",", ":")))

    def receive(self, timeout: Optional[float] = None) -> RuntimeBrowserFrame:
        previous_timeout = self._connection.gettimeout()
        if timeout is not None:
            self._connection.settimeout(timeout)
        try:
            data = self._connection.recv()
        finally:
            if timeout is not None:
                self._connection.settimeout(previous_timeout)
        if isinstance(data, str):
            return RuntimeBrowserFrame(text=True, data=data.encode("utf-8"))
        if isinstance(data, bytes):
            return RuntimeBrowserFrame(text=False, data=data)
        raise Error("ErrResponseInvalid", "runtime browser frame must be text or binary")


class AgentBrowser:
    """Task browser handoff. Receive pairs each frame event with its image."""

    def __init__(self, connection, timeout: float):
        self._connection = connection
        self._timeout = timeout

    def close(self) -> None:
        self._connection.close()

    def compression_enabled(self) -> bool:
        return "permessage-deflate" in self._connection.response.headers.get("Sec-WebSocket-Extensions", "")

    def receive(self) -> tuple[dict[str, Any], bytes | None]:
        payload = self._connection.recv(timeout=self._timeout)
        if not isinstance(payload, str):
            raise Error("ErrResponseInvalid", "browser event must be text")
        try:
            event = json.loads(payload)
        except ValueError as exc:
            raise Error("ErrResponseInvalid", "browser event must be valid JSON") from exc
        if not isinstance(event, dict):
            raise Error("ErrResponseInvalid", "browser event must be an object")
        image = None
        if event.get("type") == "frame":
            image = self._connection.recv(timeout=self._timeout)
            if not isinstance(image, bytes):
                raise Error("ErrResponseInvalid", "browser frame image must be binary")
        return event, image

    def acknowledge(self, seq: int) -> None:
        """Release stream credit after processing a frame, using its seq."""
        self._connection.send(json.dumps({"type": "ack", "seq": seq}))

    def input_keyboard(self, event_type: str, text: str) -> None:
        self._connection.send(json.dumps({"type": "input_keyboard", "eventType": event_type, "text": text}))

    def release(self) -> None:
        self._connection.send(json.dumps({"type": "release"}))
