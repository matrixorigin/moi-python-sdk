"""Streaming response helpers for file downloads and SSE events."""

from __future__ import annotations

from typing import Iterator, Optional
import json
import requests

from .models import DataAnalysisStreamEvent


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


class DataAnalysisStream:
    """
    Wraps a streaming HTTP response for data analysis API.
    
    The stream returns Server-Sent Events (SSE) format. Use read_event to read
    individual events from the stream.
    
    Example:
        stream = client.analyze_data_stream({
            "question": "2024年收入下降的原因是什么？",
            "session_id": "session_123"
        })
        try:
            while True:
                event = stream.read_event()
                if event is None:  # EOF
                    break
                print(f"Event type: {event.type}")
        finally:
            stream.close()
    """

    def __init__(self, response: requests.Response):
        self._response = response
        self.body = response.raw
        self.headers = response.headers
        self.status_code = response.status_code
        self._scanner = None

    def close(self) -> None:
        """Close the underlying HTTP response."""
        if self._response is not None:
            self._response.close()

    def read_event(self) -> Optional[DataAnalysisStreamEvent]:
        """
        Read the next SSE event from the stream.
        
        Returns:
            DataAnalysisStreamEvent or None when the stream is complete (EOF).
        
        Example:
            while True:
                event = stream.read_event()
                if event is None:
                    break
                # Process event
        """
        if self._scanner is None:
            # Initialize scanner to read line by line
            self._scanner = iter(self._response.iter_lines(decode_unicode=True))

        event = DataAnalysisStreamEvent()
        data_lines = []
        event_type = None

        try:
            for line in self._scanner:
                line = line.strip()
                if line == "":
                    # Empty line indicates end of event
                    if len(data_lines) > 0:
                        # Parse the accumulated data
                        data_str = "\n".join(data_lines)
                        event.raw_data = data_str.encode('utf-8')
                        try:
                            parsed = json.loads(data_str)
                            if isinstance(parsed, dict):
                                # Extract all fields from parsed JSON
                                event.data = parsed
                                event.type = parsed.get("type") or event.type
                                event.source = parsed.get("source") or event.source
                                event.step_type = parsed.get("step_type") or event.step_type
                                event.step_name = parsed.get("step_name") or event.step_name
                        except json.JSONDecodeError:
                            # If JSON parsing fails, return raw data (event already has raw_data set)
                            pass
                        if event_type:
                            event.type = event_type
                        return event
                    continue

                # Parse SSE format: "field: value"
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    data_lines.append(data)
                elif line.startswith("event: "):
                    event_type = line[7:]  # Remove "event: " prefix
                # Ignore other SSE fields (id, retry, etc.)

            # Handle last event if any
            if len(data_lines) > 0:
                data_str = "\n".join(data_lines)
                event.raw_data = data_str.encode('utf-8')
                try:
                    parsed = json.loads(data_str)
                    if isinstance(parsed, dict):
                        # Extract all fields from parsed JSON
                        event.data = parsed
                        event.type = parsed.get("type") or event.type
                        event.source = parsed.get("source") or event.source
                        event.step_type = parsed.get("step_type") or event.step_type
                        event.step_name = parsed.get("step_name") or event.step_name
                except json.JSONDecodeError:
                    # If JSON parsing fails, return raw data (event already has raw_data set)
                    pass
                if event_type:
                    event.type = event_type
                return event

            # EOF
            return None

        except StopIteration:
            return None

    def __enter__(self) -> "DataAnalysisStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

