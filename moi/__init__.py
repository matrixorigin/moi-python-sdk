"""
MOI Python SDK

A Python client library for interacting with the MOI Catalog Service.
"""

from .client import RawClient
from .errors import APIError, HTTPError, ErrBaseURLRequired, ErrAPIKeyRequired, ErrNilRequest
from .sdk_client import SDKClient, TablePrivInfo
from .stream import FileStream, DataAnalysisStream
from .models import (
    DataAnalysisRequest,
    DataAnalysisConfig,
    DataAnalysisStreamEvent,
    DataSource,
    DataAskingTableConfig,
    FileConfig,
    FilterConditions,
    DataScope,
    CodeGroup,
    QuestionType,
)

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
    "FileStream",
    "DataAnalysisStream",
    "DataAnalysisRequest",
    "DataAnalysisConfig",
    "DataAnalysisStreamEvent",
    "DataSource",
    "DataAskingTableConfig",
    "FileConfig",
    "FilterConditions",
    "DataScope",
    "CodeGroup",
    "QuestionType",
]

