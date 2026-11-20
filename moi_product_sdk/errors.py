"""SDK errors are diagnostic and explicit error-branch values.

They are not user-story SDK entry points, AI task-selection sources,
recovery-strategy sources, or input-construction sources. Choose the task from
the User Story Matrix first, follow that task's User Story Error Recovery
Coverage, then inspect errors only to report request_id/code/message or to
execute a documented caller-owned branch.
"""

from __future__ import annotations

from typing import Any


class Error(Exception):
    """Product SDK error returned by the product endpoint or client."""

    def __init__(self, code: str, message: str, request_id: str = "", status: int = 0, details: dict[str, Any] | None = None, data: Any = None) -> None:
        self.code = code
        self.message = message
        self.request_id = request_id
        self.status = status
        self.details = dict(details) if details is not None else {}
        self.data = data

    def __str__(self) -> str:
        if self.request_id:
            return f"[{self.code}] {self.message} (request_id: {self.request_id})"
        return f"[{self.code}] {self.message}"


# Err... sentinel values identify validation or product failures for diagnostics
# and documented branches only.
ErrEndpointRequired = Error("ErrEndpointRequired", "product endpoint is required")
ErrAuthRequired = Error("ErrAuthRequired", "api key, token, or session cookie is required")
ErrAPIKeyRequired = Error("ErrAPIKeyRequired", "api key is required")
ErrWorkspaceRequired = Error("ErrWorkspaceRequired", "workspace id is required")
ErrAgentRequired = Error("ErrAgentRequired", "agent_code or agent_id is required")
ErrJSONRPCInvalid = Error("ErrJSONRPCInvalid", "jsonrpc must be 2.0")
ErrMethodRequired = Error("ErrMethodRequired", "method is required")
ErrMethodInvalid = Error("ErrMethodInvalid", "method is invalid")
ErrIDRequired = Error("ErrIDRequired", "id is required")
ErrNameRequired = Error("ErrNameRequired", "name is required")
ErrDatabaseRenameUnsupported = Error("ErrDatabaseRenameUnsupported", "database rename is not supported by the product API")
ErrCodeRequired = Error("ErrCodeRequired", "code is required")
ErrEmailRequired = Error("ErrEmailRequired", "email is required")
ErrMobileRequired = Error("ErrMobileRequired", "mobile number is required")
ErrInvitationContactRequired = Error("ErrInvitationContactRequired", "exactly one invitation contact is required")
ErrInvitationContactConflict = Error("ErrInvitationContactConflict", "email, mobile number, and github login cannot be combined")
ErrInvitationGitHubLoginInvalid = Error("ErrInvitationGitHubLoginInvalid", "github login must be 1-39 letters, digits, or hyphens and cannot start or end with a hyphen")
ErrInvitationMobileNumberInvalid = Error("ErrInvitationMobileNumberInvalid", "invitation mobile number must be an 11-digit mainland China number")
ErrDefaultRoleRequired = Error("ErrDefaultRoleRequired", "default role id is required")
ErrDefaultRoleNotAssigned = Error("ErrDefaultRoleNotAssigned", "default role must be included in assigned roles")
ErrFileIDRequired = Error("ErrFileIDRequired", "file id is required")
ErrFileIDsRequired = Error("ErrFileIDsRequired", "file ids are required")
ErrVolumeIDRequired = Error("ErrVolumeIDRequired", "volume id is required")
ErrWorkbookIDRequired = Error("ErrWorkbookIDRequired", "workbook_id is required")
ErrVersionIDRequired = Error("ErrVersionIDRequired", "version_id is required")
ErrConnectorIDRequired = Error("ErrConnectorIDRequired", "connector id is required")
ErrConnectorFileIDRequired = Error("ErrConnectorFileIDRequired", "conn_file_id is required")
ErrDatabaseRequired = Error("ErrDatabaseRequired", "database is required")
ErrTableRequired = Error("ErrTableRequired", "table is required")
ErrTaskIDRequired = Error("ErrTaskIDRequired", "task_id is required")
ErrTokenRequired = Error("ErrTokenRequired", "token is required")
ErrOriginRequired = Error("ErrOriginRequired", "origin is required")
ErrTurnIDRequired = Error("ErrTurnIDRequired", "turn_id is required")
ErrAnswersRequired = Error("ErrAnswersRequired", "answers are required")
ErrVersionRequired = Error("ErrVersionRequired", "version is required")
ErrIAMBindingVersionInvalid = Error("ErrIAMBindingVersionInvalid", "IAM binding version is invalid")
ErrServiceNameRequired = Error("ErrServiceNameRequired", "service_name is required")
ErrPayloadRequired = Error("ErrPayloadRequired", "payload is required")
ErrWorkflowIDRequired = Error("ErrWorkflowIDRequired", "workflow_id is required")
ErrExecutionIDRequired = Error("ErrExecutionIDRequired", "execution_id is required")
ErrTaskNameRequired = Error("ErrTaskNameRequired", "task name is required")
ErrSourceConfigRequired = Error("ErrSourceConfigRequired", "source_config is required")
ErrProviderRequired = Error("ErrProviderRequired", "provider is required")
ErrQueryRequired = Error("ErrQueryRequired", "query is required")
ErrSubjectRequired = Error("ErrSubjectRequired", "subject_id is required")
ErrQueryIDRequired = Error("ErrQueryIDRequired", "query_id is required")
ErrDataSourcesRequired = Error("ErrDataSourcesRequired", "data_sources is required")
ErrStatementIDRequired = Error("ErrStatementIDRequired", "statement_id is required")
ErrDSLYAMLRequired = Error("ErrDSLYAMLRequired", "dsl_yaml is required")
ErrDescriptionRequired = Error("ErrDescriptionRequired", "description is required")
ErrIdentifierRequired = Error("ErrIdentifierRequired", "identifier is required")
ErrInputSchemaRequired = Error("ErrInputSchemaRequired", "input_schema is required")
ErrOutputSchemaRequired = Error("ErrOutputSchemaRequired", "output_schema is required")
ErrModeRequired = Error("ErrModeRequired", "mode is required")
ErrSourceNodeRequired = Error("ErrSourceNodeRequired", "source_node_execution_id is required")
ErrRerunContractHashRequired = Error("ErrRerunContractHashRequired", "expected_rerun_contract_hash is required")
ErrSpecIDRequired = Error("ErrSpecIDRequired", "spec_id is required")
ErrCPURequired = Error("ErrCPURequired", "cpu is required")
ErrMemoryRequired = Error("ErrMemoryRequired", "memory_gib is required")
ErrAddressRequired = Error("ErrAddressRequired", "address is required")
ErrModelsRequired = Error("ErrModelsRequired", "models are required")
ErrStatusRequired = Error("ErrStatusRequired", "status is required")
ErrTablesRequired = Error("ErrTablesRequired", "tables are required")
ErrTargetWorkspaceRequired = Error("ErrTargetWorkspaceRequired", "target_workspace_ids are required")
ErrSourceDatabaseIDRequired = Error("ErrSourceDatabaseIDRequired", "source_database_id is required")
ErrTableScopeRequired = Error("ErrTableScopeRequired", "table_scope is invalid")
ErrGroupIDRequired = Error("ErrGroupIDRequired", "group_id is required")
ErrExpressionIDRequired = Error("ErrExpressionIDRequired", "expression_id is required")
ErrLevelRequired = Error("ErrLevelRequired", "level is required")
ErrKindRequired = Error("ErrKindRequired", "kind is required")
ErrWorkerTypeConflict = Error("ErrWorkerTypeConflict", "worker_type and kind must match when both are provided")
ErrKeyRequired = Error("ErrKeyRequired", "key is required")
ErrSpecRequired = Error("ErrSpecRequired", "spec is required")
ErrEntriesRequired = Error("ErrEntriesRequired", "entries are required")
ErrKnowledgeBaseIDRequired = Error("ErrKnowledgeBaseIDRequired", "knowledge_base_id is required")
ErrConfigRequired = Error("ErrConfigRequired", "config is required")
ErrTypeRequired = Error("ErrTypeRequired", "type is required")
ErrSessionIDRequired = Error("ErrSessionIDRequired", "session_id is required")
ErrMessageIDRequired = Error("ErrMessageIDRequired", "message_id is required")
ErrActionRequired = Error("ErrActionRequired", "action is required")
ErrCategoryRequired = Error("ErrCategoryRequired", "category is required")
ErrSQLRequired = Error("ErrSQLRequired", "sql is required")
ErrURLRequired = Error("ErrURLRequired", "url is required")
ErrColumnsRequired = Error("ErrColumnsRequired", "columns are required")
ErrPathInvalid = Error("ErrPathInvalid", "path is invalid")

ErrCurrentRoleInvalid = Error("ErrCurrentRoleInvalid", "current role id must be a canonical positive int64")
ErrWorkspaceCurrentRoleConflict = Error("ErrWorkspaceCurrentRoleConflict", "workspace has conflicting current role ids")
