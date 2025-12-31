"""Streaming response helpers for file downloads and SSE events."""

from __future__ import annotations

from typing import Iterator, Optional
import json
import os
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

    def write_to_file(self, file_path: str) -> int:
        """
        Write the stream content to a file at the specified path.
        
        The method creates the file and any necessary parent directories.
        It returns the number of bytes written.
        
        Args:
            file_path: Path to the output file
        
        Returns:
            Number of bytes written
        
        Example:
            stream = client.download_table_data({"id": 1})
            try:
                written = stream.write_to_file("/path/to/output.csv")
                print(f"Wrote {written} bytes to file")
            finally:
                stream.close()
        """
        if self._response is None or self.body is None:
            raise IOError("Stream is closed or invalid")
        
        # Create parent directories if they don't exist
        dir_path = os.path.dirname(file_path)
        if dir_path and dir_path != "":
            os.makedirs(dir_path, mode=0o755, exist_ok=True)
        
        # Write the stream content to the file
        written = 0
        with open(file_path, 'wb') as f:
            for chunk in self._response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    written += len(chunk)
        
        return written

    def __enter__(self) -> "FileStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class DataAnalysisStream:
    """
    Wraps a streaming HTTP response for data analysis API.
    
    The stream returns Server-Sent Events (SSE) format. Use read_event to read
    individual events from the stream.
    
    The stream includes events such as:
    - init: Initialization event (first event) with request_id and session_title
      (step_type="init", data contains request_id and session_title)
    - classification: Question classification result
    - complete: Analysis complete
    - error: Error information
    
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
                # Check for init event
                if event.step_type == "init":
                    init_data = event.get_init_event_data()
                    if init_data:
                        print(f"Request ID: {init_data.request_id}, Session Title: {init_data.session_title}")
                print(f"Event type: {event.type}")
        finally:
            stream.close()
    """

    def __init__(self, response: requests.Response, initial_buffer_size: int = 0):
        """
        Initialize a DataAnalysisStream.
        
        Args:
            response: The HTTP response object
            initial_buffer_size: Initial buffer size for reading lines (in bytes).
                                Default is 0, which means use default chunk size (512 bytes).
                                The buffer will dynamically grow as needed to handle lines of
                                arbitrary length, so this option only sets the initial buffer
                                size for better performance. This is provided for API consistency
                                with Go SDK.
        """
        self._response = response
        self.body = response.raw
        self.headers = response.headers
        self.status_code = response.status_code
        self._scanner = None
        self._initial_buffer_size = initial_buffer_size

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
            # Set chunk_size based on initial_buffer_size if specified
            # Default chunk_size is 512 bytes. iter_lines will dynamically grow to handle
            # lines of arbitrary length, so this only sets the initial chunk size.
            chunk_size = 512
            if self._initial_buffer_size > 0:
                # Use a reasonable chunk size based on initial buffer size
                # Default to 4KB if not specified, but allow custom sizes
                chunk_size = max(512, min(self._initial_buffer_size, 8192))  # Between 512B and 8KB
            else:
                # Default initial buffer size: 4KB (4096 bytes)
                chunk_size = 4096
            self._scanner = iter(self._response.iter_lines(decode_unicode=True, chunk_size=chunk_size))

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
                            # But still set event.type if event_type was specified
                            if event_type:
                                event.type = event_type
                            return event
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
                    # But still set event.type if event_type was specified
                    if event_type:
                        event.type = event_type
                    return event
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

