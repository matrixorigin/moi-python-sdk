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
    rule_list: Optional[List["TableRowColRule"]] = None


@dataclass
class TableRowColExpression:
    operator: str
    expression: str


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


# Additional sections (Tables, Files, Folders, Roles, Users, etc.) would follow
# using the same pattern. For brevity, only the core structures are defined here.
