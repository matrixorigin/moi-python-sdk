"""
MOI Python SDK

A Python client library for interacting with the MOI Catalog Service.
"""

from .client import RawClient
from .errors import APIError, HTTPError, ErrBaseURLRequired, ErrAPIKeyRequired, ErrNilRequest
from .sdk_client import SDKClient, TablePrivInfo, ExistedTableOption, ExistedTableOptions
from .stream import FileStream, DataAnalysisStream
from .models import (
    DataAnalysisRequest,
    DataAnalysisConfig,
    DataAnalysisStreamEvent,
    InitEventData,
    DataSource,
    DataAskingTableConfig,
    FileConfig,
    FilterConditions,
    DataScope,
    CodeGroup,
    QuestionType,
    DedupBy,
    DedupStrategy,
    DedupConfig,
    new_dedup_config,
    new_dedup_config_skip_by_name_and_md5,
    new_dedup_config_skip_by_name,
    new_dedup_config_skip_by_md5,
)

__version__ = "0.1.0"
__all__ = [
    "RawClient",
    "SDKClient",
    "TablePrivInfo",
    "ExistedTableOption",
    "ExistedTableOptions",
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
    "InitEventData",
    "DataSource",
    "DataAskingTableConfig",
    "FileConfig",
    "FilterConditions",
    "DataScope",
    "CodeGroup",
    "QuestionType",
    "DedupBy",
    "DedupStrategy",
    "DedupConfig",
    "new_dedup_config",
    "new_dedup_config_skip_by_name_and_md5",
    "new_dedup_config_skip_by_name",
    "new_dedup_config_skip_by_md5",
]

