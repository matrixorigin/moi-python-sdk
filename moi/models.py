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
# PrivID constants (for reference):
# Knowledge: PrivID_CreateKnowledge = 300, PrivID_QueryKnowledge = 301, PrivID_UpdateKnowledge = 302,
#            PrivID_DeleteKnowledge = 303, PrivID_UseKnowledge = 304
# Publication/Subscription: PrivID_CreatePublication = 400, PrivID_QueryPublication = 401,
#                          PrivID_UpdatePublication = 402, PrivID_DeletePublication = 403,
#                          PrivID_CreateSubscription = 404, PrivID_QuerySubscription = 405,
#                          PrivID_UpdateSubscription = 406, PrivID_DeleteSubscription = 407,
#                          PrivID_UseSubscription = 408

PrivCode = str
# PrivCode constants (for reference):
# Knowledge: PrivCode_CreateKnowledge = "K1", PrivCode_QueryKnowledge = "K2",
#            PrivCode_UpdateKnowledge = "K3", PrivCode_DeleteKnowledge = "K4",
#            PrivCode_UseKnowledge = "K5"
# Publication/Subscription: PrivCode_CreatePublication = "PS1", PrivCode_QueryPublication = "PS2",
#                          PrivCode_UpdatePublication = "PS3", PrivCode_DeletePublication = "PS4",
#                          PrivCode_QuerySubscription = "PS5", PrivCode_CreateSubscription = "PS6",
#                          PrivCode_UpdateSubscription = "PS7", PrivCode_DeleteSubscription = "PS8"

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
    KNOWLEDGE = 14  # 知识库
    PUBLICATION = 15  # 发布操作
    SUBSCRIPTION = 16  # 订阅操作

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
            ObjType.KNOWLEDGE: "knowledge",
            ObjType.PUBLICATION: "publication",
            ObjType.SUBSCRIPTION: "subscription",
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
    operator: str  # = != like > >= < <= regexp_like
    expression: List[str]  # Changed from str to List[str]
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
    db_name: str  # Required: database name
    database_id: Optional[int] = None  # Database ID, used when type is "all"
    table_list: List[str] = field(default_factory=list)  # Table name list, used when type is "specified"


@dataclass
class FileConfig:
    """File configuration for RAG."""
    type: str  # "all", "none", "specified"
    database_id: Optional[int] = None  # Database ID, used when type is "all"
    file_id_list: List[str] = field(default_factory=list)  # File ID list, used when type is "specified"


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
    mcp_server_url: Optional[str] = None  # MCP server URL
    data_object_type: str = "default"  # "default", "audit_related" (default: "default")
    data_category: str = "admin"  # "admin", "common" (default: "admin")
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
class InitEventData:
    """Data field in an init event."""
    request_id: str
    session_title: str = ""


@dataclass
class DataAnalysisStreamEvent:
    """
    Single event in the SSE stream.
    
    Common event formats:
    - init event: step_type="init", data contains request_id and session_title
    - classification event: type="classification"
    - events with step_type field: StepType field contains the step type (e.g., "init", "sql_generated")
    - events with source field: Source field indicates the source (e.g., "rag", "nl2sql")
    """
    type: Optional[str] = None
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    step_type: Optional[str] = None  # For events that don't have a "type" field but have step_type (e.g., step_type="init" for initialization)
    step_name: Optional[str] = None
    raw_data: Optional[bytes] = None  # Raw JSON data for flexible parsing
    
    def get_init_event_data(self) -> Optional[InitEventData]:
        """
        Extract request_id and session_title from an init event.
        
        Returns None if the event is not an init event or if the data cannot be parsed.
        
        Example:
            event = stream.read_event()
            if event.step_type == "init":
                init_data = event.get_init_event_data()
                if init_data:
                    print(f"Request ID: {init_data.request_id}, Session Title: {init_data.session_title}")
        """
        if self.step_type != "init":
            return None
        
        # Try to extract from Data field first
        if self.data:
            request_id = self.data.get("request_id", "")
            session_title = self.data.get("session_title", "")
            if request_id:
                return InitEventData(
                    request_id=request_id,
                    session_title=session_title
                )
        
        # Try to parse from RawData
        if self.raw_data:
            try:
                import json
                parsed = json.loads(self.raw_data.decode('utf-8'))
                if isinstance(parsed, dict) and "data" in parsed:
                    data = parsed["data"]
                    if isinstance(data, dict):
                        request_id = data.get("request_id", "")
                        session_title = data.get("session_title", "")
                        if request_id:
                            return InitEventData(
                                request_id=request_id,
                                session_title=session_title
                            )
            except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
                pass
        
        return None


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


