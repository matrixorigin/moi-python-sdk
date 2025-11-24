"""Streaming response helpers for file downloads."""

from __future__ import annotations

from typing import Iterator
import requests


class FileStream:
    """Wraps a streaming HTTP response body."""

    def __init__(self, response: requests.Response):
        self._response = response
        self.body = response.raw
        self.headers = response.headers
        self.status_code = response.status_code

    def iter_content(self, chunk_size: int = 8192) -> Iterator[bytes]:
        """Iterate over the response body."""
        yield from self._response.iter_content(chunk_size)

    def read(self, size: int = -1) -> bytes:
        """Read raw bytes from the response."""
        return self._response.raw.read(size)

    def close(self) -> None:
        """Close the underlying HTTP response."""
        self._response.close()

    def __enter__(self) -> "FileStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

