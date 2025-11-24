"""Error types for the MOI SDK."""


class SDKError(Exception):
    """Base exception for all SDK errors."""
    pass


class ErrBaseURLRequired(SDKError):
    """Indicates that NewRawClient was called without a base URL."""
    pass


class ErrAPIKeyRequired(SDKError):
    """Indicates that NewRawClient was called without an API key."""
    pass


class ErrNilRequest(SDKError):
    """Indicates that a required request payload was None."""
    pass


class APIError(SDKError):
    """
    Captures an application-level error returned by the catalog service envelope.
    
    APIError represents business logic errors returned by the server, such as
    validation errors, resource not found, permission denied, etc.
    
    Attributes:
        code: The error code returned by the server (e.g., "ErrInternal").
        message: The human-readable error message.
        request_id: The unique request identifier for tracking purposes.
        http_status: The HTTP status code of the response.
    """
    
    def __init__(self, code: str, message: str, request_id: str = "", http_status: int = 0):
        self.code = code
        self.message = message
        self.request_id = request_id
        self.http_status = http_status
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        return (
            f"catalog service error: code={self.code} "
            f"msg={self.message} request_id={self.request_id} status={self.http_status}"
        )


class HTTPError(SDKError):
    """
    Represents a non-2xx HTTP response that occurred before the SDK could parse the envelope.
    
    HTTPError represents network-level errors or server errors that occur before
    the response can be parsed as a valid API response envelope.
    
    Attributes:
        status_code: The HTTP status code (e.g., 401, 404, 500).
        body: The raw response body, if available.
    """
    
    def __init__(self, status_code: int, body: bytes = b""):
        self.status_code = status_code
        self.body = body
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if len(self.body) == 0:
            return f"http error: status={self.status_code}"
        try:
            body_str = self.body.decode('utf-8')
        except UnicodeDecodeError:
            body_str = repr(self.body)
        return f"http error: status={self.status_code} body={body_str}"