# ============ Models: File types ============

class FileType:
    """File type constants."""
    UNKNOWN = 0
    TXT = 1
    PDF = 2
    IMAGE = 3
    PPT = 4
    DOC = 5
    MARKDOWN = 6
    CSV = 7
    PARQUET = 8
    SQL_FILES = 9
    DIR = 10
    DOCX = 11
    PPTX = 12
    WAV = 13
    MP3 = 14
    AAC = 15
    FLAC = 16
    MP4 = 17
    MOV = 18
    MKV = 19
    PNG = 20
    JPG = 21
    JPEG = 22
    BMP = 23
    XLS = 24
    XLSX = 25
    HTM = 27
    HTML = 28
    EML = 29
    MSG = 30
    P7S = 31
    DWG = 32
    DXF = 33
    FAS = 34


# ============ Handler: Workflow types ============

@dataclass
class ProcessMode:
    """Processing mode for workflows."""
    interval: int  # Processing interval in seconds
    offset: int = 0  # Processing offset in seconds


class WorkflowJobStatus:
    """Workflow job status constants."""
    UNKNOWN = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3
    
    @staticmethod
    def to_string(status: int) -> str:
        """Convert status integer to string."""
        if status == WorkflowJobStatus.RUNNING:
            return "running"
        elif status == WorkflowJobStatus.COMPLETED:
            return "completed"
        elif status == WorkflowJobStatus.FAILED:
            return "failed"
        elif status == WorkflowJobStatus.UNKNOWN:
            return "unknown"
        else:
            return f"unknown({status})"


@dataclass
class WorkflowMetadata:
    """Workflow metadata for creating a workflow."""
    name: str = ""
    source_volume_names: List[str] = field(default_factory=list)  # Required: must be present even if empty
    source_volume_ids: List[str] = field(default_factory=list)  # Required: must be present even if empty
    target_volume_name: str = ""  # deprecated at moi 3.2.4
    target_volume_id: str = ""
    create_target_volume_name: str = ""
    process_mode: Optional[ProcessMode] = None  # Required: must be present even if empty
    file_types: List[int] = field(default_factory=list)
    workflow: Optional["CatalogWorkflow"] = None


@dataclass
class CatalogWorkflow:
    """Workflow definition with nodes and connections."""
    nodes: List["CatalogWorkflowNode"] = field(default_factory=list)
    connections: List["CatalogWorkflowConnection"] = field(default_factory=list)


@dataclass
class CatalogWorkflowNode:
    """Workflow node definition."""
    id: str
    type: str
    init_parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Required: must be present, use empty dict {} if no parameters


@dataclass
class CatalogWorkflowConnection:
    """Workflow connection definition."""
    sender: str
    receiver: str  # Note: JSON may use "reciever" instead of "receiver" (typo)
    sender_port: str = ""  # Optional port for sender component
    receiver_port: str = ""  # Optional port for receiver component


@dataclass
class WorkflowCreateResponse:
    """Response from creating a workflow."""
    created_at: str = ""
    creator: str = ""
    content: str = ""
    updated_at: str = ""
    modifier: str = ""
    id: str = ""
    file_types: str = ""
    name: str = ""
    source_volume_ids: str = ""
    user_id: str = ""
    source_volume_names: str = ""
    group_id: str = ""
    target_volume_id: str = ""
    version: str = ""
    flow_interval: int = 0
    target_volume_name: str = ""
    priority: int = 0
    flow_offset: int = 0
    files: str = ""


@dataclass
class WorkflowJobListRequest:
    """Request to list workflow jobs."""
    workflow_id: str = ""  # Filter by workflow ID
    source_file_id: str = ""  # Filter by source file ID
    status: str = ""  # Filter by job status
    page: int = 0  # Page number (starts from 1, default 1)
    page_size: int = 0  # Page size (default 20)


@dataclass
class WorkflowJob:
    """Workflow job in the list."""
    job_id: str  # Job ID (API returns "id")
    workflow_id: str  # Workflow ID
    source_file_id: str = ""  # Source file ID (not in API response, populated from query param)
    status: int = 0  # Job status (API returns number: 1=running, 2=completed, 3=failed)
    start_time: str = ""  # Job start time
    end_time: str = ""  # Job end time (empty if not finished)


@dataclass
class WorkflowJobListResponse:
    """Response from listing workflow jobs."""
    jobs: List[WorkflowJob] = field(default_factory=list)  # List of workflow jobs (API returns "jobs" not "list")
    total: int = 0  # Total number of jobs


# Additional sections (Tables, Files, Folders, Roles, etc.) would follow
# using the same pattern. For brevity, only the core structures are defined here.
