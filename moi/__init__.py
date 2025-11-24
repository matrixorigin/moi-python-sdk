"""
MOI Python SDK

A Python client library for interacting with the MOI Catalog Service.
"""

from .client import RawClient
from .errors import APIError, HTTPError, ErrBaseURLRequired, ErrAPIKeyRequired, ErrNilRequest
from .sdk_client import SDKClient, TablePrivInfo

__version__ = "0.1.0"
__all__ = [
    "RawClient",
    "SDKClient",
    "TablePrivInfo",
    "APIError",
    "HTTPError",
    "ErrBaseURLRequired",
    "ErrAPIKeyRequired",
    "ErrNilRequest",
]

