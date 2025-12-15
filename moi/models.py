"""Data models for the MOI Python SDK.

This module mirrors the structures defined in the Go SDK's models.go file.
Where possible, dataclasses are used for clarity. These types cover request
and response payloads exchanged with the MOI Catalog Service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

# ============ Infra: Filter types ============


@dataclass
class CommonFilter:
    name: str
    values: List[str] = field(default_factory=list)
    fuzzy: bool = False
    filter_values: List[Any] = field(default_factory=list)


@dataclass
class CommonCondition:
    page: int = 1
    page_size: int = 20
    order: str = "desc"
    order_by: str = "created_at"
    filters: List[CommonFilter] = field(default_factory=list)


# ============ Models: Common types and IDs ============

DatabaseID = int
TableID = int
CatalogID = int
VolumeID = str
FileID = str
UserID = int
RoleID = int
PrivID = int
PrivCode = str
PrivObjectID = str
ObjTypeValue = int
PrivType = int

DatabaseIDNotFound = 9223372036854775807
CatalogIDNotFound = 9223372036854775807
RoleIDNotFound = 4294967295
UserIDNotFound = 4294967295


@dataclass
class FullPath:
    id_list: List[str] = field(default_factory=list)
    name_list: List[str] = field(default_factory=list)


class ObjType(Enum):
    NONE = 0
    CONNECTOR = 1
    LOAD_TASK = 2
    WORKFLOW = 3
    VOLUME = 4
    DATASET = 5
    ALARM = 6
    USER = 7
    ROLE = 8
    EXPORT_TASK = 9
    DATA_CENTER = 10
    CATALOG = 11
    DATABASE = 12
    TABLE = 13

    def __str__(self) -> str:  # pragma: no cover - trivial
        mapping = {
            ObjType.CONNECTOR: "connector",
            ObjType.LOAD_TASK: "load_task",
            ObjType.WORKFLOW: "workflow",
            ObjType.VOLUME: "volume",
            ObjType.DATASET: "dataset",
            ObjType.ALARM: "alarm",
            ObjType.USER: "user",
            ObjType.ROLE: "role",
            ObjType.EXPORT_TASK: "export_task",
            ObjType.DATA_CENTER: "data_center",
            ObjType.CATALOG: "catalog",
            ObjType.DATABASE: "database",
            ObjType.TABLE: "table",
        }
        return mapping.get(self, "none")


@dataclass
class CheckPriv:
    priv_id: PrivID
    obj_id: PrivObjectID


@dataclass
class AuthorityCodeAndRule:
    code: str
    black_column_list: List[str] = field(default_factory=list)
    rule_list: Optional[List["TableRowColRule"]] = None


@dataclass
class TableRowColExpression:
    operator: str
    expression: str
    match_type: str = ""  # c,i,m,n,u


@dataclass
class TableRowColRule:
    column: str
    relation: str
    expression_list: List[TableRowColExpression] = field(default_factory=list)


@dataclass
class ObjPrivResponse:
    obj_id: str
    obj_type: str
    obj_name: str = ""
    authority_code_list: Optional[List[AuthorityCodeAndRule]] = None


@dataclass
class PrivObjectIDAndName:
    object_id: str
    object_name: str
    database_id: str = ""
    object_type: str = ""
    node_list: List["PrivObjectIDAndName"] = field(default_factory=list)


# ============ Catalog types ============


@dataclass
class CatalogCreateRequest:
    catalog_name: str
    comment: str = ""


@dataclass
class CatalogCreateResponse:
    catalog_id: CatalogID


@dataclass
class CatalogDeleteRequest:
    catalog_id: CatalogID


@dataclass
class CatalogDeleteResponse:
    catalog_id: CatalogID


@dataclass
class CatalogUpdateRequest:
    catalog_id: CatalogID
    catalog_name: str
    comment: str = ""


@dataclass
class CatalogUpdateResponse:
    catalog_id: CatalogID


@dataclass
class CatalogInfoRequest:
    catalog_id: CatalogID


@dataclass
class CatalogInfoResponse:
    catalog_id: CatalogID
    catalog_name: str
    comment: str


@dataclass
class CatalogResponse:
    catalog_id: CatalogID
    catalog_name: str
    comment: str
    database_count: int = 0
    table_count: int = 0
    volume_count: int = 0
    file_count: int = 0
    reserved: bool = False
    created_at: str = ""
    created_by: str = ""
    updated_at: str = ""
    updated_by: str = ""


@dataclass
class TreeNode:
    typ: str
    id: str
    name: str
    description: str
    reserved: bool = False
    has_workflow_target_ref: bool = False
    node_list: List["TreeNode"] = field(default_factory=list)


@dataclass
class CatalogTreeResponse:
    tree: List[TreeNode] = field(default_factory=list)


@dataclass
class CatalogListResponse:
    list: List[CatalogResponse] = field(default_factory=list)


@dataclass
class CatalogRefListRequest:
    catalog_id: CatalogID


@dataclass
class CatalogRefListResponse:
    list: List["VolumeRefResp"] = field(default_factory=list)


# ============ Database types ============


@dataclass
class DatabaseCreateRequest:
    database_name: str
    comment: str
    catalog_id: CatalogID


@dataclass
class DatabaseCreateResponse:
    database_id: DatabaseID


@dataclass
class DatabaseDeleteRequest:
    database_id: DatabaseID


@dataclass
class DatabaseDeleteResponse:
    database_id: DatabaseID


@dataclass
class DatabaseUpdateRequest:
    database_id: DatabaseID
    comment: str


@dataclass
class DatabaseUpdateResponse:
    database_id: DatabaseID


@dataclass
class DatabaseInfoRequest:
    database_id: DatabaseID


@dataclass
class DatabaseInfoResponse:
    database_id: DatabaseID
    database_name: str
    comment: str
    created_at: str = ""
    updated_at: str = ""


@dataclass
class DatabaseResponse:
    database_id: DatabaseID
    database_name: str
    comment: str
    table_count: int = 0
    volume_count: int = 0
    file_count: int = 0
    reserved: bool = False
    created_at: str = ""
    created_by: str = ""
    updated_at: str = ""
    updated_by: str = ""


@dataclass
class DatabaseListRequest:
    catalog_id: CatalogID


@dataclass
class DatabaseListResponse:
    list: List[DatabaseResponse] = field(default_factory=list)


@dataclass
class DatabaseChildrenRequest:
    database_id: DatabaseID


@dataclass
class DatabaseChildrenResponse:
    id: str
    name: str
    typ: str
    children_count: int
    size: int
    comment: str
    reserved: bool
    created_at: str
    created_by: str
    updated_at: str
    updated_by: str


@dataclass
class DatabaseChildrenResponseData:
    list: List[DatabaseChildrenResponse] = field(default_factory=list)


@dataclass
class DatabaseRefListRequest:
    database_id: DatabaseID


@dataclass
class DatabaseRefListResponse:
    list: List["VolumeRefResp"] = field(default_factory=list)


# ============ Volume types ============


@dataclass
class VolumeCreateRequest:
    name: str
    database_id: DatabaseID
    comment: str


@dataclass
class VolumeCreateResponse:
    volume_id: VolumeID


@dataclass
class VolumeDeleteRequest:
    volume_id: VolumeID


@dataclass
class VolumeDeleteResponse:
    volume_id: VolumeID


@dataclass
class VolumeUpdateRequest:
    volume_id: VolumeID
    name: str
    comment: str


@dataclass
class VolumeUpdateResponse:
    volume_id: VolumeID


@dataclass
class VolumeInfoRequest:
    volume_id: VolumeID


@dataclass
class VolumeInfoResponse:
    volume_id: VolumeID
    volume_name: str
    comment: str
    ref: bool = False
    created_at: str = ""
    updated_at: str = ""


@dataclass
class VolumeRefResp:
    volume_id: VolumeID
    volume_name: str
    ref_type: str
    ref_id: str


@dataclass
class VolumeRefListRequest:
    volume_id: VolumeID


@dataclass
class VolumeRefListResponse:
    list: List[VolumeRefResp] = field(default_factory=list)


@dataclass
class VolumeChildrenResponse:
    id: str
    name: str
    file_type: str
    show_type: str
    file_ext: str
    origin_file_ext: str
    ref_file_id: str
    size: int
    volume_id: str
    volume_name: str
    volume_reserved: bool
    ref_workflow_id: str
    parent_id: str
    show_path: str
    save_path: str
    created_at: str
    created_by: str
    updated_at: str


@dataclass
class VolumeFullPathRequest:
    database_id_list: Optional[List[DatabaseID]] = None
    volume_id_list: Optional[List[VolumeID]] = None
    folder_id_list: Optional[List[FileID]] = None


@dataclass
class VolumeFullPathResponse:
    database_full_path: List[FullPath] = field(default_factory=list)
    volume_full_path: List[FullPath] = field(default_factory=list)
    folder_full_path: List[FullPath] = field(default_factory=list)


@dataclass
class VolumeAddRefWorkflowRequest:
    volume_id: VolumeID


@dataclass
class VolumeAddRefWorkflowResponse:
    volume_id: VolumeID


@dataclass
class VolumeRemoveRefWorkflowRequest:
    volume_id: VolumeID


@dataclass
class VolumeRemoveRefWorkflowResponse:
    volume_id: VolumeID


# ============ Data Analysis types ============


@dataclass
class DataAskingTableConfig:
    """Table configuration for NL2SQL in data asking context."""
    type: str  # "all", "none", "specified"
    db_name: Optional[str] = None
    table_list: List[str] = field(default_factory=list)


@dataclass
class FileConfig:
    """File configuration for RAG."""
    type: str  # "all", "none", "specified"
    target_volume_name: Optional[str] = None
    target_volume_id: Optional[str] = None
    file_id_list: List[str] = field(default_factory=list)


@dataclass
class FilterConditions:
    """Filter conditions."""
    type: str  # "all", "non_inter_data"


@dataclass
class CodeGroup:
    """Code group."""
    code: str = ""  # Parent-level code
    name: str = ""  # Code group name
    values: List[str] = field(default_factory=list)  # Code value list


@dataclass
class DataScope:
    """Data scope configuration."""
    type: str  # "all", "specified"
    code_type: Optional[int] = None  # 0-company, 1-business unit
    code_group: List[CodeGroup] = field(default_factory=list)


@dataclass
class DataSource:
    """Data source configuration."""
    type: str  # "all", "specified"
    tables: Optional[DataAskingTableConfig] = None
    files: Optional[FileConfig] = None


@dataclass
class DataAnalysisConfig:
    """Data analysis configuration."""
    data_category: str  # "admin", "common"
    filter_conditions: Optional[FilterConditions] = None
    data_source: Optional[DataSource] = None
    data_scope: Optional[DataScope] = None


@dataclass
class DataAnalysisRequest:
    """Request for data analysis."""
    question: str
    source: Optional[str] = None
    session_id: Optional[str] = None
    session_name: Optional[str] = None
    config: Optional[DataAnalysisConfig] = None


@dataclass
class QuestionType:
    """Question classification result."""
    type: str  # "query", "attribution"
    confidence: float
    reason: str


@dataclass
class DataAnalysisStreamEvent:
    """Single event in the SSE stream."""
    type: Optional[str] = None
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    step_type: Optional[str] = None
    step_name: Optional[str] = None
    raw_data: Optional[bytes] = None  # Raw JSON data for flexible parsing


@dataclass
class CancelAnalyzeRequest:
    """Request to cancel a data analysis request."""
    request_id: str  # Required: The request ID of the analysis to cancel


@dataclass
class CancelAnalyzeResponse:
    """Response from canceling a data analysis request."""
    request_id: str  # The request ID that was cancelled
    status: str  # Status after cancellation (typically "cancelled")
    user_id: str  # User ID who cancelled the request
    user_name: str = ""  # User name who cancelled the request


# ============ Models: File/Dedup types ============


class DedupBy:
    """Deduplication criteria constants."""
    NAME = "name"  # Deduplicate files by filename
    MD5 = "md5"    # Deduplicate files by MD5 hash


class DedupStrategy:
    """Deduplication strategy constants."""
    SKIP = "skip"      # Skip duplicate files (does not upload)
    REPLACE = "replace"  # Replace duplicate files


@dataclass
class DedupConfig:
    """Deduplication configuration."""
    by: List[str]
    strategy: str


def new_dedup_config(by: List[str], strategy: str) -> Optional[DedupConfig]:
    """
    Create a new DedupConfig with the specified criteria and strategy.
    
    This is a helper function to create DedupConfig in a type-safe way.
    Use DedupBy constants for criteria and DedupStrategy constants for strategy.
    
    Args:
        by: List of deduplication criteria (e.g., [DedupBy.NAME, DedupBy.MD5])
        strategy: Deduplication strategy (e.g., DedupStrategy.SKIP)
    
    Returns:
        DedupConfig instance, or None if by list is empty
    
    Example:
        # Skip files that have the same name or MD5 hash
        dedup = new_dedup_config([DedupBy.NAME, DedupBy.MD5], DedupStrategy.SKIP)
        
        # Skip files that have the same name
        dedup = new_dedup_config([DedupBy.NAME], DedupStrategy.SKIP)
    """
    if not by or len(by) == 0:
        return None
    return DedupConfig(by=by, strategy=strategy)


def new_dedup_config_skip_by_name_and_md5() -> DedupConfig:
    """
    Create a DedupConfig that skips files with the same name or MD5 hash.
    
    This is a convenience function for the most common deduplication scenario.
    
    Returns:
        DedupConfig instance configured to skip by name and MD5
    
    Example:
        dedup = new_dedup_config_skip_by_name_and_md5()
        resp = sdk_client.import_local_file_to_volume(file_path, volume_id, meta, dedup)
    """
    return DedupConfig(by=[DedupBy.NAME, DedupBy.MD5], strategy=DedupStrategy.SKIP)


def new_dedup_config_skip_by_name() -> DedupConfig:
    """
    Create a DedupConfig that skips files with the same name.
    
    Returns:
        DedupConfig instance configured to skip by name
    
    Example:
        dedup = new_dedup_config_skip_by_name()
        resp = sdk_client.import_local_file_to_volume(file_path, volume_id, meta, dedup)
    """
    return DedupConfig(by=[DedupBy.NAME], strategy=DedupStrategy.SKIP)


def new_dedup_config_skip_by_md5() -> DedupConfig:
    """
    Create a DedupConfig that skips files with the same MD5 hash.
    
    Returns:
        DedupConfig instance configured to skip by MD5
    
    Example:
        dedup = new_dedup_config_skip_by_md5()
        resp = sdk_client.import_local_file_to_volume(file_path, volume_id, meta, dedup)
    """
    return DedupConfig(by=[DedupBy.MD5], strategy=DedupStrategy.SKIP)


# ============ Handler: Task types ============


TaskID = int


@dataclass
class TaskInfoRequest:
    """Request to get task information."""
    task_id: TaskID


@dataclass
class LoadResult:
    """Represents a single file load result."""
    lines: int
    reason: Optional[str] = None


@dataclass
class TaskInfoResponse:
    """Task information response."""
    id: str
    source_connector_id: int
    source_connector_type: str
    volume_id: str
    volume_name: str
    volume_path: Optional[FullPath] = None
    name: str = ""
    creator: str = ""
    status: str = ""
    source_config: Optional[Dict[str, Any]] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    connector_name: Optional[str] = None
    table_path: Optional[FullPath] = None
    source_files: Optional[List[List[str]]] = None
    load_results: Optional[List[LoadResult]] = None


# ============ Handler: User types ============


@dataclass
class UserCreateRequest:
    """Request to create a user."""
    name: str
    password: str
    role_id_list: List[RoleID] = field(default_factory=list)
    description: str = ""
    phone: str = ""
    email: str = ""
    get_api_key: bool = False  # Whether to return API key in response


@dataclass
class UserCreateResponse:
    """Response from creating a user."""
    id: UserID
    api_key: Optional[str] = None  # API key (only present if get_api_key was true in request)


# Additional sections (Tables, Files, Folders, Roles, etc.) would follow
# using the same pattern. For brevity, only the core structures are defined here.
