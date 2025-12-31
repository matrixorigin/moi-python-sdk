"""Client and call options for the MOI SDK."""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import requests


@dataclass
class ClientOptions:
    """Configuration options for the SDK client."""
    http_client: Optional[requests.Session] = None
    user_agent: str = "matrixflow-sdk-python/0.1.0"
    default_headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class CallOptions:
    """Configuration options for individual API calls."""
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    stream_buffer_size: int = 0  # Initial buffer size for stream reader (in bytes), 0 means use default (4KB)


class ClientOption:
    """Function type for client configuration options."""
    def __call__(self, options: ClientOptions) -> None:
        raise NotImplementedError


class CallOption:
    """Function type for call configuration options."""
    def __call__(self, options: CallOptions) -> None:
        raise NotImplementedError


def with_http_client(client: requests.Session) -> ClientOption:
    """Override the default HTTP client used by the SDK."""
    class _Option(ClientOption):
        def __call__(self, options: ClientOptions) -> None:
            if client is not None:
                options.http_client = client
    return _Option()


def with_timeout(timeout: float) -> ClientOption:
    """Configure the timeout on the underlying HTTP client."""
    class _Option(ClientOption):
        def __call__(self, options: ClientOptions) -> None:
            if timeout > 0:
                options.timeout = timeout
    return _Option()


def with_user_agent(user_agent: str) -> ClientOption:
    """Override the default User-Agent header."""
    class _Option(ClientOption):
        def __call__(self, options: ClientOptions) -> None:
            ua = user_agent.strip()
            if ua:
                options.user_agent = ua
    return _Option()


def with_default_header(key: str, value: str) -> ClientOption:
    """Add a header that will be included on every request."""
    class _Option(ClientOption):
        def __call__(self, options: ClientOptions) -> None:
            if key:
                options.default_headers[key] = value
    return _Option()


def with_default_headers(headers: Dict[str, str]) -> ClientOption:
    """Merge a set of headers that will be included on every request."""
    class _Option(ClientOption):
        def __call__(self, options: ClientOptions) -> None:
            if headers:
                options.default_headers.update(headers)
    return _Option()


def with_request_id(request_id: str) -> CallOption:
    """Set the X-Request-ID header on the outgoing request."""
    class _Option(CallOption):
        def __call__(self, options: CallOptions) -> None:
            rid = request_id.strip()
            if rid:
                options.request_id = rid
    return _Option()


def with_header(key: str, value: str) -> CallOption:
    """Set or override a header on the outgoing request."""
    class _Option(CallOption):
        def __call__(self, options: CallOptions) -> None:
            if key:
                options.headers[key] = value
    return _Option()


def with_headers(headers: Dict[str, str]) -> CallOption:
    """Merge headers into the outgoing request."""
    class _Option(CallOption):
        def __call__(self, options: CallOptions) -> None:
            if headers:
                options.headers.update(headers)
    return _Option()


def with_query_param(key: str, value: Any) -> CallOption:
    """Append a single query parameter to the request URL."""
    class _Option(CallOption):
        def __call__(self, options: CallOptions) -> None:
            if key:
                options.query_params[key] = value
    return _Option()


def with_query(query_params: Dict[str, Any]) -> CallOption:
    """Merge an entire query parameter map into the request URL."""
    class _Option(CallOption):
        def __call__(self, options: CallOptions) -> None:
            if query_params:
                options.query_params.update(query_params)
    return _Option()


def with_stream_buffer_size(size: int) -> CallOption:
    """
    Set the initial buffer size for stream reader.
    
    The buffer will dynamically grow as needed to handle lines of arbitrary length,
    so this option only sets the initial buffer size for better performance.
    If not set, the default initial buffer size is 4KB.
    
    The size is specified in bytes. A larger initial buffer can improve performance
    for streams with consistently large lines, but is not required for correctness.
    
    Args:
        size: Initial buffer size in bytes. Must be > 0 to take effect.
    
    Example:
        stream = client.analyze_data_stream(
            {"question": "..."},
            with_stream_buffer_size(64 * 1024)  # 64KB initial buffer
        )
    """
    class _Option(CallOption):
        def __call__(self, options: CallOptions) -> None:
            if size > 0:
                options.stream_buffer_size = size
    return _Option()

