from __future__ import annotations

import threading
from ._proto.product.dashboard_pb2 import (
    DataDashboardWebSocketMessage,
    DataDashboardWebSocketError,
)
from ._proto.product.agent_pb2 import (
    AgentArtifact,
    AgentArtifactAgentSource,
    AgentArtifactCreatorSource,
    AgentArtifactListResult,
    AgentArtifactRef,
    AgentArtifactFailure,
    AgentArtifactBatchRequest,
    AgentArtifactDeleteResult,
    AgentArtifactResolveItem,
    AgentArtifactResolveResult,
    AgentArtifactBackfillRequest,
    AgentArtifactBackfillResult,
)
from ._proto.product.iam_pb2 import (
    IAMSetDefaultRoleRequest,
    IAMSetDefaultRoleResult,
    IAMOwnershipImpactTypeCount,
    IAMOwnershipImpactItem,
    IAMOwnershipImpactResult,
    IAMRoleAuditEvent,
    IAMRoleAuditEventsResult,
    IAMUserAuditSummary,
    IAMUserAuditEvent,
    IAMUserAuditEventsResult,
)
from ._proto.product.semantic_pb2 import (KnowledgeFindFilesRequest, KnowledgeSearchRequest, KnowledgeSourcePage, KnowledgeReadDocumentRequest, KnowledgeSearchDocumentRequest, KnowledgeSearchImagesRequest, KnowledgeReadEvidenceRequest, KnowledgeDescribeTablesRequest, KnowledgeQueryRequest, KnowledgeCiteRequest, KnowledgeRuntimeResult)
from ._proto.product.runtime_gateway_pb2 import (RuntimeEdgeTokenRequest, RuntimeEdgeTokenCheck, RuntimeEdgeTokenRenewal, RuntimeModelResolveRequest, RuntimeModelResolution, RuntimeRPCRequest, RuntimeRPCResponse, RuntimeExecutorAuthorizationRequest, ComputeBindingEvent)
from ._proto.product.account_pb2 import ServiceAccountWorkspaceList, ServiceAccountRoleList
from ._proto.product.iam_pb2 import IAMRoleMembersResult
from ._proto.product.workflow_pb2 import WorkflowVersion, WorkflowVersionList, WorkflowVersionCreateRequest, WorkflowWorkerTaskCreateRequest, WorkflowWorkerTask
from ._proto.product.model_pb2 import (WorkspaceEndpointMutationResult,WorkspaceLLMBackend, WorkspaceLLMBackendCreateRequest, WorkspaceLLMBackendUpdateRequest, WorkspaceLLMBackendList, WorkspaceLLMEndpoint, WorkspaceLLMRouterConfig, WorkspaceLLMRouterConfigResult, WorkspaceLLMRouterUpdateRequest, WorkspaceChatCompletionProxy, WorkspaceChatCompletionRequest)
from ._proto.product.conversation_pb2 import (ConversationTag, ConversationSession, ConversationSessionList, ConversationUISessionRequest, ConversationWorkspaceSessionRequest, ConversationUISessionListRequest, ConversationMutation, ConversationUIMessageListRequest, ConversationUIMessage, ConversationWorkspaceMessage, ConversationWorkspaceMessageRequest, ConversationWorkspaceMessageList, ConversationLatestMessageID, ConversationTagRequest, ConversationTagList)
from ._proto.product.data_share_pb2 import (DataShareRecoveryApproval, DataShareDDLRecoveryRequest, DataShareDDLRecoveryResult, DataShareSagaTerminationRequest, DataShareSagaTerminationResult)
from ._proto.product.workflow_pb2 import (WorkflowAuthoringScope, WorkflowCandidateSubmitRequest, WorkflowScratchScope, WorkflowScratchLease, WorkflowScratchObservation, WorkflowScratchResetResult, WorkflowCandidateTestRequest, WorkflowCandidateTestWorkItem, WorkflowCandidateTestReport)
from ._proto.product.semantic_pb2 import SemanticModelImportEntry, SemanticModelImportRequest
from ._proto.product.catalog_common_pb2 import (CatalogGarbageCollectionRequest, CatalogGarbageCollectionResult, WorkspaceTableColumnsRequest, WorkspaceTableOverviewItem, WorkspaceTableOverviewResult, RefListResult)
from ._proto.product import resource_tag_pb2 as resource_tags
from google.protobuf.json_format import MessageToDict

from dataclasses import dataclass
import copy
import json
import math
import http.client
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import quote
from typing import Any, Callable, Optional

from google.protobuf import json_format
from google.protobuf.message import Message

DEFAULT_QUERY_HISTORY_LOOKBACK = timedelta(minutes=5)

from ._proto.product.account_pb2 import (
    BillingMeterRolloutResult,
    CurrentCreditResult,
    BrowserLoginCallbackRequest,
    BrowserSessionResult,
    BrowserLogoutRequest,
    BrowserLogoutResult,
    AuthPreferencesRequest,
    AuthPreferencesResult,
    NativeBootstrapResult,
    SystemComponentVersion,
    SystemVersionsResult,
    WebappConfigResult,
    WebappLogo,
    SystemRouteCoverageResult,

    DBConnectionResult,
)
from ._proto.product.agent_pb2 import (
    ConfirmSkillCandidateRequest,
    ConfirmSkillCandidateResult,
    SkillCandidateConfirmationResult,
    AgentCatalogCard,
    AgentCatalogCardListResult,
    AgentTeamRecord,
    AgentTeamMemberRef,
    AgentTeamMember,
    AgentTargetRef,
    IngressConnection,
    WeComQRBindingResult,
    AgentTeamSession,
    AgentTeamListResult,
    AgentTeamSessionListResult,
    AgentTeamMemberList,
    IngressConnectionList,
    IngressCapability,
    IngressCapabilityList,
    AgentTeamSubmitResult,
    AgentTeamMessageListResult,
    FeedbackTicketAdminUpdateRequest,
    FeedbackTicketCreateRequest,
    FeedbackTicketMessageInput,
    AgentA2AResult,
    AgentCardResult,
    ExecutorHealthResponse,
    SandboxTerminalToken,
)
from ._proto.product.plugin_pb2 import (
    PluginPublication, PluginPublicationList, PluginRelease, PluginDiscoveryPage,
    PluginCapabilityDescriptor, PluginInstallation,
    PluginInstallationList, PluginInstallationBinding, PluginConnection,
    PluginConnectionList, PluginAuthorizationStatus, PluginOAuthAction,
    PluginOAuthProgress, PluginMutationResult, PluginInstallRequest,
    PluginUpdateInstallationRequest, PluginCreateConnectionRequest,
    PluginUpdateConnectionRequest, PluginStoreSecretRequest,
)
from ._proto.product.audit_pb2 import (
    AuditLogListResult,
    AuditLogOverviewResult,
)
from ._proto.product.catalog_common_pb2 import (
    BoolDataResult,
    CatalogCreateTableResult,
    CatalogMultiTableInfoResult,
    CatalogTableDataColumn,
    CatalogTableDataResult,
    CatalogTableInfoResult,
    CatalogTableOverviewItem,
    CatalogTableOverviewResult,
    CatalogTableStatistic,
    CatalogInfoResult,
    CatalogListResult,
    CatalogTreeResult,
    CatalogAllowedActionsResult,
    CatalogNL2SQLRunResult,
    CatalogTableColumn,
    CreateFolderResult,
    DataTag,
    DataTagListResult,
    DatabaseChildrenResult,
    DataDashboardTableSearchResult,
    DatabaseTableLeavesResult,
    DatabaseInfoResult,
    DatabaseListResult,
    HealthResult,
    IDResult,
    PathResult,
    URLResult,
    VolumeInfoResult,
)
from ._proto.product.catalog_file_pb2 import (
    CatalogBatchGetDataAssetsResult,
    CatalogBatchResolveFileArtifactsResult,
    CatalogDataAsset,
    CatalogDataAssetResolveResult,
    CatalogDataDerivation,
    CatalogFileArtifactResolveItem,
    CatalogFileArtifactResult,
    CatalogFileFolder,
    CatalogFileListResult,
    WorkspaceFilePlacement,
    WorkspaceFileListResult,
    CatalogFileUploadLocation,
    CatalogParsedManifest,
    FileInfoResult,
    RuntimeArtifactUploadResult,
    RuntimeImageAnalysisResult,
    TriggerFileWorkflowResult,
    UploadFileResult,
)
from ._proto.product.compute_pb2 import (
    AdminComputeResource,
    AdminComputeResourceListResult,
    BoundWorkflowInfo,
    ComputeDeletePreflightResult,
    ComputeResource,
    ComputeResourcePyDeps,
    ComputeResourceOwnership,
    ComputeResourceSpec,
    ComputeResourceSpecManagementPermission,
    ComputeWorkerRuntime,
    ComputeWorkerRuntimeListResult,
    WorkerImage,
    WorkerImageSelection,
)
from ._proto.product.connector_pb2 import (
    ColumnSchema,
    Connector,
    ConnectorFile,
    ConnectorFileListResult,
    ConnectorListResult,
    ConnectorValidateResult,
    DBListDatabasesResult,
    DBListSchemasResult,
    DBListTablesResult,
    DBSourceSchemaResult,
    ExportTask,
    ExportTaskFile,
    ExportTaskFileStats,
    ExportTaskFilesResult,
    ExportTaskInfo,
    ExportTaskListResult,
    ExportTaskStats,
    ExportTaskStateResult,
    FileDownloadResult,
    ImportTask,
    ImportTaskCreateResult,
    ImportTaskFile,
    ImportTaskFileListResult,
    ImportTaskInfoResult,
    ImportTaskListResult,
    ImportTaskStats,
    ImportTaskRun,
    ImportTaskRunListResult,
    MOCheckTableNameResult,
    MOColumnMappingResult,
    MODatabaseListResult,
    MODatabaseTableListResult,
    LocalUploadResult,
    PreviewFileResult,
    PreviewRow,
    PreviewSheet,
    RESTReadResult,
    RESTSourceField,
    UploadResponse,
    UploadResult,
)
from ._proto.product.data_share_pb2 import (
    CheckNameResult,
    DataSharePublish,
    DataSharePublishListResult,
    DataSharePublishTarget,
    DataShareScope,
    DataShareSourceTable,
    DataShareSourceTableListResult,
    DataShareSubscription,
    DataShareSubscriptionListResult,
    DataShareWorkspaceName,
    DataShareWorkspaceNameListResult,
    PublishSummaryResult,
)
from ._proto.product.iam_pb2 import (
    IAMRoleInheritanceEdge,
    IAMRoleInheritanceResult,
    IAMRoleInheritanceMutationRequest,
    IAMRoleInheritanceMutationResult,
    IAMApplicationPolicyRequest,
    IAMApplicationPolicyValidationResult,
    IAMApplicationPolicyApplyResult,
    IAMApplicationPolicyStatement,
    IAMDataPrivilegeColumn,
    IAMDataPrivilegeFieldError,
    IAMDataPrivilegeItem,
    IAMDataPrivilegeMutation,
    IAMDataPrivilegeMutationRequest,
    IAMDataPrivilegeOperationResult,
    IAMDataPrivilegeRepairRequest,
    IAMDataPrivilegeResourceResult,
    IAMDataPrivilegeRowColumnDraft,
    IAMDataPrivilegeRowColumnMutation,
    IAMDataPrivilegeRowExpression,
    IAMDataPrivilegeRowRule,
    IAMDataPrivilegeValidationResult,
    IAMDataPrivilegeViewResult,
    IAMObjectGrantChange,
    IAMObjectGrantsMutationRequest,
    IAMObjectGrantsMutationResult,
    IAMObjectPermissionViewResult,
    IAMObjectOwnershipTransferRequest,
    IAMObjectOwnershipTransferResult,
    IAMPermissionSchemaResult,
    IAMUserRoleBindingItem,
    IAMUserRoleBindingsResult,
    IAMUserRoleBindingsRequest,
    IAMUserRoleBindingsMutationResult,
    IAMRoleCreateRequest,
    IAMRoleCreateResult,
    IAMRoleDeleteImpactResult,
    IAMRoleDeleteOwnershipList,
    IAMRoleDeleteRequest,
    IAMRoleLifecycleRequest,
    IAMRoleListResult,
    IAMRoleMutationResult,
    IAMRolePermissionViewResult,
    IAMRoleRecord,
    IAMRoleSummary,
    IAMRoleUpdateRequest,
)
from ._proto.product.memory_pb2 import (
    ConsumerProfileRenderResult,
    Memory,
    MemoryListResult,
)
from ._proto.product.model_pb2 import (
    ProviderBackend,
    ProviderBackendListResult,
    ProviderEndpoint,
    ProviderEndpointListResult,
    ProviderModel,
    ProviderModelListResult,
    ProviderMutationResult,
    ProviderProbeModelsResult,
    ProviderRouterConfig,
    ProviderSetupBackendResult,
)
from ._proto.product.semantic_pb2 import (
    KnowledgeReferencingAgent,
    KnowledgeReferencingAgentsPage,
    KnowledgeBaseDataDomain,
    KnowledgeBaseSourceJobRun,
    KnowledgeBaseSourceJobView,
    SemanticEntry,
    SemanticEntryListResult,
    SemanticExportResult,
    SemanticImportResult,
    SemanticModelAppendSourcesResult,
    SemanticModelEmptyResult,
    SemanticModelInfo,
    SemanticModelListResult,
    SemanticModelSourceCounts,
    SemanticModelTagListResult,
    SemanticModelTagStat,
    SemanticModelSegment,
    SemanticModelDocumentSegment,
    SemanticModelSegmentMutationResult,
    SemanticModelSegmentStatus,
    SemanticModelSource,
    SemanticModelSourceDocument,
    SemanticModelSourceFileInfo,
    SemanticModelSourceGovernanceResult,
    SemanticModelSourceJobListResult,
    SemanticModelSourceListResult,
    SemanticModelSourceSelectionPreviewResult,
    SemanticModelSourceExistenceResult,
    SemanticModelSourcePreview,
    SemanticModelWithSourcesResult,
    SemanticMutationResult,
    SemanticValidateResult,
)
from ._proto.product.workflow_pb2 import (
    CustomOperator,
    CustomOperatorCodeEnvelope,
    CustomOperatorListEnvelope,
    CustomOperatorSourceEnvelope,
    CustomOperatorTestEnvelope,
    CustomOperatorTestResult,
    DeveloperLogs,
    LineageArtifactNode,
    LineageBlockRevision,
    LineageBlockRevisions,
    LineageEffectiveRevisions,
    LineageOutputBlocks,
    LineageOverview,
    LineageRerun,
    WorkflowCandidateAcceptance,
    WorkflowCandidateBundle,
    WorkflowHistoryPage,
    WorkflowHistoryEntry,
    WorkflowCandidateConfirmation,
    WorkflowCandidateProposalRejection,
    WorkflowDeleteEnvelope,
    WorkflowDeploymentEnvelope,
    WorkflowDetail,
    WorkflowEnvelope,
    WorkflowExecutionNodeDetail,
    WorkflowExecutionNodeDetailEnvelope,
    WorkflowExecutionNodeRun,
    WorkflowExecutionDetail,
    WorkflowDispatchJob,
    WorkflowDispatchJobEnvelope,
    WorkflowExecutionEnvelope,
    WorkflowExecutionListEnvelope,
    WorkflowExecutionListItem,
    WorkflowExecutionResultDetail,
    WorkflowExecutionResultEnvelope,
    WorkflowFileExecution,
    WorkflowFileExecutionList,
    WorkflowImportContext,
    WorkflowImportContextEnvelope,
    WorkflowImportFile,
    WorkflowImportFileListEnvelope,
    WorkflowListEnvelope,
    WorkflowListItem,
    WorkflowRerunAffectedNode,
    WorkflowRerunBranch,
    WorkflowRerunBranchListEnvelope,
    WorkflowRerunEnvelope,
    WorkflowRerunNodeExecutionCandidate,
    WorkflowRerunPlan,
    WorkflowRerunPlanEnvelope,
    WorkflowRerunPlanValidation,
    WorkflowRunEnvelope,
    WorkflowRunResult,
    WorkflowBatchRetryEnvelope,
    WorkflowSummary,
    WorkflowTemplate,
    WorkflowTemplateDeleteEnvelope,
    WorkflowTemplateList,
    WorkitemCatalogDetail,
    WorkitemCatalogItem,
    WorkitemCatalogList,
    WorkitemAPIService,
    WorkitemAPIServiceEnvelope,
    WorkitemAPIServiceInvokeEnvelope,
    WorkitemAPIServiceInvokeInfo,
    WorkitemAPIServiceInvokeResult,
)
from ._proto.product.sql_pb2 import (
    SQLColumnMetadata,
    SQLDatabaseListResult,
    SQLDatabaseMetadata,
    SQLDatabaseTablesResult,
    SQLDatabaseTreeResult,
    SQLExplainData,
    SQLExplainStep,
    SQLGraphData,
    SQLGraphEdge,
    SQLGraphGlobal,
    SQLGraphLabel,
    SQLGraphNode,
    SQLQueryHistoryOverviewResult,
    SQLQueryHistoryResult,
    SQLQueryOperation,
    SQLQueryProfileResult,
    SQLQueryResult,
    SQLQueryResultColumn,
    SQLQueryResultItem,
    SQLQueryStartResult,
    SQLQueryWebSocketMessage,
    SQLStatementRecord,
    SQLTableColumnsResult,
    SQLTableDDLResult,
    SQLTableGroup,
    SQLTableInfoResult,
    SQLTableMetadata,
    SQLWorkbook,
    SQLWorkbookDetailResult,
    SQLWorkbookListResult,
    SQLWorkbookVersion,
    SQLWorkbookVersionCreateResult,
    SQLWorkbookVersionListResult,
    SQLEmptySet,
)
from ._proto.product.workspace_pb2 import (
    WorkspaceCreationJob,
    WorkspaceCreationsResult,
    WorkspaceIAMPrincipalContext as IAMCurrentPrincipalRolesResult,
    WorkspaceIAMCapabilities as IAMCurrentPrincipalCapabilitiesResult,
    CurrentWorkspacePrincipalResult,
    Workspace,
    WorkspaceClaimResult,
    WorkspaceCreateResult,
    WorkspaceListResult,
    WorkspaceMember,
    WorkspaceMemberInviteResult,
    WorkspaceInvitationAcceptResult,
    WorkspaceMemberListResult,
)
from .errors import (
    Error,
    ErrActionRequired,
    ErrAgentRequired,
    ErrAnswersRequired,
    ErrAuthRequired,
    ErrCategoryRequired,
    ErrCodeRequired,
    ErrConfigRequired,
    ErrColumnsRequired,
    ErrConnectorFileIDRequired,
    ErrConnectorIDRequired,
    ErrDataSourcesRequired,
    ErrDatabaseRequired,
    ErrDatabaseRenameUnsupported,
    ErrDescriptionRequired,
    ErrDSLYAMLRequired,
    ErrEmailRequired,
    ErrEndpointRequired,
    ErrEntriesRequired,
    ErrKnowledgeBaseIDRequired,
    ErrExpressionIDRequired,
    ErrFileIDRequired,
    ErrFileIDsRequired,
    ErrGroupIDRequired,
    ErrIDRequired,
    ErrIAMBindingVersionInvalid,
    ErrIdentifierRequired,
    ErrInputSchemaRequired,
    ErrInvitationContactConflict,
    ErrInvitationContactRequired,
    ErrInvitationGitHubLoginInvalid,
    ErrInvitationMobileNumberInvalid,
    ErrDefaultRoleNotAssigned,
    ErrDefaultRoleRequired,
    ErrJSONRPCInvalid,
    ErrKeyRequired,
    ErrKindRequired,
    ErrLevelRequired,
    ErrMobileRequired,
    ErrMethodInvalid,
    ErrMethodRequired,
    ErrModeRequired,
    ErrNameRequired,
    ErrOutputSchemaRequired,
    ErrSourceDatabaseIDRequired,
    ErrTableScopeRequired,
    ErrPathInvalid,
    ErrPayloadRequired,
    ErrWorkflowIDRequired,
    ErrExecutionIDRequired,
    ErrProviderRequired,
    ErrAddressRequired,
    ErrAPIKeyRequired,
    ErrCPURequired,
    ErrQueryIDRequired,
    ErrQueryRequired,
    ErrSQLRequired,
    ErrServiceNameRequired,
    ErrMemoryRequired,
    ErrMessageIDRequired,
    ErrModelsRequired,
    ErrSessionIDRequired,
    ErrSubjectRequired,
    ErrSourceConfigRequired,
    ErrSourceNodeRequired,
    ErrRerunContractHashRequired,
    ErrSpecRequired,
    ErrSpecIDRequired,
    ErrStatementIDRequired,
    ErrStatusRequired,
    ErrTableRequired,
    ErrTaskIDRequired,
    ErrTaskNameRequired,
    ErrTargetWorkspaceRequired,
    ErrTokenRequired,
    ErrOriginRequired,
    ErrTypeRequired,
    ErrTurnIDRequired,
    ErrURLRequired,
    ErrVersionRequired,
    ErrVolumeIDRequired,
    ErrVersionIDRequired,
    ErrWorkbookIDRequired,
    ErrWorkspaceRequired,
    ErrCurrentRoleInvalid,
    ErrWorkspaceCurrentRoleConflict,
    ErrWorkerTypeConflict,
)

# A2A method constants are explicit protocol-control values for low-level A2A calls.
# They are not user-story SDK entry points or AI task-selection sources; prefer AgentHandle typed A2A helpers for promoted workflows.
A2A_METHOD_SEND = "message/send"
A2A_METHOD_STREAM = "message/stream"
A2A_METHOD_TASKS_GET = "tasks/get"
A2A_METHOD_TASKS_CANCEL = "tasks/cancel"
A2A_METHOD_TASKS_RESUBSCRIBE = "tasks/resubscribe"
A2A_METHOD_INPUT_SUBMIT = "matrixflow/input.submit"

class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None

ClientOption = Callable[["ClientConfig"], None]

class ClientConfig:
    def __init__(self) -> None:
        self.api_key = ""
        self.token = ""
        self.session_cookie = ""
        self.allow_unauthenticated = False
        self.timeout = 60.0
        self.a2a_wait_timeout = 600.0
        self.custom_headers: dict[str, str] = {}
        self.workspace_current_roles: list[tuple[str, str]] = []

def validate_current_role_id(role_id: str) -> None:
    """Validate a canonical positive int64 Role Candidate; Core validates access."""
    if not isinstance(role_id, str) or not role_id.isascii() or not role_id.isdecimal():
        raise ErrCurrentRoleInvalid
    value = int(role_id) if len(role_id) <= 19 else 0
    if value <= 0 or value > 9223372036854775807 or str(value) != role_id:
        raise ErrCurrentRoleInvalid

def with_workspace_current_role_id(workspace_id: str, role_id: str) -> ClientOption:
    """Select an untrusted Role Candidate only for this workspace."""
    def apply(config: ClientConfig) -> None:
        config.workspace_current_roles.append((workspace_id, role_id))
    return apply

def with_api_key(api_key: str) -> ClientOption:
    def apply(config: ClientConfig) -> None:
        config.api_key = api_key

    return apply

def new_with_personal_access_token(
    product_endpoint: str,
    personal_access_token: str,
    *opts: ClientOption,
) -> "Client":
    """Create a product SDK client authenticated by a UC PAT.

    The token is opaque and is sent only in ``X-API-Key``. PAT clients cannot
    combine a bearer token or a browser session cookie with that credential.
    """
    if not personal_access_token:
        raise ErrAPIKeyRequired
    if personal_access_token.strip() != personal_access_token or any(char.isspace() for char in personal_access_token):
        raise Error("ErrMalformedPersonalAccessToken", "personal access token must be a single raw header value")
    client = Client(product_endpoint, *opts, with_api_key(personal_access_token))
    if client._config.token or client._config.session_cookie:
        raise Error("ErrPersonalAccessTokenAuthConflict", "personal access token clients cannot use bearer tokens or session cookies")
    return client

def with_token(token: str) -> ClientOption:
    def apply(config: ClientConfig) -> None:
        config.token = token

    return apply

def with_session_cookie(cookie: str) -> ClientOption:
    def apply(config: ClientConfig) -> None:
        config.session_cookie = cookie

    return apply

def with_unauthenticated() -> ClientOption:
    def apply(config: ClientConfig) -> None:
        config.allow_unauthenticated = True

    return apply

def with_timeout(timeout: float) -> ClientOption:
    def apply(config: ClientConfig) -> None:
        config.timeout = timeout

    return apply

def with_a2a_wait_timeout(seconds: float) -> ClientOption:
    """Bound the internal message/send follow to a terminal A2A task state.

    A2A 0.3 answers message/send at admission; the SDK follows a still-running
    task (tasks/resubscribe with eventCursor resume, degrading to tasks/get
    polling) until a terminal state. This budget caps the whole follow, not the
    single-request timeout set by with_timeout.
    """
    def apply(config: ClientConfig) -> None:
        config.a2a_wait_timeout = seconds

    return apply

def with_custom_header(key: str, value: str) -> ClientOption:
    def apply(config: ClientConfig) -> None:
        config.custom_headers[key] = value

    return apply

def with_runtime_authorization(value: str) -> ClientOption:
    """Add the short-lived sandbox child proof for native runtime operations."""
    return with_custom_header("X-MOI-Runtime-Authorization", value)

def _ingress_callback_path(provider: str, workspace_id: str, connection_id: str) -> str:
    return f"/ingress-callbacks/{_path_id(provider)}/{_path_id(workspace_id)}/{_path_id(connection_id)}"


def _websocket_headers(client, workspace_id: str) -> list[str]:
    headers: list[str] = []
    if client._config.api_key:
        headers.append("X-API-Key: " + client._config.api_key)
    if client._config.token:
        headers.append("Authorization: Bearer " + client._config.token)
    if client._config.session_cookie:
        headers.append("Cookie: " + client._config.session_cookie)
    for key, value in client._config.custom_headers.items():
        if key.lower() not in {"x-workspace-id", "x-moi-role-id"}:
            headers.append(f"{key}: {value}")
    headers.extend(f"{key}: {value}" for key, value in client._workspace_scope_headers(workspace_id).items())
    return headers

def _websocket_subprotocols(client) -> list[str]:
    if client._config.api_key:
        return ["moi-api-key","moi-api-key."+client._config.api_key]
    if client._config.token:
        return ["moi-bearer","moi-bearer."+client._config.token]
    return []


def _channel_callback_path(provider: str, workspace_id: str, credential_ref: str) -> str:
    return f"/callbacks/{_path_id(provider)}/{_path_id(workspace_id)}/{_path_id(credential_ref)}"


class Client:
    def __init__(self, product_endpoint: str, *opts: ClientOption) -> None:
        if not product_endpoint:
            raise ErrEndpointRequired
        config = ClientConfig()
        for opt in opts:
            opt(config)
        if not config.allow_unauthenticated and not config.api_key and not config.token and not config.session_cookie:
            raise ErrAuthRequired
        roles: dict[str, str] = {}
        for workspace_id, role_id in config.workspace_current_roles:
            if not workspace_id:
                raise ErrWorkspaceRequired
            validate_current_role_id(role_id)
            if workspace_id in roles and roles[workspace_id] != role_id:
                raise ErrWorkspaceCurrentRoleConflict
            roles[workspace_id] = role_id
        self._workspace_current_roles = roles
        self._base = product_endpoint.rstrip("/")
        self._config = config

    def _workspace_scope_headers(self, workspace_id: str) -> dict[str, str]:
        if not workspace_id:
            return {}
        headers = {"X-Workspace-ID": workspace_id}
        if workspace_id in self._workspace_current_roles:
            headers["X-MOI-Role-ID"] = self._workspace_current_roles[workspace_id]
        return headers

    def _apply_workspace_scope(self, request: urllib.request.Request, workspace_id: str) -> None:
        for headers in (request.headers, request.unredirected_hdrs):
            for key in list(headers):
                if key.lower() in {"x-workspace-id", "x-moi-role-id"}:
                    del headers[key]
        for key, value in self._workspace_scope_headers(workspace_id).items():
            request.add_header(key, value)

    def _clear_public_product_headers(self, request: urllib.request.Request) -> None:
        blocked = {"x-api-key", "authorization", "cookie", "x-moi-runtime-authorization", "x-workspace-id", "x-moi-role-id"}
        for headers in (request.headers, request.unredirected_hdrs):
            for key in list(headers):
                if key.lower() in blocked:
                    del headers[key]

    def _product_url(self, path: str) -> str:
        return self._base + path

    def _native_url(self, path: str) -> str:
        endpoint = urllib.parse.urlsplit(self._base)
        prefix = endpoint.path.removesuffix("/newmoi")
        return urllib.parse.urlunsplit((endpoint.scheme, endpoint.netloc, prefix + path, "", ""))

    def complete_plugin_oauth_callback(self, registration_id: str, request: BrowserLoginCallbackRequest, issuer: str = "") -> StreamResponse:
        """Complete the fixed MOI browser callback without SDK credentials or redirects.

        The browser begin request and callback share the cookie jar of the
        process-installed urllib opener; cookies are not isolated per Client.
        Configured headers and session_cookie are omitted from the callback.
        Configured endpoints containing userinfo or fragments are rejected.
        """
        return self._complete_plugin_oauth_callback(registration_id, request, issuer, False)

    def complete_plugin_oauth_product_callback(self, registration_id: str, request: BrowserLoginCallbackRequest, issuer: str = "") -> StreamResponse:
        """Complete the browser callback at the configured product prefix.

        Normally this preserves /newmoi. It uses the same cookie jar, credential
        exclusion, validation and redirect policy as the legacy-root callback.
        """
        return self._complete_plugin_oauth_callback(registration_id, request, issuer, True)

    def _complete_plugin_oauth_callback(self, registration_id: str, request: BrowserLoginCallbackRequest, issuer: str, product_route: bool) -> StreamResponse:
        if not isinstance(request, BrowserLoginCallbackRequest):
            raise TypeError("request must be BrowserLoginCallbackRequest")
        registration = _path_id(registration_id)
        if registration_id in {".", ".."}:
            raise ErrPathInvalid
        configured_endpoint = urllib.parse.urlsplit(self._base)
        if configured_endpoint.username is not None or configured_endpoint.fragment:
            raise ErrPathInvalid
        query = {"state": request.state, "code": request.code, "error": request.error}
        if issuer:
            query["iss"] = issuer
        path = "/api/v1/plugins/oauth/callback/" + registration
        endpoint = (urllib.parse.urlunsplit((configured_endpoint.scheme, configured_endpoint.netloc, configured_endpoint.path + path, "", ""))
                    if product_route else self._native_url(path)) + "?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(endpoint, method="GET", headers={"Accept": "*/*"})
        # Keep browser cookies and TLS settings, excluding auth handlers and
        # default headers. Copy handlers so the installed opener is unchanged.
        installed = urllib.request._opener
        handlers = [copy.copy(handler) for handler in installed.handlers
                    if isinstance(handler, (urllib.request.HTTPCookieProcessor, urllib.request.HTTPSHandler))] if installed else []
        opener = urllib.request.build_opener(*handlers, _NoBrowserRedirect())
        opener.addheaders = []
        return StreamResponse(_open_product_response(req, self._config.timeout, no_redirect=True, opener=opener))

    def conversations(self, workspace_id: str) -> ConversationService:
        return ConversationService(self,workspace_id)

    def runtime_gateway(self) -> "RuntimeGatewayService":
        return RuntimeGatewayService(self)

    def system(self) -> "SystemService":
        """Route-aligned escape hatch; prefer typed system health/version helpers for user-facing workflows."""
        return SystemService(self)

    def healthcheck_result(self) -> ProductResult:
        return self._product_result("GET", "/healthcheck", native=True)

    def webapp_config(self) -> dict[str, Any]:
        return self._request("GET", "/webapp/config")

    def webapp_config_result(self) -> ProductResult:
        return self._product_result("GET", "/webapp/config")

    def webapp_config_method_result(self, method: str) -> ProductResult:
        return self._product_result(method, "/webapp/config")

    def webapp_config_preflight_result(
        self,
        request_method: str,
        *,
        origin: Optional[str] = None,
    ) -> ProductResult:
        headers = {
            "Access-Control-Request-Method": request_method,
            "Access-Control-Request-Headers": "Content-Type,Authorization,X-Workspace-ID",
        }
        if origin is not None:
            headers["Origin"] = origin
        return self._product_result(
            "OPTIONS",
            "/webapp/config",
            headers=headers,
        )

    def workspaces(self) -> "WorkspaceService":
        """Route-aligned escape hatch; prefer typed ensure_workspace results and WorkspaceHandle for user-facing workflows."""
        return WorkspaceService(self)

    def workspace(self, workspace_id: str) -> "WorkspaceHandle":
        return WorkspaceHandle(self, workspace_id)

    def ensure_workspace(self, name: str) -> "WorkspaceHandle":
        if not name:
            raise ErrNameRequired
        workspaces = self.workspaces().list(with_workspace_name_filter(name))
        matched: Optional[WorkspaceHandle] = None
        for workspace in workspaces.workspaces:
            if workspace.name == name:
                if matched is not None:
                    raise _duplicate_name_error("workspace", name)
                matched = WorkspaceHandle(self, workspace.id, workspace.name)
        if matched is not None:
            return matched
        created = self.workspaces().create(name)
        return WorkspaceHandle(self, created.id, name)

    def ai_studio(self) -> "AIStudioService":
        """Account-level AI Studio service slot administration."""
        return AIStudioService(self)

    def account(self) -> "AccountService":
        """Route-aligned escape hatch; prefer typed WorkspaceHandle db_connection helpers for user-facing workflows."""
        return AccountService(self)

    def resource_tags(self, workspace_id: str) -> "ResourceTagService":
        """Manage workspace tags, predefined values and resource assignments."""
        return ResourceTagService(self, workspace_id)

    def workspace_members(self, workspace_id: str) -> "WorkspaceMemberService":
        """Route-aligned escape hatch; prefer typed WorkspaceHandle member methods for user-facing workflows."""
        return WorkspaceMemberService(self, workspace_id)

    def iam(self, workspace_id: str) -> "IAMService":
        """Route-aligned escape hatch; prefer typed WorkspaceHandle IAM methods for user-facing workflows."""
        return IAMService(self, workspace_id)

    def catalog(self, workspace_id: str) -> "CatalogService":
        """Route-aligned escape hatch; prefer typed catalog, database, table, volume, folder, and file handles for user-facing workflows."""
        return CatalogService(self, workspace_id)

    def knowledge(self, workspace_id: str) -> "KnowledgeService":
        """Route-aligned escape hatch; prefer typed semantic model and entry handles for user-facing workflows."""
        return KnowledgeService(self, workspace_id)

    def workflows(self, workspace_id: str) -> "WorkflowService":
        """Route-aligned escape hatch; prefer typed workflow, run, operator, template, and WorkItem API handles for user-facing workflows."""
        return WorkflowService(self, workspace_id)

    def agents(self, workspace_id: str) -> "AgentService":
        """Route-aligned escape hatch; prefer typed AgentHandle A2A helpers for user-facing workflows."""
        return AgentService(self, workspace_id)

    def webapp(self) -> "WebappService":
        """Route-aligned escape hatch for anonymous Webapp visitors; prefer typed AgentHandle helpers for publisher user-facing workflows."""
        return WebappService(self)

    def runners(self, workspace_id: str):
        """Manage workspace execution runners."""
        from .runner import RunnerService
        return RunnerService(self, workspace_id)

    def sandboxes(self, workspace_id: str):
        """Manage workspace execution sandboxes."""
        from .sandbox import SandboxService
        return SandboxService(self, workspace_id)

    def models(self, workspace_id: str) -> "ModelService":
        """Route-aligned escape hatch; prefer typed provider backend and router handles for user-facing workflows."""
        return ModelService(self, workspace_id)

    def verify_wecom_callback(
        self,
        workspace_id: str,
        credential_ref: str,
        query: Optional[dict[str, str]] = None,
    ) -> bytes:
        return self.verify_channel_callback("wecom", workspace_id, credential_ref, query)

    def verify_channel_callback(self, provider: str, workspace_id: str, credential_ref: str, query: Optional[dict[str, str]] = None) -> bytes:
        path = _channel_callback_path(provider, workspace_id, credential_ref)
        return self._public_raw_bytes("GET", path, query=query)

    def post_channel_callback(self, provider: str, workspace_id: str, credential_ref: str, body: bytes, query: Optional[dict[str, str]] = None) -> bytes:
        path = _channel_callback_path(provider, workspace_id, credential_ref)
        return self._public_raw_bytes("POST", path, body=body, content_type="application/json; charset=utf-8", query=query)

    def post_wecom_callback(
        self,
        workspace_id: str,
        credential_ref: str,
        body: bytes,
        query: Optional[dict[str, str]] = None,
    ) -> bytes:
        path = f"/callbacks/wecom/{_path_id(workspace_id)}/{_path_id(credential_ref)}"
        return self._public_raw_bytes(
            "POST",
            path,
            body=body,
            content_type="application/xml; charset=utf-8",
            query=query,
        )

    def verify_ingress_callback(
        self,
        provider: str,
        workspace_id: str,
        connection_id: str,
        query: Optional[dict[str, str]] = None,
    ) -> bytes:
        """Send a provider challenge without product authentication."""
        path = _ingress_callback_path(provider, workspace_id, connection_id)
        return self._public_raw_bytes("GET", path, query=query)

    def post_ingress_callback(
        self,
        provider: str,
        workspace_id: str,
        connection_id: str,
        body: bytes,
        query: Optional[dict[str, str]] = None,
    ) -> bytes:
        """Send the provider payload; signature headers use custom_headers."""
        path = _ingress_callback_path(provider, workspace_id, connection_id)
        return self._public_raw_bytes(
            "POST", path, body=body, content_type="application/octet-stream", query=query
        )

    def memory(self, workspace_id: str) -> "MemoryService":
        """Legacy route-aligned escape hatch; prefer typed consumer memory handles on legacy servers.

        Deprecated for current MOI: it does not serve the consumer-memory/profile API.
        """
        return MemoryService(self, workspace_id)

    def connectors(self, workspace_id: str) -> "ConnectorService":
        """Route-aligned escape hatch; prefer typed connector, import task, export task, and connector file handles for user-facing workflows."""
        return ConnectorService(self, workspace_id)

    def sql(self, workspace_id: str) -> "SQLService":
        """Route-aligned escape hatch; prefer typed SQL metadata, workbook, query, and statement handles for user-facing workflows."""
        return SQLService(self, workspace_id)

    def compute(self, workspace_id: str) -> "ComputeService":
        """Route-aligned escape hatch; prefer typed compute resource handles for user-facing workflows."""
        return ComputeService(self, workspace_id)

    def dashboard(self, workspace_id: str) -> "DashboardService":
        """Route-aligned escape hatch; prefer typed workflow handles for user-facing workflows."""
        return DashboardService(self, workspace_id)

    def data_share(self, workspace_id: str) -> "DataShareService":
        """Route-aligned escape hatch; prefer typed publish and subscription handles for user-facing workflows."""
        return DataShareService(self, workspace_id)

    def _request(
        self,
        method: str,
        path: str,
        workspace_id: str = "",
        body: Optional[dict[str, Any]] = None,
        require_envelope: bool = False,
        data_nullable: Optional[bool] = None,
    ) -> Any:
        """Send exactly one product HTTP request. The SDK never retries."""
        return self._request_once(method, path, workspace_id, body, require_envelope, data_nullable)

    def _request_once(
        self,
        method: str,
        path: str,
        workspace_id: str,
        body: Optional[dict[str, Any]],
        require_envelope: bool,
        data_nullable: Optional[bool] = None,
    ) -> Any:
        return self._request_endpoint(method, self._product_url(path), workspace_id, body, require_envelope, data_nullable)

    def _request_endpoint(self, method: str, endpoint_url: str, workspace_id: str = "", body: Optional[dict[str, Any]] = None, require_envelope: bool = False, data_nullable: Optional[bool] = None) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(endpoint_url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self._config.api_key:
            req.add_header("X-API-Key", self._config.api_key)
        if self._config.token:
            req.add_header("Authorization", "Bearer " + self._config.token)
        if self._config.session_cookie:
            req.add_header("Cookie", self._config.session_cookie)
        if workspace_id:
            req.add_header("X-Workspace-ID", workspace_id)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        self._apply_workspace_scope(req, workspace_id)
        with _open_product_response(req, self._config.timeout) as resp:
            return _parse_response(_read_product_response(resp), _request_id(resp.headers), require_envelope=require_envelope, data_nullable=data_nullable, status=resp.status)

    def _stream(
        self,
        method: str,
        path: str,
        workspace_id: str = "",
        body: Optional[dict[str, Any]] = None,
        accept: str = "text/event-stream",
        timeout: Optional[float] = None,
    ) -> Any:
        return self._stream_endpoint(method, self._product_url(path), workspace_id, body, accept, timeout=timeout)

    def _stream_endpoint(self, method: str, endpoint_url: str, workspace_id: str = "", body: Optional[dict[str, Any]] = None, accept: str = "text/event-stream", no_redirect: bool = False, timeout: Optional[float] = None) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(endpoint_url, data=data, method=method)
        req.add_header("Accept", accept)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self._config.api_key:
            req.add_header("X-API-Key", self._config.api_key)
        if self._config.token:
            req.add_header("Authorization", "Bearer " + self._config.token)
        if self._config.session_cookie:
            req.add_header("Cookie", self._config.session_cookie)
        if workspace_id:
            req.add_header("X-Workspace-ID", workspace_id)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        self._apply_workspace_scope(req, workspace_id)
        return _open_product_response(req, self._config.timeout if timeout is None else timeout, no_redirect=no_redirect)

    def _raw_request(
        self,
        method: str,
        path: str,
        workspace_id: str,
        data: bytes,
        content_type: str,
        accept: str = "application/json",
        require_envelope: bool = False,
    ) -> Any:
        req = urllib.request.Request(self._product_url(path), data=data, method=method)
        req.add_header("Accept", accept)
        req.add_header("Content-Type", content_type)
        if self._config.api_key:
            req.add_header("X-API-Key", self._config.api_key)
        if self._config.token:
            req.add_header("Authorization", "Bearer " + self._config.token)
        if self._config.session_cookie:
            req.add_header("Cookie", self._config.session_cookie)
        if workspace_id:
            req.add_header("X-Workspace-ID", workspace_id)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        self._apply_workspace_scope(req, workspace_id)
        with _open_product_response(req, self._config.timeout) as resp:
            return _parse_response(_read_product_response(resp), _request_id(resp.headers), require_envelope=require_envelope, status=resp.status)

    def _public_raw_bytes(
        self,
        method: str,
        path: str,
        *,
        body: Optional[bytes] = None,
        content_type: str = "",
        query: Optional[dict[str, str]] = None,
        accept: str = "text/plain",
    ) -> bytes:
        _, _, raw = self._public_raw_response(
            method, path, body=body, content_type=content_type, query=query, accept=accept,
        )
        return raw

    def _public_raw_response(
        self,
        method: str,
        path: str,
        *,
        body: Optional[bytes] = None,
        content_type: str = "",
        query: Optional[dict[str, str]] = None,
        accept: str = "text/plain",
    ) -> tuple[int, str, bytes]:
        if query:
            path += "?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(self._product_url(path), data=body, method=method)
        req.add_header("Accept", accept)
        if content_type:
            req.add_header("Content-Type", content_type)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        self._apply_workspace_scope(req, "")
        self._clear_public_product_headers(req)
        try:
            with urllib.request.build_opener().open(req, timeout=self._config.timeout) as resp:
                return resp.status, _request_id(resp.headers), resp.read()
        except urllib.error.HTTPError as err:
            raise _parse_error(err.code, err.read(), _request_id(err.headers)) from err

    def _public_stream(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict[str, Any]] = None,
        accept: str = "text/event-stream",
    ) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self._product_url(path), data=data, method=method)
        req.add_header("Accept", accept)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        self._apply_workspace_scope(req, "")
        self._clear_public_product_headers(req)
        return _open_product_response(req, self._config.timeout, opener=urllib.request.build_opener())

    def _raw_product_result(
        self,
        method: str,
        path: str,
        workspace_id: str,
        data: bytes,
        content_type: str,
        accept: str = "application/json",
    ) -> ProductResult:
        req = urllib.request.Request(self._product_url(path), data=data, method=method)
        req.add_header("Accept", accept)
        req.add_header("Content-Type", content_type)
        if self._config.api_key:
            req.add_header("X-API-Key", self._config.api_key)
        if self._config.token:
            req.add_header("Authorization", "Bearer " + self._config.token)
        if self._config.session_cookie:
            req.add_header("Cookie", self._config.session_cookie)
        if workspace_id:
            req.add_header("X-Workspace-ID", workspace_id)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        self._apply_workspace_scope(req, workspace_id)
        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                return ProductResult(resp.status, dict(resp.headers.items()), _decode_result_body(resp.read()))
        except urllib.error.HTTPError as err:
            return ProductResult(err.code, dict(err.headers.items()), _decode_result_body(err.read()))

    def _http_result(
        self,
        method: str,
        path: str,
        *,
        workspace_id: str = "",
        body: Optional[dict[str, Any]] = None,
        query: Optional[dict[str, Any]] = None,
        allow_redirects: bool = False,
        headers: Optional[dict[str, str]] = None,
    ) -> HTTPResult:
        full_path = path
        if query:
            full_path += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self._product_url(full_path), data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self._config.api_key:
            req.add_header("X-API-Key", self._config.api_key)
        if self._config.token:
            req.add_header("Authorization", "Bearer " + self._config.token)
        if self._config.session_cookie:
            req.add_header("Cookie", self._config.session_cookie)
        if workspace_id:
            req.add_header("X-Workspace-ID", workspace_id)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        for key, value in (headers or {}).items():
            req.add_header(key, value)

        self._apply_workspace_scope(req, workspace_id)
        opener = urllib.request.build_opener() if allow_redirects else urllib.request.build_opener(_NoRedirectHandler)
        try:
            with opener.open(req, timeout=self._config.timeout) as resp:
                return HTTPResult(
                    resp.status,
                    dict(resp.headers.items()),
                    _parse_result_response(resp.read(), _request_id(resp.headers)),
                )
        except urllib.error.HTTPError as err:
            raw = err.read()
            if 300 <= err.code < 400:
                return HTTPResult(err.code, dict(err.headers.items()), _decode_result_body(raw))
            raise _parse_error(err.code, raw, _request_id(err.headers)) from err

    def _product_result(
        self,
        method: str,
        path: str,
        *,
        workspace_id: str = "",
        body: Optional[dict[str, Any]] = None,
        query: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        native: bool = False,
    ) -> ProductResult:
        full_path = path
        if query:
            full_path += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self._native_url(full_path) if native else self._product_url(full_path), data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self._config.api_key:
            req.add_header("X-API-Key", self._config.api_key)
        if self._config.token:
            req.add_header("Authorization", "Bearer " + self._config.token)
        if self._config.session_cookie:
            req.add_header("Cookie", self._config.session_cookie)
        if workspace_id:
            req.add_header("X-Workspace-ID", workspace_id)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)
        for key, value in (headers or {}).items():
            req.add_header(key, value)
        self._apply_workspace_scope(req, workspace_id)
        request_headers = dict(req.header_items())

        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                return ProductResult(resp.status, dict(resp.headers.items()), _decode_result_body(resp.read()), request_headers)
        except urllib.error.HTTPError as err:
            return ProductResult(err.code, dict(err.headers.items()), _decode_result_body(err.read()), request_headers)

    def _bytes_result(
        self,
        method: str,
        path: str,
        *,
        workspace_id: str = "",
        query: Optional[dict[str, Any]] = None,
    ) -> BytesResult:
        full_path = path
        if query:
            full_path += "?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(self._product_url(full_path), method=method)
        req.add_header("Accept", "*/*")
        if self._config.api_key:
            req.add_header("X-API-Key", self._config.api_key)
        if self._config.token:
            req.add_header("Authorization", "Bearer " + self._config.token)
        if self._config.session_cookie:
            req.add_header("Cookie", self._config.session_cookie)
        if workspace_id:
            req.add_header("X-Workspace-ID", workspace_id)
        for key, value in self._config.custom_headers.items():
            req.add_header(key, value)

        self._apply_workspace_scope(req, workspace_id)
        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                return BytesResult(resp.status, dict(resp.headers.items()), resp.read())
        except urllib.error.HTTPError as err:
            return BytesResult(err.code, dict(err.headers.items()), err.read())

class WorkspaceService:
    """Route-aligned escape hatch; prefer typed Client workspace helpers and WorkspaceHandle for user-facing workflows."""

    def creations(self) -> WorkspaceCreationsResult:
        return _product_message(self._client._request("GET", "/workspaces/creations"), WorkspaceCreationsResult(), "workspace creations data")

    def start_creation(self, name: str) -> WorkspaceCreationJob:
        # body 用关键字传入；第三个位置参数是 workspace_id，dict 会触发 TypeError。
        return _product_message(self._client._request("POST", "/workspaces/creations", body={"name": name}), WorkspaceCreationJob(), "workspace creation data")

    def update(self, workspace_id: str, name: str) -> None:
        # body 用关键字传入；第三个位置参数是 workspace_id，dict 会触发 TypeError。
        self._client._request("PATCH", f"/workspaces/{_path_id(workspace_id)}", body={"name": name})

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self, *opts: Callable[["ListOptions"], None]) -> WorkspaceListResult:
        return _workspace_list_result(self._client._request("GET", _with_list_query("/workspaces", opts)))

    def list_result(self, *opts: Callable[["ListOptions"], None]) -> ProductResult:
        return self._client._product_result("GET", _with_list_query("/workspaces", opts))

    def create(self, name: str, *opts: Callable[["CreateWorkspaceOptions"], None]) -> WorkspaceCreateResult:
        if not name:
            raise ErrNameRequired
        options = CreateWorkspaceOptions()
        for opt in opts:
            opt(options)
        return _workspace_create_result(self._client._request("POST", "/workspaces", body={"name": name}))

    def create_raw(self, body: dict[str, Any]) -> WorkspaceCreateResult:
        return _workspace_create_result(self._client._request("POST", "/workspaces", body=body))

    def create_raw_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workspaces", body=body)

    def claim(self, workspace_id: str) -> WorkspaceClaimResult:
        if not workspace_id:
            raise ErrWorkspaceRequired
        return _workspace_claim_result(
            self._client._request("POST", "/workspaces/claim", body={"workspace_id": workspace_id})
        )

    def delete(self, workspace_id: str, *opts: Callable[["QueryOptions"], None]) -> None:
        """Delete a workspace; with_query_param('wait', 'true') waits for account cleanup."""
        self._client._request("DELETE", _with_query(f"/workspaces/{_path_id(workspace_id)}", opts))

    def delete_result(self, workspace_id: str, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result("DELETE", _with_query(f"/workspaces/{_path_id(workspace_id)}", opts))

class WorkspaceHandle:
    def __init__(self, client: Client, workspace_id: str, name: str = "") -> None:
        if not workspace_id:
            raise ErrWorkspaceRequired
        self._client = client
        self.id = workspace_id
        self.name = name

    def members(self) -> "WorkspaceMemberService":
        return self._client.workspace_members(self.id)

    def iam(self) -> "IAMService":
        return self._client.iam(self.id)

    def member(self, user_id: str) -> "WorkspaceMemberHandle":
        if not user_id:
            raise ErrIDRequired
        return WorkspaceMemberHandle(self, user_id)

    def invite_member(
        self,
        name: str,
        default_role_id: int,
        *opts: Callable[["CreateUserOptions"], None],
    ) -> WorkspaceMemberInviteResult:
        """Invite by email, mobile, or GitHub login. Email/mobile stay pending until accept.
        A GitHub directory hit seats immediately and returns the canonical user id;
        a miss returns USER_NOT_FOUND without creating an invitation.
        """
        return self.members().invite(name, default_role_id, *opts)

    def delete(self, *opts: Callable[["QueryOptions"], None]) -> None:
        self._client.workspaces().delete(self.id, *opts)

    def db_connection(self) -> DBConnectionResult:
        return self._client.account().db_connection(self.id)

    def recent_failed_audit_logs(self, limit: int) -> AuditLogListResult:
        if limit <= 0:
            raise Error("ErrLimitRequired", "limit is required")
        return self.members().audit_logs(with_audit_result("failed"), with_page(1), with_page_size(limit))

    def prepare_catalog(self, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> "CatalogHandle":
        if not name:
            raise ErrNameRequired
        matched: Optional[CatalogHandle] = None
        for catalog in self.catalog().list().list:
            if catalog.name != name:
                continue
            if matched is not None:
                raise _duplicate_name_error("catalog", name)
            matched = CatalogHandle(self, catalog.id, catalog.name)
        if matched is not None:
            return matched
        created = self.catalog().create(name, *opts)
        return CatalogHandle(self, created.id, name)

    def prepare_data_volume(self, catalog_name: str, database_name: str, volume_name: str) -> "VolumeHandle":
        catalog = self.prepare_catalog(catalog_name)
        database = catalog.prepare_database(database_name)
        return database.prepare_volume(volume_name)

    def upload_bytes_to_data_volume(
        self, catalog_name: str, database_name: str, volume_name: str, filename: str, data: bytes
    ) -> "FileHandle":
        volume = self.prepare_data_volume(catalog_name, database_name, volume_name)
        return volume.upload_bytes_handle(filename, data)

    def upload_file_to_data_volume(self, catalog_name: str, database_name: str, volume_name: str, file_path: str) -> "FileHandle":
        """local file input convenience method, not AI file-discovery, local-filesystem probing, filename inference, or default upload entry point; prefer upload_bytes_to_data_volume when bytes are already caller-owned."""
        volume = self.prepare_data_volume(catalog_name, database_name, volume_name)
        return volume.upload_file_handle(file_path)

    def upload_bytes_preview_to_data_volume(
        self, catalog_name: str, database_name: str, volume_name: str, filename: str, data: bytes
    ) -> "UploadedFilePreview":
        file = self.upload_bytes_to_data_volume(catalog_name, database_name, volume_name, filename, data)
        return UploadedFilePreview(file, file.preview())

    def upload_file_preview_to_data_volume(
        self, catalog_name: str, database_name: str, volume_name: str, file_path: str
    ) -> "UploadedFilePreview":
        """local file input convenience method, not AI file-discovery, local-filesystem probing, filename inference, or default upload entry point; prefer upload_bytes_preview_to_data_volume when bytes are already caller-owned."""
        file = self.upload_file_to_data_volume(catalog_name, database_name, volume_name, file_path)
        return UploadedFilePreview(file, file.preview())

    def data_volume_full_path(self, catalog_name: str, database_name: str, volume_name: str) -> PathResult:
        volume = self.prepare_data_volume(catalog_name, database_name, volume_name)
        return volume.full_path()

    def catalogs(self, *opts: Callable[["CatalogListOptions"], None]) -> tuple[list["CatalogHandle"], CatalogListResult]:
        result = self.catalog().list(*opts)
        return [CatalogHandle(self, catalog.id, catalog.name) for catalog in result.list], result

    def workflow(self, workflow_id: str) -> "WorkflowHandle":
        if not workflow_id:
            raise ErrIDRequired
        return WorkflowHandle(self, workflow_id)

    def deploy_workflow(
        self,
        name: str,
        dsl_yaml: str,
        workflow_id: str = "",
        *opts: Callable[["WorkflowDeployOptions"], None],
    ) -> tuple["WorkflowHandle", WorkflowDeploymentEnvelope]:
        """Create with an empty ID, or deploy a new version of an existing workflow."""
        if workflow_id:
            opts = (with_workflow_id(workflow_id), *opts)
        result = self.workflows().deploy(name, dsl_yaml, *opts)
        return self._workflow_deployment_handle(result)

    def accept_workflow_candidate(self, candidate_ref: "WorkflowCandidateRef", confirmation: "WorkflowCandidateConfirmation") -> "AcceptedWorkflowCandidate":
        """Explicitly accept a server-owned candidate for later deployment."""

        return self.workflows().accept_candidate(candidate_ref, confirmation)

    def deploy_workflow_candidate(
        self,
        name: str,
        accepted_candidate: "AcceptedWorkflowCandidate",
        workflow_id: str = "",
        *opts: Callable[["WorkflowDeployOptions"], None],
    ) -> tuple["WorkflowHandle", WorkflowDeploymentEnvelope]:
        """An empty ID performs the accepted candidate's first deployment or its replay."""
        if workflow_id:
            opts = (with_workflow_id(workflow_id), *opts)
        result = self.workflows().deploy_candidate(name, accepted_candidate, *opts)
        return self._workflow_deployment_handle(result)

    def _workflow_deployment_handle(self, result: WorkflowDeploymentEnvelope) -> tuple["WorkflowHandle", WorkflowDeploymentEnvelope]:
        return WorkflowHandle(self, _created_string_path_id(result.workflow.id, "workflow")), result

    def custom_operator(self, operator_id: str) -> "CustomOperatorHandle":
        if not operator_id:
            raise ErrIDRequired
        return CustomOperatorHandle(self, operator_id)

    def workitem_api_service(self, node_id: str, version: str) -> "WorkitemAPIServiceHandle":
        if not node_id:
            raise ErrIDRequired
        if not version:
            raise ErrVersionRequired
        return WorkitemAPIServiceHandle(self, node_id, version)

    def create_custom_operator(
        self,
        name: str,
        identifier: str,
        description: str,
        input_schema: Any,
        output_schema: Any,
        *opts: Callable[["CustomOperatorOptions"], None],
    ) -> tuple["CustomOperatorHandle", CustomOperator]:
        result = self.workflows().create_custom_operator(
            CustomOperatorSpec(name, identifier, description, input_schema, output_schema),
            *opts,
        )
        return CustomOperatorHandle(self, _created_int_path_id(result.id, "custom operator")), result

    def create_custom_operator_from_spec(
        self,
        spec: "CustomOperatorSpec",
        *opts: Callable[["CustomOperatorOptions"], None],
    ) -> tuple["CustomOperatorHandle", CustomOperator]:
        spec.validate()
        result = self.workflows().create_custom_operator(spec, *opts)
        return CustomOperatorHandle(self, _created_int_path_id(result.id, "custom operator")), result

    def workflow_template(self, template_id: str) -> "WorkflowTemplateHandle":
        if not template_id:
            raise ErrIDRequired
        return WorkflowTemplateHandle(self, template_id)

    def create_workflow_template(
        self,
        name: str,
        dsl_yaml: str,
        *opts: Callable[["WorkflowTemplateOptions"], None],
    ) -> tuple["WorkflowTemplateHandle", WorkflowTemplate]:
        result = self.workflows().create_workflow_template(name, dsl_yaml, *opts)
        return WorkflowTemplateHandle(self, _created_int_path_id(result.id, "workflow template")), result

    def connector(self, connector_id: str) -> "ConnectorHandle":
        if not connector_id:
            raise ErrConnectorIDRequired
        return ConnectorHandle(self, connector_id)

    def connector_file(self, conn_file_id: str) -> "ConnectorFileHandle":
        if not conn_file_id:
            raise ErrConnectorFileIDRequired
        return ConnectorFileHandle(self, conn_file_id)

    def create_connector(
        self,
        name: str,
        source_type: int,
        usage_type: int,
        *opts: Callable[["ConnectorDefinitionOptions"], None],
    ) -> tuple["ConnectorHandle", Connector]:
        result = self.connectors().create(name, source_type, usage_type, *opts)
        return ConnectorHandle(self, result.id), result

    def semantic_model(self, model_id: str) -> "SemanticModelHandle":
        if not model_id:
            raise ErrIDRequired
        return SemanticModelHandle(self, model_id)

    def create_semantic_model(
        self,
        name: str,
        *opts: Callable[["SemanticModelOptions"], None],
    ) -> tuple["SemanticModelHandle", SemanticModelInfo]:
        result = self.knowledge().create(name, *opts)
        return SemanticModelHandle(self, _created_int_path_id(result.id, "semantic model")), result

    def artifact(self, artifact_id: str) -> "ArtifactHandle":
        if not artifact_id:
            raise ErrIDRequired
        return ArtifactHandle(self, artifact_id)

    def llm_provider(self) -> "ModelProviderHandle":
        return ModelProviderHandle(self, self.models().llm_backends(), "llm")

    def embedding_provider(self) -> "ModelProviderHandle":
        return ModelProviderHandle(self, self.models().embedding_backends(), "embedding")

    def parser_provider(self) -> "ModelProviderHandle":
        return ModelProviderHandle(self, self.models().parser_backends(), "parser")

    def llm_backend(self, backend_id: str) -> "ProviderBackendHandle":
        return self.llm_provider().backend(backend_id)

    def embedding_backend(self, backend_id: str) -> "ProviderBackendHandle":
        return self.embedding_provider().backend(backend_id)

    def parser_backend(self, backend_id: str) -> "ProviderBackendHandle":
        return self.parser_provider().backend(backend_id)

    def setup_llm_backend(
        self,
        name: str,
        address: str,
        models: list[str],
        *opts: Callable[["ProviderBackendOptions"], None],
    ) -> tuple["ProviderBackendHandle", ProviderSetupBackendResult]:
        if not name:
            raise ErrNameRequired
        if not address:
            raise ErrAddressRequired
        if not models:
            raise ErrModelsRequired
        result = self.models().setup_llm_backend(name, address, models, *opts)
        if not result.backend.id:
            raise Error("ErrResponseInvalid", "provider setup backend data missing backend id")
        return ProviderBackendHandle(self.llm_provider(), str(result.backend.id)), result

    def compute_resource(self, resource_id: str) -> "ComputeResourceHandle":
        if not resource_id:
            raise ErrIDRequired
        return ComputeResourceHandle(self, resource_id)

    def create_compute_resource(
        self,
        name: str,
        spec_id: str,
        cpu: int,
        memory_gib: int,
        *opts: Callable[["ComputeCreateOptions"], None],
    ) -> tuple["ComputeResourceHandle", ComputeResource]:
        result = self.compute().create(name, spec_id, cpu, memory_gib, *opts)
        return ComputeResourceHandle(self, _created_string_path_id(result.id, "compute resource")), result

    def data_share_publish(self, publish_id: str) -> "DataSharePublishHandle":
        if not publish_id:
            raise ErrIDRequired
        return DataSharePublishHandle(self, publish_id)

    def create_data_share_publish(
        self,
        name: str,
        source_database_id: str,
        table_scope: DataShareScope,
        target_workspace_ids: list[str],
        *opts: Callable[["DataSharePublishOptions"], None],
    ) -> tuple["DataSharePublishHandle", DataSharePublish]:
        result = self.data_share().create_publish(name, source_database_id, table_scope, target_workspace_ids, *opts)
        return DataSharePublishHandle(self, _created_string_path_id(result.id, "data-share publish")), result

    def data_share_subscription(self, subscription_id: str) -> "DataShareSubscriptionHandle":
        if not subscription_id:
            raise ErrIDRequired
        return DataShareSubscriptionHandle(self, subscription_id)

    def agent_by_code(self, agent_code: str) -> "AgentHandle":
        if not agent_code:
            raise ErrAgentRequired
        return AgentHandle(self, AgentSelector(agent_code=agent_code))

    def agent_by_code_in_workspace(self, agent_code: str, agent_workspace_id: str) -> "AgentHandle":
        if not agent_code:
            raise ErrAgentRequired
        if not agent_workspace_id:
            raise ErrWorkspaceRequired
        return AgentHandle(
            self,
            AgentSelector(agent_code=agent_code, agent_workspace_id=agent_workspace_id),
        )

    def agent_by_id(self, agent_id: str) -> "AgentHandle":
        if not agent_id:
            raise ErrAgentRequired
        return AgentHandle(self, AgentSelector(agent_id=agent_id))

    def sql_metadata(self) -> "SQLMetadataHandle":
        return SQLMetadataHandle(self)

    def sql_workbook(self, workbook_id: str) -> "SQLWorkbookHandle":
        if not workbook_id:
            raise ErrWorkbookIDRequired
        return SQLWorkbookHandle(self, workbook_id)

    def create_sql_workbook(self, name: str) -> tuple["SQLWorkbookHandle", SQLWorkbook]:
        result = self.sql().create_workbook(name)
        return SQLWorkbookHandle(self, result.workbook_id), result

    def sql_query(self, query_id: str) -> "SQLQueryHandle":
        if not query_id:
            raise ErrQueryIDRequired
        return SQLQueryHandle(self, query_id)

    def execute_sql(
        self,
        query: str,
        *opts: Callable[["SQLQueryOptions"], None],
    ) -> tuple["SQLQueryHandle", SQLQueryStartResult]:
        result = self.sql().execute_query(query, *opts)
        return SQLQueryHandle(self, result.query_id), result

    def sql_statement(self, statement_id: str) -> "SQLStatementHandle":
        if not statement_id:
            raise ErrStatementIDRequired
        return SQLStatementHandle(self, statement_id)

    def catalog(self) -> "CatalogService":
        return self._client.catalog(self.id)

    def knowledge(self) -> "KnowledgeService":
        return self._client.knowledge(self.id)

    def workflows(self) -> "WorkflowService":
        return self._client.workflows(self.id)

    def agents(self) -> "AgentService":
        return self._client.agents(self.id)

    def models(self) -> "ModelService":
        return self._client.models(self.id)

    def connectors(self) -> "ConnectorService":
        return self._client.connectors(self.id)

    def sql(self) -> "SQLService":
        return self._client.sql(self.id)

    def compute(self) -> "ComputeService":
        return self._client.compute(self.id)

    def memory(self) -> "MemoryService":
        """Legacy consumer-memory service, unavailable on the current MOI product API."""
        return self._client.memory(self.id)

    def consumer_memory(self, subject_id: str) -> "ConsumerMemoryHandle":
        """Legacy consumer-memory handle, unavailable on the current MOI product API."""
        if not subject_id:
            raise ErrSubjectRequired
        return ConsumerMemoryHandle(self, subject_id)

    def data_share(self) -> "DataShareService":
        return self._client.data_share(self.id)

    def data_share_summary(self) -> PublishSummaryResult:
        return self.data_share().publish_summary()

    def data_share_source_tables(
        self,
        source_database_id: str,
        *opts: Callable[["QueryOptions"], None],
    ) -> DataShareSourceTableListResult:
        return self.data_share().source_tables(source_database_id, *opts)

class WorkspaceMemberHandle:
    def __init__(self, workspace: WorkspaceHandle, user_id: str) -> None:
        self._workspace = workspace
        self.id = user_id

    def service(self) -> "WorkspaceMemberService":
        """Route-aligned escape hatch for canonical member APIs; prefer typed handle methods for user-facing workflows."""
        return self._workspace.members()

    def info(self) -> WorkspaceMember:
        return self.service().member(self.id)

    def update(self, name: str, description: str, *opts: Callable[["UpdateUserOptions"], None]) -> None:
        self.service().update(self.id, name, description, *opts)

    def update_status(self, action: str) -> None:
        self.service().update_status(self.id, action)

    def delete(self) -> None:
        self.service().delete(self.id)

class UploadedFilePreview:
    def __init__(self, file: "FileHandle", preview: "StreamResponse") -> None:
        self.file = file
        self.preview = preview

class StreamResponse:
    """Live streaming response; not task completion signal, AI task-selection source, or copy anchor; consume or explicitly hand off partial stream state, then close it."""

    def __init__(self, response: Any) -> None:
        self._response = response

    def read(self, size: Optional[int] = None) -> bytes:
        if size is None:
            return self._response.read()
        return self._response.read(size)

    def readline(self, size: int = -1) -> bytes:
        """Read one stream line for bounded SSE consumers."""
        return self._response.readline(size)

    def close(self) -> None:
        """Close the live response body after reading or handoff."""
        self._response.close()

    @property
    def status(self) -> int:
        return self._response.status

    @property
    def headers(self) -> Any:
        return self._response.headers

class HTTPResult:
    def __init__(self, status: int, headers: dict[str, str], body: Any) -> None:
        self.status = status
        self.headers = headers
        self.body = body

class ProductResult:
    def __init__(
        self,
        status: int,
        headers: dict[str, str],
        body: Any,
        request_headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.status = status
        self.headers = headers
        self.body = body
        self.request_headers = request_headers or {}
        self.code = ""
        self.message = ""
        self.data: Any = None
        if isinstance(body, dict):
            self.code = str(body.get("code") or "")
            self.message = str(body.get("msg") or body.get("message") or "")
            self.data = body.get("data")

class BytesResult:
    def __init__(self, status: int, headers: dict[str, str], content: bytes) -> None:
        self.status = status
        self.headers = headers
        self.content = content


class AgentTeamCreateRequest:
    """Typed input for the Team product API."""
    def __init__(self, name: str = "", description: str = "", members: Optional[list[AgentTeamMemberRef]] = None):
        self.name = name
        self.description = description
        self.members = members

    def body(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        result["name"] = self.name
        result["description"] = self.description
        result["members"] = [{"agent_workspace_id": member.agent_workspace_id, "agent_id": member.agent_id} for member in (self.members or [])]
        return result


class AgentTeamUpdateRequest:
    """Typed input for the Team product API."""
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None, expected_version: int = 0):
        self.name = name
        self.description = description
        self.expected_version = expected_version

    def body(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        result["expected_version"] = self.expected_version
        return result


class IngressCallbackConfig:
    def __init__(self, channel_instance_id: str):
        self.channel_instance_id = channel_instance_id

    def body(self) -> dict[str, Any]:
        return {"channel_instance_id": self.channel_instance_id}


class IngressManagedStreamConfig:
    def __init__(self, bot_id: str = "", secret: str = "", app_id: str = "", app_token: str = "", bot_token: str = "", app_secret: str = ""):
        self.bot_id = bot_id
        self.secret = secret
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.bot_token = bot_token

    def body(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "bot_id": self.bot_id,
                "secret": self.secret,
                "app_id": self.app_id,
                "app_secret": self.app_secret,
                "app_token": self.app_token,
                "bot_token": self.bot_token,
            }.items()
            if value
        }


class IngressMailPollingConfig:
    def __init__(self, channel_instance_id: str):
        self.channel_instance_id = channel_instance_id

    def body(self) -> dict[str, Any]:
        return {"channel_instance_id": self.channel_instance_id}


class IngressConnectionCreateRequest:
    def __init__(self, target: AgentTargetRef, provider: str, channel_type: str, receive_mode: str, agent_model: str = "", callback: Optional[IngressCallbackConfig] = None, mail_polling: Optional[IngressMailPollingConfig] = None, managed_stream: Optional[IngressManagedStreamConfig] = None):
        self.target = target
        self.provider = provider
        self.channel_type = channel_type
        self.receive_mode = receive_mode
        self.agent_model = agent_model
        self.callback = callback
        self.mail_polling = mail_polling
        self.managed_stream = managed_stream

    def body(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "target": {"kind": self.target.kind, "workspace_id": self.target.workspace_id, "id": self.target.id},
            "provider": self.provider,
            "channel_type": self.channel_type,
            "receive_mode": self.receive_mode,
        }
        if self.agent_model:
            result["agent_model"] = self.agent_model
        if self.callback is not None:
            result["callback"] = self.callback.body()
        if self.mail_polling is not None:
            result["mail_polling"] = self.mail_polling.body()
        if self.managed_stream is not None:
            result["managed_stream"] = self.managed_stream.body()
        return result


class IngressConnectionUpdateRequest:
    def __init__(self, enabled: Optional[bool] = None, agent_model: Optional[str] = None, managed_stream_secret: Optional[str] = None, expected_association_version: int = 0, expected_config_version: int = 0, managed_stream_app_token: Optional[str] = None, managed_stream_bot_token: Optional[str] = None, managed_stream_app_secret: Optional[str] = None):
        self.enabled = enabled
        self.agent_model = agent_model
        self.managed_stream_secret = managed_stream_secret
        self.managed_stream_app_secret = managed_stream_app_secret
        self.managed_stream_app_token = managed_stream_app_token
        self.managed_stream_bot_token = managed_stream_bot_token
        self.expected_association_version = expected_association_version
        self.expected_config_version = expected_config_version

    def body(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.enabled is not None:
            result["enabled"] = self.enabled
        if self.agent_model is not None:
            result["agent_model"] = self.agent_model
        managed_stream = {
            key: value
            for key, value in {
                "secret": self.managed_stream_secret,
                "app_secret": self.managed_stream_app_secret,
                "app_token": self.managed_stream_app_token,
                "bot_token": self.managed_stream_bot_token,
            }.items()
            if value is not None
        }
        if managed_stream:
            result["managed_stream"] = managed_stream
        result["expected_association_version"] = self.expected_association_version
        result["expected_config_version"] = self.expected_config_version
        return result


class IngressConnectionVerifyRequest:
    def __init__(self, expected_association_version: int, expected_config_version: int, callback_url: str = ""):
        self.expected_association_version = expected_association_version
        self.expected_config_version = expected_config_version
        self.callback_url = callback_url

    def body(self) -> dict[str, Any]:
        result = {
            "expected_association_version": self.expected_association_version,
            "expected_config_version": self.expected_config_version,
        }
        if self.callback_url:
            result["callback_url"] = self.callback_url
        return result

class IngressVerificationResult:
    def __init__(self, data: dict[str, Any], connection: Optional[IngressConnection], test_result: Optional[ChannelInstanceTestResult]) -> None:
        self.raw = data
        self.connection = connection
        self.test_result = test_result


class AgentTeamSessionCreateRequest:
    def __init__(self, name: str = ""):
        self.name = name

    def body(self) -> dict[str, Any]:
        return {"name": self.name} if self.name else {}


class AgentTeamSessionRenameRequest:
    def __init__(self, name: str, expected_version: int):
        self.name = name
        self.expected_version = expected_version

    def body(self) -> dict[str, Any]:
        return {"name": self.name, "expected_version": self.expected_version}


class AgentTeamMessageRequest:
    def __init__(self, message_id: str, parts: list[dict[str, Any]], idempotency_key: str, requested_member: Optional[AgentTeamMemberRef] = None, metadata: Optional[dict[str, Any]] = None):
        self.message_id = message_id
        self.parts = parts
        self.idempotency_key = idempotency_key
        self.requested_member = requested_member
        self.metadata = metadata

    def body(self) -> dict[str, Any]:
        result: dict[str, Any] = {"message_id": self.message_id, "parts": self.parts, "idempotency_key": self.idempotency_key}
        if self.requested_member is not None:
            result["requested_member"] = {"agent_workspace_id": self.requested_member.agent_workspace_id, "agent_id": self.requested_member.agent_id}
        if self.metadata is not None:
            result["metadata"] = self.metadata
        return result


class ChannelInstanceCreateRequest:
    def __init__(
        self,
        channel_type: str,
        *,
        name: str = "",
        description: str = "",
        config: Optional[dict[str, str]] = None,
        secrets: Optional[dict[str, str]] = None,
        visibility: str = "",
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        self.channel_type = channel_type
        self.name = name
        self.description = description
        self.config = config
        self.secrets = secrets
        self.visibility = visibility
        self.labels = labels

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {"channel_type": self.channel_type}
        for key, value in {
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "secrets": self.secrets,
            "visibility": self.visibility,
            "labels": self.labels,
        }.items():
            if value is not None and value != "":
                data[key] = value
        return data

class ChannelInstanceUpdateRequest:
    def __init__(
        self,
        *,
        channel_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict[str, str]] = None,
        secrets: Optional[dict[str, str]] = None,
        visibility: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        expected_version: Optional[int] = None,
    ) -> None:
        self.channel_type = channel_type
        self.name = name
        self.description = description
        self.config = config
        self.secrets = secrets
        self.visibility = visibility
        self.labels = labels
        self.expected_version = expected_version

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key, value in {
            "channel_type": self.channel_type,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "secrets": self.secrets,
            "visibility": self.visibility,
            "labels": self.labels,
            "expected_version": self.expected_version,
        }.items():
            if value is not None:
                data[key] = value
        return data

class ChannelInstanceRecord:
    def __init__(self, data: dict[str, Any]) -> None:
        self.id = str(data.get("id") or "")
        self.workspace_id = str(data.get("workspace_id") or "")
        self.provider = str(data.get("provider") or "")
        self.channel_type = str(data.get("channel_type") or "")
        self.name = str(data.get("name") or "")
        self.description = str(data.get("description") or "")
        self.status = str(data.get("status") or "")
        self.credential_ref = str(data.get("credential_ref") or "")
        self.callback_path = str(data.get("callback_path") or "")
        self.capabilities = _string_list(data.get("capabilities"))
        self.tool_ids = _string_list(data.get("tool_ids"))
        self.config = dict(data.get("config") or {}) if isinstance(data.get("config"), dict) else {}
        self.last_test_status = str(data.get("last_test_status") or "")
        self.last_tested_at = str(data.get("last_tested_at") or "")
        self.last_test_error = str(data.get("last_test_error") or "")
        self.last_test_error_code = str(data.get("last_test_error_code") or "")
        self.labels = dict(data.get("labels") or {}) if isinstance(data.get("labels"), dict) else {}
        self.created_at = str(data.get("created_at") or "")
        self.updated_at = str(data.get("updated_at") or "")
        self.version = int(data.get("version") or 0)
        self.raw = data

class ConnectorCatalogItem:
    def __init__(self, data: dict[str, Any]) -> None:
        self.provider = str(data.get("provider") or "")
        self.name = str(data.get("name") or "")
        self.description = str(data.get("description") or "")
        self.configured = bool(data.get("configured"))
        self.raw = data

class ConnectorCatalogResult:
    def __init__(self, data: dict[str, Any]) -> None:
        items = data.get("items")
        self.items = [ConnectorCatalogItem(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        self.raw = data

class ChannelInstanceListResult:
    def __init__(self, data: dict[str, Any]) -> None:
        items = data.get("items")
        self.items = [_channel_instance_record(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        self.total = _required_int_field(data, "total")
        self.limit = _required_int_field(data, "limit")
        self.offset = _required_int_field(data, "offset")
        self.raw = data

class ChannelInstanceTestResult:
    def __init__(self, data: dict[str, Any]) -> None:
        # 未持久化配置的测试连接不携带 instance；只有持久化实例测试才返回。
        self.instance = (
            _channel_instance_record(data.get("instance"))
            if isinstance(data.get("instance"), dict)
            else None
        )
        self.ok = bool(data.get("ok"))
        self.status = str(data.get("status") or "")
        self.worker_id = str(data.get("worker_id") or "")
        self.request_id = str(data.get("request_id") or "")
        self.last_test_status = str(data.get("last_test_status") or "")
        self.last_test_error = str(data.get("last_test_error") or "")
        self.error_code = str(data.get("error_code") or "")
        self.error_stage = str(data.get("error_stage") or "")
        self.provider_error_code = str(data.get("provider_error_code") or "")
        self.provider_error_message = str(data.get("provider_error_message") or "")
        self.error_category = str(data.get("error_category") or "")
        self.suggestion = str(data.get("suggestion") or "")
        self.last_tested_at = str(data.get("last_tested_at") or "")
        self.raw = data

class CallbackRuleMatch:
    def __init__(
        self,
        *,
        resource_kinds: Optional[list[str]] = None,
        event_types: Optional[list[str]] = None,
        event_actions: Optional[list[str]] = None,
        field_equals: Optional[dict[str, str]] = None,
    ) -> None:
        self.resource_kinds = resource_kinds or []
        self.event_types = event_types or []
        self.event_actions = event_actions or []
        self.field_equals = field_equals or {}

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.resource_kinds:
            data["resource_kinds"] = self.resource_kinds
        if self.event_types:
            data["event_types"] = self.event_types
        if self.event_actions:
            data["event_actions"] = self.event_actions
        if self.field_equals:
            data["field_equals"] = self.field_equals
        return data

class CallbackRuleCreateRequest:
    def __init__(
        self,
        provider: str,
        credential_ref: str,
        name: str,
        target_type: str,
        *,
        description: str = "",
        enabled: Optional[bool] = None,
        priority: Optional[int] = None,
        match: Optional[CallbackRuleMatch] = None,
        target_config: Optional[dict[str, Any]] = None,
        stop_after_match: Optional[bool] = None,
    ) -> None:
        self.provider = provider
        self.credential_ref = credential_ref
        self.name = name
        self.target_type = target_type
        self.description = description
        self.enabled = enabled
        self.priority = priority
        self.match = match
        self.target_config = target_config
        self.stop_after_match = stop_after_match

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "provider": self.provider,
            "credential_ref": self.credential_ref,
            "name": self.name,
            "target_type": self.target_type,
        }
        if self.description:
            data["description"] = self.description
        if self.enabled is not None:
            data["enabled"] = self.enabled
        if self.priority is not None:
            data["priority"] = self.priority
        if self.match is not None:
            data["match"] = self.match.body()
        if self.target_config is not None:
            data["target_config"] = self.target_config
        if self.stop_after_match is not None:
            data["stop_after_match"] = self.stop_after_match
        return data

class CallbackRuleUpdateRequest:
    def __init__(
        self,
        version: int,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        priority: Optional[int] = None,
        match: Optional[CallbackRuleMatch] = None,
        target_type: Optional[str] = None,
        target_config: Optional[dict[str, Any]] = None,
        stop_after_match: Optional[bool] = None,
    ) -> None:
        self.version = version
        self.name = name
        self.description = description
        self.enabled = enabled
        self.priority = priority
        self.match = match
        self.target_type = target_type
        self.target_config = target_config
        self.stop_after_match = stop_after_match

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {"version": self.version}
        for key, value in {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority,
            "target_type": self.target_type,
            "target_config": self.target_config,
            "stop_after_match": self.stop_after_match,
        }.items():
            if value is not None:
                data[key] = value
        if self.match is not None:
            data["match"] = self.match.body()
        return data

class CallbackRuleRecord:
    def __init__(self, data: dict[str, Any]) -> None:
        self.id = str(data.get("id") or "")
        self.workspace_id = str(data.get("workspace_id") or "")
        self.provider = str(data.get("provider") or "")
        self.credential_ref = str(data.get("credential_ref") or "")
        self.name = str(data.get("name") or "")
        self.description = str(data.get("description") or "")
        self.enabled = bool(data.get("enabled"))
        self.priority = int(data.get("priority") or 0)
        self.match = _callback_rule_match(data.get("match"))
        self.target_type = str(data.get("target_type") or "")
        self.target_config = dict(data.get("target_config") or {}) if isinstance(data.get("target_config"), dict) else {}
        self.stop_after_match = bool(data.get("stop_after_match"))
        self.version = int(data.get("version") or 0)
        self.created_by = str(data.get("created_by") or "")
        self.updated_by = str(data.get("updated_by") or "")
        self.created_at = str(data.get("created_at") or "")
        self.updated_at = str(data.get("updated_at") or "")
        self.raw = data

class CallbackRuleListResult:
    def __init__(self, data: dict[str, Any]) -> None:
        items = data.get("items")
        self.items = [_callback_rule_record(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        self.total = _required_int_field(data, "total")
        self.limit = _required_int_field(data, "limit")
        self.offset = _required_int_field(data, "offset")
        self.raw = data

class CallbackRuleDeleteResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self.deleted = bool(data.get("deleted"))
        self.raw = data

class RESTParameter:
    def __init__(self, name: str, value: str) -> None:
        self.name = name
        self.value = value

    def body(self) -> dict[str, str]:
        return {"name": self.name, "value": self.value}


class RESTRequest:
    def __init__(
        self,
        path: str,
        method: str,
        params: Optional[list[RESTParameter]] = None,
        headers: Optional[list[RESTParameter]] = None,
        json: str = "",
        data: Optional[list[RESTParameter]] = None,
    ) -> None:
        self.path = path
        self.method = method
        self.params = params
        self.headers = headers
        self.json = json
        self.data = data

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {"path": self.path, "method": self.method}
        if self.params:
            data["params"] = [item.body() for item in self.params]
        if self.headers:
            data["headers"] = [item.body() for item in self.headers]
        if self.json:
            data["json"] = self.json
        if self.data:
            data["data"] = [item.body() for item in self.data]
        return data


class RESTPagination:
    def __init__(
        self,
        type: str,
        param: str = "",
        start: Optional[int] = None,
        step: int = 0,
        next_path: str = "",
        total_path: str = "",
    ) -> None:
        self.type = type
        self.param = param
        self.start = start
        self.step = step
        self.next_path = next_path
        self.total_path = total_path

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.type}
        if self.param:
            data["param"] = self.param
        if self.start is not None:
            data["start"] = self.start
        if self.step:
            data["step"] = self.step
        if self.next_path:
            data["next_path"] = self.next_path
        if self.total_path:
            data["total_path"] = self.total_path
        return data


class RESTPreview:
    def __init__(
        self,
        request: RESTRequest,
        pagination: RESTPagination,
        read_only_post: bool = False,
        records_path: str = "",
        schema_path: str = "",
        schema_format: str = "",
        cursor_param: str = "",
        initial_cursor: str = "",
    ) -> None:
        self.request = request
        self.pagination = pagination
        self.read_only_post = read_only_post
        self.records_path = records_path
        self.schema_path = schema_path
        self.schema_format = schema_format
        self.cursor_param = cursor_param
        self.initial_cursor = initial_cursor

    def body(self) -> dict[str, Any]:
        data = self.request.body()
        if self.read_only_post:
            data["read_only_post"] = True
        if self.records_path:
            data["records_path"] = self.records_path
        if self.schema_path:
            data["schema_path"] = self.schema_path
        if self.schema_format:
            data["schema_format"] = self.schema_format
        data["pagination"] = self.pagination.body()
        if self.cursor_param:
            data["cursor_param"] = self.cursor_param
        if self.initial_cursor:
            data["initial_cursor"] = self.initial_cursor
        return data


class StructuredSourceRef:
    def __init__(
        self,
        connector_id: str,
        source_type: str,
        database: str,
        schema: str = "",
        table: str = "",
        collection: str = "",
    ) -> None:
        self.connector_id = connector_id
        self.source_type = source_type
        self.database = database
        self.schema = schema
        self.table = table
        self.collection = collection

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "connector_id": self.connector_id,
            "source_type": self.source_type,
        }
        if self.database:
            data["database"] = self.database
        if self.schema:
            data["schema"] = self.schema
        if self.table:
            data["table"] = self.table
        if self.collection:
            data["collection"] = self.collection
        return data

class StructuredSourceObjectsRequest:
    def __init__(self, connector_id: str, source_type: str, database: str, schema: str = "") -> None:
        self.connector_id = connector_id
        self.source_type = source_type
        self.database = database
        self.schema = schema

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "connector_id": self.connector_id,
            "source_type": self.source_type,
            "database": self.database,
        }
        if self.schema:
            data["schema"] = self.schema
        return data

class StructuredKafkaSampleSpec:
    def __init__(self, topic_mode: str, topics: Optional[list[str]] = None, topic_pattern: str = "") -> None:
        self.topic_mode = topic_mode
        self.topics = topics
        self.topic_pattern = topic_pattern

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {"topic_mode": self.topic_mode}
        if self.topics:
            data["topics"] = self.topics
        if self.topic_pattern:
            data["topic_pattern"] = self.topic_pattern
        return data


class StructuredKafkaSchemaSpec:
    def __init__(self, key_format: str, value_format: str, schema_source: str,
                 json_schema: str = "", sample: Optional[StructuredKafkaSampleSpec] = None,
                 sample_limit: Optional[int] = None) -> None:
        self.key_format = key_format
        self.value_format = value_format
        self.schema_source = schema_source
        self.json_schema = json_schema
        self.sample = sample
        self.sample_limit = sample_limit

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {"key_format": self.key_format, "value_format": self.value_format,
                                "schema_source": self.schema_source}
        if self.json_schema:
            data["json_schema"] = self.json_schema
        if self.sample is not None:
            data["sample"] = self.sample.body()
        if self.sample_limit is not None:
            data["sample_limit"] = self.sample_limit
        return data


class StructuredSourceSchemaRequest:
    def __init__(
        self,
        connector_id: str,
        source: StructuredSourceRef,
        mongo_sample_limit: Optional[int] = None,
        kafka_schema: Optional[StructuredKafkaSchemaSpec] = None,
    ) -> None:
        self.connector_id = connector_id
        self.source = source
        self.mongo_sample_limit = mongo_sample_limit
        self.kafka_schema = kafka_schema

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "connector_id": self.connector_id,
            "source": self.source.body(),
        }
        if self.mongo_sample_limit is not None:
            data["mongo_sample_limit"] = self.mongo_sample_limit
        if self.kafka_schema is not None:
            data["kafka_schema"] = self.kafka_schema.body()
        return data

class StructuredBackfillStartResolveRequest:
    def __init__(
        self,
        connector_id: str,
        source: StructuredSourceRef,
        start_mode: str,
        watermark: Optional[object] = None,
        custom_start_value: Optional[object] = None,
    ) -> None:
        self.connector_id = connector_id
        self.source = source
        self.start_mode = start_mode
        self.watermark = watermark
        self.custom_start_value = custom_start_value

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "connector_id": self.connector_id,
            "source": self.source.body(),
            "start_mode": self.start_mode,
        }
        if self.watermark is not None:
            data["watermark"] = self.watermark
        if self.custom_start_value is not None:
            data["custom_start_value"] = self.custom_start_value
        return data

class StructuredSourceCapabilities:
    def __init__(self, data: dict[str, Any]) -> None:
        self.list_databases = bool(data.get("list_databases"))
        self.list_schemas = bool(data.get("list_schemas"))
        self.list_tables = bool(data.get("list_tables"))
        self.describe_schema = bool(data.get("describe_schema"))
        self.sample = bool(data.get("sample"))
        self.backfill_start_resolve = bool(data.get("backfill_start_resolve"))
        self.hive_partitions = bool(data.get("hive_partitions"))
        self.mongodb_flatten = bool(data.get("mongodb_flatten"))
        self.raw = data

class StructuredSourceDescriptor:
    def __init__(self, data: dict[str, Any]) -> None:
        capabilities = data.get("capabilities")
        self.connector_id = str(data.get("connector_id") or "")
        self.connector_name = str(data.get("connector_name") or "")
        self.source_type = str(data.get("source_type") or "")
        self.enabled = bool(data.get("enabled"))
        self.disabled_reason = str(data.get("disabled_reason") or "")
        self.capability_profile_hash = str(data.get("capability_profile_hash") or "")
        self.capabilities = StructuredSourceCapabilities(capabilities if isinstance(capabilities, dict) else {})
        self.raw = data

class StructuredSourceListResult:
    def __init__(self, data: dict[str, Any]) -> None:
        sources = data.get("sources")
        self.sources = [StructuredSourceDescriptor(item) for item in sources if isinstance(item, dict)] if isinstance(sources, list) else []
        self.raw = data

class StructuredSourceNamedRef:
    def __init__(self, data: dict[str, Any]) -> None:
        self.name = str(data.get("name") or "")
        self.display_name = str(data.get("display_name") or "")
        self.raw = data

class StructuredSourceDatabasesResult:
    def __init__(self, data: dict[str, Any]) -> None:
        databases = data.get("databases")
        self.databases = [StructuredSourceNamedRef(item) for item in databases if isinstance(item, dict)] if isinstance(databases, list) else []
        endpoint_results = data.get("endpoint_results")
        self.endpoint_results = endpoint_results if isinstance(endpoint_results, list) else []
        self.raw = data

class StructuredSourceSchemasResult:
    def __init__(self, data: dict[str, Any]) -> None:
        schemas = data.get("schemas")
        self.schemas = [StructuredSourceNamedRef(item) for item in schemas if isinstance(item, dict)] if isinstance(schemas, list) else []
        endpoint_results = data.get("endpoint_results")
        self.endpoint_results = endpoint_results if isinstance(endpoint_results, list) else []
        self.raw = data

class StructuredSourceObject:
    def __init__(self, data: dict[str, Any]) -> None:
        self.database = str(data.get("database") or "")
        self.schema = str(data.get("schema") or "")
        self.table = str(data.get("table") or "")
        self.collection = str(data.get("collection") or "")
        self.display_name = str(data.get("display_name") or "")
        self.object_kind = str(data.get("object_kind") or "")
        self.raw = data

class StructuredSourceObjectsResult:
    def __init__(self, data: dict[str, Any]) -> None:
        objects = data.get("objects")
        self.objects = [StructuredSourceObject(item) for item in objects if isinstance(item, dict)] if isinstance(objects, list) else []
        endpoint_results = data.get("endpoint_results")
        self.endpoint_results = endpoint_results if isinstance(endpoint_results, list) else []
        self.raw = data

class StructuredSourceSchemaResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self.schema_snapshot = data.get("schema_snapshot")
        self.mapping_draft = data.get("mapping_draft")
        self.target_type_catalog = data.get("target_type_catalog")
        self.field_compatibilities = data.get("field_compatibilities")
        self.source_schema_hash = str(data.get("source_schema_hash") or "")
        self.source_object_hash = str(data.get("source_object_hash") or "")
        self.connector_config_hash = str(data.get("connector_config_hash") or "")
        self.mapping_hash = str(data.get("mapping_hash") or "")
        self.flatten_hash = str(data.get("flatten_hash") or "")
        endpoint_results = data.get("endpoint_results")
        self.endpoint_results = endpoint_results if isinstance(endpoint_results, list) else []
        self.raw = data

class StructuredSourceCapabilityResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self.capability_profile_hash = str(data.get("capability_profile_hash") or "")
        self.doris_cdc_available = bool(data.get("doris_cdc_available"))
        mysql_cdc_available = data.get("mysql_cdc_available")
        if mysql_cdc_available is not None and not isinstance(mysql_cdc_available, bool):
            raise Error("ErrResponseInvalid", "structured source capability mysql_cdc_available must be a boolean")
        self.mysql_cdc_available = mysql_cdc_available is True
        disabled_reasons = data.get("disabled_reasons")
        self.disabled_reasons = [str(reason) for reason in disabled_reasons] if isinstance(disabled_reasons, list) else []
        self.doris_flight_sql_read_available = bool(data.get("doris_flight_sql_read_available"))
        self.doris_thrift_read_available = bool(data.get("doris_thrift_read_available"))
        self.doris_jdbc_read_available = bool(data.get("doris_jdbc_read_available"))
        self.doris_read_mode = str(data.get("doris_read_mode") or "")
        doris_read_disabled_reasons = data.get("doris_read_disabled_reasons")
        self.doris_read_disabled_reasons = [str(reason) for reason in doris_read_disabled_reasons] if isinstance(doris_read_disabled_reasons, list) else []
        self.raw = data

class StructuredSourceSampleResult:
    def __init__(self, data: dict[str, Any]) -> None:
        rows = data.get("rows")
        self.rows = rows if isinstance(rows, list) else []
        self.next_position = data.get("next_position")
        self.has_more = bool(data.get("has_more"))
        self.raw = data

class StructuredBackfillStartResolveResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self.start_position = data.get("start_position")
        self.display_value = str(data.get("display_value") or "")
        self.source_object_hash = str(data.get("source_object_hash") or "")
        self.source_schema_hash = str(data.get("source_schema_hash") or "")
        self.raw = data

class CatalogHandle:
    def __init__(self, workspace: WorkspaceHandle, catalog_id: int, name: str) -> None:
        if not catalog_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = catalog_id
        self.name = name

    def service(self) -> "CatalogService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.catalog()

    def info(self) -> CatalogInfoResult:
        return self.service().info(self.id)

    def delete(self) -> None:
        self.service().delete(self.id)

    def rename(self, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> "CatalogHandle":
        self.service().update(self.id, name, *opts)
        self.name = name
        return self

    def databases(self, *opts: Callable[["CatalogListOptions"], None]) -> tuple[list["DatabaseHandle"], DatabaseListResult]:
        result = self.service().list_databases(self.id, *opts)
        return [DatabaseHandle(self, database.id, database.name) for database in result.list], result

    def prepare_database(self, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> "DatabaseHandle":
        if not name:
            raise ErrNameRequired
        matched: Optional[DatabaseHandle] = None
        for database in self.service().list_databases(self.id).list:
            if database.name != name:
                continue
            if matched is not None:
                raise _duplicate_name_error("database", name)
            matched = DatabaseHandle(self, database.id, database.name)
        if matched is not None:
            return matched
        created = self.service().create_database(self.id, name, *opts)
        return DatabaseHandle(self, created.id, name)

class DatabaseHandle:
    def __init__(self, catalog: CatalogHandle, database_id: int, name: str) -> None:
        if not database_id:
            raise ErrIDRequired
        self._catalog = catalog
        self.id = database_id
        self.name = name

    def service(self) -> "CatalogService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._catalog.service()

    def info(self) -> DatabaseInfoResult:
        return self.service().database_info(self.id)

    def delete(self) -> None:
        self.service().delete_database(self.id)

    def rename(self, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> "DatabaseHandle":
        raise ErrDatabaseRenameUnsupported

    def update_description(self, description: str) -> "DatabaseHandle":
        self.service().update_database_description(self.id, with_catalog_description(description))
        return self

    def table(self, table_id: int) -> "TableHandle":
        if not table_id:
            raise ErrIDRequired
        return TableHandle(self, table_id)

    def children(self, *opts: Callable[["CatalogListOptions"], None]) -> DatabaseChildrenResult:
        return self.service().database_children(self.id, *opts)

    def volumes(self) -> tuple[list["VolumeHandle"], DatabaseChildrenResult]:
        children = self.service().database_children(self.id)
        return [
            VolumeHandle(self, _parse_positive_int_id(child.id, "volume"), child.name)
            for child in children.list
            if child.type == "volume"
        ], children

    def tables(self) -> tuple[list["TableHandle"], DatabaseChildrenResult]:
        children = self.service().database_children(self.id)
        return [
            TableHandle(self, _parse_positive_int_id(child.id, "table"), child.name)
            for child in children.list
            if child.type == "table"
        ], children

    def create_table(
        self,
        name: str,
        columns: list[dict[str, Any]],
        *opts: Callable[["CreateTableOptions"], None],
    ) -> tuple["TableHandle", CatalogCreateTableResult]:
        created = self.service().create_table(self.id, name, columns, *opts)
        return TableHandle(self, created.id, name), created

    def create_table_from_columns(
        self,
        name: str,
        columns: list["TableColumn"],
        *opts: Callable[["CreateTableOptions"], None],
    ) -> tuple["TableHandle", CatalogCreateTableResult]:
        if not columns:
            raise ErrColumnsRequired
        return self.create_table(name, [column.to_dict() for column in columns], *opts)

    def table_exists(self, name: str) -> BoolDataResult:
        return self.service().table_exists(self.id, name)

    def table_overview(self) -> CatalogTableOverviewResult:
        return self.service().table_overview(self.id)

    def prepare_volume(self, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> "VolumeHandle":
        if not name:
            raise ErrNameRequired
        matched: Optional[VolumeHandle] = None
        for child in self.service().database_children(self.id).list:
            if child.type != "volume" or child.name != name:
                continue
            if matched is not None:
                raise _duplicate_name_error("volume", name)
            matched = VolumeHandle(self, _parse_positive_int_id(child.id, "volume"), child.name)
        if matched is not None:
            return matched
        created = self.service().create_volume(self.id, name, *opts)
        return VolumeHandle(self, created.id, name)

class TableHandle:
    def __init__(self, database: DatabaseHandle, table_id: int, name: str = "") -> None:
        if not table_id:
            raise ErrIDRequired
        self._database = database
        self.id = table_id
        self.name = name

    def service(self) -> "CatalogService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._database.service()

    def info(self, *opts: Callable[["TableLookupOptions"], None]) -> CatalogTableInfoResult:
        return self.service().table_info(self.id, *opts)

    def data(self, *opts: Callable[["TableDataOptions"], None]) -> CatalogTableDataResult:
        return self.service().table_data(self.id, *opts)

    def preview(self, *opts: Callable[["TableDataOptions"], None]) -> CatalogTableDataResult:
        return self.service().preview_table(self.id, *opts)

    def download(self) -> "StreamResponse":
        return self.service().download_table(self.id)

    def full_path(self) -> PathResult:
        return self.service().table_full_path(self.id)

    def truncate(self) -> None:
        self.service().truncate_table(self.id)

    def delete(self) -> None:
        self.service().delete_table(self.id)

class VolumeHandle:
    def __init__(self, database: DatabaseHandle, volume_id: int, name: str) -> None:
        if not volume_id:
            raise ErrVolumeIDRequired
        self._database = database
        self.id = volume_id
        self.name = name

    def service(self) -> "CatalogService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._database.service()

    def info(self) -> VolumeInfoResult:
        return self.service().volume_info(str(self.id))

    def delete(self) -> None:
        self.service().delete_volume(self.id)

    def rename(self, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> "VolumeHandle":
        self.service().update_volume(self.id, name, *opts)
        self.name = name
        return self

    def full_path(self) -> PathResult:
        return self.service().volume_full_path(self.id)

    def folder(self, folder_id: int) -> "FolderHandle":
        if not folder_id:
            raise ErrIDRequired
        return FolderHandle(self, folder_id)

    def create_folder(self, name: str, *opts: Callable[["CreateFolderOptions"], None]) -> tuple["FolderHandle", CreateFolderResult]:
        created = self.service().create_folder(self.id, self._database.id, name, *opts)
        return FolderHandle(self, created.id, name), created

    def upload_bytes(self, filename: str, data: bytes) -> UploadFileResult:
        uploaded = self.service().upload_bytes(filename, data)
        self.service().create_file(self.id, uploaded.file_id)
        return uploaded

    def upload_bytes_handle(self, filename: str, data: bytes) -> "FileHandle":
        uploaded = self.upload_bytes(filename, data)
        return self.file(uploaded.file_id)

    def upload_file(self, file_path: str) -> UploadFileResult:
        """local file input convenience method, not AI file-discovery, local-filesystem probing, filename inference, or default upload entry point."""
        uploaded = self.service().upload_file(file_path)
        self.service().create_file(self.id, uploaded.file_id)
        return uploaded

    def upload_file_handle(self, file_path: str) -> "FileHandle":
        """local file input convenience method, not AI file-discovery, local-filesystem probing, filename inference, or default upload entry point; prefer upload_bytes_handle when bytes are already caller-owned."""
        uploaded = self.upload_file(file_path)
        return self.file(uploaded.file_id)

    def upload_bytes_preview(self, filename: str, data: bytes) -> UploadedFilePreview:
        file = self.upload_bytes_handle(filename, data)
        return UploadedFilePreview(file, file.preview())

    def upload_file_preview(self, file_path: str) -> UploadedFilePreview:
        """local file input convenience method, not AI file-discovery, local-filesystem probing, filename inference, or default upload entry point; prefer upload_bytes_preview when bytes are already caller-owned."""
        file = self.upload_file_handle(file_path)
        return UploadedFilePreview(file, file.preview())

    def file(self, file_id: str) -> "FileHandle":
        if not file_id:
            raise ErrFileIDRequired
        return FileHandle(self, file_id)

    def files(self, *opts: Callable[["FileListOptions"], None]) -> CatalogFileListResult:
        return self.service().files(with_file_list_filter("volume_id", str(self.id)), *opts)

class FolderHandle:
    def __init__(self, volume: VolumeHandle, folder_id: int, name: str = "") -> None:
        if not folder_id:
            raise ErrIDRequired
        self._volume = volume
        self.id = folder_id
        self.name = name

    def rename(self, name: str, *opts: Callable[["UpdateFolderOptions"], None]) -> "FolderHandle":
        self._volume.service().update_folder(self.id, with_folder_name(name), *opts)
        self.name = name
        return self

    def clean(self) -> None:
        self._volume.service().clean_folder(self.id)

    def delete(self) -> None:
        self._volume.service().delete_folder(self.id)

class FileHandle:
    def __init__(self, volume: VolumeHandle, file_id: str) -> None:
        if not file_id:
            raise ErrFileIDRequired
        self._volume = volume
        self.id = file_id

    def rename(self, name: str) -> "FileHandle":
        """Product catalog file update is a backend no-op; keep the handle for chaining."""
        if not name:
            raise ErrNameRequired
        # Backend POST /catalog/file/update does not persist renames. Keep the
        # method for facade symmetry with other catalog resources, but do not
        # pretend the product API mutated the file name.
        return self

    def info(self) -> FileInfoResult:
        return self._volume.service().file_info(self.id)

    def download(self, *opts: Callable[["DownloadFileOptions"], None]) -> StreamResponse:
        return self._volume.service().download_file(str(self._volume.id), self.id, *opts)

    def preview(self) -> StreamResponse:
        return self._volume.service().preview_file(str(self._volume.id), self.id)

    def trigger_workflows(self) -> TriggerFileWorkflowResult:
        return self._volume.service().trigger_file_workflow(self._volume.id, self.id)

    def data_asset(self) -> CatalogDataAssetResolveResult:
        return self._volume.service().file_data_asset(self.id)

    def artifact(self) -> CatalogFileArtifactResult:
        return self._volume.service().file_artifact(self.id)

    def lineage_overview(self, *opts: Callable[["QueryOptions"], None]) -> LineageOverview:
        return self._volume._database._catalog._workspace.workflows().catalog_file_lineage_overview(self.id, *opts)

    def delete_ref(self) -> None:
        self._volume.service().delete_file_ref(self._volume.id, self.id)

    def delete(self) -> None:
        self._volume.service().delete_file(self.id, str(self._volume.id))

class ArtifactHandle:
    def __init__(self, workspace: WorkspaceHandle, artifact_id: str) -> None:
        if not artifact_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = artifact_id

    def service(self) -> "WorkflowService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.workflows()

    def overview(self) -> LineageOverview:
        return self.service().artifact_lineage_overview(self.id)

    def output_blocks(self) -> LineageOutputBlocks:
        return self.service().artifact_output_blocks(self.id)

    def block(self, block_id: str) -> "ArtifactBlockHandle":
        if not block_id:
            raise ErrIDRequired
        return ArtifactBlockHandle(self, block_id)

    def switch_effective_revisions(
        self,
        switches: list["LineageRevisionSwitch"],
        *opts: Callable[["LineageSwitchOptions"], None],
    ) -> LineageEffectiveRevisions:
        return self.service().switch_artifact_effective_revisions(self.id, switches, *opts)

    def node(self, node_id: str) -> "ArtifactNodeHandle":
        if not node_id:
            raise ErrIDRequired
        return ArtifactNodeHandle(self, node_id)

class ArtifactBlockHandle:
    def __init__(self, artifact: ArtifactHandle, block_id: str) -> None:
        if not block_id:
            raise ErrIDRequired
        self._artifact = artifact
        self.id = block_id

    def revisions(self) -> LineageBlockRevisions:
        return self._artifact.service().artifact_block_revisions(self._artifact.id, self.id)

    def create_revision(self, *opts: Callable[["LineageRevisionOptions"], None]) -> LineageBlockRevision:
        return self._artifact.service().create_artifact_block_revision(self._artifact.id, self.id, *opts)

class ArtifactNodeHandle:
    def __init__(self, artifact: ArtifactHandle, node_id: str) -> None:
        if not node_id:
            raise ErrIDRequired
        self._artifact = artifact
        self.id = node_id

    def info(self) -> LineageArtifactNode:
        return self._artifact.service().artifact_node(self._artifact.id, self.id)

    def output_blocks(self) -> LineageOutputBlocks:
        return self._artifact.service().artifact_node_output_blocks(self._artifact.id, self.id)

    def block(self, block_id: str) -> "ArtifactNodeBlockHandle":
        if not block_id:
            raise ErrIDRequired
        return ArtifactNodeBlockHandle(self, block_id)

    def switch_effective_revisions(
        self,
        switches: list["LineageRevisionSwitch"],
        *opts: Callable[["LineageSwitchOptions"], None],
    ) -> LineageEffectiveRevisions:
        return self._artifact.service().switch_artifact_node_effective_revisions(self._artifact.id, self.id, switches, *opts)

    def rerun(self, *opts: Callable[["LineageRerunOptions"], None]) -> LineageRerun:
        return self._artifact.service().create_artifact_node_rerun(self._artifact.id, self.id, *opts)

    def rerun_target_with_revisions(
        self,
        target_output_emission_id: str,
        *opts: Callable[["LineageRevisionRerunOptions"], None],
    ) -> LineageRerun:
        return self._artifact.service().create_target_artifact_node_revision_rerun(self._artifact.id, self.id, target_output_emission_id, *opts)

class ArtifactNodeBlockHandle:
    def __init__(self, node: ArtifactNodeHandle, block_id: str) -> None:
        if not block_id:
            raise ErrIDRequired
        self._node = node
        self.id = block_id

    def revisions(self) -> LineageBlockRevisions:
        return self._node._artifact.service().artifact_node_block_revisions(self._node._artifact.id, self._node.id, self.id)

    def create_revision(self, *opts: Callable[["LineageRevisionOptions"], None]) -> LineageBlockRevision:
        return self._node._artifact.service().create_artifact_node_block_revision(self._node._artifact.id, self._node.id, self.id, *opts)

class WorkflowHandle:
    def __init__(self, workspace: WorkspaceHandle, workflow_id: str) -> None:
        if not workflow_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = workflow_id

    def service(self) -> "WorkflowService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.workflows()

    def info(self) -> WorkflowEnvelope:
        return self.service().get(self.id)

    def update(self, *opts: Callable[["WorkflowUpdateOptions"], None]) -> WorkflowEnvelope:
        return self.service().update(self.id, *opts)

    def delete(self) -> WorkflowDeleteEnvelope:
        return self.service().delete(self.id)

    def run(self, *opts: Callable[["WorkflowRunOptions"], None]) -> WorkflowRunEnvelope:
        return self.service().run(self.id, *opts)

    def pause(self) -> WorkflowEnvelope:
        return self.service().pause(self.id)

    def enable(self) -> WorkflowEnvelope:
        return self.service().enable(self.id)

    def resume(self) -> WorkflowEnvelope:
        return self.service().resume(self.id)

    def runs(self, *opts: Callable[["ListOptions"], None]) -> WorkflowExecutionListEnvelope:
        return self.service().list_runs(self.id, *opts)

    def run_handle(self, execution_id: str) -> "WorkflowRunHandle":
        if not execution_id:
            raise ErrIDRequired
        return WorkflowRunHandle(self, execution_id)

class WorkflowRunHandle:
    def __init__(self, workflow: WorkflowHandle, execution_id: str) -> None:
        if not execution_id:
            raise ErrIDRequired
        self._workflow = workflow
        self.id = execution_id

    def info(self) -> WorkflowExecutionEnvelope:
        return self._workflow.service().get_run(self._workflow.id, self.id)

    def refresh(self) -> WorkflowExecutionEnvelope:
        return self._workflow.service().refresh_run(self._workflow.id, self.id)

    def pause(self) -> WorkflowExecutionEnvelope:
        return self._workflow.service().pause_run(self._workflow.id, self.id)

    def resume(self) -> WorkflowExecutionEnvelope:
        return self._workflow.service().resume_run(self._workflow.id, self.id)

    def result(self) -> WorkflowExecutionResultEnvelope:
        return self._workflow.service().get_run_result(self._workflow.id, self.id)

    def import_context(self) -> WorkflowImportContextEnvelope:
        return self._workflow.service().get_run_import_context(self._workflow.id, self.id)

    def import_files(self, *opts: Callable[["QueryOptions"], None]) -> WorkflowImportFileListEnvelope:
        return self._workflow.service().list_run_import_files(self._workflow.id, self.id, *opts)

    def node(self, node_key: str) -> WorkflowExecutionNodeDetailEnvelope:
        return self._workflow.service().get_run_node(self._workflow.id, self.id, node_key)

    def node_handle(self, node_key: str) -> "WorkflowRunNodeHandle":
        if not node_key:
            raise ErrIDRequired
        return WorkflowRunNodeHandle(self, node_key)

    def rerun_branches(self) -> WorkflowRerunBranchListEnvelope:
        return self._workflow.service().list_run_rerun_branches(self._workflow.id, self.id)

    def rerun(self, rerun_id: str) -> "WorkflowRunRerunHandle":
        if not rerun_id:
            raise ErrIDRequired
        return WorkflowRunRerunHandle(self, rerun_id)

    def retry(self, *opts: Callable[["WorkflowRerunOptions"], None]) -> WorkflowRunEnvelope:
        return self._workflow.service().retry_run(self._workflow.id, self.id, *opts)

    def cancel(self, *opts: Callable[["WorkflowCancelOptions"], None]) -> WorkflowExecutionEnvelope:
        return self._workflow.service().cancel_run(self._workflow.id, self.id, *opts)

    def delete(self) -> WorkflowDeleteEnvelope:
        return self._workflow.service().delete_run(self._workflow.id, self.id)

class WorkflowRunNodeHandle:
    def __init__(self, run: WorkflowRunHandle, node_key: str) -> None:
        if not node_key:
            raise ErrIDRequired
        self._run = run
        self.key = node_key

    def info(self) -> WorkflowExecutionNodeDetailEnvelope:
        return self._run._workflow.service().get_run_node(self._run._workflow.id, self._run.id, self.key)

    def rerun_plan(self, *opts: Callable[["QueryOptions"], None]) -> WorkflowRerunPlanEnvelope:
        return self._run._workflow.service().get_run_node_rerun_plan(self._run._workflow.id, self._run.id, self.key, *opts)

    def create_rerun(
        self,
        mode: str,
        source_node_execution_id: str,
        *opts: Callable[["WorkflowRerunOptions"], None],
    ) -> WorkflowRerunEnvelope:
        return self._run._workflow.service().create_run_node_rerun(
            self._run._workflow.id,
            self._run.id,
            self.key,
            mode,
            source_node_execution_id,
            *opts,
        )

class WorkflowRunRerunHandle:
    def __init__(self, run: WorkflowRunHandle, rerun_id: str) -> None:
        if not rerun_id:
            raise ErrIDRequired
        self._run = run
        self.id = rerun_id

    def info(self) -> WorkflowRerunEnvelope:
        return self._run._workflow.service().get_run_rerun(self._run._workflow.id, self._run.id, self.id)

    def cancel(self, *opts: Callable[["WorkflowCancelOptions"], None]) -> WorkflowRerunEnvelope:
        return self._run._workflow.service().cancel_run_rerun(self._run._workflow.id, self._run.id, self.id, *opts)

class CustomOperatorMCPPublicationRetired:
    """Floor marker for retired custom operator MCP publication Storybook consumption.

    The Product custom-operator mcp-publish/mcp-unpublish/mcp-status routes are
    removed; workspace MCP tools are published-and-enabled API services. This
    export exists so coverage-lock floor + public_export evidence can remain
    without restoring the retired SDK methods.
    """

    retired = True
    reason = "custom_operator_mcp_publication_api_removed"


class ComputeMetricsRetired:
    """Floor marker for retired compute.metrics Storybook consumption (#17177).

    The Product metrics HTTP/SDK route is removed. This export exists so
    coverage-lock floor + public_export evidence can remain without restoring
    Client.compute(...).metrics.
    """

    retired = True
    reason = "product_metrics_api_removed"


class CustomOperatorHandle:
    def __init__(self, workspace: WorkspaceHandle, operator_id: str) -> None:
        if not operator_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = operator_id

    def service(self) -> "WorkflowService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.workflows()

    def info(self) -> CustomOperator:
        return self.service().get_custom_operator(self.id)

    def code(self) -> CustomOperatorCodeEnvelope:
        return self.service().get_custom_operator_code(self.id)

    def test(self, input: dict[str, Any], wait_timeout_seconds: Optional[int] = None) -> CustomOperatorTestEnvelope:
        return self.service().test_custom_operator(self.id, CustomOperatorTestInput(input, wait_timeout_seconds))

    def test_with_input(self, input: "CustomOperatorTestInput") -> CustomOperatorTestEnvelope:
        input.validate()
        return self.service().test_custom_operator(self.id, input)

    def update(self, *opts: Callable[["CustomOperatorUpdateOptions"], None]) -> CustomOperator:
        return self.service().update_custom_operator(self.id, *opts)

    def enable(self) -> CustomOperator:
        return self.service().enable_custom_operator(self.id)

    def disable(self) -> CustomOperator:
        return self.service().disable_custom_operator(self.id)

    def delete(self) -> WorkflowDeleteEnvelope:
        return self.service().delete_custom_operator(self.id)

class WorkitemAPIServiceHandle:
    def __init__(self, workspace: WorkspaceHandle, node_id: str, version: str) -> None:
        if not node_id:
            raise ErrIDRequired
        if not version:
            raise ErrVersionRequired
        self._workspace = workspace
        self.node_id = node_id
        self.version = version

    def service(self) -> "WorkflowService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.workflows()

    def info(self) -> WorkitemAPIServiceEnvelope:
        return self.service().get_workitem_api_service(self.node_id, self.version)

    def publish(self, spec: "WorkitemAPIServicePublishSpec") -> WorkitemAPIServiceEnvelope:
        return self.service().publish_workitem_api_service(self.node_id, spec)

    def enable(self) -> WorkitemAPIServiceEnvelope:
        return self.service().enable_workitem_api_service(self.node_id, self.version)

    def disable(self) -> WorkitemAPIServiceEnvelope:
        return self.service().disable_workitem_api_service(self.node_id, self.version)

    def invoke(self, spec: "WorkitemAPIServiceInvokeSpec") -> WorkitemAPIServiceInvokeEnvelope:
        return self.service().invoke_workitem_api_service(self.node_id, spec)

class CustomOperatorSpec:
    def __init__(
        self,
        name: str,
        identifier: str,
        description: str,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        *,
        node_id: Optional[str] = None,
        kind: Optional[str] = None,
        language: Optional[str] = None,
        handler: Optional[str] = None,
        version: Optional[str] = None,
        isolation_level: Optional[str] = None,
        enabled: Optional[bool] = None,
        code: Optional[str] = None,
        source_file_id: Optional[str] = None,
        base_node_id: Optional[str] = None,
        base_node_version: Optional[str] = None,
        binding_config: Any = None,
        catalog_id: Optional[int] = None,
        database_id: Optional[int] = None,
    ) -> None:
        self.name = name
        self.identifier = identifier
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.node_id = node_id
        self.kind = kind
        self.language = language
        self.handler = handler
        self.version = version
        self.isolation_level = isolation_level
        self.enabled = enabled
        self.code = code
        self.source_file_id = source_file_id
        self.base_node_id = base_node_id
        self.base_node_version = base_node_version
        self.binding_config = binding_config
        self.catalog_id = catalog_id
        self.database_id = database_id

    def validate(self) -> None:
        if not self.name:
            raise ErrNameRequired
        if not self.identifier:
            raise ErrIdentifierRequired
        if not self.description:
            raise ErrDescriptionRequired
        if self.input_schema is None:
            raise ErrInputSchemaRequired
        if self.output_schema is None:
            raise ErrOutputSchemaRequired

    def body(self, opts: tuple[Callable[["CustomOperatorOptions"], None], ...]) -> dict[str, Any]:
        self.validate()
        return _custom_operator_body(self, opts)

class CustomOperatorTestInput:
    def __init__(self, input: dict[str, Any], wait_timeout_seconds: Optional[int] = None) -> None:
        self.input = input
        self.wait_timeout_seconds = wait_timeout_seconds

    def validate(self) -> None:
        if self.input is None:
            raise ErrPayloadRequired

class WorkitemAPIServicePublishSpec:
    def __init__(
        self,
        version: str = "",
        compute_resource_id: str = "",
        timeout_seconds: int = 0,
        max_concurrency: int = 0,
        rate_limit_per_min: int = 0,
        service_name: str = "",
        ui_resource: Optional[dict[str, Any]] = None,
    ) -> None:
        self.version = version
        self.service_name = service_name
        self.compute_resource_id = compute_resource_id
        self.timeout_seconds = timeout_seconds
        self.max_concurrency = max_concurrency
        self.rate_limit_per_min = rate_limit_per_min
        self.ui_resource = ui_resource

    def validate(self) -> None:
        if not self.version:
            raise ErrVersionRequired

    def body(self) -> dict[str, Any]:
        self.validate()
        body: dict[str, Any] = {"version": self.version}
        if self.service_name:
            body["service_name"] = self.service_name
        if self.compute_resource_id:
            body["compute_resource_id"] = self.compute_resource_id
        if self.timeout_seconds:
            body["timeout_seconds"] = self.timeout_seconds
        if self.max_concurrency:
            body["max_concurrency"] = self.max_concurrency
        if self.rate_limit_per_min:
            body["rate_limit_per_min"] = self.rate_limit_per_min
        if self.ui_resource is not None:
            body["ui_resource"] = self.ui_resource
        return body

def _workitem_api_service_invoke_validation_error(sentinel: Error, message: str, field: str, reason: str, expected: str = "") -> Error:
    details = {"field": field, "reason": reason}
    if expected:
        details["expected"] = expected
    return Error(sentinel.code, message, details=details)

class WorkitemAPIServiceInvokeSpec:
    def __init__(self, service_name: str, type: str, version: str, payload: Any) -> None:
        self.service_name = service_name
        self.type = type
        self.version = version
        self.payload = payload

    def validate(self) -> None:
        if not self.service_name:
            raise _workitem_api_service_invoke_validation_error(
                ErrServiceNameRequired,
                "service_name is required for WorkItem API service invocation; use the published service.service_name",
                "service_name",
                "required",
            )
        if not self.type:
            raise _workitem_api_service_invoke_validation_error(
                ErrTypeRequired,
                'type is required for WorkItem API service invocation; use "operator"',
                "type",
                "required",
                "operator",
            )
        if not self.version:
            raise _workitem_api_service_invoke_validation_error(
                ErrVersionRequired,
                "version is required for WorkItem API service invocation; use the published service.version",
                "version",
                "required",
            )
        if self.payload is None:
            raise _workitem_api_service_invoke_validation_error(
                ErrPayloadRequired,
                "payload is required for WorkItem API service invocation; provide the business input object, not an input wrapper",
                "payload",
                "required",
            )

    def body(self) -> dict[str, Any]:
        self.validate()
        return {
            "service_name": self.service_name,
            "type": self.type,
            "version": self.version,
            "payload": self.payload,
        }

_JSON_VALUE_UNSET = object()

class DynamicServiceInvokeSpec:
    def __init__(
        self,
        service_name: str,
        payload: object,
        version_number: int = 0,
        *,
        files: Optional[list[tuple[str, str, bytes]]] = None,
        version: str = "",
        trace: Any = _JSON_VALUE_UNSET,
    ) -> None:
        self.files = files or []
        self.service_name = service_name
        self.payload = payload
        self.version_number = version_number
        self.version = version
        self.trace = trace

    def validate(self) -> None:
        if not self.service_name:
            raise ErrServiceNameRequired
        if self.payload is None:
            raise ErrPayloadRequired

    def body(self) -> dict[str, object]:
        self.validate()
        body: dict[str, object] = {
            "service_name": self.service_name,
            "payload": self.payload,
        }
        if self.version:
            body["version"] = self.version
        if self.version_number:
            body["version_number"] = self.version_number
        if self.trace is not _JSON_VALUE_UNSET:
            body["trace"] = self.trace
        return body

class DynamicServiceInvokeResult:
    def __init__(self, value: object) -> None:
        if not isinstance(value, dict):
            raise Error("ErrResponseInvalid", "dynamic service invoke response must be an object")
        self.case_id = value.get("case_id")
        self.run_id = value.get("run_id")
        self.status = value.get("status")
        self.result = value.get("result")
        self.error = value.get("error")
        self.result_url = value.get("result_url")

class TableColumn:
    def __init__(
        self,
        name: str,
        type: str,
        *,
        is_pk: Optional[bool] = None,
        comment: str = "",
        precision: Optional[list[int]] = None,
        default: Optional[str] = None,
    ) -> None:
        self.name = name
        self.type = type
        self.is_pk = is_pk
        self.comment = comment
        self.precision = precision
        self.default = default

    def validate(self) -> None:
        if not self.name:
            raise ErrNameRequired
        if not self.type:
            raise ErrTypeRequired

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        body: dict[str, Any] = {"name": self.name, "type": self.type}
        if self.is_pk is not None:
            body["is_pk"] = self.is_pk
        if self.comment:
            body["comment"] = self.comment
        if self.precision:
            body["precision"] = self.precision
        if self.default is not None:
            body["default"] = self.default
        return body

class WorkflowTemplateHandle:
    def __init__(self, workspace: WorkspaceHandle, template_id: str) -> None:
        if not template_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = template_id

    def service(self) -> "WorkflowService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.workflows()

    def info(self) -> WorkflowTemplate:
        return self.service().get_workflow_template(self.id)

    def update(self, name: str, dsl_yaml: str, *opts: Callable[["WorkflowTemplateOptions"], None]) -> WorkflowTemplate:
        return self.service().update_workflow_template(self.id, name, dsl_yaml, *opts)

    def update_mowl(self, name: str, workflow: dict[str, Any], *opts: Callable[["WorkflowTemplateOptions"], None]) -> WorkflowTemplate:
        """Replace this template's MOWL publication graph."""
        return self.service().update_mowl_workflow_template(self.id, name, workflow, *opts)

    def delete(self) -> WorkflowTemplateDeleteEnvelope:
        return self.service().delete_workflow_template(self.id)

class SemanticModelHandle:
    def __init__(self, workspace: WorkspaceHandle, model_id: str) -> None:
        if not model_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = model_id

    def service(self) -> "KnowledgeService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.knowledge()

    def info(self) -> SemanticModelInfo:
        return self.service().get(self.id)

    def update(self, name: str, *opts: Callable[["SemanticModelOptions"], None]) -> SemanticMutationResult:
        """Update this knowledge base; name must equal its existing immutable name."""
        return self.service().update(self.id, name, *opts)

    def delete(self) -> SemanticMutationResult:
        return self.service().delete(self.id)

    def entries(self, *opts: Callable[["QueryOptions"], None]) -> SemanticEntryListResult:
        return self.service().list_entries(self.id, *opts)

    def create_entry(self, entry: "SemanticEntryInput") -> tuple["SemanticEntryHandle", SemanticEntry]:
        entry.validate()
        result = self.service().create_entry(self.id, entry)
        return SemanticEntryHandle(self, _created_int_path_id(result.id, "semantic entry")), result

    def entry(self, entry_id: str) -> "SemanticEntryHandle":
        if not entry_id:
            raise ErrIDRequired
        return SemanticEntryHandle(self, entry_id)

    def import_entries(self, entries: list["SemanticEntryInput"]) -> SemanticImportResult:
        if not entries:
            raise ErrEntriesRequired
        for entry in entries:
            entry.validate()
        return self.service().import_entries(self.id, entries)

    def export(self) -> SemanticExportResult:
        return self.service().export(self.id)

    def validate(self) -> SemanticValidateResult:
        return self.service().validate(self.id)

class SemanticEntryHandle:
    def __init__(self, model: SemanticModelHandle, entry_id: str) -> None:
        if not entry_id:
            raise ErrIDRequired
        self._model = model
        self.id = entry_id

    def model(self) -> SemanticModelHandle:
        return self._model

    def update(self, entry: "SemanticEntryInput") -> SemanticMutationResult:
        entry.validate()
        return self._model.service().update_entry(self._model.id, self.id, entry)

    def delete(self) -> SemanticMutationResult:
        return self._model.service().delete_entry(self._model.id, self.id)

class ConnectorHandle:
    def __init__(self, workspace: WorkspaceHandle, connector_id: str) -> None:
        if not connector_id:
            raise ErrConnectorIDRequired
        self._workspace = workspace
        self.id = connector_id

    def service(self) -> "ConnectorService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.connectors()

    def info(self) -> Connector:
        return self.service().get(self.id)

    def update(self, *opts: Callable[["ConnectorUpdateOptions"], None]) -> None:
        self.service().update(self.id, *opts)

    def delete(self) -> None:
        self.service().delete(self.id)

    def preview_file(self, uri: str, *opts: Callable[["ConnectorPreviewOptions"], None]) -> PreviewFileResult:
        return self.service().preview_file(self.id, uri, *opts)

    def file(self, conn_file_id: str) -> "ConnectorFileHandle":
        if not conn_file_id:
            raise ErrConnectorFileIDRequired
        return ConnectorFileHandle(self._workspace, conn_file_id, self)

    def source_databases(self) -> DBListDatabasesResult:
        return self.service().db_list_databases(self.id)

    def source_schemas(self, database: str) -> DBListSchemasResult:
        return self.service().db_list_schemas(self.id, database)

    def source_tables(self, database: str, *opts: Callable[["ConnectorDBOptions"], None]) -> DBListTablesResult:
        return self.service().db_list_tables(self.id, database, *opts)

    def source_schema(self, database: str, table: str, *opts: Callable[["ConnectorDBOptions"], None]) -> DBSourceSchemaResult:
        return self.service().db_source_schema(self.id, database, table, *opts)

    def mo_databases(self) -> MODatabaseListResult:
        return self.service().mo_database_list(self.id)

    def mo_database_tables(self, database: str) -> MODatabaseTableListResult:
        return self.service().mo_database_table_list(self.id, database)

    def check_mo_table_name(self, database: str, table: str) -> MOCheckTableNameResult:
        return self.service().mo_check_table_name(self.id, database, table)

    def mo_column_mapping(self, database: str, table: str, export_columns: dict[str, str]) -> MOColumnMappingResult:
        return self.service().mo_column_mapping(self.id, database, table, export_columns)

    def create_import_task(
        self,
        config_type: int,
        source_config: dict[str, Any],
        *opts: Callable[["CreateImportTaskOptions"], None],
    ) -> tuple["ImportTaskHandle", ImportTaskCreateResult]:
        result = self.service().create_task(ImportTaskCreateSpec(self.id, config_type, source_config), *opts)
        return ImportTaskHandle(self, result.task_id), result

    def create_file_import_task(
        self,
        spec: "FileImportTaskSpec",
    ) -> tuple["ImportTaskHandle", ImportTaskCreateResult]:
        spec.validate()
        source_config = spec.source_config()
        opts: list[Callable[[CreateImportTaskOptions], None]] = []
        if spec.name:
            opts.append(with_import_task_name(spec.name))
        if spec.volume_id:
            opts.append(with_import_task_volume_id(spec.volume_id))
        result = self.service().create_task(ImportTaskCreateSpec(self.id, spec.config_type, source_config, task_id=spec.task_id), *opts)
        return ImportTaskHandle(self, result.task_id), result

    def import_task(self, task_id: str) -> "ImportTaskHandle":
        if not task_id:
            raise ErrTaskIDRequired
        return ImportTaskHandle(self, task_id)

    def create_export_task(
        self,
        task_name: str,
        connector_name: str,
        export_type: int,
        config: Optional[dict[str, Any]],
        files: list[dict[str, Any]],
    ) -> tuple["ExportTaskHandle", ExportTask]:
        result = self.service().create_export_task(ExportTaskCreateSpec(task_name, self.id, connector_name, export_type, config, files))
        return ExportTaskHandle(self, result.id), result

    def create_export_task_from_spec(
        self,
        spec: "ExportTaskSpec",
    ) -> tuple["ExportTaskHandle", ExportTask]:
        spec.validate()
        result = self.service().create_export_task(
            ExportTaskCreateSpec(spec.name, self.id, spec.connector_name, spec.type, spec.config.map(), [file.param() for file in spec.files], creator=spec.creator)
        )
        return ExportTaskHandle(self, result.id), result

    def export_task(self, task_id: str) -> "ExportTaskHandle":
        if not task_id:
            raise ErrTaskIDRequired
        return ExportTaskHandle(self, task_id)

class ConnectorFileHandle:
    def __init__(
        self,
        workspace: WorkspaceHandle,
        conn_file_id: str,
        connector: Optional[ConnectorHandle] = None,
    ) -> None:
        if not conn_file_id:
            raise ErrConnectorFileIDRequired
        self._workspace = workspace
        self._connector = connector
        self.id = conn_file_id

    def service(self) -> "ConnectorService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.connectors()

    def preview(self, *opts: Callable[["ConnectorPreviewOptions"], None]) -> PreviewFileResult:
        scoped = (with_connector_preview_conn_file_id(self.id), *opts)
        if self._connector is not None:
            return self._connector.preview_file("", *scoped)
        return self.service().preview_file("", "", *scoped)

    def download(self) -> FileDownloadResult:
        return self.service().file_download(self.id)

    def stream(self) -> StreamResponse:
        return self.service().file_stream(self.id)

    def delete(self) -> None:
        self.service().file_delete(self.id)

class FileImportTaskSpec:
    def __init__(
        self,
        config_type: int,
        uris: list[str],
        load_mode_config: dict[str, Any],
        file_filter_config: dict[str, Any],
        *,
        name: str = "",
        volume_id: str = "",
        unzip_keep_structure: Optional[bool] = None,
        dedup: Optional[dict[str, Any]] = None,
        table_config: Any = None,
        file_storage_mode: str = "",
        task_id: str = "",
    ) -> None:
        self.task_id = task_id
        self.config_type = config_type
        self.name = name
        self.volume_id = volume_id
        self.uris = uris
        self.load_mode_config = load_mode_config
        self.file_filter_config = file_filter_config
        self.unzip_keep_structure = unzip_keep_structure
        self.dedup = dedup
        self.table_config = table_config
        # copy (default) duplicates source content into MOI storage; reference
        # (issue #19365) points the Catalog file at the source object.
        self.file_storage_mode = file_storage_mode

    def source_config(self) -> dict[str, Any]:
        if not self.uris:
            raise ErrURLRequired
        if self.load_mode_config is None:
            raise ErrModeRequired
        if self.file_filter_config is None:
            raise ErrSourceConfigRequired
        common: dict[str, Any] = {
            "uris": self.uris,
            "load_mode_config": self.load_mode_config,
            "file_filter_config": self.file_filter_config,
        }
        if self.unzip_keep_structure is not None:
            common["unzip_keep_structure"] = self.unzip_keep_structure
        if self.dedup is not None:
            common["dedup"] = self.dedup
        if self.table_config is not None:
            common["table_config"] = self.table_config
        if self.file_storage_mode:
            common["file_storage_mode"] = self.file_storage_mode
        return {"common_file_task_config": common}

    def validate(self) -> None:
        if not self.config_type:
            raise ErrTypeRequired
        self.source_config()

class ImportTaskCreateSpec:
    def __init__(self, source_connector_id: str, config_type: int, source_config: Optional[dict[str, Any]] = None, *, structured_load_config: Optional[dict[str, Any]] = None, task_id: str = "") -> None:
        self.task_id = task_id
        self.source_connector_id = source_connector_id
        self.config_type = config_type
        self.source_config = source_config
        self.structured_load_config = structured_load_config

    def body(self, opts: tuple[Callable[["CreateImportTaskOptions"], None], ...]) -> dict[str, Any]:
        if not self.source_connector_id:
            raise ErrConnectorIDRequired
        if self.source_config is None and self.structured_load_config is None:
            raise ErrSourceConfigRequired
        options = CreateImportTaskOptions()
        for opt in opts:
            opt(options)
        body: dict[str, Any] = {
            "source_connector_id": self.source_connector_id,
            "config_type": self.config_type,
        }
        if self.task_id:
            body["task_id"] = self.task_id
        if self.source_config is not None:
            body["source_config"] = self.source_config
        if self.structured_load_config is not None:
            body["structured_load_config"] = self.structured_load_config
        if options.name is not None:
            body["name"] = options.name
        if options.volume_id is not None:
            body["volume_id"] = options.volume_id
        return body

class ImportTaskUpdateSpec:
    def __init__(
        self,
        load_mode_config: Optional[dict[str, Any]] = None,
        *,
        name: str = "",
        file_filter_config: Optional[dict[str, Any]] = None,
        uris: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.load_mode_config = load_mode_config
        self.file_filter_config = file_filter_config
        self.uris = uris

    def updates(self) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        if self.name:
            updates["name"] = self.name
        if self.load_mode_config is not None:
            updates["load_mode_config"] = self.load_mode_config
        if self.file_filter_config is not None:
            updates["file_filter_config"] = self.file_filter_config
        if self.uris is not None:
            if not self.uris:
                raise ErrURLRequired
            updates["uris"] = self.uris
        if not updates:
            raise ErrSourceConfigRequired
        return updates

class ExportTaskCreateSpec:
    def __init__(
        self,
        task_name: str,
        connector_id: str,
        connector_name: str,
        export_type: int,
        config: Optional[dict[str, Any]],
        files: list[dict[str, Any]],
        *,
        creator: str = "",
    ) -> None:
        self.task_name = task_name
        self.connector_id = connector_id
        self.connector_name = connector_name
        self.export_type = export_type
        self.config = config
        self.files = files
        self.creator = creator

    def body(self) -> dict[str, Any]:
        if not self.task_name:
            raise ErrTaskNameRequired
        if not self.connector_id:
            raise ErrConnectorIDRequired
        body = {
            "task_name": self.task_name,
            "connector_id": self.connector_id,
            "connector_name": self.connector_name,
            "type": self.export_type,
            "config": self.config,
            "files": self.files,
        }
        if self.creator:
            body["creator"] = self.creator
        return body

class ExportTaskConfig:
    def __init__(
        self,
        *,
        merge_title_to_text: Optional[bool] = None,
        dify_config: Optional[dict[str, Any]] = None,
        mo_config: Optional[dict[str, Any]] = None,
        s3_config: Optional[dict[str, Any]] = None,
    ) -> None:
        self.merge_title_to_text = merge_title_to_text
        self.dify_config = dify_config
        self.mo_config = mo_config
        self.s3_config = s3_config

    def map(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if self.merge_title_to_text is not None:
            body["merge_title_to_text"] = self.merge_title_to_text
        if self.dify_config is not None:
            body["dify_config"] = self.dify_config
        if self.mo_config is not None:
            body["mo_config"] = self.mo_config
        if self.s3_config is not None:
            body["s3_config"] = self.s3_config
        return body

    def validate(self) -> None:
        if self.merge_title_to_text is None and self.dify_config is None and self.mo_config is None and self.s3_config is None:
            raise ErrConfigRequired

class ExportTaskFile:
    def __init__(
        self,
        file_id: str,
        full_path: list[str],
        *,
        is_raw: Optional[bool] = None,
        ref_file_id: str = "",
        parsed_file_id: str = "",
    ) -> None:
        self.file_id = file_id
        self.full_path = full_path
        self.is_raw = is_raw
        self.ref_file_id = ref_file_id
        self.parsed_file_id = parsed_file_id

    def param(self) -> dict[str, Any]:
        if not self.file_id:
            raise ErrFileIDRequired
        if not self.full_path:
            raise ErrPathInvalid
        body: dict[str, Any] = {
            "file_id": self.file_id,
            "full_path": self.full_path,
        }
        if self.is_raw is not None:
            body["is_raw"] = self.is_raw
        if self.ref_file_id:
            body["ref_file_id"] = self.ref_file_id
        if self.parsed_file_id:
            body["parsed_file_id"] = self.parsed_file_id
        return body

class ExportTaskSpec:
    def __init__(
        self,
        name: str,
        connector_name: str,
        type: int,
        config: ExportTaskConfig,
        files: list[ExportTaskFile],
        *,
        creator: str = "",
    ) -> None:
        self.name = name
        self.connector_name = connector_name
        self.type = type
        self.config = config
        self.files = files
        self.creator = creator

    def validate(self) -> None:
        if not self.name:
            raise ErrTaskNameRequired
        if not self.connector_name:
            raise ErrConnectorIDRequired
        if not self.type:
            raise ErrTypeRequired
        self.config.validate()
        if not self.files:
            raise ErrFileIDsRequired
        for file in self.files:
            file.param()

class ImportTaskHandle:
    def __init__(self, connector: ConnectorHandle, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector = connector
        self.id = task_id

    def info(self) -> ImportTaskInfoResult:
        return self._connector.service().get_task(self.id)

    def update(self, spec: ImportTaskUpdateSpec) -> None:
        self._connector.service().update_task_from_spec(self.id, spec)

    def update_config(self, spec: ImportTaskUpdateSpec) -> None:
        self._connector.service().update_task_from_spec(self.id, spec)

    def pause(self) -> None:
        self._connector.service().pause_task(self.id)

    def resume(self) -> None:
        self._connector.service().resume_task(self.id)

    def runs(self) -> ImportTaskRunListResult:
        return self._connector.service().task_runs(self.id)

    def files(self, *opts: Callable[["QueryOptions"], None]) -> ImportTaskFileListResult:
        return self._connector.service().task_files(with_query_param("task_id", self.id), *opts)

    def retry_files(self, *ids: str) -> None:
        self._connector.service().retry_task_files(self.id, *ids)

    def delete(self) -> None:
        self._connector.service().delete_task(self.id)

class ExportTaskHandle:
    def __init__(self, connector: ConnectorHandle, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector = connector
        self.id = task_id

    def info(self) -> ExportTaskInfo:
        return self._connector.service().export_task_info(self.id)

    def files(self, *opts: Callable[["ExportTaskFilesOptions"], None]) -> ExportTaskFilesResult:
        return self._connector.service().export_task_files(self.id, *opts)

    def retry(self, *file_ids: str) -> None:
        self._connector.service().retry_export_task(self.id, *file_ids)

    def state(self) -> ExportTaskStateResult:
        return self._connector.service().export_task_state(self.id)

    def delete(self) -> None:
        self._connector.service().delete_export_task(self.id)

class ModelProviderHandle:
    def __init__(self, workspace: WorkspaceHandle, service: "ProviderBackendService", kind: str) -> None:
        self._workspace = workspace
        self._service = service
        self.kind = kind

    def service(self) -> "ProviderBackendService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._service

    def backends(self) -> ProviderBackendListResult:
        return self._service.list()

    def create_backend(
        self,
        name: str,
        *opts: Callable[["ProviderBackendOptions"], None],
    ) -> tuple["ProviderBackendHandle", ProviderBackend]:
        if not name:
            raise ErrNameRequired
        result = self._service.create(name, *opts)
        if not result.id:
            raise Error("ErrResponseInvalid", "provider backend data missing id")
        return ProviderBackendHandle(self, str(result.id)), result

    def backend(self, backend_id: str) -> "ProviderBackendHandle":
        if not backend_id:
            raise ErrIDRequired
        return ProviderBackendHandle(self, backend_id)

    def router(self) -> "ProviderRouterHandle":
        return ProviderRouterHandle(self)

    def probe_address(self, address: str, *opts: Callable[["ProviderBackendOptions"], None]) -> ProviderProbeModelsResult:
        if self.kind == "llm":
            return self._workspace.models().probe_llm_models(address, *opts)
        if self.kind == "embedding":
            return self._workspace.models().probe_embedding_models(address, *opts)
        raise Error("ErrUnsupportedOperation", f"provider kind does not support address probe: {self.kind}")

class ProviderBackendHandle:
    def __init__(self, provider: ModelProviderHandle, backend_id: str) -> None:
        if not backend_id:
            raise ErrIDRequired
        self._provider = provider
        self.id = backend_id

    def provider(self) -> ModelProviderHandle:
        return self._provider

    def service(self) -> "ProviderBackendService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._provider.service()

    def info(self) -> ProviderBackend:
        return self.service().get(self.id)

    def update(self, *opts: Callable[["ProviderBackendUpdateOptions"], None]) -> ProviderBackend:
        return self.service().update(self.id, *opts)

    def delete(self) -> ProviderMutationResult:
        return self.service().delete(self.id)

    def create_endpoint(self, address: str) -> ProviderEndpoint:
        if not address:
            raise ErrAddressRequired
        return self.service().create_endpoint(self.id, address)

    def endpoints(self) -> ProviderEndpointListResult:
        return self.service().list_endpoints(self.id)

    def set_endpoint_status(self, endpoint_id: str, status: str) -> ProviderMutationResult:
        if not endpoint_id:
            raise ErrIDRequired
        if not status:
            raise ErrStatusRequired
        return self.service().set_endpoint_status(self.id, endpoint_id, status)

    def probe_models(self, *opts: Callable[["ProviderBackendOptions"], None]) -> ProviderProbeModelsResult:
        return self.service().probe_backend_models(self.id, *opts)

class ProviderRouterHandle:
    def __init__(self, provider: ModelProviderHandle) -> None:
        self._provider = provider

    def provider(self) -> ModelProviderHandle:
        return self._provider

    def info(self) -> ProviderRouterConfig:
        return self._provider.service().router()

    def update(self, *opts: Callable[["RouterOptions"], None]) -> ProviderRouterConfig:
        return self._provider.service().update_router(*opts)



class ConsumerMemoryFulltextSearchInput:
    """Keyword-retrieval input for one consumer handle; subject scope comes from the handle."""

    def __init__(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[list[str]] = None,
        trust_tier: Optional[str] = None,
        branch: Optional[str] = None,
        extra_metadata_filter: Optional[dict[str, Any]] = None,
    ) -> None:
        self.query = query
        self.top_k = top_k
        self.session_id = session_id
        self.memory_types = memory_types
        self.trust_tier = trust_tier
        self.branch = branch
        self.extra_metadata_filter = extra_metadata_filter

    def validate(self) -> None:
        if not self.query or not self.query.strip():
            raise ErrQueryRequired
        if self.top_k is not None and not 0 <= self.top_k <= 100:
            raise Error("ErrInvalidArgument", "top_k must be between 0 and 100")
        _validate_memory_metadata_filter(self.extra_metadata_filter)


class ConsumerMemoryStructuredQueryInput:
    """Exact structured-query input for one consumer handle; subject scope comes from the handle."""

    def __init__(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[list[str]] = None,
        trust_tier: Optional[str] = None,
        branch: Optional[str] = None,
        extra_metadata_filter: Optional[dict[str, Any]] = None,
    ) -> None:
        self.limit = limit
        self.cursor = cursor
        self.session_id = session_id
        self.memory_types = memory_types
        self.trust_tier = trust_tier
        self.branch = branch
        self.extra_metadata_filter = extra_metadata_filter

    def validate(self) -> None:
        if self.limit is not None and not 0 <= self.limit <= 500:
            raise Error("ErrInvalidArgument", "limit must be between 0 and 500")
        _validate_memory_metadata_filter(self.extra_metadata_filter)


class ConsumerMemoryHandle:
    """Typed handle for a legacy server's consumer memories and rendered profile.

    Deprecated for current MOI: its public API does not serve these routes.
    """

    def __init__(self, workspace: WorkspaceHandle, subject_id: str) -> None:
        if not subject_id:
            raise ErrSubjectRequired
        self._workspace = workspace
        self.id = subject_id

    def service(self) -> "MemoryService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.memory()

    def retrieve(self, query: str) -> MemoryListResult:
        return self.service().retrieve(query, self.id)

    def fulltext_search(self, input: ConsumerMemoryFulltextSearchInput) -> MemoryListResult:
        input.validate()
        return self.service().fulltext_search(
            input.query,
            self.id,
            top_k=input.top_k,
            session_id=input.session_id,
            memory_types=input.memory_types,
            trust_tier=input.trust_tier,
            branch=input.branch,
            extra_metadata_filter=input.extra_metadata_filter,
        )

    def query(self, input: ConsumerMemoryStructuredQueryInput) -> MemoryListResult:
        input.validate()
        return self.service().query(
            self.id,
            limit=input.limit,
            cursor=input.cursor,
            session_id=input.session_id,
            memory_types=input.memory_types,
            trust_tier=input.trust_tier,
            branch=input.branch,
            extra_metadata_filter=input.extra_metadata_filter,
        )

    def render_profile(self) -> ConsumerProfileRenderResult:
        return self.service().render_profile(self.id)


class ComputeResourceHandle:
    def __init__(self, workspace: WorkspaceHandle, resource_id: str) -> None:
        if not resource_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = resource_id

    def service(self) -> "ComputeService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.compute()

    def info(self) -> ComputeResource:
        return self.service().get(self.id)

    def runtime(self) -> list[ComputeWorkerRuntime]:
        return self.service().runtime(compute_resource_id=self.id)

    def update(self, *opts: Callable[["ComputeUpdateOptions"], None]) -> ComputeResource:
        return self.service().update(self.id, *opts)

    def adopt_legacy_ownership(self) -> ComputeResourceOwnership:
        """Explicitly records canonical Ownership through the audited repair API."""
        return self.service().adopt_legacy_ownership(self.id)

    def preflight_delete(self) -> ComputeDeletePreflightResult:
        return self.service().preflight_delete(self.id)

    def delete(self, *opts: Callable[["QueryOptions"], None]) -> None:
        self.service().delete(self.id, *opts)

    def suspend(self) -> ComputeResource:
        return self.service().suspend(self.id)

    def resume(self) -> ComputeResource:
        return self.service().resume(self.id)

    def retry(self) -> ComputeResource:
        return self.service().retry(self.id)

class DataSharePublishHandle:
    def __init__(self, workspace: WorkspaceHandle, publish_id: str) -> None:
        if not publish_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = publish_id

    def service(self) -> "DataShareService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.data_share()

    def update(self, *opts: Callable[["DataSharePublishUpdateOptions"], None]) -> DataSharePublish:
        return self.service().update_publish(self.id, *opts)

    def delete(self) -> None:
        self.service().delete_publish(self.id)

class DataShareSubscriptionHandle:
    def __init__(self, workspace: WorkspaceHandle, subscription_id: str) -> None:
        if not subscription_id:
            raise ErrIDRequired
        self._workspace = workspace
        self.id = subscription_id

    def service(self) -> "DataShareService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.data_share()

    def subscribe(self, sub_name: str) -> DataShareSubscription:
        return self.service().subscribe(self.id, sub_name)

    def unsubscribe(self) -> None:
        self.service().unsubscribe(self.id)

class AgentHandle:
    def __init__(self, workspace: WorkspaceHandle, selector: "AgentSelector") -> None:
        if not selector.agent_code and not selector.agent_id:
            raise ErrAgentRequired
        self._workspace = workspace
        self.selector = selector

    def service(self) -> "AgentService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.agents()

    def a2a(self, request: "A2ARequest") -> AgentA2AResult:
        """Explicit protocol-control escape hatch; prefer typed A2A helpers for promoted workflows."""
        return self.service().a2a(AgentA2ARequest(self.selector, request))

    def send_text(self, message: "AgentTextMessage") -> AgentA2AResult:
        return self.a2a(A2ARequest(A2A_METHOD_SEND, id_=message.request_id, params=message.params(), model=message.model))

    def stream_text(self, message: "AgentTextMessage") -> StreamResponse:
        return self.service().a2a_stream(AgentA2ARequest(self.selector, A2ARequest(A2A_METHOD_STREAM, id_=message.request_id, params=message.params(), model=message.model)))

    def get_task(self, request: "AgentTaskRequest") -> AgentA2AResult:
        return self._task_control(A2A_METHOD_TASKS_GET, request)

    def cancel_task(self, request: "AgentTaskRequest") -> AgentA2AResult:
        return self._task_control(A2A_METHOD_TASKS_CANCEL, request)

    def submit_input(self, submission: "AgentInputSubmission") -> AgentA2AResult:
        return self.a2a(A2ARequest(A2A_METHOD_INPUT_SUBMIT, id_=submission.request_id, params=submission.params()))

    def resubscribe_task(self, request: "AgentTaskRequest") -> StreamResponse:
        return self.service().a2a_stream(AgentA2ARequest(self.selector, A2ARequest(A2A_METHOD_TASKS_RESUBSCRIBE, id_=request.request_id, params=request.params())))

    def _task_control(self, method: str, request: "AgentTaskRequest") -> AgentA2AResult:
        return self.a2a(A2ARequest(method, id_=request.request_id, params=request.params()))

class SQLMetadataHandle:
    def __init__(self, workspace: WorkspaceHandle) -> None:
        self._workspace = workspace

    def service(self) -> "SQLService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.sql()

    def databases(self, *opts: Callable[["SQLDatabaseListOptions"], None]) -> SQLDatabaseListResult:
        return self.service().meta_databases(*opts)

    def tree(self) -> SQLDatabaseTreeResult:
        return self.service().meta_db_tree()

    def database(self, name: str) -> "SQLDatabaseMetadataHandle":
        if not name:
            raise ErrDatabaseRequired
        return SQLDatabaseMetadataHandle(self, name)

class SQLDatabaseMetadataHandle:
    def __init__(self, metadata: SQLMetadataHandle, name: str) -> None:
        if not name:
            raise ErrDatabaseRequired
        self._metadata = metadata
        self.name = name

    def tables(self) -> SQLDatabaseTablesResult:
        return self._metadata.service().meta_db_tables(self.name)

    def table(self, name: str) -> "SQLTableMetadataHandle":
        if not name:
            raise ErrTableRequired
        return SQLTableMetadataHandle(self, name)

    def drop(self) -> None:
        self._metadata.service().drop_meta_database(self.name)

class SQLTableMetadataHandle:
    def __init__(self, database: SQLDatabaseMetadataHandle, name: str) -> None:
        if not name:
            raise ErrTableRequired
        self._database = database
        self.name = name

    def info(self) -> SQLTableInfoResult:
        return self._database._metadata.service().meta_table_info(self._database.name, self.name)

    def columns(self) -> SQLTableColumnsResult:
        return self._database._metadata.service().meta_table_columns(self._database.name, self.name)

    def column_stats(self) -> SQLTableColumnsResult:
        return self._database._metadata.service().meta_table_column_stats(self._database.name, self.name)

    def ddl(self) -> SQLTableDDLResult:
        return self._database._metadata.service().meta_table_ddl(self._database.name, self.name)

    def drop_table(self) -> None:
        self._database._metadata.service().drop_meta_table(self._database.name, self.name)

    def drop_view(self) -> None:
        self._database._metadata.service().drop_meta_view(self._database.name, self.name)

class SQLWorkbookHandle:
    def __init__(self, workspace: WorkspaceHandle, workbook_id: str) -> None:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        self._workspace = workspace
        self.id = workbook_id

    def service(self) -> "SQLService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.sql()

    def rename(self, name: str) -> None:
        self.service().update_workbook(self.id, name)

    def delete(self) -> None:
        self.service().delete_workbook(self.id)

    def versions(self, *opts: Callable[["WorkbookVersionListOptions"], None]) -> SQLWorkbookVersionListResult:
        return self.service().workbook_versions(self.id, *opts)

    def create_version(self, sql_content: str) -> tuple["SQLWorkbookVersionHandle", SQLWorkbookVersionCreateResult]:
        result = self.service().create_workbook_version(self.id, sql_content)
        return SQLWorkbookVersionHandle(self, result.id), result

    def version(self, version_id: str) -> "SQLWorkbookVersionHandle":
        if not version_id:
            raise ErrVersionIDRequired
        return SQLWorkbookVersionHandle(self, version_id)

class SQLWorkbookVersionHandle:
    def __init__(self, workbook: SQLWorkbookHandle, version_id: str) -> None:
        if not version_id:
            raise ErrVersionIDRequired
        self._workbook = workbook
        self.id = version_id

    def workbook(self) -> SQLWorkbookHandle:
        return self._workbook

    def info(self) -> SQLWorkbookDetailResult:
        return self._workbook.service().workbook_detail(self._workbook.id, self.id)

    def update(self, sql_content: str) -> None:
        self._workbook.service().update_workbook_version(self._workbook.id, self.id, sql_content)

    def save(self, sql_content: Optional[str] = None) -> None:
        self._workbook.service().save_workbook_version(self._workbook.id, self.id, sql_content)

class SQLQueryHandle:
    def __init__(self, workspace: WorkspaceHandle, query_id: str) -> None:
        if not query_id:
            raise ErrQueryIDRequired
        self._workspace = workspace
        self.id = query_id

    def service(self) -> "SQLService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.sql()

    def describe(self) -> SQLQueryOperation:
        return self.service().describe_query(self.id)

    def kill(self) -> None:
        self.service().kill_query(self.id)

class SQLStatementHandle:
    def __init__(self, workspace: WorkspaceHandle, statement_id: str) -> None:
        if not statement_id:
            raise ErrStatementIDRequired
        self._workspace = workspace
        self.id = statement_id

    def service(self) -> "SQLService":
        """Route-aligned escape hatch for explicit route-level control; prefer typed handle methods for user-facing workflows."""
        return self._workspace.sql()

    def result(self, *opts: Callable[["SQLResultOptions"], None]) -> SQLQueryResult:
        return self.service().query_result(self.id, *opts)

    def detail(self, *opts: Callable[["QueryRecordOptions"], None]) -> Optional[SQLStatementRecord]:
        return self.service().query_detail(self.id, *opts)

    def profile(self, *opts: Callable[["QueryRecordOptions"], None]) -> SQLQueryProfileResult:
        return self.service().query_profile(self.id, *opts)

def _duplicate_name_error(kind: str, name: str) -> Error:
    return Error("ErrDuplicateName", f"{kind} name is not unique: {name}")

def _parse_positive_int_id(value: int, kind: str) -> int:
    if value <= 0:
        raise Error("ErrResponseInvalid", f"{kind} id is invalid: {value}")
    return int(value)

def _created_string_path_id(value: str, kind: str) -> str:
    if not value:
        raise _created_id_error(kind)
    return value

def _created_int_path_id(value: int, kind: str) -> str:
    if not value:
        raise _created_id_error(kind)
    return str(value)

def _created_id_error(kind: str) -> Error:
    return Error("ErrResponseInvalid", f"{kind} create response missing id", details={"kind": kind})

def agent_a2a_payload(result: AgentA2AResult) -> dict[str, Any]:
    """Return the A2A task/message object carried by an A2A result.

    Product backends may return either a bare A2A object or a JSON-RPC
    envelope with that object under "result"; both shapes are accepted.
    """
    try:
        payload = json.loads(result.json)
    except json.JSONDecodeError as err:
        raise Error("ErrResponseInvalid", "A2A result missing payload") from err
    if not isinstance(payload, dict):
        raise Error("ErrResponseInvalid", "A2A result missing payload")
    return _unwrap_agent_a2a_payload(payload)

def _unwrap_agent_a2a_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # JSON-RPC 2.0 success responses nest the A2A object under "result". Prefer
    # that object when present so helpers do not read the RPC request id as the
    # task id.
    nested = payload.get("result")
    if isinstance(nested, dict):
        if "jsonrpc" in payload or "kind" in nested or "id" in nested:
            return nested
    return payload

def _agent_a2a_string_field(result: AgentA2AResult, field: str, label: str) -> str:
    try:
        payload = agent_a2a_payload(result)
    except Error as err:
        raise Error("ErrResponseInvalid", f"A2A result missing {label}") from err
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise Error("ErrResponseInvalid", f"A2A result missing {label}")
    return value

# A2A task states that end the internal message/send follow. The interrupted
# states (input-required/auth-required) are terminal for the transport but are
# handed back to the caller for disposal.
_A2A_TASK_TERMINAL_STATES = frozenset({"completed", "failed", "canceled", "rejected", "input-required", "auth-required"})
# A dropped resubscribe stream is re-opened from the durable eventCursor with
# bounded exponential backoff; an environment that cannot open SSE at all
# degrades to tasks/get polling instead.
_A2A_FOLLOW_RECONNECT_LIMIT = 5
_A2A_FOLLOW_RECONNECT_BACKOFF = 0.5
_A2A_FOLLOW_POLL_INTERVAL = 2.0

def _a2a_task_state(payload: dict[str, Any]) -> str:
    status = payload.get("status")
    if not isinstance(status, dict):
        return ""
    state = status.get("state")
    return state if isinstance(state, str) else ""

def _a2a_event_cursor(payload: dict[str, Any]) -> int:
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        cursor = metadata.get("eventCursor")
        if type(cursor) is int and cursor > 0:
            return cursor
    return 0

def _a2a_wait_timeout_error(task_id: str) -> Error:
    # An exhausted wait budget is recoverable, not a task failure: the task id
    # lets the caller resume following the persisted task explicitly.
    return Error("ErrTimeout", "A2A task wait timeout", details={"task_id": task_id})

def _a2a_follow_error(task_id: str, err: Error) -> Error:
    # Follow failures always carry the task id so callers can recover the task.
    return Error(err.code, err.message, request_id=err.request_id, status=err.status, details={**err.details, "task_id": task_id}, data=err.data)

def agent_a2a_task_id(result: AgentA2AResult) -> str:
    return _agent_a2a_string_field(result, "id", "task id")

def agent_a2a_turn_id(result: AgentA2AResult) -> str:
    return _agent_a2a_string_field(result, "turnId", "turn id")

class AccountService:
    """Route-aligned escape hatch; prefer typed WorkspaceHandle DB connection helpers for user-facing workflows."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def bootstrap_native(self) -> NativeBootstrapResult:
        """Prepare the product identity using a UC native CLI access token."""
        return _product_message(self._client._request("POST", "/auth/cli/bootstrap", data_nullable=False), NativeBootstrapResult(), "native bootstrap data")

    def current_credit(self) -> CurrentCreditResult:
        """Read the authenticated UC browser account's available credit."""
        return _product_message(self._client._request("GET", "/billing/credits/current", data_nullable=False), CurrentCreditResult(), "current credit data")

    def begin_browser_login(self, return_to: str) -> StreamResponse:
        path = "/auth/login"
        if return_to:
            path += "?" + urllib.parse.urlencode({"return_to": return_to})
        return StreamResponse(self._client._stream_endpoint("GET", self._client._product_url(path), accept="*/*", no_redirect=True))

    def complete_browser_login(self, request: BrowserLoginCallbackRequest) -> StreamResponse:
        if not isinstance(request, BrowserLoginCallbackRequest): raise TypeError("request must be BrowserLoginCallbackRequest")
        path = "/auth/callback?" + urllib.parse.urlencode({"code":request.code,"state":request.state,"error":request.error})
        return StreamResponse(self._client._stream_endpoint("GET", self._client._product_url(path), accept="*/*", no_redirect=True))

    def complete_browser_logout(self, state: str) -> StreamResponse:
        path = "/auth/logout/callback?" + urllib.parse.urlencode({"state":state})
        return StreamResponse(self._client._stream_endpoint("GET", self._client._product_url(path), accept="*/*", no_redirect=True))

    def browser_session(self) -> BrowserSessionResult:
        return _product_message(self._client._request("GET","/auth/me"), BrowserSessionResult(), "browser session data")

    def logout_browser_session(self, request: BrowserLogoutRequest) -> BrowserLogoutResult:
        if not isinstance(request,BrowserLogoutRequest): raise TypeError("request must be BrowserLogoutRequest")
        return _product_message(self._client._request("POST","/auth/logout",body=json_format.MessageToDict(request,preserving_proto_field_name=True)),BrowserLogoutResult(),"browser logout data")

    def preferences(self) -> AuthPreferencesResult:
        return _product_message(self._client._request("GET","/auth/preferences"),AuthPreferencesResult(),"preferences data")

    def update_preferences(self, request: AuthPreferencesRequest) -> AuthPreferencesResult:
        if not isinstance(request,AuthPreferencesRequest): raise TypeError("request must be AuthPreferencesRequest")
        return _product_message(self._client._request("PATCH","/auth/preferences",body=json_format.MessageToDict(request,preserving_proto_field_name=True)),AuthPreferencesResult(),"preferences data")

    def checkin(self, source: str) -> Any:
        return self._client._request("POST", "/user/me/checkin", body={"source":source})

    def checkin_status(self) -> Any:
        return self._client._request("GET","/user/me/checkin")

    def registration_invite(self) -> Any:
        return self._client._request("GET", "/user/me/registration-invite")

    def reward_center_items(self) -> Any:
        return self._client._request("GET", "/user/me/reward-center/items")

    def reward_center_events(self, event_type: str = "") -> Any:
        path = "/user/me/reward-center/events"
        if event_type:
            path += "?" + urllib.parse.urlencode({"event_type": event_type})
        return self._client._request("GET", path)

    def reward_center_invitations(self, page: str = "", page_size: str = "") -> Any:
        path = "/user/me/reward-center/invitations"
        params = {}
        if page:
            params["page"] = page
        if page_size:
            params["page_size"] = page_size
        if params:
            path += "?" + urllib.parse.urlencode(params)
        return self._client._request("GET", path)

    def db_connection(self, workspace_id: str) -> DBConnectionResult:
        if not workspace_id:
            raise ErrWorkspaceRequired
        return _db_connection_result(self._client._request("GET", "/user/me/db-connection", workspace_id))

    def db_connection_result(self, workspace_id: str = "") -> ProductResult:
        return self._client._product_result("GET", "/user/me/db-connection", workspace_id=workspace_id)

    def _request(self, method: str, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        return self._client._request(method, path, body=body)

@dataclass
class ComputeResourceWorker:
    """Per-instance 观测态 row for one compute resource (GET /compute-resources/{id}/workers).

    Served as raw DTO JSON (no proto message); field names mirror the backend
    computeResourceWorkerDTO wire shape.
    """
    instance_id: str = ""
    worker_type: str = ""
    status: str = ""
    py_requirements_sha: str = ""
    py_requirements_status: str = ""
    py_requirements_error: str = ""

@dataclass
class ComputePyDepsLimits:
    """Read-only projection of the py_deps.* runtime dynamic config (GET /compute-resources/py-deps-limits).

    Served as raw DTO JSON (no proto message). enabled=False (or the backend's
    503 ErrLimitsUnavailable surfaced as an Error) means the feature is off.
    """
    enabled: bool = False
    max_bytes: int = 0
    max_lines: int = 0
    allowed_index_hosts: Optional[list[str]] = None
    pip_index_url: str = ""
    install_timeout_seconds: int = 0

@dataclass
class PutAIStudioServiceSlotRequest:
    """Service slot write body; model_ids is always sent as an array."""
    default_model_id: str
    model_ids: Optional[list[str]] = None
    slot_id: str = ""
    extra_json: str = ""

    def to_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if self.slot_id:
            body["slot_id"] = self.slot_id
        body["default_model_id"] = self.default_model_id
        body["model_ids"] = list(self.model_ids) if self.model_ids is not None else []
        body["extra_json"] = self.extra_json
        return body

class AIStudioService:
    """Account-level model policy and Genesis service slot administration."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def chat_model_policy(self) -> Any:
        """Read agent_chat policy with a product identity; no workspace required."""
        return self._client._request("GET", "/aistudio/model-policy")

    def service_slots(self) -> Any:
        return self._client._request("GET", "/admin/aistudio/service-slots")

    def service_slot_candidates(self) -> Any:
        return self._client._request("GET", "/admin/aistudio/service-slots/candidates")

    def service_slot_logs(self, *options: Callable[["QueryOptions"], None]) -> Any:
        return self._client._request("GET", _with_query("/admin/aistudio/service-slots/operation-logs", options))

    def put_service_slot(self, slot_id: str, request: PutAIStudioServiceSlotRequest) -> Any:
        slot_path = _path_id(slot_id)
        if request is None:
            raise Error(code="ErrRequestRequired", message="service slot request is required")
        return self._client._request("PUT", f"/admin/aistudio/service-slots/{slot_path}", body=request.to_body())

def with_service_slot_log_slot_id(slot_id: str) -> Callable[[QueryOptions], None]:
    return with_query_param("slot_id", slot_id)

def with_service_slot_log_page_size(page_size: int) -> Callable[[QueryOptions], None]:
    return with_query_param("page_size", str(page_size))

class WorkspaceScopedService:
    def __init__(self, client: Client, workspace_id: str) -> None:
        if not workspace_id:
            raise ErrWorkspaceRequired
        self._client = client
        self._workspace_id = workspace_id

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
        require_envelope: bool = False,
        data_nullable: Optional[bool] = None,
    ) -> Any:
        if data_nullable is not None:
            return self._client._request(method, path, self._workspace_id, body, require_envelope, data_nullable=data_nullable)
        return self._client._request(method, path, self._workspace_id, body, require_envelope)

    def _stream(self, method: str, path: str, body: Optional[dict[str, Any]] = None) -> StreamResponse:
        return StreamResponse(self._client._stream(method, path, self._workspace_id, body))

    def _download(self, method: str, path: str, body: Optional[dict[str, Any]] = None) -> StreamResponse:
        return StreamResponse(self._client._stream(method, path, self._workspace_id, body, accept="*/*"))

    def _raw_request(self, method: str, path: str, data: bytes, content_type: str, *, require_envelope: bool = False) -> Any:
        return self._client._raw_request(method, path, self._workspace_id, data, content_type, require_envelope=require_envelope)

class ResourceTagService(WorkspaceScopedService):
    """Workspace tag definitions, values and lazy grouping queries."""

    def create(self, request: resource_tags.ResourceTagCreateRequest) -> resource_tags.ResourceTag:
        return _product_message(self._request("POST", "/tags", MessageToDict(request, preserving_proto_field_name=True)), resource_tags.ResourceTag(), "resource tag")

    def list(self, request: resource_tags.ResourceTagListRequest) -> resource_tags.ResourceTagList:
        query = urllib.parse.urlencode({"type": request.type, "name_search": request.name_search, "resource_id": request.resource_id, "offset": request.offset, "limit": request.limit})
        return _product_message(self._request("GET", "/tags?" + query), resource_tags.ResourceTagList(), "resource tags")

    def update(self, tag_id: str, request: resource_tags.ResourceTagUpdateRequest) -> resource_tags.ResourceTag:
        return _product_message(self._request("PATCH", f"/tags/{_path_id(tag_id)}", MessageToDict(request, preserving_proto_field_name=True)), resource_tags.ResourceTag(), "resource tag")

    def delete(self, tag_id: str) -> None:
        self._request("DELETE", f"/tags/{_path_id(tag_id)}")

    def create_value(self, tag_id: str, request: resource_tags.ResourceTagValueRequest) -> resource_tags.ResourceTagValue:
        return _product_message(self._request("POST", f"/tags/{_path_id(tag_id)}/values", MessageToDict(request, preserving_proto_field_name=True)), resource_tags.ResourceTagValue(), "tag value")

    def list_values(self, tag_id: str, request: resource_tags.ResourceTagListRequest) -> resource_tags.ResourceTagValueList:
        query = urllib.parse.urlencode({"value_search": request.value_search, "offset": request.offset, "limit": request.limit})
        return _product_message(self._request("GET", f"/tags/{_path_id(tag_id)}/values?{query}"), resource_tags.ResourceTagValueList(), "tag values")

    def update_value(self, tag_id: str, value_id: str, request: resource_tags.ResourceTagValueRequest) -> resource_tags.ResourceTagValue:
        return _product_message(self._request("PATCH", f"/tags/{_path_id(tag_id)}/values/{_path_id(value_id)}", MessageToDict(request, preserving_proto_field_name=True)), resource_tags.ResourceTagValue(), "tag value")

    def delete_value(self, tag_id: str, value_id: str) -> None:
        self._request("DELETE", f"/tags/{_path_id(tag_id)}/values/{_path_id(value_id)}")

    def update_relations(self, request: resource_tags.ResourceTagRelationsRequest) -> None:
        self._request("POST", "/tags/relations/update", MessageToDict(request, preserving_proto_field_name=True))

    def groups(self, request: resource_tags.ResourceTagQueryRequest) -> resource_tags.ResourceTagGroupList:
        return _product_message(self._request("POST", "/tags/groups/query", MessageToDict(request, preserving_proto_field_name=True)), resource_tags.ResourceTagGroupList(), "tag groups")

    def resources(self, request: resource_tags.ResourceTagQueryRequest) -> resource_tags.ResourceTagResourceList:
        return _product_message(self._request("POST", "/tags/resources/query", MessageToDict(request, preserving_proto_field_name=True)), resource_tags.ResourceTagResourceList(), "tagged resources")

    def assignments(self, request: resource_tags.ResourceTagAssignmentsRequest) -> resource_tags.ResourceTagAssignmentsList:
        return _product_message(self._request("POST", "/tags/resources/tags/query", MessageToDict(request, preserving_proto_field_name=True)), resource_tags.ResourceTagAssignmentsList(), "tag assignments")

class IAMService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed WorkspaceHandle IAM methods for user-facing workflows."""

    def role_members(self, role_id: str, *options: Callable[["QueryOptions"], None]) -> IAMRoleMembersResult:
        return _product_message(self._request("GET",_with_query(f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/members",options)),IAMRoleMembersResult(),"role members")

    def _result(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
        query: Optional[dict[str, Any]] = None,
    ) -> ProductResult:
        """Preserve the Backend envelope for route-level contract diagnostics."""
        return self._client._product_result(
            method,
            path,
            workspace_id=self._workspace_id,
            body=body,
            query=query,
        )

    def ownership_impact(self, role_id: str, *opts: Callable[["QueryOptions"], None]) -> IAMOwnershipImpactResult:
        path = f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/ownership-impact"
        return _product_message(self._request("GET", _with_query(path, opts)), IAMOwnershipImpactResult(), "IAM ownership impact data")

    def role_audit_events(self, role_id: str, *opts: Callable[["QueryOptions"], None]) -> IAMRoleAuditEventsResult:
        path = f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/audit-events"
        return _product_message(self._request("GET", _with_query(path, opts)), IAMRoleAuditEventsResult(), "IAM role audit data")

    def user_audit_events(self, user_id: str, *opts: Callable[["QueryOptions"], None]) -> IAMUserAuditEventsResult:
        path = f"/workspaces/{_path_id(self._workspace_id)}/iam/users/{_path_id(user_id)}/audit-events"
        return _product_message(self._request("GET", _with_query(path, opts)), IAMUserAuditEventsResult(), "IAM user audit data")

    def set_default_role(self, request: IAMSetDefaultRoleRequest) -> IAMSetDefaultRoleResult:
        _require_iam_request(request, IAMSetDefaultRoleRequest)
        body = {"target_role_id": request.target_role_id, "expected_default_role_version": request.expected_default_role_version, "request_id": request.request_id}
        path = f"/workspaces/{_path_id(self._workspace_id)}/iam/me/default-role"
        return _product_message(self._request("PUT", path, body), IAMSetDefaultRoleResult(), "IAM default role data")

    def permission_schema(self) -> IAMPermissionSchemaResult:
        return _iam_permission_schema_result(
            self._request(
                "GET",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/schema",
            )
        )

    def permission_schema_result(self) -> ProductResult:
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/schema",
        )

    def roles(self) -> IAMRoleListResult:
        return _iam_role_list_result(
            self._request("GET", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles")
        )

    def roles_result(self) -> ProductResult:
        return self._result("GET", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles")

    def user_role_bindings_result(self, user_id: str) -> ProductResult:
        """Read canonical Role bindings for a Core user ID.

        ``user_id`` is the canonical ID returned by workspace invitation or
        member ``iam_user_id`` fields, never an account email or Backend UID.
        The raw Backend envelope is preserved for CAS/version diagnostics.
        """
        if not user_id:
            raise ErrIDRequired
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/users/{_path_id(user_id)}/role-bindings",
        )

    def user_role_bindings(self, user_id: str) -> IAMUserRoleBindingsResult:
        """Read canonical role bindings for a workspace user."""
        if not user_id:
            raise ErrIDRequired
        return _iam_user_role_bindings_result(
            self._request(
                "GET",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/users/{_path_id(user_id)}/role-bindings",
            )
        )

    def put_user_role_bindings(
        self,
        user_id: str,
        request: IAMUserRoleBindingsRequest,
    ) -> IAMUserRoleBindingsMutationResult:
        """Replace canonical role bindings with explicit CAS and request data."""
        if not user_id:
            raise ErrIDRequired
        return _iam_user_role_bindings_mutation_result(
            self._request(
                "PUT",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/users/{_path_id(user_id)}/role-bindings",
                self._user_role_bindings_body(request),
            )
        )

    def put_user_role_bindings_result(
        self,
        user_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        """Preserve the canonical role-binding mutation envelope for diagnostics."""
        if not user_id:
            raise ErrIDRequired
        return self._result(
            "PUT",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/users/{_path_id(user_id)}/role-bindings",
            body,
        )

    def create_role(self, request: IAMRoleCreateRequest) -> IAMRoleCreateResult:
        _require_iam_request(request, IAMRoleCreateRequest)
        return _iam_role_create_result(
            self._request(
                "POST",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles",
                json_format.MessageToDict(request, preserving_proto_field_name=True),
            )
        )

    def create_role_result(self, body: dict[str, Any]) -> ProductResult:
        return self._result(
            "POST",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles",
            body,
        )

    def role_permission_view(self, role_id: str) -> IAMRolePermissionViewResult:
        return _iam_role_permission_view_result(
            self._request(
                "GET",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/permission-view",
            )
        )

    def role_permission_view_result(self, role_id: str) -> ProductResult:
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/permission-view",
        )

    def update_role(self, role_id: str, request: IAMRoleUpdateRequest) -> IAMRoleCreateResult:
        _require_iam_request(request, IAMRoleUpdateRequest)
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        body["expected_lifecycle_version"] = request.expected_lifecycle_version
        body["expected_policy_version"] = request.expected_policy_version
        body["expected_data_privilege_version"] = request.expected_data_privilege_version
        return _iam_role_create_result(
            self._request(
                "PATCH",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}",
                body,
            )
        )

    def update_role_result(self, role_id: str, body: dict[str, Any]) -> ProductResult:
        return self._result(
            "PATCH",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}",
            body,
        )

    def update_role_lifecycle(
        self,
        role_id: str,
        request: IAMRoleLifecycleRequest,
    ) -> IAMRoleMutationResult:
        _require_iam_request(request, IAMRoleLifecycleRequest)
        return _iam_role_mutation_result(
            self._request(
                "PUT",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/lifecycle",
                {
                    "target_state": request.target_state,
                    "reason_code": request.reason_code,
                    "expected_lifecycle_version": request.expected_lifecycle_version,
                    "request_id": request.request_id,
                },
            )
        )

    def update_role_lifecycle_result(
        self,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "PUT",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/lifecycle",
            body,
        )

    def role_delete_impact(
        self,
        role_id: str,
        expected_lifecycle_version: int,
        *,
        include_ownership: bool = False,
        ownership_cursor: str = "",
        ownership_limit: int = 50,
        transfer_requested: bool = False,
    ) -> IAMRoleDeleteImpactResult:
        if expected_lifecycle_version <= 0:
            raise ErrVersionRequired
        options = [with_query_param("expected_lifecycle_version", str(expected_lifecycle_version))]
        if include_ownership:
            options.extend((with_query_param("include_ownership", "true"), with_query_param("ownership_limit", str(ownership_limit))))
            if ownership_cursor:
                options.append(with_query_param("ownership_cursor", ownership_cursor))
        if transfer_requested:
            options.append(with_query_param("transfer_requested", "true"))
        return _iam_role_delete_impact_result(
            self._request(
                "GET",
                _with_query(
                    f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/delete-impact",
                    options,
                ),
            )
        )

    def role_delete_ownerships(self, role_id: str, *, cursor: Optional[str] = None, limit: Optional[int] = None, transfer_requested: Optional[bool] = None) -> IAMRoleDeleteOwnershipList:
        options = []
        if cursor is not None:
            options.append(with_query_param("cursor", cursor))
        if limit is not None:
            options.append(with_query_param("limit", str(limit)))
        if transfer_requested is not None:
            options.append(with_query_param("transfer_requested", str(transfer_requested).lower()))
        return _product_message(
            self._request(
                "GET",
                _with_query(
                    f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/delete-ownerships",
                    options,
                ),
            ),
            IAMRoleDeleteOwnershipList(),
            "IAM role delete ownership page data",
        )

    def delete_role(self, role_id: str, request: IAMRoleDeleteRequest) -> IAMRoleMutationResult:
        _require_iam_request(request, IAMRoleDeleteRequest)
        body = {
            "reason_code": request.reason_code,
            "expected_lifecycle_version": request.expected_lifecycle_version,
            "request_id": request.request_id,
        }
        if request.HasField("ownership_transfer"):
            body["ownership_transfer"] = MessageToDict(request.ownership_transfer, preserving_proto_field_name=True)
        return _iam_role_mutation_result(
            self._request(
                "DELETE",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}",
                body,
            )
        )

    def delete_role_result(self, role_id: str, body: dict[str, Any]) -> ProductResult:
        return self._result(
            "DELETE",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}",
            body,
        )

    def validate_application_policy_result(
        self,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "POST",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/application-policy:validate",
            body,
        )

    def apply_application_policy_result(
        self,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "PUT",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/application-policy",
            body,
        )

    def list_permission_resources_result(
        self,
        *,
        resource_type: str,
        action_id: str,
        purpose: str = "",
        parent_id: str = "",
        cursor: str = "",
        q: str = "",
        limit: int = 0,
    ) -> ProductResult:
        query: dict[str, Any] = {
            "resource_type": resource_type,
            "action_id": action_id,
        }
        if purpose:
            query["purpose"] = purpose
        if parent_id:
            query["parent_id"] = parent_id
        if cursor:
            query["cursor"] = cursor
        if q:
            query["q"] = q
        if limit > 0:
            query["limit"] = limit
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/resources",
            query=query,
        )

    def list_permission_resources(
        self,
        resource_type: str,
        action_id: str,
        purpose: str = "",
        *options: Callable[["QueryOptions"], None],
    ) -> Any:
        if not resource_type:
            raise ErrTypeRequired
        if not action_id:
            raise ErrActionRequired
        query_options = list(options)
        query = {
            "resource_type": resource_type,
            "action_id": action_id,
            "purpose": purpose,
        }
        if not purpose:
            del query["purpose"]
        option_values = ListOptions()
        for option in query_options:
            option(option_values)
        for key, values in option_values.query.items():
            query[key] = values[-1]
        return self._request(
            "GET",
            _with_query(
                f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/resources",
                tuple(with_query_param(key, value) for key, value in query.items()),
            ),
        )

    def batch_describe_permission_resources_result(
        self,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "POST",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/resources:batchDescribe",
            body,
        )

    def batch_describe_permission_resources(
        self,
        resource_type: str,
        action_id: str,
        purpose: str,
        resource_ids: list[str],
    ) -> Any:
        if not resource_type:
            raise ErrTypeRequired
        if not action_id:
            raise ErrActionRequired
        if not resource_ids:
            raise ErrIDRequired
        body = {
            "resource_type": resource_type,
            "resource_ids": resource_ids,
            "action_id": action_id,
        }
        if purpose:
            body["purpose"] = purpose
        return self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/resources:batchDescribe", body)

    def validate_object_grants(
        self,
        resource_type: str,
        resource_id: str,
        role_id: str,
        request: IAMObjectGrantsMutationRequest,
    ) -> IAMObjectGrantsMutationResult:
        if not resource_type:
            raise ErrTypeRequired
        return _iam_object_grants_mutation_result(
            self._request(
                "POST",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/objects/{_path_id(resource_type)}/{_path_id(resource_id)}/roles/{_path_id(role_id)}/grants:validate",
                self._object_grants_body(request),
            )
        )

    def validate_object_grants_result(
        self,
        resource_type: str,
        resource_id: str,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "POST",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/objects/{_path_id(resource_type)}/{_path_id(resource_id)}/roles/{_path_id(role_id)}/grants:validate",
            body,
        )

    def apply_object_grants(
        self,
        resource_type: str,
        resource_id: str,
        role_id: str,
        request: IAMObjectGrantsMutationRequest,
    ) -> IAMObjectGrantsMutationResult:
        if not resource_type:
            raise ErrTypeRequired
        return _iam_object_grants_mutation_result(
            self._request(
                "PUT",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/objects/{_path_id(resource_type)}/{_path_id(resource_id)}/roles/{_path_id(role_id)}/grants",
                self._object_grants_body(request),
            )
        )

    def apply_object_grants_result(
        self,
        resource_type: str,
        resource_id: str,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "PUT",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/objects/{_path_id(resource_type)}/{_path_id(resource_id)}/roles/{_path_id(role_id)}/grants",
            body,
        )

    def transfer_object_ownership(
        self,
        resource_type: str,
        resource_id: str,
        request: IAMObjectOwnershipTransferRequest,
    ) -> IAMObjectOwnershipTransferResult:
        if not resource_type:
            raise ErrTypeRequired
        _require_iam_request(request, IAMObjectOwnershipTransferRequest)
        return _product_message(
            self._request(
                "PUT",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/objects/{_path_id(resource_type)}/{_path_id(resource_id)}/owner",
                {
                    "target_role_id": request.target_role_id,
                    "expected_ownership_version": request.expected_ownership_version,
                    "request_id": request.request_id,
                },
            ),
            IAMObjectOwnershipTransferResult(),
            "IAM object ownership transfer data",
        )

    def object_permission_view(
        self,
        resource_type: str,
        resource_id: str,
    ) -> IAMObjectPermissionViewResult:
        if not resource_type:
            raise ErrTypeRequired
        return _iam_object_permission_view_result(
            self._request(
                "GET",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/objects/{_path_id(resource_type)}/{_path_id(resource_id)}/permission-view",
            )
        )

    def object_permission_view_result(
        self,
        resource_type: str,
        resource_id: str,
    ) -> ProductResult:
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/permissions/objects/{_path_id(resource_type)}/{_path_id(resource_id)}/permission-view",
        )

    def data_privileges(self, role_id: str) -> IAMDataPrivilegeViewResult:
        """Read a role's current MatrixOne data-privilege projection."""
        return _iam_data_privilege_view_result(
            self._request(
                "GET",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privileges",
            )
        )

    def validate_data_privileges(
        self,
        role_id: str,
        request: IAMDataPrivilegeMutationRequest,
    ) -> IAMDataPrivilegeValidationResult:
        """Validate a data-privilege mutation without writing MatrixOne DCL."""
        return _iam_data_privilege_validation_result(
            self._request(
                "POST",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privileges:validate",
                self._data_privilege_mutation_body(request),
            )
        )

    def apply_data_privileges(
        self,
        role_id: str,
        request: IAMDataPrivilegeMutationRequest,
    ) -> IAMDataPrivilegeOperationResult:
        """Apply a validated data-privilege mutation through the native service."""
        return _iam_data_privilege_operation_result(
            self._request(
                "PUT",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privileges",
                self._data_privilege_mutation_body(request),
            )
        )

    def data_privilege_operation(
        self,
        role_id: str,
        request_id: str,
    ) -> IAMDataPrivilegeOperationResult:
        """Read a durable data-privilege operation by request ID."""
        return _iam_data_privilege_operation_result(
            self._request(
                "GET",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privilege-operations/{_path_id(request_id)}",
            )
        )

    def repair_data_privileges(
        self,
        role_id: str,
        repair_operation: str,
        request: IAMDataPrivilegeRepairRequest,
    ) -> IAMDataPrivilegeOperationResult:
        """Retry a recorded data-privilege operation through its repair contract."""
        return _iam_data_privilege_operation_result(
            self._request(
                "POST",
                f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privilege-operations/{_path_id(repair_operation)}",
                self._data_privilege_repair_body(request),
            )
        )

    def data_privileges_result(self, role_id: str) -> ProductResult:
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privileges",
        )

    def validate_data_privileges_result(
        self,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "POST",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privileges:validate",
            body,
        )

    def apply_data_privileges_result(
        self,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "PUT",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privileges",
            body,
        )

    def data_privilege_operation_result(
        self,
        role_id: str,
        request_id: str,
    ) -> ProductResult:
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privilege-operations/{_path_id(request_id)}",
        )

    def repair_data_privileges_result(
        self,
        role_id: str,
        repair_operation: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "POST",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/data-privilege-operations/{_path_id(repair_operation)}",
            body,
        )

    def current_principal_roles(self) -> IAMCurrentPrincipalRolesResult:
        return _product_message(self._request("GET", f"/workspaces/{_path_id(self._workspace_id)}/iam/me/roles"), IAMCurrentPrincipalRolesResult(), "IAM principal roles data")

    def current_principal_capabilities(self, *capability_ids: str) -> IAMCurrentPrincipalCapabilitiesResult:
        """Query selected IDs; unsupported_capability_ids reports unknown IDs.

        Omitting IDs returns the full projection.
        """
        path = _with_query(
            f"/workspaces/{_path_id(self._workspace_id)}/iam/me/capabilities",
            (with_query_values("capability_id", *capability_ids),),
        )
        return _product_message(self._request("GET", path), IAMCurrentPrincipalCapabilitiesResult(), "IAM principal capabilities data")

    def role_inheritance(self, role_id: str) -> IAMRoleInheritanceResult:
        return _product_message(
            self._request("GET", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/inheritance"),
            IAMRoleInheritanceResult(), "IAM role inheritance data",
        )

    def role_inheritance_graph(self, role_id: str) -> IAMRoleInheritanceResult:
        return _product_message(
            self._request("GET", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/inheritance-graph"),
            IAMRoleInheritanceResult(), "IAM role inheritance graph data",
        )

    def add_role_inheritance(self, role_id: str, request: IAMRoleInheritanceMutationRequest) -> IAMRoleInheritanceMutationResult:
        body = self._role_inheritance_body(request)
        return _product_message(
            self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/parents", body),
            IAMRoleInheritanceMutationResult(), "IAM add role inheritance data",
        )

    def remove_role_inheritance(self, role_id: str, request: IAMRoleInheritanceMutationRequest) -> IAMRoleInheritanceMutationResult:
        body = self._role_inheritance_body(request)
        return _product_message(
            self._request("DELETE", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/parents/{_path_id(request.parent_role_id)}", body),
            IAMRoleInheritanceMutationResult(), "IAM remove role inheritance data",
        )

    def validate_application_policy(self, role_id: str, request: IAMApplicationPolicyRequest) -> IAMApplicationPolicyValidationResult:
        body = self._application_policy_body(request)
        return _product_message(
            self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/application-policy:validate", body),
            IAMApplicationPolicyValidationResult(), "IAM validate application policy data",
        )

    def apply_application_policy(self, role_id: str, request: IAMApplicationPolicyRequest) -> IAMApplicationPolicyApplyResult:
        body = self._application_policy_body(request)
        return _product_message(
            self._request("PUT", f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/application-policy", body),
            IAMApplicationPolicyApplyResult(), "IAM apply application policy data",
        )

    @staticmethod
    def _role_inheritance_body(request: IAMRoleInheritanceMutationRequest) -> dict[str, Any]:
        _require_iam_request(request, IAMRoleInheritanceMutationRequest)
        return {
            "parent_role_id": request.parent_role_id,
            "expected_child_lifecycle_version": request.expected_child_lifecycle_version,
            "expected_parent_lifecycle_version": request.expected_parent_lifecycle_version,
            "request_id": request.request_id,
        }

    @staticmethod
    def _application_policy_body(request: IAMApplicationPolicyRequest) -> dict[str, Any]:
        _require_iam_request(request, IAMApplicationPolicyRequest)
        return {
            "schema_version": request.schema_version,
            "expected_policy_version": request.expected_policy_version,
            "expected_role_lifecycle_version": request.expected_role_lifecycle_version,
            "request_id": request.request_id,
            "statements": [
                {
                    "statement_id": statement.statement_id,
                    "action_id": statement.action_id,
                    "resource_type": statement.resource_type,
                    "scope_mode": statement.scope_mode,
                    "resource_id": statement.resource_id,
                    "condition_hash": statement.condition_hash,
                    "target_action_id": statement.target_action_id,
                    "grant_scope_mode": statement.grant_scope_mode,
                    "grant_resource_id": statement.grant_resource_id,
                    "grant_delegatable": statement.grant_delegatable,
                }
                for statement in request.statements
            ],
        }

    def role_inheritance_result(self, role_id: str) -> ProductResult:
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/inheritance",
        )

    def role_inheritance_graph_result(self, role_id: str) -> ProductResult:
        return self._result(
            "GET",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/inheritance-graph",
        )

    def add_role_inheritance_result(
        self,
        role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "POST",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/parents",
            body,
        )

    def remove_role_inheritance_result(
        self,
        role_id: str,
        parent_role_id: str,
        body: dict[str, Any],
    ) -> ProductResult:
        return self._result(
            "DELETE",
            f"/workspaces/{_path_id(self._workspace_id)}/iam/roles/{_path_id(role_id)}/parents/{_path_id(parent_role_id)}",
            body,
        )

    @staticmethod
    def _object_grants_body(request: IAMObjectGrantsMutationRequest) -> dict[str, Any]:
        _require_iam_request(request, IAMObjectGrantsMutationRequest)
        return {
            "schema_version": request.schema_version,
            "expected_policy_version": request.expected_policy_version,
            "expected_role_lifecycle_version": request.expected_role_lifecycle_version,
            "request_id": request.request_id,
            "changes": [
                {
                    "remove": change.remove,
                    "action_id": change.action_id,
                    "condition_hash": change.condition_hash,
                }
                for change in request.changes
            ],
        }

    @staticmethod
    def _user_role_bindings_body(request: IAMUserRoleBindingsRequest) -> dict[str, Any]:
        _require_iam_request(request, IAMUserRoleBindingsRequest)
        return {
            "assigned_role_ids": list(request.assigned_role_ids),
            "default_role_id": request.default_role_id,
            "expected_binding_version": request.expected_binding_version,
            "expected_default_role_version": request.expected_default_role_version,
            "request_id": request.request_id,
            "clear_default_role": request.clear_default_role,
        }

    @staticmethod
    def _data_privilege_mutation_body(request: IAMDataPrivilegeMutationRequest) -> dict[str, Any]:
        _require_iam_request(request, IAMDataPrivilegeMutationRequest)
        mutations: list[dict[str, Any]] = []
        for mutation in request.mutations:
            item: dict[str, Any] = {
                "operation": mutation.operation,
                "action_id": mutation.action_id,
                "resource_type": mutation.resource_type,
                "resource_id": mutation.resource_id,
                "privilege": mutation.privilege,
                "with_grant_option": mutation.with_grant_option,
            }
            if mutation.HasField("row_column"):
                row_column: dict[str, Any] = {"mode": mutation.row_column.mode}
                if mutation.row_column.HasField("draft"):
                    row_column["draft"] = {
                        "black_column_list": list(mutation.row_column.draft.black_column_list),
                        "rule_list": [
                            {
                                "column": rule.column,
                                "relation": rule.relation,
                                "expression_list": [
                                    {
                                        "operator": expression.operator,
                                        "expression": list(expression.expression),
                                        "match_type": expression.match_type,
                                    }
                                    for expression in rule.expression_list
                                ],
                            }
                            for rule in mutation.row_column.draft.rule_list
                        ],
                    }
                item["row_column"] = row_column
            mutations.append(item)
        return {
            "request_id": request.request_id,
            "expected_data_privilege_version": request.expected_data_privilege_version,
            "mutations": mutations,
        }

    @staticmethod
    def _data_privilege_repair_body(request: IAMDataPrivilegeRepairRequest) -> dict[str, Any]:
        _require_iam_request(request, IAMDataPrivilegeRepairRequest)
        return {
            "request_id": request.request_id,
            "expected_data_privilege_version": request.expected_data_privilege_version,
        }

class RuntimeGatewayService:
    """Task-grant and edge-registration callbacks on the native gateway."""
    def __init__(self, client: Client) -> None:
        self._client = client

    def _call(self, path: str, request: Message) -> Any:
        return self._client._request_endpoint("POST", self._client._native_url(path), body=MessageToDict(request, preserving_proto_field_name=True))

    def check_edge_token(self, token: str) -> RuntimeEdgeTokenCheck:
        return _product_message(self._call("/api/v1/astra/edge-tokens/check", RuntimeEdgeTokenRequest(token=token)), RuntimeEdgeTokenCheck(), "edge token check")

    def renew_edge_token(self, token: str) -> RuntimeEdgeTokenRenewal:
        return _product_message(self._client._request("POST", "/edge-tokens/renew", body={"token":token}), RuntimeEdgeTokenRenewal(), "edge token renewal")

    def resolve_model(self, request: RuntimeModelResolveRequest) -> RuntimeModelResolution:
        return _product_message(self._call("/api/v1/models/resolve", request), RuntimeModelResolution(), "runtime model resolution")

    def invoke_model(self, request: dict[str, Any]) -> StreamResponse:
        return StreamResponse(self._client._stream_endpoint("POST", self._client._native_url("/api/v1/models/openai/chat/completions"), body=request, accept="*/*"))

    def mcp(self, request: RuntimeRPCRequest) -> Optional[RuntimeRPCResponse]:
        """Cancellation notifications return None on acceptance, not settlement."""
        if request.method == "notifications/cancelled" and not request.HasField("id"):
            _notify_runtime_mcp(self._client, self._client._native_url("/api/v1/mcp/http"), request)
            return None
        return _product_message(self._call("/api/v1/mcp/http", request), RuntimeRPCResponse(), "runtime MCP")

    def authorize_executor(self, request: RuntimeExecutorAuthorizationRequest) -> None:
        self._call("/api/v1/runtime-executors/authorize", request)

    def apply_compute_binding_event(self, request: ComputeBindingEvent) -> dict[str, Any]:
        body = MessageToDict(request, preserving_proto_field_name=True)
        # This owner decodes into int64 with encoding/json rather than protojson.
        # Match Go's JSON number instead of MessageToDict's int64 string form.
        if request.fencing_token != 0:
            body["fencing_token"] = request.fencing_token
        return self._client._request_endpoint("POST", self._client._native_url("/api/v1/internal/compute-bindings/events"), body=body)

def _notify_runtime_mcp(client: Client, endpoint: str, request: RuntimeRPCRequest, workspace_id: str = "") -> None:
    body = MessageToDict(request, preserving_proto_field_name=True)
    with client._stream_endpoint("POST", endpoint, workspace_id, body, accept="application/json") as response:
        if response.status != 202 or response.read(1):
            raise Error("ErrResponseInvalid", "MCP notification requires an empty HTTP 202 acknowledgement", request_id=_request_id(response.headers))


class WebappService:
    """Route-aligned escape hatch for anonymous Webapp routes; prefer typed AgentHandle helpers for publisher user-facing workflows; never forward product credentials or workspace/runtime grants."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
        opts: tuple[Callable[["QueryOptions"], None], ...] = (),
    ) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        status, request_id, raw = self._client._public_raw_response(
            method,
            _with_query(path, opts),
            body=data,
            content_type="application/json" if data is not None else "",
            accept="application/json",
        )
        return _parse_response(raw, request_id, require_envelope=True, status=status)

    def resolve(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/public/webapp/resolve", body)

    def create_session(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/public/webapp/session", body)

    def refresh_session(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/public/webapp/session/refresh", body)

    def create_conversation(self, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("POST", "/public/webapp/conversations", body, opts)

    def list_conversations(self, *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("GET", "/public/webapp/conversations", opts=opts)

    def rename_conversation(self, conversation_id: str, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("PATCH", f"/public/webapp/conversations/{_path_id(conversation_id)}", body, opts)

    def delete_conversation(self, conversation_id: str, *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("DELETE", f"/public/webapp/conversations/{_path_id(conversation_id)}", opts=opts)

    def list_messages(self, conversation_id: str, *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("GET", f"/public/webapp/conversations/{_path_id(conversation_id)}/messages", opts=opts)

    def list_task_events(self, conversation_id: str, task_id: str, *opts: Callable[["QueryOptions"], None]) -> Any:
        path = f"/public/webapp/conversations/{_path_id(conversation_id)}/tasks/{_path_id(task_id)}/events"
        return self._request("GET", path, opts=opts)

    def submit_feedback(self, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("POST", "/public/webapp/feedback", body, opts)

    def call_mcp_app(self, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("POST", "/public/webapp/mcp-apps/call", body, opts)

    def read_mcp_app_resource(self, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        return self._request("POST", "/public/webapp/mcp-apps/resource", body, opts)

    def a2a_stream(self, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> StreamResponse:
        return StreamResponse(self._client._public_stream("POST", _with_query("/public/webapp/a2a", opts), body=body))

    def _task_file_path(self, conversation_id: str, task_id: str, file_id: str, action: str) -> str:
        return f"/public/webapp/conversations/{_path_id(conversation_id)}/tasks/{_path_id(task_id)}/files/{_path_id(file_id)}/{action}"

    def download_task_file(self, conversation_id: str, task_id: str, file_id: str, *opts: Callable[["QueryOptions"], None]) -> StreamResponse:
        path = _with_query(self._task_file_path(conversation_id, task_id, file_id, "download"), opts)
        return StreamResponse(self._client._public_stream("GET", path, accept="*/*"))

    def preview_task_file(self, conversation_id: str, task_id: str, file_id: str, *opts: Callable[["QueryOptions"], None]) -> StreamResponse:
        path = _with_query(self._task_file_path(conversation_id, task_id, file_id, "preview"), opts)
        return StreamResponse(self._client._public_stream("GET", path, accept="*/*"))

    def upload_file(self, filename: str, data: bytes, *opts: Callable[["QueryOptions"], None], content_type: str = "application/octet-stream") -> Any:
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, {}, [("file", filename, data)], file_content_type=content_type or "application/octet-stream")
        status, request_id, raw = self._client._public_raw_response(
            "POST", _with_query("/public/webapp/files", opts), body=body,
            content_type=f"multipart/form-data; boundary={boundary}", accept="application/json",
        )
        return _parse_response(raw, request_id, require_envelope=True, status=status)


class SystemService:
    """Public bootstrap and operational diagnostics on the MOI gateway."""
    def service_account_workspaces(self) -> ServiceAccountWorkspaceList:
        return _product_message(self._client._request_endpoint("GET", self._client._native_url("/api/v1/service-accounts/workspaces")),ServiceAccountWorkspaceList(),"provisioner workspaces")

    def service_account_assignable_roles(self, workspace_id: str) -> ServiceAccountRoleList:
        return _product_message(self._client._request_endpoint("GET", self._client._native_url(f"/api/v1/service-accounts/workspaces/{_path_id(workspace_id)}/assignable-roles")),ServiceAccountRoleList(),"provisioner roles")

    def enable_compute_billing(self) -> BillingMeterRolloutResult:
        return self._enable_billing_meter("/api/v1/system/billing/compute-rollout:enable")

    def enable_ai_service_billing(self) -> BillingMeterRolloutResult:
        return self._enable_billing_meter("/api/v1/system/billing/ai-service-rollout:enable")

    def _enable_billing_meter(self, path: str) -> BillingMeterRolloutResult:
        data = self._client._request_endpoint("POST", self._client._native_url(path), data_nullable=False)
        return _product_message(data, BillingMeterRolloutResult(), "billing meter rollout data")

    def resume_data_share_ddl(self, request: DataShareDDLRecoveryRequest) -> DataShareDDLRecoveryResult:
        if not isinstance(request, DataShareDDLRecoveryRequest): raise TypeError("request must be DataShareDDLRecoveryRequest")
        body = MessageToDict(request,preserving_proto_field_name=True,always_print_fields_with_no_presence=True)
        return _product_message(self._client._request_endpoint("POST",self._client._native_url("/api/v1/system/data-share/recovery:resume"),body=body,require_envelope=True),DataShareDDLRecoveryResult(),"data share recovery result")

    def terminate_data_share_saga(self, request: DataShareSagaTerminationRequest) -> DataShareSagaTerminationResult:
        if not isinstance(request, DataShareSagaTerminationRequest): raise TypeError("request must be DataShareSagaTerminationRequest")
        body = MessageToDict(request,preserving_proto_field_name=True,always_print_fields_with_no_presence=True)
        return _product_message(self._client._request_endpoint("POST",self._client._native_url("/api/v1/system/data-share/recovery/terminate"),body=body,require_envelope=True),DataShareSagaTerminationResult(),"data share recovery result")

    def __init__(self, client: Client) -> None:
        self._client = client

    def health(self) -> HealthResult:
        return _product_message(self._client._request_endpoint("GET", self._client._native_url("/healthcheck")), HealthResult(), "health data")

    def metrics(self) -> StreamResponse:
        return StreamResponse(self._client._stream_endpoint("GET", self._client._native_url("/metrics"), accept="*/*"))

    def versions(self) -> SystemVersionsResult:
        return _product_message(self._client._request("GET", "/system/versions"), SystemVersionsResult(), "versions data")

    def webapp_config(self) -> WebappConfigResult:
        return _product_message(self._client._request("GET", "/webapp/config"), WebappConfigResult(), "webapp config data")

    def route_coverage(self) -> SystemRouteCoverageResult:
        return _product_message(self._client._request_endpoint("GET", self._client._native_url("/__moi_test/route-coverage")), SystemRouteCoverageResult(), "route coverage data")

    def versions_result(self) -> ProductResult:
        return self._client._product_result("GET", "/system/versions")

from ._proto.product.dashboard_pb2 import (
    TaskExecutionOverviewResult,
    DataDashboardSourceInput,
    DataDashboardMutationRequest,
    DataDashboardListRequest,
    DataDashboardChartMutationRequest,
    DataDashboardDrillThroughDimension,
    DataDashboardDrillThroughRequest,
    DataDashboardChartOrderRequest,
    DataDashboardListResult,
    DataDashboardMutationResult,
    DataDashboardGeneratedSQLResult,
    DataDashboardChartRun,
    DataDashboardChartRuns,
    DataDashboardChartExecution,
    DataDashboardDrillThroughResult,
    DataDashboard,
    DataDashboardSource,
    DataDashboardChartSummary,
    DataDashboardChart,
    DataDashboardAlert,
)
@dataclass
class DashboardPreviewOptions:
    chart_id: Optional[str] = None


def with_dashboard_preview_chart_id(chart_id: str) -> Callable[[DashboardPreviewOptions], None]:
    def apply(options: DashboardPreviewOptions) -> None:
        options.chart_id = chart_id
    return apply


class DashboardService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed workflow handles for user-facing workflows."""

    def connect_web_socket(self) -> "DashboardWebSocket":
        """固定工作区身份建连；不自动重连或重放写操作。"""
        import websocket
        if not self._workspace_id:
            raise ErrWorkspaceRequired
        parsed = urllib.parse.urlparse(self._client._base)
        if parsed.scheme not in {"http", "https"}:
            raise Error("ErrEndpointSchemeUnsupported", "product endpoint must use http or https")
        path = parsed.path.rstrip("/") + "/data-dashboards/ws"
        url = urllib.parse.urlunparse(("wss" if parsed.scheme == "https" else "ws", parsed.netloc, path, "", urllib.parse.urlencode({"workspace_id": self._workspace_id}), ""))
        protocols = _websocket_subprotocols(self._client)
        role_id = self._client._workspace_scope_headers(self._workspace_id).get("X-MOI-Role-ID")
        if role_id:
            protocols.append("moi-role-id." + role_id)
        connection = _dashboard_socket_call(lambda: websocket.create_connection(url, timeout=self._client._config.timeout, header=_websocket_headers(self._client, self._workspace_id), subprotocols=protocols))
        return DashboardWebSocket(connection)

    def create(self, request: DataDashboardMutationRequest) -> DataDashboard:
        if not isinstance(request, DataDashboardMutationRequest): raise TypeError("request has the wrong dashboard contract type")
        return _product_message(self._request("POST", "/data-dashboards", _dashboard_request_body(request)), DataDashboard(), "dashboard data")

    def list(self, request: DataDashboardListRequest) -> DataDashboardListResult:
        if not isinstance(request, DataDashboardListRequest): raise TypeError("request has the wrong dashboard contract type")
        return _product_message(self._request("POST", "/data-dashboards/list", _dashboard_request_body(request)), DataDashboardListResult(), "dashboard data")

    def get(self, dashboard_id: str) -> DataDashboard:
        return _product_message(self._request("GET", f"/data-dashboards/{_path_id(dashboard_id)}", None), DataDashboard(), "dashboard data")

    def update(self, dashboard_id: str, request: DataDashboardMutationRequest) -> DataDashboardMutationResult:
        if not isinstance(request, DataDashboardMutationRequest): raise TypeError("request has the wrong dashboard contract type")
        return _product_message(self._request("PATCH", f"/data-dashboards/{_path_id(dashboard_id)}", _dashboard_request_body(request)), DataDashboardMutationResult(), "dashboard data")

    def delete(self, dashboard_id: str) -> DataDashboardMutationResult:
        return _product_message(self._request("DELETE", f"/data-dashboards/{_path_id(dashboard_id)}", None), DataDashboardMutationResult(), "dashboard data")

    def create_chart(self, dashboard_id: str, request: DataDashboardChartMutationRequest) -> DataDashboardChart:
        if not isinstance(request, DataDashboardChartMutationRequest): raise TypeError("request has the wrong dashboard contract type")
        return _product_message(self._request("POST", f"/data-dashboards/{_path_id(dashboard_id)}/charts", _dashboard_request_body(request)), DataDashboardChart(), "dashboard data")

    def update_chart(self, dashboard_id: str, chart_id: str, request: DataDashboardChartMutationRequest) -> DataDashboardChart:
        if not isinstance(request, DataDashboardChartMutationRequest): raise TypeError("request has the wrong dashboard contract type")
        return _product_message(self._request("PATCH", f"/data-dashboards/{_path_id(dashboard_id)}/charts/{_path_id(chart_id)}", _dashboard_request_body(request)), DataDashboardChart(), "dashboard data")

    def delete_chart(self, dashboard_id: str, chart_id: str) -> DataDashboardMutationResult:
        return _product_message(self._request("DELETE", f"/data-dashboards/{_path_id(dashboard_id)}/charts/{_path_id(chart_id)}", None), DataDashboardMutationResult(), "dashboard data")

    def update_chart_order(self, dashboard_id: str, request: DataDashboardChartOrderRequest) -> DataDashboardChartOrderRequest:
        if not isinstance(request, DataDashboardChartOrderRequest): raise TypeError("request has the wrong dashboard contract type")
        return _product_message(self._request("PATCH", f"/data-dashboards/{_path_id(dashboard_id)}/chart-order", _dashboard_request_body(request)), DataDashboardChartOrderRequest(), "dashboard data")

    def preview_sql(self, dashboard_id: str, sql_text: str, *options: Callable[[DashboardPreviewOptions], None]) -> SQLQueryResult:
        config = DashboardPreviewOptions()
        for option in options:
            option(config)
        body = {"sql_text": sql_text}
        if config.chart_id is not None:
            body["chart_id"] = config.chart_id
        return _product_message(self._request("POST", f"/data-dashboards/{_path_id(dashboard_id)}/preview", body), SQLQueryResult(), "dashboard data")

    def generate_sql(self, dashboard_id: str, question: str, title: str) -> DataDashboardGeneratedSQLResult:
        return _product_message(self._request("POST", f"/data-dashboards/{_path_id(dashboard_id)}/generate-sql", {"question": question, "title": title}), DataDashboardGeneratedSQLResult(), "dashboard data")

    def refresh(self, dashboard_id: str) -> DataDashboardChartRuns:
        return _product_message(self._request("POST", f"/data-dashboards/{_path_id(dashboard_id)}/refresh", None), DataDashboardChartRuns(), "dashboard data")

    def run_chart(self, dashboard_id: str, chart_id: str) -> DataDashboardChartRun:
        return _product_message(self._request("POST", f"/data-dashboards/{_path_id(dashboard_id)}/charts/{_path_id(chart_id)}/run", None), DataDashboardChartRun(), "dashboard data")

    def chart_result(self, dashboard_id: str, chart_id: str, *options: Callable[["QueryOptions"], None]) -> DataDashboardChartExecution:
        return _product_message(self._request("GET", _with_query(f"/data-dashboards/{_path_id(dashboard_id)}/charts/{_path_id(chart_id)}/result", options), None), DataDashboardChartExecution(), "dashboard data")

    def download_chart_result(self, dashboard_id: str, chart_id: str, *options: Callable[["QueryOptions"], None]) -> StreamResponse:
        return self._download("GET", _with_query(f"/data-dashboards/{_path_id(dashboard_id)}/charts/{_path_id(chart_id)}/result/download", options), None)

    def drill_through(self, dashboard_id: str, chart_id: str, request: DataDashboardDrillThroughRequest) -> DataDashboardDrillThroughResult:
        if not isinstance(request, DataDashboardDrillThroughRequest): raise TypeError("request has the wrong dashboard contract type")
        return _product_message(self._request("POST", f"/data-dashboards/{_path_id(dashboard_id)}/charts/{_path_id(chart_id)}/drill-through", _dashboard_request_body(request)), DataDashboardDrillThroughResult(), "dashboard data")

    def download_drill_through(self, dashboard_id: str, chart_id: str, request: DataDashboardDrillThroughRequest) -> StreamResponse:
        if not isinstance(request, DataDashboardDrillThroughRequest): raise TypeError("request has the wrong dashboard contract type")
        return self._download("POST", f"/data-dashboards/{_path_id(dashboard_id)}/charts/{_path_id(chart_id)}/drill-through/download", _dashboard_request_body(request))

    def task_execution_overview(self) -> TaskExecutionOverviewResult:
        return _product_message(self._request("GET", "/dashboard/task-execution-overview"), TaskExecutionOverviewResult(), "task execution overview")

def _required_int_field(data: dict[str, Any], key: str) -> int:
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be int")
    return value

class WorkspaceMemberService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed WorkspaceHandle member methods and WorkspaceMemberHandle for user-facing workflows."""

    def current_principal(self) -> CurrentWorkspacePrincipalResult:
        return _current_workspace_principal_result(self._post("/user/info", None))

    def accept_invitation(self, invitation_id: str) -> WorkspaceInvitationAcceptResult:
        value = self._request("POST", f"/workspaces/invitations/{_path_id(invitation_id)}/accept", {})
        return _product_message(value, WorkspaceInvitationAcceptResult(), "workspace invitation accept data")

    def current_principal_result(self) -> ProductResult:
        return self._client._product_result("POST", "/user/info", workspace_id=self._workspace_id)

    def members(self, *opts: Callable[["WorkspaceMemberListOptions"], None]) -> WorkspaceMemberListResult:
        return _workspace_member_list_result(self._post("/user/list", _member_list_body(opts)))

    def members_raw(self, body: dict[str, Any]) -> WorkspaceMemberListResult:
        return _workspace_member_list_result(self._post("/user/list", body))

    def invite(self, name: str, default_role_id: int, *opts: Callable[["CreateUserOptions"], None]) -> WorkspaceMemberInviteResult:
        if not name:
            raise ErrNameRequired
        options = CreateUserOptions()
        for opt in opts:
            opt(options)
        has_email = options.email is not None and bool(options.email.strip())
        has_mobile = options.mobile_number is not None and bool(options.mobile_number.strip())
        has_github = options.github_login is not None and bool(options.github_login.strip())
        contacts = sum(1 for present in (has_email, has_mobile, has_github) if present)
        if contacts == 0:
            raise ErrInvitationContactRequired
        if contacts > 1:
            raise ErrInvitationContactConflict
        if has_mobile and re.fullmatch(r"1\d{10}", options.mobile_number) is None:
            raise ErrInvitationMobileNumberInvalid
        if has_github:
            login = options.github_login.strip()
            if login.startswith("@"):
                login = login[1:]
            login = login.strip().lower()
            if re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?", login) is None:
                raise ErrInvitationGitHubLoginInvalid
            options.github_login = login
        _validate_assigned_default_role(options.role_ids, default_role_id)
        body: dict[str, Any] = {"name": name, "default_role_id": default_role_id}
        if options.email is not None:
            body["email"] = options.email
        if options.mobile_number is not None:
            body["mobile_number"] = options.mobile_number
        if options.github_login is not None:
            body["github_login"] = options.github_login
        if options.description is not None:
            body["description"] = options.description
        if options.role_ids is not None:
            body["role_id_list"] = options.role_ids
        if options.tags is not None:
            body["tag_list"] = options.tags
        if options.auto_accept:
            body["auto_accept"] = True
        return _workspace_member_invite_result(self._post("/user/create", body))

    def invite_raw(self, body: dict[str, Any]) -> WorkspaceMemberInviteResult:
        return _workspace_member_invite_result(self._post("/user/create", body))

    def invite_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/user/create", workspace_id=self._workspace_id, body=body)

    def member(self, user_id: str) -> WorkspaceMember:
        if not user_id:
            raise ErrIDRequired
        return _workspace_member(self._post("/user/detail_info", {"id": user_id}))

    def member_raw(self, body: dict[str, Any]) -> WorkspaceMember:
        return _workspace_member(self._post("/user/detail_info", body))

    def update(self, user_id: str, name: str, description: str, *opts: Callable[["UpdateUserOptions"], None]) -> None:
        if not user_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        options = UpdateUserOptions()
        for opt in opts:
            opt(options)
        self._post("/user/update_info", {"id": user_id, "name": name, "description": description, "tag_list": options.tags})

    def update_raw(self, body: dict[str, Any]) -> None:
        self._post("/user/update_info", body)

    def delete(self, user_id: str) -> None:
        if not user_id:
            raise ErrIDRequired
        self._post("/user/delete", {"id": user_id})

    def delete_raw(self, body: dict[str, Any]) -> None:
        self._post("/user/delete", body)

    def delete_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/user/delete", workspace_id=self._workspace_id, body=body)

    def update_status(self, user_id: str, action: str) -> None:
        if not user_id:
            raise ErrIDRequired
        if not action:
            raise ErrActionRequired
        self._post("/user/update_status", {"id": user_id, "action": action})

    def update_status_raw(self, body: dict[str, Any]) -> None:
        self._post("/user/update_status", body)

    def create_user_tag(self, name: str) -> IDResult:
        if not name:
            raise ErrNameRequired
        return _id_result(self._post("/user/tag/create", {"name": name}))

    def user_tags(self) -> DataTagListResult:
        return _data_tag_list_result(self._post("/user/tag/list", {}))

    def update_user_tag(self, tag_id: int, name: str) -> IDResult:
        if not tag_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        return _id_result(self._post("/user/tag/update", {"id": tag_id, "name": name}))

    def delete_user_tag(self, tag_id: int) -> IDResult:
        if not tag_id:
            raise ErrIDRequired
        return _id_result(self._post("/user/tag/delete", {"id": tag_id}))

    def audit_logs(self, *opts: Callable[["AuditLogOptions"], None]) -> AuditLogListResult:
        return _audit_log_list_result(self._request("GET", _with_query("/audit/logs", opts)))

    def audit_log_overview(self) -> AuditLogOverviewResult:
        return _audit_log_overview_result(self._request("GET", "/audit/logs/overview"))

    def _post(self, path: str, body: Optional[dict[str, Any]]) -> Any:
        return self._request("POST", path, body)

class CatalogService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed catalog, database, table, volume, folder, and file handles for user-facing workflows."""

    def catalog_references(self, id: int) -> RefListResult:
        return _product_message(self._request("POST", "/catalog/ref_list", {"id":id}), RefListResult(), "catalog references")

    def database_references(self, id: int) -> RefListResult:
        return _product_message(self._request("POST", "/catalog/database/ref_list", {"id":id}), RefListResult(), "catalog references")

    def volume_references(self, id: int) -> RefListResult:
        return _product_message(self._request("POST", "/catalog/volume/ref_list", {"id":id}), RefListResult(), "catalog references")

    def folder_references(self, id: int) -> RefListResult:
        return _product_message(self._request("POST", "/catalog/folder/ref_list", {"id":id}), RefListResult(), "catalog references")

    def table_references(self, id: int) -> RefListResult:
        return _product_message(self._request("POST", "/catalog/table/ref_list", {"id":id}), RefListResult(), "catalog references")

    def catalog_file_content(self, file_id: str, capability: str) -> StreamResponse:
        return self._download("GET", f"/catalog-files/{_path_id(file_id)}/content?" + urllib.parse.urlencode({"capability": capability}))

    def workspace_file_model_url(self, file_id: str) -> URLResult:
        return _url_result(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/files/{_path_id(file_id)}/model-url"))

    def garbage_collection(self, request: CatalogGarbageCollectionRequest) -> CatalogGarbageCollectionResult:
        if not isinstance(request, CatalogGarbageCollectionRequest): raise TypeError("request must be CatalogGarbageCollectionRequest")
        body = {}
        if request.orphan_file_threshold_hours:
            body["orphan_file_threshold_hours"] = request.orphan_file_threshold_hours
        if request.batch_size:
            body["batch_size"] = request.batch_size
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/garbage-collection",body),CatalogGarbageCollectionResult(),"catalog garbage collection")

    def workspace_table_columns(self, request: WorkspaceTableColumnsRequest) -> WorkspaceTableOverviewItem:
        if not isinstance(request, WorkspaceTableColumnsRequest): raise TypeError("request must be WorkspaceTableColumnsRequest")
        body = {"database_id":request.database_id,"table_id":request.table_id,"table_name":request.table_name}
        return _product_message(self._request("POST","/table/columns",body),WorkspaceTableOverviewItem(),"workspace table columns")

    def workspace_database_tables(self, database_id: int) -> WorkspaceTableOverviewResult:
        return _product_message(self._request("POST","/table/database/tables",{"database_id":database_id}),WorkspaceTableOverviewResult(),"workspace database tables")

    def workspace_table_overview(self) -> WorkspaceTableOverviewResult:
        return _product_message(self._request("POST","/table/overview",{}),WorkspaceTableOverviewResult(),"workspace table overview")

    def preview_workspace_file(self, file_id: str) -> StreamResponse:
        return self._download("GET", f"/workspaces/{_path_id(self._workspace_id)}/files/{_path_id(file_id)}/preview")

    def health(self) -> HealthResult:
        return _health_result(self._request("GET", "/catalog/healthz"))

    def health_result(self) -> ProductResult:
        return self._client._product_result("GET", "/catalog/healthz", workspace_id=self._workspace_id)

    def allowed_actions(self, resource_type: str, resource_ids: list[str]) -> CatalogAllowedActionsResult:
        """Return UI hints for 1–100 same-type candidates, not execution permission."""
        return _product_message(self._catalog_post("/catalog/allowed-actions", {"resource_type": resource_type, "resource_ids": resource_ids}), CatalogAllowedActionsResult(), "catalog allowed actions")

    def tree(self, *, page_size: Optional[int] = None, page_token: Optional[str] = None, search: Optional[str] = None, resource_types: Optional[list[str]] = None, resource_id: Optional[int] = None, include_table_leaves: Optional[bool] = None) -> CatalogTreeResult:
        body = {key: value for key, value in {"page_size": page_size, "page_token": page_token, "search": search, "resource_id": resource_id, "include_table_leaves": include_table_leaves}.items() if value is not None}
        if resource_types:
            body["resource_types"] = resource_types
        return _catalog_tree_result(self._catalog_post("/catalog/tree", body))

    def tree_raw(self, body: dict[str, Any]) -> CatalogTreeResult:
        return _catalog_tree_result(self._catalog_post("/catalog/tree", body))

    def tree_raw_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/tree", workspace_id=self._workspace_id, body=body)

    def system_tree(self, *, include_table_leaves: Optional[bool] = None, database_name: Optional[str] = None, table_name: Optional[str] = None, page_size: Optional[int] = None, page_token: Optional[str] = None, search: Optional[str] = None) -> CatalogTreeResult:
        body: dict[str, Any] = {}
        if include_table_leaves is not None:
            body["include_table_leaves"] = include_table_leaves
        if database_name is not None:
            body["database_name"] = database_name
        if table_name is not None:
            body["table_name"] = table_name
        body.update({key: value for key, value in {"page_size": page_size, "page_token": page_token, "search": search}.items() if value is not None})
        return _catalog_tree_result(self._catalog_post("/catalog/system/tree", body))

    def system_tree_raw(self, body: dict[str, Any]) -> CatalogTreeResult:
        return _catalog_tree_result(self._catalog_post("/catalog/system/tree", body))

    def system_tree_raw_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/system/tree", workspace_id=self._workspace_id, body=body)

    def list(self, *opts: Callable[["CatalogListOptions"], None]) -> CatalogListResult:
        body: dict[str, Any] = {}
        _add_catalog_list_options(body, opts)
        return _catalog_list_result(self._catalog_post("/catalog/list", body))

    def list_raw(self, body: dict[str, Any]) -> CatalogListResult:
        return _catalog_list_result(self._catalog_post("/catalog/list", body))

    def list_raw_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/list", workspace_id=self._workspace_id, body=body)

    def create(self, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> IDResult:
        if not name:
            raise ErrNameRequired
        body: dict[str, Any] = {"name": name}
        _add_catalog_info_options(body, opts)
        return _id_result(self._catalog_post("/catalog/create", body))

    def create_raw(self, body: dict[str, Any]) -> IDResult:
        return _id_result(self._catalog_post("/catalog/create", body))

    def create_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/create", workspace_id=self._workspace_id, body=body)

    def info(self, catalog_id: int) -> CatalogInfoResult:
        if not catalog_id:
            raise ErrIDRequired
        return _catalog_info_result(self._catalog_post("/catalog/info", {"id": catalog_id}))

    def info_raw(self, body: dict[str, Any]) -> CatalogInfoResult:
        return _catalog_info_result(self._catalog_post("/catalog/info", body))

    def info_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/info", workspace_id=self._workspace_id, body=body)

    def update(self, catalog_id: int, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> None:
        if not catalog_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        body: dict[str, Any] = {"id": catalog_id, "name": name}
        _add_catalog_info_options(body, opts)
        self._catalog_post("/catalog/update", body)

    def update_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/update", body)

    def update_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/update", workspace_id=self._workspace_id, body=body)

    def delete(self, catalog_id: int) -> None:
        if not catalog_id:
            raise ErrIDRequired
        self._catalog_post("/catalog/delete", {"id": catalog_id})

    def delete_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/delete", body)

    def delete_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/delete", workspace_id=self._workspace_id, body=body)

    def list_databases(self, catalog_id: int, *opts: Callable[["CatalogListOptions"], None]) -> DatabaseListResult:
        if not catalog_id:
            raise ErrIDRequired
        body: dict[str, Any] = {"id": catalog_id}
        _add_catalog_list_options(body, opts)
        return _database_list_result(self._catalog_post("/catalog/database/list", body))

    def list_databases_raw(self, body: dict[str, Any]) -> DatabaseListResult:
        return _database_list_result(self._catalog_post("/catalog/database/list", body))

    def create_database(self, catalog_id: int, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> IDResult:
        if not catalog_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        body: dict[str, Any] = {"catalog_id": catalog_id, "name": name}
        _add_catalog_info_options(body, opts)
        return _id_result(self._catalog_post("/catalog/database/create", body))

    def create_database_raw(self, body: dict[str, Any]) -> IDResult:
        return _id_result(self._catalog_post("/catalog/database/create", body))

    def create_database_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/database/create", workspace_id=self._workspace_id, body=body)

    def database_info(self, database_id: int) -> DatabaseInfoResult:
        if not database_id:
            raise ErrIDRequired
        return _database_info_result(self._catalog_post("/catalog/database/info", {"id": database_id}))

    def database_info_raw(self, body: dict[str, Any]) -> DatabaseInfoResult:
        return _database_info_result(self._catalog_post("/catalog/database/info", body))

    def update_database(self, database_id: int, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> IDResult:
        if not database_id:
            raise ErrIDRequired
        raise ErrDatabaseRenameUnsupported

    def update_database_description(self, database_id: int, *opts: Callable[["CatalogInfoOptions"], None]) -> IDResult:
        if not database_id:
            raise ErrIDRequired
        body: dict[str, Any] = {"id": database_id}
        _add_catalog_info_options(body, opts)
        return _id_result(self._catalog_post("/catalog/database/update", body))

    def update_database_raw(self, body: dict[str, Any]) -> IDResult:
        return _id_result(self._catalog_post("/catalog/database/update", body))

    def delete_database(self, database_id: int) -> None:
        if not database_id:
            raise ErrIDRequired
        self._catalog_post("/catalog/database/delete", {"id": database_id})

    def delete_database_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/database/delete", body)

    def database_children(self, database_id: int, *opts: Callable[["CatalogListOptions"], None]) -> DatabaseChildrenResult:
        if not database_id:
            raise ErrIDRequired
        body: dict[str, Any] = {"id": database_id}
        _add_catalog_list_options(body, opts)
        return _database_children_result(self._catalog_post("/catalog/database/children", body))

    def database_children_raw(self, body: dict[str, Any]) -> DatabaseChildrenResult:
        return _database_children_result(self._catalog_post("/catalog/database/children", body))

    def database_table_leaves(
        self,
        database_id: int,
        *,
        page_size: int | None = None,
        page_token: str | None = None,
        search: str | None = None,
    ) -> DatabaseTableLeavesResult:
        if not database_id:
            raise ErrIDRequired
        body: dict[str, Any] = {"database_id": database_id}
        if page_size is not None:
            body["page_size"] = page_size
        if page_token is not None:
            body["page_token"] = page_token
        if search is not None:
            body["search"] = search
        return _database_table_leaves_result(self._catalog_post("/catalog/database/table-leaves", body))

    def search_data_dashboard_tables(
        self,
        *,
        search: str | None = None,
        page_size: int | None = None,
        page_token: str | None = None,
    ) -> DataDashboardTableSearchResult:
        body: dict[str, Any] = {}
        if search is not None:
            body["search"] = search
        if page_size is not None:
            body["page_size"] = page_size
        if page_token is not None:
            body["page_token"] = page_token
        return _data_dashboard_table_search_result(
            self._catalog_post("/catalog/data-dashboard/table-search", body)
        )

    def create_volume(self, database_id: int, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> IDResult:
        if not database_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        body: dict[str, Any] = {"database_id": database_id, "name": name}
        _add_catalog_info_options(body, opts)
        return _id_result(self._catalog_post("/catalog/volume/create", body))

    def create_volume_raw(self, body: dict[str, Any]) -> IDResult:
        return _id_result(self._catalog_post("/catalog/volume/create", body))

    def create_volume_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/volume/create", workspace_id=self._workspace_id, body=body)

    def volume_info(self, volume_id: str) -> VolumeInfoResult:
        if not volume_id:
            raise ErrIDRequired
        return _volume_info_result(self._catalog_post("/catalog/volume/info", {"id": volume_id}))

    def volume_info_raw(self, body: dict[str, Any]) -> VolumeInfoResult:
        return _volume_info_result(self._catalog_post("/catalog/volume/info", body))

    def update_volume(self, volume_id: int, name: str, *opts: Callable[["CatalogInfoOptions"], None]) -> IDResult:
        if not volume_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        body: dict[str, Any] = {"id": volume_id, "name": name}
        _add_catalog_info_options(body, opts)
        return _id_result(self._catalog_post("/catalog/volume/update", body))

    def update_volume_raw(self, body: dict[str, Any]) -> IDResult:
        return _id_result(self._catalog_post("/catalog/volume/update", body))

    def delete_volume(self, volume_id: int) -> None:
        if not volume_id:
            raise ErrIDRequired
        self._catalog_post("/catalog/volume/delete", {"id": volume_id})

    def delete_volume_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/volume/delete", body)

    def volume_full_path(self, volume_id: int) -> PathResult:
        if not volume_id:
            raise ErrIDRequired
        return _path_result(self._catalog_post("/catalog/volume/full_path", {"id": volume_id}))

    def volume_full_path_raw(self, body: dict[str, Any]) -> PathResult:
        return _path_result(self._catalog_post("/catalog/volume/full_path", body))

    def create_table(
        self,
        database_id: int,
        name: str,
        columns: list[dict[str, Any]],
        *opts: Callable[["CreateTableOptions"], None],
    ) -> CatalogCreateTableResult:
        if not database_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        if not columns:
            raise ErrColumnsRequired
        body: dict[str, Any] = {"database_id": database_id, "name": name, "columns": columns}
        _add_create_table_options(body, opts)
        return _catalog_create_table_result(self._catalog_post("/catalog/table/create", body))

    def create_table_raw(self, body: dict[str, Any]) -> CatalogCreateTableResult:
        return _catalog_create_table_result(self._catalog_post("/catalog/table/create", body))

    def create_table_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/table/create", workspace_id=self._workspace_id, body=body)

    def create_table_from_columns(
        self,
        database_id: int,
        name: str,
        columns: list[TableColumn],
        *opts: Callable[["CreateTableOptions"], None],
    ) -> CatalogCreateTableResult:
        if not columns:
            raise ErrColumnsRequired
        return self.create_table(database_id, name, [column.to_dict() for column in columns], *opts)

    def table_info(self, table_id: int, *opts: Callable[["TableLookupOptions"], None]) -> CatalogTableInfoResult:
        return _catalog_table_info_result(self._catalog_post("/catalog/table/info", _table_lookup_body(table_id, opts)))

    def table_info_raw(self, body: dict[str, Any]) -> CatalogTableInfoResult:
        return _catalog_table_info_result(self._catalog_post("/catalog/table/info", body))

    def multi_table_info(self, *table_ids: int) -> CatalogMultiTableInfoResult:
        return _catalog_multi_table_info_result(self._catalog_post("/catalog/table/multi_info", {"ids": list(table_ids)}))

    def multi_table_info_raw(self, body: dict[str, Any]) -> CatalogMultiTableInfoResult:
        return _catalog_multi_table_info_result(self._catalog_post("/catalog/table/multi_info", body))

    def delete_table(self, table_id: int) -> None:
        if not table_id:
            raise ErrIDRequired
        self._catalog_post("/catalog/table/delete", {"id": table_id})

    def delete_table_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/table/delete", body)

    def table_data(self, table_id: int, *opts: Callable[["TableDataOptions"], None]) -> CatalogTableDataResult:
        return _catalog_table_data_result(self._catalog_post("/catalog/table/data", _table_data_body(table_id, opts)))

    def table_data_raw(self, body: dict[str, Any]) -> CatalogTableDataResult:
        return _catalog_table_data_result(self._catalog_post("/catalog/table/data", body))

    def preview_table(self, table_id: int, *opts: Callable[["TableDataOptions"], None]) -> CatalogTableDataResult:
        return _catalog_table_data_result(self._catalog_post("/catalog/table/preview", _table_data_body(table_id, opts)))

    def preview_table_raw(self, body: dict[str, Any]) -> CatalogTableDataResult:
        return _catalog_table_data_result(self._catalog_post("/catalog/table/preview", body))

    def download_table(self, table_id: int) -> StreamResponse:
        if not table_id:
            raise ErrIDRequired
        return self._download("POST", "/catalog/table/download", {"id": table_id})

    def table_exists(self, database_id: int, name: str) -> BoolDataResult:
        if not database_id:
            raise ErrIDRequired
        if not name:
            raise ErrNameRequired
        return _bool_data_result(self._catalog_post("/catalog/table/exist", {"database_id": database_id, "name": name}))

    def table_exists_raw(self, body: dict[str, Any]) -> BoolDataResult:
        return _bool_data_result(self._catalog_post("/catalog/table/exist", body))

    def table_full_path(self, table_id: int) -> PathResult:
        if not table_id:
            raise ErrIDRequired
        return _path_result(self._catalog_post("/catalog/table/full_path", {"id": table_id}))

    def table_full_path_raw(self, body: dict[str, Any]) -> PathResult:
        return _path_result(self._catalog_post("/catalog/table/full_path", body))

    def truncate_table(self, table_id: int) -> None:
        if not table_id:
            raise ErrIDRequired
        self._catalog_post("/catalog/table/truncate", {"id": table_id})

    def truncate_table_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/table/truncate", body)

    def table_overview(self, database_id: int) -> CatalogTableOverviewResult:
        if not database_id:
            raise ErrIDRequired
        return _catalog_table_overview_result(self._catalog_post("/catalog/table/overview", {"id": database_id}))

    def table_overview_raw(self, body: dict[str, Any]) -> CatalogTableOverviewResult:
        return _catalog_table_overview_result(self._catalog_post("/catalog/table/overview", body))

    def list_workspace_files(self, *opts: Callable[["QueryOptions"], None]) -> WorkspaceFileListResult:
        """Discover IAM-visible placements using the caller's ordinary or runtime identity."""
        path = _with_query(f"/workspaces/{_path_id(self._workspace_id)}/files", opts)
        return _product_message(self._request("GET", path), WorkspaceFileListResult(), "workspace file list")

    def files(self, *opts: Callable[["FileListOptions"], None]) -> CatalogFileListResult:
        return _catalog_file_list_result(self._catalog_post("/catalog/file/list", _file_list_body(opts)))

    def create_file(self, volume_id: int, *file_ids: str) -> None:
        if not volume_id:
            raise ErrVolumeIDRequired
        if not file_ids:
            raise ErrFileIDsRequired
        self._catalog_post("/catalog/file/create", {"volume_id": volume_id, "file_ids": list(file_ids)})

    def create_file_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/file/create", body)

    def create_file_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/file/create", workspace_id=self._workspace_id, body=body)

    def file_info(self, file_id: str) -> FileInfoResult:
        if not file_id:
            raise ErrFileIDRequired
        return _file_info_result(self._catalog_post("/catalog/file/info", {"file_id": file_id}))

    def file_info_raw(self, body: dict[str, Any]) -> FileInfoResult:
        return _file_info_result(self._catalog_post("/catalog/file/info", body))

    def delete_file(self, file_id: str, volume_id: str) -> None:
        if not file_id:
            raise ErrFileIDRequired
        self._catalog_post("/catalog/file/delete", {"id": file_id, "volume_id": volume_id})

    def delete_file_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/file/delete", body)

    def delete_file_ref(self, volume_id: int, *file_ids: str) -> None:
        if not volume_id:
            raise ErrVolumeIDRequired
        if not file_ids:
            raise ErrFileIDsRequired
        self._catalog_post("/catalog/file/delete_ref", {"volume_id": volume_id, "file_ids": list(file_ids)})

    def delete_file_ref_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/file/delete_ref", body)

    def trigger_file_workflow(self, volume_id: int, *file_ids: str) -> TriggerFileWorkflowResult:
        if not volume_id:
            raise ErrVolumeIDRequired
        if not file_ids:
            raise ErrFileIDsRequired
        return _trigger_file_workflow_result(
            self._catalog_post("/catalog/file/trigger_workflow", {"volume_id": volume_id, "file_ids": list(file_ids)})
        )

    def download_file(self, volume_id: str, file_id: str, *opts: Callable[["DownloadFileOptions"], None]) -> StreamResponse:
        if not volume_id:
            raise ErrVolumeIDRequired
        if not file_id:
            raise ErrFileIDRequired
        body: dict[str, Any] = {"volume_id": volume_id, "file_id": file_id}
        options = DownloadFileOptions()
        for opt in opts:
            opt(options)
        if options.as_zip is not None:
            body["as_zip"] = options.as_zip
        return self._download("POST", "/catalog/file/download", body)

    def preview_file(self, volume_id: str, file_id: str) -> StreamResponse:
        if not volume_id:
            raise ErrVolumeIDRequired
        if not file_id:
            raise ErrFileIDRequired
        return self._download("POST", "/catalog/file/preview_stream", {"volume_id": volume_id, "file_id": file_id})

    def upload_bytes(self, filename: str, data: bytes) -> UploadFileResult:
        return self.upload(filename, data)

    def upload_file(self, file_path: str) -> UploadFileResult:
        """Upload a caller-supplied local file path; local file input convenience method, not AI file-discovery, local-filesystem probing, filename inference, or default upload entry point."""
        with open(file_path, "rb") as file:
            return self.upload(os.path.basename(file_path), file.read())

    def upload(self, filename: str, data: bytes, *, content_type: str = "application/octet-stream", external_source_uri: Optional[str] = None) -> UploadFileResult:
        body, content_type = self._upload_payload(filename, data, content_type, external_source_uri=external_source_uri)
        return _upload_file_result(self._raw_request("POST", "/catalog/file/upload", body, content_type))

    def upload_private_bytes(self, filename: str, data: bytes) -> UploadFileResult:
        return self.upload_private(filename, data)

    def upload_private_file(self, file_path: str) -> UploadFileResult:
        """Upload a caller-supplied local file path to the current user's private Catalog volume; local file input convenience method, not AI file-discovery, local-filesystem probing, filename inference, or default upload entry point."""
        with open(file_path, "rb") as file:
            return self.upload_private(os.path.basename(file_path), file.read())

    def upload_private(self, filename: str, data: bytes, *, content_type: str = "application/octet-stream") -> UploadFileResult:
        workspace_id = _path_id(self._workspace_id)
        body, content_type = self._upload_payload(filename, data, content_type)
        return _upload_file_result(
            self._raw_request("POST", f"/workspaces/{workspace_id}/catalog-files/uploads", body, content_type)
        )

    def upload_runtime_artifact(self, filename: str, data: bytes) -> RuntimeArtifactUploadResult:
        """Publish one sandbox-child file through MOI's task-scoped native endpoint.

        Configure the client with ``with_runtime_authorization`` using only the
        short-lived child environment value. This native-only transport is not
        part of the moi-backend route manifest.
        """
        workspace_id = _path_id(self._workspace_id)
        body, content_type = self._upload_payload(filename, data)
        return _runtime_artifact_upload_result(
            self._raw_request("POST", f"/workspaces/{workspace_id}/runtime-artifacts", body, content_type)
        )

    def analyze_runtime_image(self, filename: str, data: bytes, question: str) -> RuntimeImageAnalysisResult:
        """Analyze one sandbox-child image through MOI's task-scoped native endpoint.

        Configure the client with ``with_runtime_authorization`` using the
        short-lived child environment value. This native-only transport is not
        part of the moi-backend route manifest.
        """
        workspace_id = _path_id(self._workspace_id)
        if not filename:
            raise Error("ErrFilenameRequired", "filename is required")
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, {"question": question}, [("file", filename, data)])
        return _runtime_image_analysis_result(
            self._raw_request(
                "POST",
                f"/workspaces/{workspace_id}/runtime-image-analysis",
                body,
                f"multipart/form-data; boundary={boundary}",
            )
        )

    def download_workspace_file(self, file_id: str) -> StreamResponse:
        """Stream a task-visible workspace file; callers must close the stream."""
        workspace_id = _path_id(self._workspace_id)
        return self._download("GET", f"/workspaces/{workspace_id}/files/{_path_id(file_id)}/download")

    def _upload_payload(self, filename: str, data: bytes, content_type: str = "application/octet-stream", external_source_uri: Optional[str] = None) -> tuple[bytes, str]:
        if not filename:
            raise Error("ErrFilenameRequired", "filename is required")
        fields: dict[str, str] = {}
        origin = (external_source_uri or "").strip()
        if origin:
            fields["external_source_uri"] = origin
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, fields, [("file", filename, data)], file_content_type=content_type)
        return body, f"multipart/form-data; boundary={boundary}"

    def upload_raw_result(self, fields: Optional[dict[str, str]] = None, files: Optional[list[tuple[str, str, bytes]]] = None) -> ProductResult:
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, fields or {}, files or [])
        return self._client._raw_product_result(
            "POST",
            "/catalog/file/upload",
            self._workspace_id,
            body,
            f"multipart/form-data; boundary={boundary}",
        )

    def data_asset(self, asset_id: str) -> CatalogDataAssetResolveResult:
        return _catalog_data_asset_resolve_result(self._request("GET", f"/catalog/data-assets/{_path_id(asset_id)}"))

    def batch_get_data_assets(self, *raw_file_ids: str) -> CatalogBatchGetDataAssetsResult:
        if not raw_file_ids:
            raise ErrFileIDsRequired
        return _catalog_batch_get_data_assets_result(
            self._catalog_post("/catalog/data-assets/batch-get", {"raw_file_ids": list(raw_file_ids)})
        )

    def file_data_asset(self, file_id: str) -> CatalogDataAssetResolveResult:
        return _catalog_data_asset_resolve_result(self._request("GET", f"/catalog/files/{_path_id(file_id)}/data-asset"))

    def file_artifact(self, file_id: str) -> CatalogFileArtifactResult:
        return _catalog_file_artifact_result(self._request("GET", f"/catalog/file-artifacts/{_path_id(file_id)}"))

    def batch_resolve_file_artifacts(self, *file_ids: str) -> CatalogBatchResolveFileArtifactsResult:
        if not file_ids:
            raise ErrFileIDsRequired
        return _catalog_batch_resolve_file_artifacts_result(
            self._catalog_post("/catalog/file-artifacts:batchResolve", {"file_ids": list(file_ids)})
        )

    def create_folder(
        self,
        parent_volume_id: int,
        database_id: int,
        name: str,
        *opts: Callable[["CreateFolderOptions"], None],
    ) -> CreateFolderResult:
        if not parent_volume_id:
            raise ErrVolumeIDRequired
        if not name:
            raise ErrNameRequired
        body: dict[str, Any] = {"parent_volume_id": parent_volume_id, "database_id": database_id, "name": name}
        options = CreateFolderOptions()
        for opt in opts:
            opt(options)
        if options.description is not None:
            body["description"] = options.description
        return _create_folder_result(self._catalog_post("/catalog/folder/create", body))

    def create_folder_raw(self, body: dict[str, Any]) -> CreateFolderResult:
        return _create_folder_result(self._catalog_post("/catalog/folder/create", body))

    def create_folder_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/catalog/folder/create", workspace_id=self._workspace_id, body=body)

    def update_folder(self, folder_id: int, *opts: Callable[["UpdateFolderOptions"], None]) -> None:
        if not folder_id:
            raise ErrIDRequired
        body: dict[str, Any] = {"id": folder_id}
        options = UpdateFolderOptions()
        for opt in opts:
            opt(options)
        if options.name is not None:
            body["name"] = options.name
        if options.description is not None:
            body["description"] = options.description
        self._catalog_post("/catalog/folder/update", body)

    def update_folder_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/folder/update", body)

    def delete_folder(self, folder_id: int) -> None:
        if not folder_id:
            raise ErrIDRequired
        self._catalog_post("/catalog/folder/delete", {"id": folder_id})

    def delete_folder_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/folder/delete", body)

    def clean_folder(self, folder_id: int) -> None:
        if not folder_id:
            raise ErrIDRequired
        self._catalog_post("/catalog/folder/clean", {"id": folder_id})

    def clean_folder_raw(self, body: dict[str, Any]) -> None:
        self._catalog_post("/catalog/folder/clean", body)

    def run_nl2sql(self, database_id: int, sql: str) -> CatalogNL2SQLRunResult:
        if not database_id:
            raise ErrIDRequired
        if not sql:
            raise ErrSQLRequired
        return _catalog_nl2sql_run_result(self._catalog_post("/catalog/nl2sql/run_sql", {"database_id": database_id, "sql": sql}))

    def run_nl2sql_raw(self, body: dict[str, Any]) -> CatalogNL2SQLRunResult:
        return _catalog_nl2sql_run_result(self._catalog_post("/catalog/nl2sql/run_sql", body))

    def _catalog_post(self, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        return self._request("POST", path, body)

def _knowledge_runtime_request_body(request: Message) -> dict[str, Any]:
    """Match Go's integer JSON values without changing presence or opaque data."""
    body = MessageToDict(request, preserving_proto_field_name=True)

    def encode_integer_fields(message: Message, encoded: dict[str, Any]) -> None:
        for field, value in message.ListFields():
            if field.type == field.TYPE_INT64:
                encoded[field.name] = value
            elif field.message_type is not None and not field.message_type.full_name.startswith("google.protobuf."):
                if field.is_repeated:
                    for index, child in enumerate(value):
                        encode_integer_fields(child, encoded[field.name][index])
                else:
                    encode_integer_fields(value, encoded[field.name])

    encode_integer_fields(request, body)
    return body


class KnowledgeService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed semantic model and entry handles for user-facing workflows."""

    def find_files(self, request: KnowledgeFindFilesRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeFindFilesRequest):
            raise TypeError("request must be KnowledgeFindFilesRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/find-files", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def search(self, request: KnowledgeSearchRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeSearchRequest):
            raise TypeError("request must be KnowledgeSearchRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/search", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def read_document(self, request: KnowledgeReadDocumentRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeReadDocumentRequest):
            raise TypeError("request must be KnowledgeReadDocumentRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/read-document", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def search_document(self, request: KnowledgeSearchDocumentRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeSearchDocumentRequest):
            raise TypeError("request must be KnowledgeSearchDocumentRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/search-document", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def search_images(self, request: KnowledgeSearchImagesRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeSearchImagesRequest):
            raise TypeError("request must be KnowledgeSearchImagesRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/search-images", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def read_evidence(self, request: KnowledgeReadEvidenceRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeReadEvidenceRequest):
            raise TypeError("request must be KnowledgeReadEvidenceRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/read-evidence", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def describe_tables(self, request: KnowledgeDescribeTablesRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeDescribeTablesRequest):
            raise TypeError("request must be KnowledgeDescribeTablesRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/describe-tables", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def query(self, request: KnowledgeQueryRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeQueryRequest):
            raise TypeError("request must be KnowledgeQueryRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/query", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def cite(self, request: KnowledgeCiteRequest) -> KnowledgeRuntimeResult:
        if not isinstance(request, KnowledgeCiteRequest):
            raise TypeError("request must be KnowledgeCiteRequest")
        body = _knowledge_runtime_request_body(request)
        return _product_message(self._request("POST", "/semantic-models/runtime/cite", body), KnowledgeRuntimeResult(), "runtime knowledge result")

    def import_model(self, request: SemanticModelImportRequest) -> SemanticModelInfo:
        if not isinstance(request, SemanticModelImportRequest): raise TypeError("request must be SemanticModelImportRequest")
        body = MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(self._request("POST","/semantic-models/import",body),SemanticModelInfo(),"imported semantic model")

    def import_models(self, requests: list[SemanticModelImportRequest]) -> SemanticModelListResult:
        if any(not isinstance(request, SemanticModelImportRequest) for request in requests): raise TypeError("requests must contain SemanticModelImportRequest")
        body = [MessageToDict(request,preserving_proto_field_name=True) for request in requests]
        return _product_message(self._request("POST","/semantic-models/import",body),SemanticModelListResult(),"imported semantic models")

    def preview_source_file(self, model_id: str, file_id: str) -> StreamResponse:
        return self._download("GET", f"/semantic-models/{_path_id(model_id)}/sources/file/{_path_id(file_id)}/preview")

    def preview_artifact(self, model_id: str, file_id: str) -> StreamResponse:
        return self._download("GET", f"/semantic-models/{_path_id(model_id)}/artifacts/{_path_id(file_id)}/preview")

    def list(self, *opts: Callable[["ListOptions"], None]) -> SemanticModelListResult:
        return _semantic_model_list_result(self._request("GET", _with_list_query("/semantic-models", opts)))

    def list_raw(self, *opts: Callable[["QueryOptions"], None]) -> SemanticModelListResult:
        return _semantic_model_list_result(self._request("GET", _with_query("/semantic-models", opts)))

    def list_result(self, *opts: Callable[["ListOptions"], None]) -> ProductResult:
        return self._client._product_result("GET", _with_list_query("/semantic-models", opts), workspace_id=self._workspace_id)

    def list_tags(self, *opts: Callable[["QueryOptions"], None]) -> SemanticModelTagListResult:
        return _semantic_model_tag_list_result(self._request("GET", _with_query("/semantic-models/tags", opts)))

    def create(self, name: str, *opts: Callable[["SemanticModelOptions"], None]) -> SemanticModelInfo:
        return self.create_with_spec(SemanticModelCreateSpec(name), *opts)

    def create_with_spec(self, spec: "SemanticModelCreateSpec", *opts: Callable[["SemanticModelOptions"], None]) -> SemanticModelInfo:
        """Create with embedding/drawing controls; policies are validated by the server."""
        if not spec.name:
            raise ErrNameRequired
        body = _semantic_model_body(spec.name, opts)
        for field in ("preserve_embedding", "text_send_dimensions", "image_send_dimensions", "drawing_structured_enabled", "drawing_number_policy"):
            value = getattr(spec, field)
            if value is not None:
                body[field] = value
        return _semantic_model_info(self._request("POST", "/semantic-models", body))

    def create_raw(self, body: dict[str, Any]) -> SemanticModelInfo:
        return _semantic_model_info(self._request("POST", "/semantic-models", body))

    def create_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/semantic-models", workspace_id=self._workspace_id, body=body)

    def get(self, model_id: str) -> SemanticModelInfo:
        return _semantic_model_info(self._request("GET", f"/semantic-models/{_path_id(model_id)}"))

    def list_referencing_agents(self, model_id: str, limit: int = 0, cursor: str = "") -> KnowledgeReferencingAgentsPage:
        opts = []
        if limit > 0:
            opts.append(with_limit(limit))
        if cursor:
            opts.append(with_query_param("cursor", cursor))
        value = self._request("GET", _with_query(f"/semantic-models/{_path_id(model_id)}/referencing-agents", tuple(opts)))
        return _product_message(value, KnowledgeReferencingAgentsPage(), "knowledge referencing agents data")

    def get_raw(self, model_id: str) -> SemanticModelInfo | SemanticModelListResult:
        if model_id == "":
            return _semantic_model_list_result(self._request("GET", "/semantic-models/"))
        value = self._request("GET", f"/semantic-models/{_path_id(model_id)}")
        return _semantic_model_info(value)

    def get_result(self, model_id: str) -> ProductResult:
        return self._client._product_result("GET", f"/semantic-models/{_path_id(model_id)}", workspace_id=self._workspace_id)

    def update(self, model_id: str, name: str, *opts: Callable[["SemanticModelOptions"], None]) -> SemanticMutationResult:
        """Update a knowledge base; name must equal its existing immutable name."""
        if not name:
            raise ErrNameRequired
        return _semantic_mutation_result(
            self._request("PUT", f"/semantic-models/{_path_id(model_id)}", _semantic_model_body(name, opts))
        )

    def update_raw(self, model_id: str, body: dict[str, Any]) -> SemanticMutationResult:
        return _semantic_mutation_result(self._request("PUT", f"/semantic-models/{_path_id(model_id)}", body))

    def update_result(self, model_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "PUT",
            f"/semantic-models/{_path_id(model_id)}",
            workspace_id=self._workspace_id,
            body=body,
        )

    def delete(self, model_id: str) -> SemanticMutationResult:
        return _semantic_mutation_result(self._request("DELETE", f"/semantic-models/{_path_id(model_id)}"))

    def delete_raw(self, model_id: str) -> SemanticMutationResult:
        return _semantic_mutation_result(self._request("DELETE", f"/semantic-models/{_path_id(model_id)}"))

    def delete_result(self, model_id: str) -> ProductResult:
        return self._client._product_result("DELETE", f"/semantic-models/{_path_id(model_id)}", workspace_id=self._workspace_id)

    def create_with_sources(
        self,
        name: str,
        sources: list[SemanticModelSourceInput],
        *opts: Callable[[SemanticModelWithSourcesOptions], None],
    ) -> SemanticModelWithSourcesResult:
        if not name:
            raise ErrNameRequired
        return _semantic_model_with_sources_result(
            self._request("POST", "/semantic-models/create-with-sources", _semantic_model_with_sources_body(name, sources, opts))
        )

    def create_empty(
        self,
        name: str,
        *opts: Callable[[SemanticModelEmptyOptions], None],
    ) -> SemanticModelEmptyResult:
        if not name:
            raise ErrNameRequired
        return _semantic_model_empty_result(
            self._request("POST", "/semantic-models/create-empty", _semantic_model_empty_body(name, opts))
        )

    def upload_local_file(self, filename: str, data: bytes) -> UploadFileResult:
        """Upload a local knowledge file before creating a semantic model."""
        if not filename:
            raise Error("ErrFilenameRequired", "filename is required")
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_file_body(boundary, "file", filename, data)
        return _upload_file_result(
            self._raw_request(
                "POST",
                "/semantic-models/local-files/upload",
                body,
                f"multipart/form-data; boundary={boundary}",
            )
        )

    def upload_model_local_file(self, model_id: str, filename: str, data: bytes) -> UploadFileResult:
        """Upload a local knowledge file for an existing semantic model."""
        if not filename:
            raise Error("ErrFilenameRequired", "filename is required")
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_file_body(boundary, "file", filename, data)
        return _upload_file_result(
            self._raw_request(
                "POST",
                f"/semantic-models/{_path_id(model_id)}/local-files/upload",
                body,
                f"multipart/form-data; boundary={boundary}",
            )
        )

    def preview_artifact(self, model_id: str, file_id: str) -> StreamResponse:
        """Stream a parsed image artifact that belongs to one semantic model."""
        if not file_id:
            raise ErrFileIDRequired
        return self._download(
            "GET",
            f"/semantic-models/{_path_id(model_id)}/artifacts/{_path_id(file_id)}/preview",
        )

    def preview_source_selection_counts(
        self, selections: list["SemanticModelSourceSelectionInput"]
    ) -> SemanticModelSourceSelectionPreviewResult:
        return _semantic_model_source_selection_preview_result(
            self._request(
                "POST",
                "/semantic-models/source-selections/preview",
                {"source_selections": _semantic_model_source_selections_body(selections)},
            )
        )

    def preview_model_source_selection_counts(
        self, model_id: str, selections: list["SemanticModelSourceSelectionInput"]
    ) -> SemanticModelSourceSelectionPreviewResult:
        return _semantic_model_source_selection_preview_result(
            self._request(
                "POST",
                f"/semantic-models/{_path_id(model_id)}/source-selections/preview",
                {"source_selections": _semantic_model_source_selections_body(selections)},
            )
        )

    def list_sources(self, model_id: str | int, *opts: Callable[['QueryOptions'], None]) -> SemanticModelSourceListResult:
        path = _with_query(f"/semantic-models/{_path_id(model_id)}/sources", opts)
        return _semantic_model_source_list_result(self._request("GET", path))

    def list_sources_page(self, model_id: str | int, page: int, page_size: int, *opts: Callable[['QueryOptions'], None]) -> SemanticModelSourceListResult:
        path = _with_query(
            f"/semantic-models/{_path_id(model_id)}/sources",
            (with_page(page), with_page_size(page_size), *opts),
        )
        return _semantic_model_source_list_result(self._request("GET", path))

    def check_source_existence(
        self,
        model_id: str,
        file_ids: list[str],
        table_ids: list[int],
    ) -> SemanticModelSourceExistenceResult:
        return _semantic_model_source_existence_result(
            self._request(
                "POST",
                f"/semantic-models/{_path_id(model_id)}/sources/existence",
                {"file_ids": file_ids, "table_ids": table_ids},
            )
        )

    def append_sources(
        self,
        model_id: str,
        sources: list[SemanticModelSourceInput],
        *,
        selections: list[SemanticModelSourceSelectionInput] | None = None,
    ) -> SemanticModelAppendSourcesResult:
        body: dict[str, Any] = {"sources": _semantic_model_sources_body(sources)}
        if selections is not None:
            body["source_selections"] = _semantic_model_source_selections_body(selections)
        return _semantic_model_append_sources_result(
            self._request("POST", f"/semantic-models/{_path_id(model_id)}/sources", body)
        )

    def backfill_legacy_sources(self, model_id: str) -> SemanticMutationResult:
        return _semantic_mutation_result(self._request("POST", f"/semantic-models/{_path_id(model_id)}/sources/backfill-legacy"))

    def delete_source(self, model_id: str, source_id: str) -> SemanticMutationResult:
        model_path, source_path = _semantic_model_source_path(model_id, source_id)
        return _semantic_mutation_result(self._request("DELETE", f"/semantic-models/{model_path}/sources/{source_path}"))

    def get_source_document(
        self,
        model_id: str,
        source_id: str,
        *opts: Callable[["QueryOptions"], None],
    ) -> SemanticModelSourceDocument:
        model_path, source_path = _semantic_model_source_path(model_id, source_id)
        return _semantic_model_source_document(
            self._request("GET", _with_query(f"/semantic-models/{model_path}/sources/{source_path}/document", opts))
        )

    def update_source_governance(
        self,
        model_id: str,
        source_id: str,
        *opts: Callable[[SemanticModelSourceGovernanceOptions], None],
    ) -> SemanticModelSourceGovernanceResult:
        model_path, source_path = _semantic_model_source_path(model_id, source_id)
        return _semantic_model_source_governance_result(
            self._request(
                "PATCH",
                f"/semantic-models/{model_path}/sources/{source_path}/governance",
                _semantic_model_source_governance_body(opts),
            )
        )

    def update_segment(
        self,
        model_id: str,
        source_id: str,
        segment_id: str,
        input: SemanticModelSegmentUpdateInput,
    ) -> SemanticModelSegmentMutationResult:
        model_path, source_path, segment_path = _semantic_model_segment_path(model_id, source_id, segment_id)
        return _semantic_model_segment_mutation_result(
            self._request(
                "PATCH",
                f"/semantic-models/{model_path}/sources/{source_path}/segments/{segment_path}",
                _semantic_model_segment_update_body(input),
            )
        )

    def delete_segment(
        self,
        model_id: str,
        source_id: str,
        segment_id: str,
        base: SemanticModelSegmentBase,
    ) -> SemanticModelSegmentMutationResult:
        model_path, source_path, segment_path = _semantic_model_segment_path(model_id, source_id, segment_id)
        return _semantic_model_segment_mutation_result(
            self._request(
                "DELETE",
                f"/semantic-models/{model_path}/sources/{source_path}/segments/{segment_path}",
                _semantic_model_segment_base_body(base),
            )
        )

    def create_segment(
        self,
        model_id: str,
        source_id: str,
        input: SemanticModelSegmentCreateInput,
    ) -> SemanticModelSegmentMutationResult:
        model_path, source_path = _semantic_model_source_path(model_id, source_id)
        return _semantic_model_segment_mutation_result(
            self._request(
                "POST",
                f"/semantic-models/{model_path}/sources/{source_path}/segments",
                _semantic_model_segment_create_body(input),
            )
        )

    def update_segment_enabled(
        self,
        model_id: str,
        source_id: str,
        segment_id: str,
        base: SemanticModelSegmentBase,
        enabled: bool,
    ) -> SemanticModelSegmentMutationResult:
        model_path, source_path, segment_path = _semantic_model_segment_path(model_id, source_id, segment_id)
        body = _semantic_model_segment_base_body(base)
        body["enabled"] = enabled
        return _semantic_model_segment_mutation_result(
            self._request("PATCH", f"/semantic-models/{model_path}/sources/{source_path}/segments/{segment_path}/enabled", body)
        )

    def reembed_segments(self, model_id: str, source_id: str, base: SemanticModelSegmentBase) -> SemanticModelSegmentMutationResult:
        model_path, source_path = _semantic_model_source_path(model_id, source_id)
        return _semantic_model_segment_mutation_result(
            self._request(
                "POST",
                f"/semantic-models/{model_path}/sources/{source_path}/segments/re-embedding",
                _semantic_model_segment_base_body(base),
            )
        )

    def list_source_jobs(self, model_id: str) -> SemanticModelSourceJobListResult:
        return _semantic_model_source_job_list_result(self._request("GET", f"/semantic-models/{_path_id(model_id)}/source-jobs"))

    def reconcile_source_jobs(self, model_id: str, *, retry_source_row_id: str = "") -> SemanticMutationResult:
        """Retry the selected failed source; an empty retry_source_row_id does not advance jobs."""
        body = {"retry_source_row_id": retry_source_row_id} if retry_source_row_id else None
        return _semantic_mutation_result(self._request("POST", f"/semantic-models/{_path_id(model_id)}/source-jobs/reconcile", body))

    def list_entries(self, model_id: str, *opts: Callable[["QueryOptions"], None]) -> SemanticEntryListResult:
        return _semantic_entry_list_result(
            self._request("GET", _with_query(f"/semantic-models/{_path_id(model_id)}/entries", opts))
        )

    def list_entries_raw(self, model_id: str, *opts: Callable[["QueryOptions"], None]) -> SemanticEntryListResult:
        return _semantic_entry_list_result(
            self._request("GET", _with_query(f"/semantic-models/{_path_id(model_id)}/entries", opts))
        )

    def create_entry(self, model_id: str, entry: "SemanticEntryInput") -> SemanticEntry:
        _validate_semantic_entry(entry)
        return _semantic_entry(
            self._request("POST", f"/semantic-models/{_path_id(model_id)}/entries", _semantic_entry_body(entry))
        )

    def create_entry_raw(self, model_id: str, body: dict[str, Any]) -> SemanticEntry:
        return _semantic_entry(self._request("POST", f"/semantic-models/{_path_id(model_id)}/entries", body))

    def update_entry(self, model_id: str, entry_id: str, entry: "SemanticEntryInput") -> SemanticMutationResult:
        _validate_semantic_entry(entry)
        model_path, entry_path = _semantic_entry_path(model_id, entry_id)
        return _semantic_mutation_result(
            self._request("PUT", f"/semantic-models/{model_path}/entries/{entry_path}", _semantic_entry_body(entry))
        )

    def update_entry_raw(self, model_id: str, entry_id: str, body: dict[str, Any]) -> SemanticMutationResult:
        model_path, entry_path = _semantic_entry_path(model_id, entry_id)
        return _semantic_mutation_result(self._request("PUT", f"/semantic-models/{model_path}/entries/{entry_path}", body))

    def delete_entry(self, model_id: str, entry_id: str) -> SemanticMutationResult:
        model_path, entry_path = _semantic_entry_path(model_id, entry_id)
        return _semantic_mutation_result(self._request("DELETE", f"/semantic-models/{model_path}/entries/{entry_path}"))

    def delete_entry_raw(self, model_id: str, entry_id: str) -> SemanticMutationResult:
        model_path, entry_path = _semantic_entry_path(model_id, entry_id)
        return _semantic_mutation_result(self._request("DELETE", f"/semantic-models/{model_path}/entries/{entry_path}"))

    def import_entries(self, model_id: str, entries: list["SemanticEntryInput"]) -> SemanticImportResult:
        if not entries:
            raise ErrEntriesRequired
        for entry in entries:
            _validate_semantic_entry(entry)
        return _semantic_import_result(
            self._request("POST", f"/semantic-models/{_path_id(model_id)}/import", _semantic_import_body(entries))
        )

    def import_entries_raw(self, model_id: str, body: dict[str, Any]) -> SemanticImportResult:
        return _semantic_import_result(self._request("POST", f"/semantic-models/{_path_id(model_id)}/import", body))

    def export(self, model_id: str) -> SemanticExportResult:
        return _semantic_export_result(self._request("GET", f"/semantic-models/{_path_id(model_id)}/export"))

    def export_raw(self, model_id: str) -> SemanticExportResult:
        return _semantic_export_result(self._request("GET", f"/semantic-models/{_path_id(model_id)}/export"))

    def validate(self, model_id: str) -> SemanticValidateResult:
        return _semantic_validate_result(self._request("POST", f"/semantic-models/{_path_id(model_id)}/validate", None))

    def validate_raw(self, model_id: str) -> SemanticValidateResult:
        return _semantic_validate_result(self._request("POST", f"/semantic-models/{_path_id(model_id)}/validate", None))

    def search_drawings(
        self,
        knowledge_base_id: int,
        *,
        drawing_number: Optional[str] = None,
        query: Optional[str] = None,
        query_image_path: Optional[str] = None,
        query_image_bytes: Optional[bytes] = None,
        query_image_filename: Optional[str] = None,
        query_image: Any = None,
        top_k: Optional[int] = None,
    ) -> dict[str, Any]:
        """Run POST /newmoi/drawings/search. Exact drawing_number is JSON; a query image is multipart."""
        if knowledge_base_id is None or int(knowledge_base_id) <= 0:
            raise ErrKnowledgeBaseIDRequired
        number = (drawing_number or "").strip()
        query_text = (query or "").strip()
        filename = (query_image_filename or "").strip()
        file_bytes: Optional[bytes] = None
        if query_image_path:
            with open(query_image_path, "rb") as handle:
                file_bytes = handle.read()
            if not filename:
                filename = os.path.basename(query_image_path)
        elif query_image_bytes is not None:
            file_bytes = query_image_bytes
        elif query_image is not None:
            file_bytes = query_image.read() if hasattr(query_image, "read") else bytes(query_image)
        if file_bytes is not None and not filename:
            raise Error("ErrFilenameRequired", "filename is required")
        if not number and not query_text and file_bytes is None:
            raise ErrQueryRequired
        if file_bytes is None:
            body: dict[str, Any] = {"knowledge_base_id": int(knowledge_base_id)}
            if number:
                body["drawing_number"] = number
            if query_text:
                body["query"] = query_text
            if top_k is not None:
                body["top_k"] = int(top_k)
            return _drawing_search_result(self._request("POST", "/drawings/search", body))
        fields: dict[str, str] = {"knowledge_base_id": str(int(knowledge_base_id))}
        if number:
            fields["drawing_number"] = number
        if query_text:
            fields["query"] = query_text
        if top_k is not None:
            fields["top_k"] = str(int(top_k))
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        raw = _multipart_body(boundary, fields, [("file", filename, file_bytes)])
        value = self._raw_request(
            "POST",
            "/drawings/search",
            raw,
            f"multipart/form-data; boundary={boundary}",
        )
        return _drawing_search_result(value)

    def get_drawing_provenance(self, knowledge_base_id: int, source_file_id: str, page_number: Optional[int] = None) -> dict[str, Any]:
        """Run GET /newmoi/drawings/{source_file_id}/provenance."""
        if knowledge_base_id is None or int(knowledge_base_id) <= 0:
            raise ErrKnowledgeBaseIDRequired
        if not source_file_id:
            raise ErrIDRequired
        params = [("knowledge_base_id", str(int(knowledge_base_id)))]
        if page_number is not None and page_number > 0:
            params.append(("page_number", str(int(page_number))))
        value = self._request("GET", _with_query(f"/drawings/{_path_id(source_file_id)}/provenance", tuple(with_query_param(key, item) for key, item in params)))
        if not isinstance(value, dict):
            raise Error("ErrResponseInvalid", "drawing provenance response is invalid")
        return value

    def legacy_vector_indexes(self) -> Any:
        return self._request("GET", "/vector-indexes")

    def create_legacy_vector_index(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/vector-indexes", body)

    def delete_legacy_vector_index(self, index_id: str) -> Any:
        if not index_id:
            raise ErrIDRequired
        return self._request("DELETE", f"/vector-indexes/{_path_id(index_id)}")

class WorkflowService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed workflow, run, operator, template, and WorkItem API handles for user-facing workflows."""

    def create_worker_task(self, request: WorkflowWorkerTaskCreateRequest) -> WorkflowWorkerTask:
        if not isinstance(request, WorkflowWorkerTaskCreateRequest):
            raise TypeError("request must be WorkflowWorkerTaskCreateRequest")
        body = {"task": MessageToDict(request, preserving_proto_field_name=True)}
        value = self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/tasks", body)
        if not isinstance(value, dict) or set(value) != {"task"}:
            raise Error("ErrResponseInvalid", "worker task response is invalid")
        return _product_message(value["task"], WorkflowWorkerTask(), "worker task")

    def versions(self, workflow_id: str) -> WorkflowVersionList:
        return _product_message(self._request("GET", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions"), WorkflowVersionList(), "workflow version")

    def version(self, workflow_id: str, version_id: str) -> WorkflowVersion:
        return _product_message(self._request("GET", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions/{_path_id(version_id)}"), WorkflowVersion(), "workflow version")

    def version_by_number(self, workflow_id: str, number: int) -> WorkflowVersion:
        return _product_message(self._request("GET", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions/by-number/{number}"), WorkflowVersion(), "workflow version")

    def latest_published_version(self, workflow_id: str) -> WorkflowVersion:
        return _product_message(self._request("GET", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions/latest-published"), WorkflowVersion(), "workflow version")

    def create_version(self, workflow_id: str, request: WorkflowVersionCreateRequest) -> WorkflowVersion:
        return _product_message(self._request("POST", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions", MessageToDict(request, preserving_proto_field_name=True)), WorkflowVersion(), "workflow version")

    def publish_version(self, workflow_id: str, version_id: str) -> WorkflowVersion:
        return _product_message(self._request("POST", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions/{_path_id(version_id)}/publish"), WorkflowVersion(), "workflow version")

    def deprecate_version(self, workflow_id: str, version_id: str) -> WorkflowVersion:
        return _product_message(self._request("POST", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions/{_path_id(version_id)}/deprecate"), WorkflowVersion(), "workflow version")

    def delete_version(self, workflow_id: str, version_id: str) -> None:
        self._request("DELETE", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/versions/{_path_id(version_id)}")

    def submit_candidate(self, request: WorkflowCandidateSubmitRequest) -> WorkflowCandidateBundle:
        if not isinstance(request, WorkflowCandidateSubmitRequest): raise TypeError("request must be WorkflowCandidateSubmitRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        if hasattr(request,"catalog_id"): body["catalog_id"] = request.catalog_id
        if hasattr(request,"scratch") and request.HasField("scratch"): body["scratch"]["catalog_id"] = request.scratch.catalog_id
        return _product_message(self._request("POST","/workflow/v2/workflow-candidates/submit",body),WorkflowCandidateBundle(),"workflow authoring result")

    def test_candidate(self, request: WorkflowCandidateTestRequest) -> WorkflowCandidateTestReport:
        if not isinstance(request, WorkflowCandidateTestRequest): raise TypeError("request must be WorkflowCandidateTestRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        if request.catalog_id: body["catalog_id"] = request.catalog_id
        if request.HasField("scratch"): body["scratch"] = _workflow_scratch_scope_body(request.scratch)
        return _product_message(self._request("POST","/workflow/v2/workflow-candidates/test",body),WorkflowCandidateTestReport(),"workflow authoring result")

    def ensure_test_scratch(self, request: WorkflowScratchScope) -> WorkflowScratchLease:
        if not isinstance(request, WorkflowScratchScope): raise TypeError("request must be WorkflowScratchScope")
        return _product_message(self._request("POST","/workflow/v2/workflow-test-scratch/ensure",_workflow_scratch_scope_body(request)),WorkflowScratchLease(),"workflow authoring result")

    def observe_test_scratch(self, request: WorkflowScratchScope) -> WorkflowScratchObservation:
        if not isinstance(request, WorkflowScratchScope): raise TypeError("request must be WorkflowScratchScope")
        return _product_message(self._request("POST","/workflow/v2/workflow-test-scratch/observe",_workflow_scratch_scope_body(request)),WorkflowScratchObservation(),"workflow authoring result")

    def reset_test_scratch(self, task_id: str) -> WorkflowScratchResetResult:
        return _product_message(self._request("POST","/workflow/v2/workflow-test-scratch/reset",{"task_id":task_id}),WorkflowScratchResetResult(),"workflow scratch reset")

    def apps(self, *options: Callable[["QueryOptions"], None]) -> Any:
        return self._request("GET", _with_query("/workflow/v2/workflow-apps", options))

    def list(self, *opts: Callable[["ListOptions"], None]) -> WorkflowListEnvelope:
        return _workflow_list_envelope(self._request("GET", _with_list_query("/workflow/v2/workflow-apps", opts)))

    def list_result(self, *opts: Callable[["ListOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "GET",
            _with_list_query("/workflow/v2/workflow-apps", opts),
            workspace_id=self._workspace_id,
        )

    def deploy(self, name: str, dsl_yaml: str, *opts: Callable[["WorkflowDeployOptions"], None]) -> WorkflowDeploymentEnvelope:
        if not name:
            raise ErrNameRequired
        return _workflow_deployment_envelope(
            self._request("POST", "/workflow/v2/workflow-deployments", _workflow_deploy_body(name, dsl_yaml, opts))
        )

    def deploy_mowl(self, name: str, workflow: dict[str, Any], *opts: Callable[["WorkflowDeployOptions"], None]) -> WorkflowDeploymentEnvelope:
        """Deploy a caller-owned MOWL publication graph (source_type manual_mowl).

        Every custom operator reference in the graph must already exist in the
        workspace operator library; the backend rejects dangling references
        with ErrWorkflowCustomOperatorNotFound.
        """
        if not name:
            raise ErrNameRequired
        if not workflow:
            raise ValueError("MOWL workflow graph is required")
        return _workflow_deployment_envelope(
            self._request("POST", "/workflow/v2/workflow-deployments", _workflow_mowl_deploy_body(name, workflow, opts))
        )

    def accept_candidate(self, candidate_ref: "WorkflowCandidateRef", confirmation: "WorkflowCandidateConfirmation") -> "AcceptedWorkflowCandidate":
        """Explicitly accept one server-owned candidate and return its typed handoff."""

        if not isinstance(candidate_ref, WorkflowCandidateRef):
            raise TypeError("candidate_ref is required")
        if not isinstance(confirmation, WorkflowCandidateConfirmation) or not confirmation.proposal_id or not confirmation.idempotency_key:
            raise ValueError("proposal_id and idempotency_key are required")
        acceptance = _workflow_candidate_acceptance(
            self._request(
                "POST",
                "/workflow/v2/workflow-candidates/accept",
                {
                    "candidate_ref": candidate_ref.to_dict(),
                    "proposal_id": confirmation.proposal_id,
                    "idempotency_key": confirmation.idempotency_key,
                },
            )
        )
        return AcceptedWorkflowCandidate(acceptance)

    def history(self, context_id: str, limit: int, offset: int) -> WorkflowHistoryPage:
        return _product_message(
            self._request(
                "GET",
                _with_query(
                    "/workflow/v2/workflow-candidates/history",
                    (
                        with_query_param("context_id", context_id),
                        with_query_param("limit", str(limit)),
                        with_query_param("offset", str(offset)),
                    ),
                ),
            ),
            WorkflowHistoryPage(),
            "workflow history data",
        )

    def restore_history(self, request: "WorkflowHistoryRestoreRequest") -> WorkflowHistoryEntry:
        if not isinstance(request, WorkflowHistoryRestoreRequest):
            raise TypeError("workflow restore request is required")
        return _product_message(
            self._request("POST", "/workflow/v2/workflow-candidates/restore", request.to_dict()),
            WorkflowHistoryEntry(),
            "workflow restore data",
        )

    def reject_candidate_proposal(self, proposal_id: str) -> WorkflowCandidateProposalRejection:
        """Reject an unaccepted proposal without changing the accepted workflow."""
        if not proposal_id:
            raise ValueError("proposal_id is required")
        return _product_message(
            self._request(
                "POST",
                "/workflow/v2/workflow-candidates/reject-proposal",
                {"proposal_id": proposal_id},
            ),
            WorkflowCandidateProposalRejection(),
            "workflow proposal rejection data",
        )

    def deploy_candidate(
        self,
        name: str,
        accepted_candidate: "AcceptedWorkflowCandidate",
        *opts: Callable[["WorkflowDeployOptions"], None],
    ) -> WorkflowDeploymentEnvelope:
        if not name:
            raise ErrNameRequired
        return _workflow_deployment_envelope(
            self._request(
                "POST",
                "/workflow/v2/workflow-deployments",
                _workflow_candidate_deploy_body(name, accepted_candidate, opts),
            )
        )

    def deploy_result(self, name: str, dsl_yaml: Any, *opts: Callable[["WorkflowDeployOptions"], None]) -> ProductResult:
        if not name:
            raise ErrNameRequired
        return self._client._product_result(
            "POST",
            "/workflow/v2/workflow-deployments",
            workspace_id=self._workspace_id,
            body=_workflow_deploy_body(name, dsl_yaml, opts),
        )

    def get(self, workflow_id: str) -> WorkflowEnvelope:
        return _workflow_envelope(self._request("GET", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}"))

    def get_result(self, workflow_id: str) -> ProductResult:
        return self._client._product_result("GET", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}", workspace_id=self._workspace_id)

    def update(self, workflow_id: str, *opts: Callable[["WorkflowUpdateOptions"], None]) -> WorkflowEnvelope:
        return _workflow_envelope(
            self._request("PATCH", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}", _workflow_update_body(opts))
        )

    def update_result(self, workflow_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "PATCH",
            f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}",
            workspace_id=self._workspace_id,
            body=body,
        )

    def delete(self, workflow_id: str, *opts: Callable[["QueryOptions"], None]) -> WorkflowDeleteEnvelope:
        return _workflow_delete_envelope(
            self._request("DELETE", _with_query(f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}", opts))
        )

    def delete_result(self, workflow_id: str, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "DELETE",
            _with_query(f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}", opts),
            workspace_id=self._workspace_id,
        )

    def run(self, workflow_id: str, *opts: Callable[["WorkflowRunOptions"], None]) -> WorkflowRunEnvelope:
        options = WorkflowRunOptions()
        for opt in opts:
            opt(options)
        body: dict[str, Any] = {}
        if options.input is not None:
            # Backend RunWorkflowRequest binds runtime values under "values".
            body["values"] = options.input
        if options.replace_saved_defaults:
            body["replace_saved_defaults"] = True
        if options.trigger_now is not None:
            body["trigger_now"] = options.trigger_now
        return _workflow_run_envelope(self._request("POST", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/executions", body))

    def run_result(self, workflow_id: str, body: Optional[dict[str, Any]] = None) -> ProductResult:
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/executions",
            workspace_id=self._workspace_id,
            body=body or {},
        )

    def pause(self, workflow_id: str) -> WorkflowEnvelope:
        return _workflow_envelope(self._request("POST", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/pause", None))

    def pause_result(self, workflow_id: str) -> ProductResult:
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/pause",
            workspace_id=self._workspace_id,
            body=None,
        )

    def enable(self, workflow_id: str) -> WorkflowEnvelope:
        return _workflow_envelope(self._request("POST", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/enable", None))

    def enable_result(self, workflow_id: str) -> ProductResult:
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/enable",
            workspace_id=self._workspace_id,
            body=None,
        )

    def resume(self, workflow_id: str) -> WorkflowEnvelope:
        return _workflow_envelope(self._request("POST", f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/resume", None))

    def resume_result(self, workflow_id: str) -> ProductResult:
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/resume",
            workspace_id=self._workspace_id,
            body=None,
        )

    def list_runs(self, workflow_id: str, *opts: Callable[["ListOptions"], None]) -> WorkflowExecutionListEnvelope:
        return _workflow_execution_list_envelope(
            self._request("GET", _with_list_query(f"/workflow/v2/workflow-apps/{_path_id(workflow_id)}/executions", opts))
        )

    def list_all_runs(self, *opts: Callable[["ListOptions"], None]) -> WorkflowExecutionListEnvelope:
        return _workflow_execution_list_envelope(self._request("GET", _with_list_query("/workflow/v2/workflow-apps/executions", opts)))

    def list_all_runs_result(self, *opts: Callable[["ListOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "GET",
            _with_list_query("/workflow/v2/workflow-apps/executions", opts),
            workspace_id=self._workspace_id,
        )

    def get_dispatch_job(self, workflow_id: str, dispatch_job_id: str) -> WorkflowDispatchJobEnvelope:
        workflow_path, dispatch_path = _workflow_run_path(workflow_id, dispatch_job_id)
        return _product_message(self._request("GET", f"/workflow/v2/workflow-apps/{workflow_path}/dispatch-jobs/{dispatch_path}"), WorkflowDispatchJobEnvelope(), "workflow dispatch job data")

    def get_run(self, workflow_id: str, execution_id: str) -> WorkflowExecutionEnvelope:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return _workflow_execution_envelope(self._request("GET", f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}"))

    def get_run_by_id(self, execution_id: str) -> WorkflowExecutionEnvelope:
        return _workflow_execution_envelope(self._request("GET", f"/workflow/v2/workflow-apps/executions/{_path_id(execution_id)}"))

    def refresh_run(self, workflow_id: str, execution_id: str) -> WorkflowExecutionEnvelope:
        return _workflow_execution_envelope(self._workflow_run_action(workflow_id, execution_id, "refresh", None))

    def refresh_run_result(self, workflow_id: str, execution_id: str) -> ProductResult:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/refresh",
            workspace_id=self._workspace_id,
            body=None,
        )

    def pause_run(self, workflow_id: str, execution_id: str) -> WorkflowExecutionEnvelope:
        return _workflow_execution_envelope(self._workflow_run_action(workflow_id, execution_id, "pause", None))

    def pause_run_result(self, workflow_id: str, execution_id: str) -> ProductResult:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/pause",
            workspace_id=self._workspace_id,
            body=None,
        )

    def resume_run(self, workflow_id: str, execution_id: str) -> WorkflowExecutionEnvelope:
        return _workflow_execution_envelope(self._workflow_run_action(workflow_id, execution_id, "resume", None))

    def resume_run_result(self, workflow_id: str, execution_id: str) -> ProductResult:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/resume",
            workspace_id=self._workspace_id,
            body=None,
        )

    def get_run_result(self, workflow_id: str, execution_id: str) -> WorkflowExecutionResultEnvelope:
        workflow_path, execution_path = _workflow_run_result_path(workflow_id, execution_id)
        return _workflow_execution_result_envelope(
            self._request("GET", f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/result")
        )

    def get_run_result_status(self, workflow_id: str, execution_id: str) -> ProductResult:
        workflow_path, execution_path = _workflow_run_result_path(workflow_id, execution_id)
        return self._client._product_result(
            "GET",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/result",
            workspace_id=self._workspace_id,
        )

    def get_run_result_by_id(self, execution_id: str) -> WorkflowExecutionResultEnvelope:
        if not execution_id:
            raise ErrExecutionIDRequired
        return _workflow_execution_result_envelope(
            self._request("GET", f"/workflow/v2/workflow-apps/executions/{_path_id(execution_id)}/result")
        )

    def get_run_import_context(self, workflow_id: str, execution_id: str) -> WorkflowImportContextEnvelope:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return _workflow_import_context_envelope(
            self._request("GET", f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/import-context")
        )

    def get_run_import_context_by_id(self, execution_id: str) -> WorkflowImportContextEnvelope:
        return _workflow_import_context_envelope(
            self._request("GET", f"/workflow/v2/workflow-apps/executions/{_path_id(execution_id)}/import-context")
        )

    def list_run_import_files(self, workflow_id: str, execution_id: str, *opts: Callable[["QueryOptions"], None]) -> WorkflowImportFileListEnvelope:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return _workflow_import_file_list_envelope(
            self._request("GET", _with_query(f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/import-files", opts))
        )

    def list_run_import_files_by_id(self, execution_id: str, *opts: Callable[["QueryOptions"], None]) -> WorkflowImportFileListEnvelope:
        return _workflow_import_file_list_envelope(
            self._request("GET", _with_query(f"/workflow/v2/workflow-apps/executions/{_path_id(execution_id)}/import-files", opts))
        )

    def get_run_node(self, workflow_id: str, execution_id: str, node_key: str) -> WorkflowExecutionNodeDetailEnvelope:
        workflow_path, execution_path, node_path = _workflow_run_node_path(workflow_id, execution_id, node_key)
        return _workflow_execution_node_detail_envelope(
            self._request("GET", f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/nodes/{node_path}")
        )

    def get_run_node_result(self, workflow_id: str, execution_id: str, node_key: str) -> ProductResult:
        workflow_path, execution_path, node_path = _workflow_run_node_path(workflow_id, execution_id, node_key)
        return self._client._product_result(
            "GET",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/nodes/{node_path}",
            workspace_id=self._workspace_id,
        )

    def get_run_node_by_id(self, execution_id: str, node_key: str) -> WorkflowExecutionNodeDetailEnvelope:
        execution_path = _path_id(execution_id)
        node_path = _path_id(node_key)
        return _workflow_execution_node_detail_envelope(
            self._request("GET", f"/workflow/v2/workflow-apps/executions/{execution_path}/nodes/{node_path}")
        )

    def get_run_node_by_id_result(self, execution_id: str, node_key: str) -> ProductResult:
        execution_path = _path_id(execution_id)
        node_path = _path_id(node_key)
        return self._client._product_result(
            "GET",
            f"/workflow/v2/workflow-apps/executions/{execution_path}/nodes/{node_path}",
            workspace_id=self._workspace_id,
        )

    def get_run_node_rerun_plan(self, workflow_id: str, execution_id: str, node_key: str, *opts: Callable[["QueryOptions"], None]) -> WorkflowRerunPlanEnvelope:
        workflow_path, execution_path, node_path = _workflow_run_node_path(workflow_id, execution_id, node_key)
        return _workflow_rerun_plan_envelope(
            self._request("GET", _with_query(f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/nodes/{node_path}/rerun-plan", opts))
        )

    def create_run_node_rerun(
        self,
        workflow_id: str,
        execution_id: str,
        node_key: str,
        mode: str,
        source_node_execution_id: str,
        *opts: Callable[["WorkflowRerunOptions"], None],
    ) -> WorkflowRerunEnvelope:
        if not mode:
            raise ErrModeRequired
        if not source_node_execution_id:
            raise ErrSourceNodeRequired
        body = _workflow_node_rerun_body(mode, source_node_execution_id, opts)
        contract_hash = body.get("expected_rerun_contract_hash")
        if not isinstance(contract_hash, str) or not contract_hash.strip():
            raise ErrRerunContractHashRequired
        workflow_path, execution_path, node_path = _workflow_run_node_path(workflow_id, execution_id, node_key)
        return _workflow_rerun_envelope(
            self._request(
                "POST",
                f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/nodes/{node_path}/reruns",
                body,
            )
        )

    def list_run_rerun_branches(self, workflow_id: str, execution_id: str) -> WorkflowRerunBranchListEnvelope:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return _workflow_rerun_branch_list_envelope(
            self._request("GET", f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/rerun-branches")
        )

    def get_run_rerun(self, workflow_id: str, execution_id: str, rerun_id: str) -> WorkflowRerunEnvelope:
        return _workflow_rerun_envelope(self._request("GET", _workflow_rerun_path(workflow_id, execution_id, rerun_id)))

    def cancel_run_rerun(self, workflow_id: str, execution_id: str, rerun_id: str, *opts: Callable[["WorkflowCancelOptions"], None]) -> WorkflowRerunEnvelope:
        return _workflow_rerun_envelope(self._request("POST", _workflow_rerun_path(workflow_id, execution_id, rerun_id) + "/cancel", _workflow_cancel_body(opts)))

    def retry_run(self, workflow_id: str, execution_id: str, *opts: Callable[["WorkflowRerunOptions"], None]) -> WorkflowRunEnvelope:
        return _workflow_run_envelope(self._workflow_run_action(workflow_id, execution_id, "retry", _workflow_retry_body(opts)))

    def batch_retry_failed_files(
        self,
        workflow_id: str,
        source_dispatch_job_id: str,
        execution_ids: list[str] | None,
        all_failed: bool,
        request_id: str,
    ) -> WorkflowBatchRetryEnvelope:
        workflow_path = _path_id(workflow_id)
        if not source_dispatch_job_id.strip():
            raise ValueError("source dispatch job id is required")
        if not request_id.strip():
            raise ValueError("request id is required")
        selected = list(execution_ids or [])
        if all_failed == bool(selected):
            raise ValueError("exactly one of execution ids or all failed must be specified")
        body: dict[str, Any] = {
            "source_dispatch_job_id": source_dispatch_job_id.strip(),
            "request_id": request_id.strip(),
        }
        if all_failed:
            body["all_failed"] = True
        else:
            body["execution_ids"] = selected
        return _workflow_batch_retry_envelope(
            self._request("POST", f"/workflow/v2/workflow-apps/{workflow_path}/executions/batch-retry", body)
        )

    def retry_run_result(self, workflow_id: str, execution_id: str, *opts: Callable[["WorkflowRerunOptions"], None]) -> ProductResult:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/retry",
            workspace_id=self._workspace_id,
            body=_workflow_retry_body(opts),
        )

    def cancel_run(self, workflow_id: str, execution_id: str, *opts: Callable[["WorkflowCancelOptions"], None]) -> WorkflowExecutionEnvelope:
        return _workflow_execution_envelope(self._workflow_run_action(workflow_id, execution_id, "cancel", _workflow_cancel_body(opts)))

    def cancel_run_result(self, workflow_id: str, execution_id: str, *opts: Callable[["WorkflowCancelOptions"], None]) -> ProductResult:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return self._client._product_result(
            "POST",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/cancel",
            workspace_id=self._workspace_id,
            body=_workflow_cancel_body(opts),
        )

    def delete_run(self, workflow_id: str, execution_id: str) -> WorkflowDeleteEnvelope:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return _workflow_delete_envelope(self._request("DELETE", f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}"))

    def delete_run_result(self, workflow_id: str, execution_id: str) -> ProductResult:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return self._client._product_result(
            "DELETE",
            f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}",
            workspace_id=self._workspace_id,
        )

    def list_file_executions(self, *opts: Callable[["QueryOptions"], None]) -> WorkflowFileExecutionList:
        return _workflow_file_execution_list(self._request("GET", _with_query("/workflow/v2/workflow-apps/file-executions", opts)))

    def list_file_executions_result(self, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "GET",
            _with_query("/workflow/v2/workflow-apps/file-executions", opts),
            workspace_id=self._workspace_id,
        )

    def workitem_catalog(self) -> WorkitemCatalogList:
        return _workitem_catalog_list(self._request("GET", "/workflow/v2/workitems/catalog"))

    def workitem_catalog_item(self, node_id: str) -> WorkitemCatalogDetail:
        return _workitem_catalog_detail(self._request("GET", f"/workflow/v2/workitems/catalog/{_path_id(node_id)}"))

    def get_workitem_api_service(self, node_id: str, version: str) -> WorkitemAPIServiceEnvelope:
        if not version:
            raise ErrVersionRequired
        return _workitem_api_service_envelope(
            self._request(
                "GET",
                _with_query(
                    f"/workflow/v2/workitems/catalog/{_path_id(node_id)}/api-service",
                    (with_query_param("version", version),),
                ),
            )
        )

    def publish_workitem_api_service(self, node_id: str, spec: "WorkitemAPIServicePublishSpec") -> WorkitemAPIServiceEnvelope:
        return _workitem_api_service_envelope(
            self._request(
                "POST",
                f"/workflow/v2/workitems/catalog/{_path_id(node_id)}/api-service",
                spec.body(),
            )
        )

    def invoke_workitem_api_service(self, node_id: str, spec: "WorkitemAPIServiceInvokeSpec") -> WorkitemAPIServiceInvokeEnvelope:
        return _workitem_api_service_invoke_envelope(
            self._request(
                "POST",
                f"/workflow/v2/workitems/catalog/{_path_id(node_id)}/api-service/invoke",
                spec.body(),
            )
        )

    def invoke_dynamic_service(self, spec: DynamicServiceInvokeSpec) -> DynamicServiceInvokeResult:
        path = f"/workspaces/{_path_id(self._workspace_id)}/dynamic-services/invoke"
        return self._invoke_dynamic_service(path, spec)

    def invoke_workflow_dynamic_service(self, spec: DynamicServiceInvokeSpec) -> DynamicServiceInvokeResult:
        return self._invoke_dynamic_service("/workflow/v2/dynamic-services/invoke", spec)

    def _invoke_dynamic_service(self, path: str, spec: DynamicServiceInvokeSpec) -> DynamicServiceInvokeResult:
        spec.validate()
        if spec.files:
            boundary = "moi-product-sdk-" + uuid.uuid4().hex
            fields = {"service_name":spec.service_name,"payload":json.dumps(spec.payload)}
            if spec.version: fields["version"] = spec.version
            if spec.version_number: fields["version_number"] = str(spec.version_number)
            if spec.trace is not _JSON_VALUE_UNSET: fields["trace"] = json.dumps(spec.trace)
            body = _multipart_body(boundary,fields,spec.files)
            return _dynamic_service_invoke_result(self._raw_request("POST",path,body,f"multipart/form-data; boundary={boundary}"))
        return _dynamic_service_invoke_result(self._request("POST",path,spec.body()))

    def enable_workitem_api_service(self, node_id: str, version: str) -> WorkitemAPIServiceEnvelope:
        return self._set_workitem_api_service_enabled(node_id, version, "enable")

    def disable_workitem_api_service(self, node_id: str, version: str) -> WorkitemAPIServiceEnvelope:
        return self._set_workitem_api_service_enabled(node_id, version, "disable")

    def _set_workitem_api_service_enabled(self, node_id: str, version: str, action: str) -> WorkitemAPIServiceEnvelope:
        if not version:
            raise ErrVersionRequired
        return _workitem_api_service_envelope(
            self._request(
                "POST",
                _with_query(
                    f"/workflow/v2/workitems/catalog/{_path_id(node_id)}/api-service/{action}",
                    (with_query_param("version", version),),
                ),
                {},
            )
        )

    def custom_operators(self, *opts: Callable[["QueryOptions"], None]) -> CustomOperatorListEnvelope:
        return _custom_operator_list_envelope(self._request("GET", _with_query("/workflow/v2/custom-operators", opts)))

    def create_custom_operator(
        self,
        spec: "CustomOperatorSpec",
        *opts: Callable[["CustomOperatorOptions"], None],
    ) -> CustomOperator:
        spec.validate()
        return _custom_operator(
            self._request(
                "POST",
                "/workflow/v2/custom-operators",
                spec.body(opts),
            )
        )

    def get_custom_operator(self, operator_id: str) -> CustomOperator:
        return _custom_operator(self._request("GET", f"/workflow/v2/custom-operators/{_path_id(operator_id)}"))

    def get_custom_operator_code(self, operator_id: str) -> CustomOperatorCodeEnvelope:
        return _custom_operator_code_envelope(self._request("GET", f"/workflow/v2/custom-operators/{_path_id(operator_id)}/code"))

    def get_custom_operator_source(self, node_id: str, version: str, task_id: str = "") -> CustomOperatorSourceEnvelope:
        if not node_id.strip():
            raise ErrIDRequired
        if not version.strip():
            raise ErrVersionRequired
        opts = [with_query_param("node_id", node_id.strip()), with_query_param("version", version.strip())]
        if task_id.strip():
            opts.append(with_query_param("task_id", task_id.strip()))
        return _custom_operator_source_envelope(
            self._request("GET", _with_query("/workflow/v2/custom-operators/source", tuple(opts)))
        )

    def test_custom_operator(self, operator_id: str, input: "CustomOperatorTestInput") -> CustomOperatorTestEnvelope:
        input.validate()
        body: dict[str, Any] = {"input": input.input}
        if input.wait_timeout_seconds is not None:
            body["wait_timeout_seconds"] = input.wait_timeout_seconds
        return _custom_operator_test_envelope(self._request("POST", f"/workflow/v2/custom-operators/{_path_id(operator_id)}/test-run", body))

    def update_custom_operator(self, operator_id: str, *opts: Callable[["CustomOperatorUpdateOptions"], None]) -> CustomOperator:
        return _custom_operator(self._request("PUT", f"/workflow/v2/custom-operators/{_path_id(operator_id)}", _custom_operator_update_body(opts)))

    def enable_custom_operator(self, operator_id: str) -> CustomOperator:
        return self._custom_operator_action(operator_id, "enable")

    def disable_custom_operator(self, operator_id: str) -> CustomOperator:
        return self._custom_operator_action(operator_id, "disable")

    def delete_custom_operator(self, operator_id: str) -> WorkflowDeleteEnvelope:
        return _workflow_delete_envelope(self._request("DELETE", f"/workflow/v2/custom-operators/{_path_id(operator_id)}"))

    def catalog_file_lineage_overview(self, file_id: str, *opts: Callable[["QueryOptions"], None]) -> LineageOverview:
        return _lineage_overview(self._request("GET", _with_query(f"/lineage/catalog-files/{_path_id(file_id)}/overview", opts)))

    def catalog_file_lineage_overview_result(self, file_id: str, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "GET",
            _with_query(f"/lineage/catalog-files/{_path_id(file_id)}/overview", opts),
            workspace_id=self._workspace_id,
        )

    def artifact_lineage_overview(self, artifact_id: str) -> LineageOverview:
        return _lineage_overview(self._request("GET", f"/lineage/artifacts/{_path_id(artifact_id)}/overview"))

    def artifact_lineage_overview_result(self, artifact_id: str) -> ProductResult:
        return self._client._product_result(
            "GET",
            f"/lineage/artifacts/{_path_id(artifact_id)}/overview",
            workspace_id=self._workspace_id,
        )

    def artifact_output_blocks(self, artifact_id: str) -> LineageOutputBlocks:
        return _lineage_output_blocks(self._request("GET", f"/lineage/artifacts/{_path_id(artifact_id)}/output-blocks"))

    def artifact_block_revisions(self, artifact_id: str, block_id: str) -> LineageBlockRevisions:
        artifact_path, block_path = _artifact_block_path(artifact_id, block_id)
        return _lineage_block_revisions(self._request("GET", f"/lineage/artifacts/{artifact_path}/blocks/{block_path}/revisions"))

    def create_artifact_block_revision(self, artifact_id: str, block_id: str, *opts: Callable[["LineageRevisionOptions"], None]) -> LineageBlockRevision:
        artifact_path, block_path = _artifact_block_path(artifact_id, block_id)
        return _lineage_block_revision(self._request("POST", f"/lineage/artifacts/{artifact_path}/blocks/{block_path}/revisions", _lineage_revision_body(opts)))

    def switch_artifact_effective_revisions(
        self,
        artifact_id: str,
        switches: list["LineageRevisionSwitch"],
        *opts: Callable[["LineageSwitchOptions"], None],
    ) -> LineageEffectiveRevisions:
        return _lineage_effective_revisions(self._request("POST", f"/lineage/artifacts/{_path_id(artifact_id)}/effective-revisions", _lineage_switch_body(switches, opts)))

    def artifact_node(self, artifact_id: str, node_id: str) -> LineageArtifactNode:
        artifact_path, node_path = _artifact_node_path(artifact_id, node_id)
        return _lineage_artifact_node(self._request("GET", f"/lineage/artifacts/{artifact_path}/nodes/{node_path}"))

    def artifact_node_result(self, artifact_id: str, node_id: str) -> ProductResult:
        artifact_path, node_path = _artifact_node_path(artifact_id, node_id)
        return self._client._product_result(
            "GET",
            f"/lineage/artifacts/{artifact_path}/nodes/{node_path}",
            workspace_id=self._workspace_id,
        )

    def artifact_node_output_blocks(self, artifact_id: str, node_id: str) -> LineageOutputBlocks:
        artifact_path, node_path = _artifact_node_path(artifact_id, node_id)
        return _lineage_output_blocks(self._request("GET", f"/lineage/artifacts/{artifact_path}/nodes/{node_path}/output-blocks"))

    def artifact_node_block_revisions(self, artifact_id: str, node_id: str, block_id: str) -> LineageBlockRevisions:
        artifact_path, node_path, block_path = _artifact_node_block_path(artifact_id, node_id, block_id)
        return _lineage_block_revisions(self._request("GET", f"/lineage/artifacts/{artifact_path}/nodes/{node_path}/blocks/{block_path}/revisions"))

    def create_artifact_node_block_revision(
        self,
        artifact_id: str,
        node_id: str,
        block_id: str,
        *opts: Callable[["LineageRevisionOptions"], None],
    ) -> LineageBlockRevision:
        artifact_path, node_path, block_path = _artifact_node_block_path(artifact_id, node_id, block_id)
        return _lineage_block_revision(self._request("POST", f"/lineage/artifacts/{artifact_path}/nodes/{node_path}/blocks/{block_path}/revisions", _lineage_revision_body(opts)))

    def switch_artifact_node_effective_revisions(
        self,
        artifact_id: str,
        node_id: str,
        switches: list["LineageRevisionSwitch"],
        *opts: Callable[["LineageSwitchOptions"], None],
    ) -> LineageEffectiveRevisions:
        artifact_path, node_path = _artifact_node_path(artifact_id, node_id)
        return _lineage_effective_revisions(self._request("POST", f"/lineage/artifacts/{artifact_path}/nodes/{node_path}/effective-revisions", _lineage_switch_body(switches, opts)))

    def create_artifact_node_rerun(self, artifact_id: str, node_id: str, *opts: Callable[["LineageRerunOptions"], None]) -> LineageRerun:
        artifact_path, node_path = _artifact_node_path(artifact_id, node_id)
        return _lineage_rerun(self._request("POST", f"/lineage/artifacts/{artifact_path}/nodes/{node_path}/rerun", _lineage_rerun_body(opts)))

    def create_target_artifact_node_revision_rerun(
        self,
        artifact_id: str,
        node_id: str,
        target_output_emission_id: str,
        *opts: Callable[["LineageRevisionRerunOptions"], None],
    ) -> LineageRerun:
        artifact_path, node_path = _artifact_node_path(artifact_id, node_id)
        target_path = _path_id(target_output_emission_id)
        return _lineage_rerun(
            self._request(
                "POST",
                f"/lineage/artifacts/{artifact_path}/nodes/{node_path}/output-emissions/{target_path}/rerun-with-revisions",
                _lineage_revision_rerun_body(opts),
            )
        )

    def workflow_templates(self) -> WorkflowTemplateList:
        return _workflow_template_list(self._request("GET", "/workflow-templates"))

    def get_workflow_template(self, template_id: str) -> WorkflowTemplate:
        return _workflow_template(self._request("GET", f"/workflow-templates/{_path_id(template_id)}"))

    def create_workflow_template(self, name: str, dsl_yaml: str, *opts: Callable[["WorkflowTemplateOptions"], None]) -> WorkflowTemplate:
        if not name:
            raise ErrNameRequired
        if not dsl_yaml:
            raise ErrDSLYAMLRequired
        return _workflow_template(self._request("POST", "/workflow-templates", _workflow_template_body(name, dsl_yaml, opts)))

    def create_mowl_workflow_template(self, name: str, workflow: dict[str, Any], *opts: Callable[["WorkflowTemplateOptions"], None]) -> WorkflowTemplate:
        """Save a caller-owned MOWL publication graph as a workflow template.

        The graph must reference published workspace artifacts; the backend
        validates custom operator references before persisting the template so
        instantiation cannot produce a dangling workflow.
        """
        return _workflow_template(self._request("POST", "/workflow-templates", _workflow_mowl_template_body(name, workflow, opts)))

    def update_mowl_workflow_template(self, template_id: str, name: str, workflow: dict[str, Any], *opts: Callable[["WorkflowTemplateOptions"], None]) -> WorkflowTemplate:
        """Replace a template graph; the server owns operator and type validation."""
        body = _workflow_mowl_template_body(name, workflow, opts)
        return _workflow_template(self._request("PUT", f"/workflow-templates/{_path_id(template_id)}", body))

    def update_workflow_template(self, template_id: str, name: str, dsl_yaml: str, *opts: Callable[["WorkflowTemplateOptions"], None]) -> WorkflowTemplate:
        if not name:
            raise ErrNameRequired
        if not dsl_yaml:
            raise ErrDSLYAMLRequired
        return _workflow_template(self._request("PUT", f"/workflow-templates/{_path_id(template_id)}", _workflow_template_body(name, dsl_yaml, opts)))

    def delete_workflow_template(self, template_id: str) -> WorkflowTemplateDeleteEnvelope:
        return _workflow_template_delete_envelope(self._request("DELETE", f"/workflow-templates/{_path_id(template_id)}"))

    def _workflow_run_action(self, workflow_id: str, execution_id: str, action: str, body: dict[str, Any]) -> Any:
        workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
        return self._request("POST", f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/{action}", body)

    def _custom_operator_action(self, operator_id: str, action: str) -> CustomOperator:
        return _custom_operator(self._request("POST", f"/workflow/v2/custom-operators/{_path_id(operator_id)}/{action}"))

class AgentService(WorkspaceScopedService):
    def artifacts(self, *opts: Callable[["QueryOptions"], None]) -> AgentArtifactListResult:
        return _product_message(self._request("GET", _with_query(_agent_resource_path(self._workspace_id, "agent-artifacts", ""), opts)), AgentArtifactListResult(), "agent artifact list data")

    def artifact(self, artifact_id: str, version: int) -> AgentArtifact:
        if version <= 0:
            raise ErrVersionRequired
        return _product_message(self._request("GET", _agent_resource_path(self._workspace_id, "agent-artifacts", f"/{_path_id(artifact_id)}/versions/{version}")), AgentArtifact(), "agent artifact data")

    def delete_artifacts(self, request: AgentArtifactBatchRequest) -> AgentArtifactDeleteResult:
        if not isinstance(request, AgentArtifactBatchRequest):
            raise TypeError("request must be AgentArtifactBatchRequest")
        body = {"items": [{"artifact_id": item.artifact_id, "version": item.version} for item in request.items]}
        return _product_message(self._request("POST", _agent_resource_path(self._workspace_id, "agent-artifacts", "/batch-delete"), body), AgentArtifactDeleteResult(), "agent artifact delete data")

    def resolve_artifacts(self, request: AgentArtifactBatchRequest) -> AgentArtifactResolveResult:
        if not isinstance(request, AgentArtifactBatchRequest):
            raise TypeError("request must be AgentArtifactBatchRequest")
        body = {"items": [{"artifact_id": item.artifact_id, "version": item.version} for item in request.items]}
        return _product_message(self._request("POST", _agent_resource_path(self._workspace_id, "agent-artifacts", "/resolve"), body), AgentArtifactResolveResult(), "agent artifact resolve data")

    def backfill_artifacts(self, request: AgentArtifactBackfillRequest) -> AgentArtifactBackfillResult:
        if not isinstance(request, AgentArtifactBackfillRequest):
            raise TypeError("request must be AgentArtifactBackfillRequest")
        body = {"dry_run": request.dry_run, "limit": request.limit}
        return _product_message(self._request("POST", _agent_resource_path(self._workspace_id, "agent-artifacts", "/backfill"), body), AgentArtifactBackfillResult(), "agent artifact backfill data")

    def runtime_browser_token(self, task_id: str) -> SandboxTerminalToken:
        path = _agent_resource_path(self._workspace_id, "agent-runtime-tasks", f"/{_path_id(task_id)}/browser/token")
        return _product_message(self._request("POST", path, {}), SandboxTerminalToken(), "runtime browser token data")

    def connect_runtime_browser(self, task_id: str, token: str, origin: str) -> "RuntimeBrowser":
        """Open a browser stream; the token is carried only by its subprotocol."""
        import websocket
        from .agent_browser import RuntimeBrowser

        if not token:
            raise ErrTokenRequired
        if not origin:
            raise ErrOriginRequired
        path = _agent_resource_path(self._workspace_id, "agent-runtime-tasks", f"/{_path_id(task_id)}/browser/stream")
        endpoint = urllib.parse.urlsplit(self._client._product_url(path))
        if endpoint.scheme == "https":
            scheme = "wss"
        elif endpoint.scheme == "http":
            scheme = "ws"
        else:
            raise Error("ErrEndpointSchemeUnsupported", "product endpoint must use http or https")
        target = urllib.parse.urlunsplit((scheme, endpoint.netloc, endpoint.path, "", ""))
        connection = websocket.create_connection(
            target,
            timeout=self._client._config.timeout,
            origin=origin,
            subprotocols=["moi-browser.v1", token],
        )
        return RuntimeBrowser(connection)
    def connect_browser(self, task_id: str, compression: bool = True):
        """Obtain a task-scoped proof and connect its browser handoff stream."""
        return self._connect_browser(task_id, compression, read_only=False)

    def watch_browser(self, task_id: str, compression: bool = True):
        """Observe the current page without acquiring control; acknowledge each rendered frame."""
        return self._connect_browser(task_id, compression, read_only=True)

    def _connect_browser(self, task_id: str, compression: bool, read_only: bool):
        from urllib.parse import urlsplit, urlunsplit
        from websockets.sync.client import connect
        from websockets.exceptions import InvalidStatus
        from .agent_browser import AgentBrowser

        path = _agent_resource_path(self._workspace_id, "agent-runtime-tasks", f"/{_path_id(task_id)}/browser")
        proof = self._request("POST", path + "/token", {})
        if not isinstance(proof, dict) or not isinstance(proof.get("token"), str) or not proof["token"]:
            raise Error("ErrResponseInvalid", "browser token response has no token")
        endpoint = urlsplit(self._client._product_url(path + "/stream"))
        target = urlunsplit(("wss" if endpoint.scheme == "https" else "ws", endpoint.netloc, endpoint.path, "mode=view" if read_only else endpoint.query, ""))
        timeout = self._client._config.timeout
        try:
            connection = connect(target, origin=f"{endpoint.scheme}://{endpoint.netloc}",
                                 subprotocols=["moi-browser.v1", proof["token"]],
                                 compression="deflate" if compression else None,
                                 open_timeout=timeout)
        except InvalidStatus as exc:
            response = exc.response
            raise _parse_error(response.status_code, bytes(response.body), _request_id(response.headers)) from exc
        return AgentBrowser(connection, timeout)

    def workspace_mcp(self, agent_id: str, request: RuntimeRPCRequest) -> Optional[RuntimeRPCResponse]:
        """Use product authentication plus with_runtime_authorization for the live task."""
        body = MessageToDict(request, preserving_proto_field_name=True)
        if request.method == "notifications/cancelled" and not request.HasField("id"):
            path = f"/workspaces/{_path_id(self._workspace_id)}/agents/{_path_id(agent_id)}/mcp/http"
            _notify_runtime_mcp(self._client, self._client._product_url(path), request, self._workspace_id)
            return None
        return _product_message(self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/agents/{_path_id(agent_id)}/mcp/http", body), RuntimeRPCResponse(), "workspace MCP")

    """Route-aligned escape hatch; prefer typed AgentHandle A2A helpers for user-facing workflows."""

    def list(self, *options: Callable[["QueryOptions"], None]) -> Any:
        return self._request("GET", _with_query("/agents", options))

    def executor_health(self) -> ExecutorHealthResponse:
        return _product_message(self._request("GET", "/agent-executors/health"), ExecutorHealthResponse(), "executor health data")

    def get_skill_candidate_confirmation(self, task_id: str, call_id: str, source_digest: str) -> SkillCandidateConfirmationResult:
        path = _agent_resource_path(self._workspace_id, "agent-runtime-tasks", f"/{_path_id(task_id)}/skills/confirmation")
        path = _with_query(path, (with_query_param("call_id", call_id), with_query_param("source_digest", source_digest)))
        return _product_message(self._request("GET", path), SkillCandidateConfirmationResult(), "skill candidate confirmation state")

    def confirm_skill_candidate(self, task_id: str, request: ConfirmSkillCandidateRequest) -> ConfirmSkillCandidateResult:
        """Save a reviewed skill and optionally bind it to the task's current agent."""
        task_path = _path_id(task_id)
        if not isinstance(request, ConfirmSkillCandidateRequest):
            raise TypeError("request must be ConfirmSkillCandidateRequest")
        path = _agent_resource_path(self._workspace_id, "agent-runtime-tasks", f"/{task_path}/skills/confirm")
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(self._request("POST", path, body), ConfirmSkillCandidateResult(), "skill candidate confirmation data")

    def preview_query_visual(self, agent_id: str, file_id: str) -> StreamResponse:
        return self._download("GET", f"/workspaces/{_path_id(self._workspace_id)}/agents/{_path_id(agent_id)}/query-visuals/{_path_id(file_id)}/preview")

    def export_agent_package(self, agent_id: str, version: str) -> StreamResponse:
        return self._download("GET", f"/workspaces/{_path_id(self._workspace_id)}/agent-packages/{_path_id(agent_id)}/versions/{_path_id(version)}/export")

    def create_feedback_ticket(self, request: FeedbackTicketCreateRequest) -> Any:
        if not isinstance(request, FeedbackTicketCreateRequest):
            raise TypeError("request must be FeedbackTicketCreateRequest")
        return self._request(
            "POST",
            "/feedback-tickets",
            json_format.MessageToDict(
                request,
                preserving_proto_field_name=True,
                always_print_fields_with_no_presence=True,
            ),
        )

    def my_feedback_tickets(self, *options: Callable[["QueryOptions"], None]) -> Any:
        return self._request("GET", _with_query("/feedback-tickets/mine", options))

    def admin_feedback_tickets(self, *options: Callable[["QueryOptions"], None]) -> Any:
        return self._request("GET", _with_query("/admin/feedback-tickets", options))

    def update_admin_feedback_ticket(self, ticket_id: str, request: FeedbackTicketAdminUpdateRequest) -> Any:
        return self._request("PATCH", f"/admin/feedback-tickets/{_path_id(ticket_id)}", json_format.MessageToDict(request, preserving_proto_field_name=True))

    def admin_feedback_ticket(self, ticket_id: str) -> Any:
        return self._request("GET", f"/admin/feedback-tickets/{_path_id(ticket_id)}")

    def build_feedback_github_issue_draft(self, ticket_id: str, kind: str) -> Any:
        return self._request("POST", f"/admin/feedback-tickets/{_path_id(ticket_id)}/github-issue-draft", {"kind": kind})

    def create_feedback_github_issue(self, ticket_id: str, kind: str, title: str, body: str, retry: bool = False) -> Any:
        return self._request("POST", f"/admin/feedback-tickets/{_path_id(ticket_id)}/github-issue",
                             {"kind": kind, "title": title, "body": body, "retry": retry})

    def approve_feedback_reward(self, ticket_id: str, request: FeedbackTicketAdminUpdateRequest) -> Any:
        ticket_path = _path_id(ticket_id)
        if not isinstance(request, FeedbackTicketAdminUpdateRequest):
            raise TypeError("request must be FeedbackTicketAdminUpdateRequest")
        return self._request("POST", f"/admin/feedback-tickets/{ticket_path}/reward-approval", json_format.MessageToDict(request, preserving_proto_field_name=True))

    def agent_card(self, *opts: Callable[["QueryOptions"], None]) -> AgentCardResult:
        return _agent_card_result(self._request("GET", _with_query("/agents/card", opts)))

    def search_plugins(self, *opts: Callable[["QueryOptions"], None]) -> PluginDiscoveryPage:
        """Search visible plugins; availability=all|installed|market, limit=1..5."""
        return _product_message(self._resource("GET", "plugin-discovery", "/search", None, opts, require_envelope=True), PluginDiscoveryPage(), "plugin discovery")

    def describe_plugin_capability(self, ref: str) -> PluginCapabilityDescriptor:
        value = self._resource("GET", "plugin-discovery", "/describe", None, (with_query_param("ref", ref),), require_envelope=True)
        return _product_message(value, PluginCapabilityDescriptor(), "plugin capability")

    def list_plugin_releases(self, *opts: Callable[["QueryOptions"], None]) -> PluginPublicationList:
        """Supply namespace=system or workspace through query options."""
        return _product_message(self._resource("GET", "plugin-releases", "", None, opts, require_envelope=True), PluginPublicationList(), "plugin releases")

    def get_plugin_release(self, release_id: str, *opts: Callable[["QueryOptions"], None]) -> PluginRelease:
        return _product_message(self._resource("GET", "plugin-releases", f"/{_path_id(release_id)}", None, opts, require_envelope=True), PluginRelease(), "plugin release")

    def install_plugin(self, req: PluginInstallRequest) -> PluginInstallation:
        body = {"release_namespace": req.release_namespace, "release_id": req.release_id, "bindings": _plugin_bindings(req.bindings)}
        if req.setup_operation_id:
            body["setup_operation_id"] = req.setup_operation_id
        return _product_message(self._resource("POST", "plugin-installations", "", body, (), require_envelope=True), PluginInstallation(), "plugin installation")

    def list_plugin_installations(self, *opts: Callable[["QueryOptions"], None]) -> PluginInstallationList:
        return _product_message(self._resource("GET", "plugin-installations", "", None, opts, require_envelope=True), PluginInstallationList(), "plugin installations")

    def get_plugin_installation(self, installation_id: str) -> PluginInstallation:
        return _product_message(self._resource("GET", "plugin-installations", f"/{_path_id(installation_id)}", None, (), require_envelope=True), PluginInstallation(), "plugin installation")

    def update_plugin_installation(self, installation_id: str, req: PluginUpdateInstallationRequest) -> PluginInstallation:
        body = {"expected_version": req.expected_version, "release_namespace": req.release_namespace, "release_id": req.release_id, "bindings": _plugin_bindings(req.bindings)}
        if req.setup_operation_id:
            body["setup_operation_id"] = req.setup_operation_id
        return _product_message(self._resource("PATCH", "plugin-installations", f"/{_path_id(installation_id)}", body, (), require_envelope=True), PluginInstallation(), "plugin installation")

    def delete_plugin_installation(self, installation_id: str, expected_version: int) -> PluginMutationResult:
        return _product_message(self._resource("DELETE", "plugin-installations", f"/{_path_id(installation_id)}", {"expected_version": expected_version}, (), require_envelope=True), PluginMutationResult(), "plugin deletion")

    def create_plugin_connection(self, req: PluginCreateConnectionRequest) -> PluginConnection:
        body = {"release_namespace": req.release_namespace, "release_id": req.release_id, "requirement": req.requirement, "profile": req.profile, "executor_id": req.executor_id, "name": req.name}
        return _product_message(self._resource("POST", "plugin-connections", "", body, (), require_envelope=True), PluginConnection(), "plugin connection")

    def list_plugin_connections(self, *opts: Callable[["QueryOptions"], None]) -> PluginConnectionList:
        return _product_message(self._resource("GET", "plugin-connections", "", None, opts, require_envelope=True), PluginConnectionList(), "plugin connections")

    def get_plugin_connection(self, connection_id: str) -> PluginConnection:
        return _product_message(self._resource("GET", "plugin-connections", f"/{_path_id(connection_id)}", None, (), require_envelope=True), PluginConnection(), "plugin connection")

    def update_plugin_connection(self, connection_id: str, req: PluginUpdateConnectionRequest) -> PluginConnection:
        body = {"expected_version": req.expected_version, "status": req.status}
        return _product_message(self._resource("PATCH", "plugin-connections", f"/{_path_id(connection_id)}", body, (), require_envelope=True), PluginConnection(), "plugin connection")

    def delete_plugin_connection(self, connection_id: str, expected_version: int) -> PluginMutationResult:
        return _product_message(self._resource("DELETE", "plugin-connections", f"/{_path_id(connection_id)}", {"expected_version": expected_version}, (), require_envelope=True), PluginMutationResult(), "plugin deletion")

    def get_plugin_authorization(self, connection_id: str) -> PluginAuthorizationStatus:
        return _product_message(self._resource("GET", "plugin-connections", f"/{_path_id(connection_id)}/authorization", None, (), require_envelope=True), PluginAuthorizationStatus(), "plugin authorization")

    def store_plugin_secret(self, connection_id: str, req: PluginStoreSecretRequest) -> PluginAuthorizationStatus:
        body = {"expected_version": req.expected_version, "fields": dict(req.fields)}
        return _product_message(self._resource("POST", "plugin-connections", f"/{_path_id(connection_id)}/secret", body, (), require_envelope=True), PluginAuthorizationStatus(), "plugin authorization")

    def begin_plugin_oauth(self, connection_id: str, expected_version: int) -> PluginOAuthAction:
        """Code grants return a signed-in browser handoff; device grants return the direct user action."""
        return _product_message(self._resource("POST", "plugin-connections", f"/{_path_id(connection_id)}/oauth", {"expected_version": expected_version, "initiator": "external"}, (), require_envelope=True), PluginOAuthAction(), "plugin authorization action")

    def poll_plugin_oauth(self, connection_id: str, attempt_id: str, expected_version: int) -> PluginOAuthProgress:
        """One device poll, no retries. Respect poll_after before the next call."""
        value = self._resource("POST", "plugin-connections", f"/{_path_id(connection_id)}/oauth/{_path_id(attempt_id)}/poll", {"expected_version": expected_version}, (), require_envelope=True)
        return _product_message(value, PluginOAuthProgress(), "plugin authorization progress")

    def disconnect_plugin_connection(self, connection_id: str, expected_generation: int) -> PluginMutationResult:
        return _product_message(self._resource("POST", "plugin-connections", f"/{_path_id(connection_id)}/disconnect", {"expected_generation": expected_generation}, (), require_envelope=True), PluginMutationResult(), "plugin disconnect")
    def list_agent_catalog_cards(self, *opts: Callable[["QueryOptions"], None]) -> AgentCatalogCardListResult:
        """Return the authorized Agent and Team cards shown in the MOI catalog."""
        path = f"/workspaces/{_path_id(self._workspace_id)}/agent-cards"
        return _product_message(self._request("GET", _with_query(path, opts), None), AgentCatalogCardListResult(), "agent catalog card data")

    def a2a(self, req: "AgentA2ARequest") -> AgentA2AResult:
        _validate_agent_a2a_request(req, stream=False)
        result = _agent_a2a_result(self._request("POST", "/agents/a2a", req.to_dict()))
        if req.request.method == A2A_METHOD_SEND and not req.request.no_wait:
            result = self._a2a_follow_send(req.selector, result)
        return result

    def _a2a_follow_send(self, selector: "AgentSelector", result: AgentA2AResult) -> AgentA2AResult:
        """Fold a non-blocking message/send answer into the settled task.

        A2A 0.3 answers send at admission; a still-running task (submitted or
        working) is followed internally until a terminal state, so one call
        observes the same persisted task the backend settles. Message
        acknowledgements and already-settled or interrupted tasks are returned
        unchanged.
        """
        payload = agent_a2a_payload(result)
        if payload.get("kind") != "task" or _a2a_task_state(payload) not in ("submitted", "working"):
            return result
        task_id = payload.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise Error("ErrResponseInvalid", "A2A task result missing task id")
        deadline = time.monotonic() + self._client._config.a2a_wait_timeout
        return self._a2a_follow_task(selector, task_id, _a2a_event_cursor(payload), deadline)

    def _a2a_follow_task(self, selector: "AgentSelector", task_id: str, cursor: int, deadline: float) -> AgentA2AResult:
        def remaining() -> float:
            return deadline - time.monotonic()

        # Preferred path: aggregate the tasks/resubscribe SSE stream, resuming
        # from the durable eventCursor after every disconnect.
        reconnects = 0
        first_open = True
        while remaining() > 0:
            try:
                stream = self._a2a_resubscribe(selector, task_id, cursor, remaining())
            except Error:
                if first_open:
                    break  # SSE is unavailable in this environment: poll instead.
                reconnects += 1
                if reconnects >= _A2A_FOLLOW_RECONNECT_LIMIT:
                    break
                time.sleep(min(_A2A_FOLLOW_RECONNECT_BACKOFF * (2 ** (reconnects - 1)), max(0.0, remaining())))
                continue
            first_open = False
            terminal, cursor, frames = self._a2a_consume_stream(stream, task_id, cursor, deadline)
            if terminal:
                # The terminal state is read back from the persisted
                # projection, never inferred from the transport frame. The
                # projection may lag the terminal event, so read back with
                # polling; re-opening the stream here would wait forever
                # because the cursor has already passed the final event.
                return self._a2a_read_terminal_task(selector, task_id, deadline)
            if frames:
                reconnects = 0
            else:
                reconnects += 1
                if reconnects >= _A2A_FOLLOW_RECONNECT_LIMIT:
                    break
            time.sleep(min(_A2A_FOLLOW_RECONNECT_BACKOFF * (2 ** max(reconnects - 1, 0)), max(0.0, remaining())))
        if remaining() <= 0:
            raise _a2a_wait_timeout_error(task_id)
        # Degraded path: tasks/get polling under the same wait budget.
        while True:
            settled = self._a2a_task_get(selector, task_id)
            if _a2a_task_state(agent_a2a_payload(settled)) in _A2A_TASK_TERMINAL_STATES:
                return settled
            left = remaining()
            if left <= 0:
                raise _a2a_wait_timeout_error(task_id)
            time.sleep(min(_A2A_FOLLOW_POLL_INTERVAL, left))

    def _a2a_read_terminal_task(self, selector: "AgentSelector", task_id: str, deadline: float) -> AgentA2AResult:
        """Read the persisted terminal projection after a terminal stream frame.

        Final-state visibility may lag the terminal event, so a non-terminal
        or transiently failing readback is retried on the poll interval under
        the remaining wait budget.
        """
        while True:
            try:
                settled = self._a2a_task_get(selector, task_id)
            except Error:
                settled = None
            if settled is not None and _a2a_task_state(agent_a2a_payload(settled)) in _A2A_TASK_TERMINAL_STATES:
                return settled
            left = deadline - time.monotonic()
            if left <= 0:
                raise _a2a_wait_timeout_error(task_id)
            time.sleep(min(_A2A_FOLLOW_POLL_INTERVAL, left))

    def _a2a_task_get(self, selector: "AgentSelector", task_id: str) -> AgentA2AResult:
        try:
            return self.a2a(AgentA2ARequest(selector, A2ARequest(A2A_METHOD_TASKS_GET, params={"id": task_id})))
        except Error as err:
            raise _a2a_follow_error(task_id, err) from err

    def _a2a_resubscribe(self, selector: "AgentSelector", task_id: str, cursor: int, budget: float) -> "StreamResponse":
        body = AgentA2ARequest(selector, A2ARequest(A2A_METHOD_TASKS_RESUBSCRIBE, params={"id": task_id, "afterSeq": cursor})).to_dict()
        timeout = self._client._config.timeout
        if budget < timeout:
            timeout = max(budget, 0.001)
        try:
            return StreamResponse(self._client._stream("POST", "/agents/a2a", self._workspace_id, body, timeout=timeout))
        except Error as err:
            raise _a2a_follow_error(task_id, err) from err

    def _a2a_consume_stream(self, stream: "StreamResponse", task_id: str, cursor: int, deadline: float) -> tuple[bool, int, int]:
        """Read one resubscribe stream until a terminal frame or a disconnect."""
        terminal = False
        frames = 0
        data_lines: list[str] = []
        try:
            while True:
                if time.monotonic() >= deadline:
                    raise _a2a_wait_timeout_error(task_id)
                try:
                    raw = stream.readline()
                except (TimeoutError, OSError, http.client.HTTPException):
                    break
                if not raw:
                    break  # The server closed the stream before the terminal frame.
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                if not line:
                    if data_lines:
                        frame_cursor, frame_terminal = self._a2a_stream_frame(task_id, "\n".join(data_lines))
                        cursor = max(cursor, frame_cursor)
                        frames += 1
                        data_lines = []
                        if frame_terminal:
                            terminal = True
                            break
                    continue
                if line.startswith(":"):
                    continue  # Heartbeat comment.
                if line.startswith("id:"):
                    sequence = line[3:].strip()
                    if sequence.isdigit():
                        cursor = max(cursor, int(sequence))
                    continue
                if line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())
        finally:
            stream.close()
        return terminal, cursor, frames

    def _a2a_stream_frame(self, task_id: str, data: str) -> tuple[int, bool]:
        try:
            envelope = json.loads(data)
        except json.JSONDecodeError as err:
            raise _a2a_follow_error(task_id, Error("ErrResponseInvalid", "A2A stream frame is not valid JSON")) from err
        if not isinstance(envelope, dict):
            raise _a2a_follow_error(task_id, Error("ErrResponseInvalid", "A2A stream frame is not a JSON-RPC envelope"))
        rpc_error = envelope.get("error")
        if isinstance(rpc_error, dict):
            code = rpc_error.get("code")
            message = rpc_error.get("message")
            raise _a2a_follow_error(task_id, Error(str(code), message if isinstance(message, str) else "", data=rpc_error.get("data")))
        result = envelope.get("result")
        if not isinstance(result, dict):
            return 0, False
        cursor = _a2a_event_cursor(result)
        kind = result.get("kind")
        if kind == "status-update":
            return cursor, result.get("final") is True and _a2a_task_state(result) in _A2A_TASK_TERMINAL_STATES
        if kind == "task":
            return cursor, _a2a_task_state(result) in _A2A_TASK_TERMINAL_STATES
        return cursor, False

    def a2a_stream(self, req: "AgentA2ARequest") -> StreamResponse:
        _validate_agent_a2a_request(req, stream=True)
        return self._stream("POST", "/agents/a2a", req.to_dict())

    def load_agent_package(self, archive: bytes) -> Any:
        """Load a raw .moiagent archive into the workspace."""
        return self._raw_request(
            "POST",
            _agent_resource_path(self._workspace_id, "agent-packages", "/load"),
            archive,
            "application/vnd.moi.agent+zip",
        )

    def upload_workspace_file(self, filename: str, data: bytes) -> Any:
        """Upload a file to the workspace file resource."""
        body, content_type = self._agent_upload_payload(filename, data)
        return self._raw_request("POST", _agent_resource_path(self._workspace_id, "files", ""), body, content_type)

    def inspect_skill_package(self, filename: str, archive: bytes) -> Any:
        """Validate a skill package before importing it."""
        body, content_type = self._agent_upload_payload(filename, archive)
        return self._raw_request("POST", _agent_resource_path(self._workspace_id, "skills", "/import/inspect"), body, content_type)

    def import_skill_package(
        self,
        filename: str,
        archive: bytes,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        tags: Any = _JSON_VALUE_UNSET,
    ) -> Any:
        """Import a skill package into the workspace."""
        fields: dict[str, str] = {}
        for key, value in (("name", name), ("description", description), ("category", category)):
            if value is not None:
                fields[key] = value
        if tags is not _JSON_VALUE_UNSET:
            fields["tags"] = json.dumps(tags, ensure_ascii=False, separators=(",", ":"))
        body, content_type = self._agent_upload_payload(filename, archive, fields)
        return self._raw_request("POST", _agent_resource_path(self._workspace_id, "skills", "/import"), body, content_type)

    def get_skill_file(self, skill_id: str, path: str) -> StreamResponse:
        """Stream one imported static skill file. Callers own the response body."""
        if not path:
            raise ErrPathInvalid
        return self._download(
            "GET",
            _with_query(
                _agent_resource_path(self._workspace_id, "skills", f"/{_path_id(skill_id)}/files/content"),
                (with_query_param("path", path),),
            ),
        )

    def polish_skill_stream(self, draft: dict[str, Any]) -> StreamResponse:
        """Open the skill polishing SSE stream for the supplied draft."""
        return self._stream("POST", _agent_resource_path(self._workspace_id, "skills", "/polish/stream"), draft)

    def resource_get(self, resource: str, tail_path: str = "", *opts: Callable[["QueryOptions"], None]) -> Any:
        """Route-aligned Agent resource proxy escape hatch; prefer AgentHandle A2A helpers for user-facing workflows."""
        return self._resource("GET", resource, tail_path, None, opts)

    def resource_post(self, resource: str, tail_path: str, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        """Route-aligned Agent resource proxy escape hatch; prefer AgentHandle A2A helpers for user-facing workflows."""
        return self._resource("POST", resource, tail_path, body, opts)

    def resource_put(self, resource: str, tail_path: str, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        """Route-aligned Agent resource proxy escape hatch; prefer AgentHandle A2A helpers for user-facing workflows."""
        return self._resource("PUT", resource, tail_path, body, opts)

    def resource_patch(self, resource: str, tail_path: str, body: dict[str, Any], *opts: Callable[["QueryOptions"], None]) -> Any:
        """Route-aligned Agent resource proxy escape hatch; prefer AgentHandle A2A helpers for user-facing workflows."""
        return self._resource("PATCH", resource, tail_path, body, opts)

    def resource_delete(self, resource: str, tail_path: str = "", *opts: Callable[["QueryOptions"], None]) -> Any:
        """Route-aligned Agent resource proxy escape hatch; prefer AgentHandle A2A helpers for user-facing workflows."""
        return self._resource("DELETE", resource, tail_path, None, opts)

    def resource_any(self, method: str, resource: str, tail_path: str, body: Optional[dict[str, Any]] = None, *opts: Callable[["QueryOptions"], None]) -> Any:
        """Route-aligned Agent resource proxy escape hatch with explicit HTTP method; prefer AgentHandle A2A helpers for user-facing workflows."""
        return self._resource(method, resource, tail_path, body, opts)

    def create_team(self, request: AgentTeamCreateRequest) -> AgentTeamRecord:
        """CreateTeam through the authenticated product gateway."""
        value = self._request("POST", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams", ()), request.body())
        return _product_message(value, AgentTeamRecord(), "agent team data")

    def list_teams(self, *opts: Callable[["QueryOptions"], None]) -> AgentTeamListResult:
        """ListTeams through the authenticated product gateway."""
        value = self._request("GET", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams", opts), None)
        return _product_message(value, AgentTeamListResult(), "agent team data")

    def get_team(self, team_id: str, *opts: Callable[["QueryOptions"], None]) -> AgentTeamRecord:
        """GetTeam through the authenticated product gateway."""
        value = self._request("GET", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}", opts), None)
        return _product_message(value, AgentTeamRecord(), "agent team data")

    def update_team(self, team_id: str, request: AgentTeamUpdateRequest) -> AgentTeamRecord:
        """UpdateTeam through the authenticated product gateway."""
        value = self._request("PATCH", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}", ()), request.body())
        return _product_message(value, AgentTeamRecord(), "agent team data")

    def delete_team(self, team_id: str, expected_version: int) -> AgentTeamRecord:
        """DeleteTeam through the authenticated product gateway."""
        value = self._request("DELETE", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}", (with_query_param("expected_version", str(expected_version)),)), None)
        return _product_message(value, AgentTeamRecord(), "agent team data")

    def list_team_members(self, team_id: str, *opts: Callable[["QueryOptions"], None]) -> AgentTeamMemberList:
        """ListTeamMembers through the authenticated product gateway."""
        value = self._request("GET", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/members", opts), None)
        return _product_message({"items": value}, AgentTeamMemberList(), "agent team data")

    def add_team_member(self, team_id: str, agent_workspace_id: str, agent_id: str, expected_membership_version: int) -> AgentTeamRecord:
        """AddTeamMember through the authenticated product gateway."""
        value = self._request("PUT", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/members/{_path_id(agent_workspace_id)}/{_path_id(agent_id)}", (with_query_param("expected_membership_version", str(expected_membership_version)),)), None)
        return _product_message(value, AgentTeamRecord(), "agent team data")

    def remove_team_member(self, team_id: str, agent_workspace_id: str, agent_id: str, expected_membership_version: int) -> AgentTeamRecord:
        """RemoveTeamMember through the authenticated product gateway."""
        value = self._request("DELETE", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/members/{_path_id(agent_workspace_id)}/{_path_id(agent_id)}", (with_query_param("expected_membership_version", str(expected_membership_version)),)), None)
        return _product_message(value, AgentTeamRecord(), "agent team data")

    def list_ingress_connections(self, target: AgentTargetRef, *opts: Callable[["QueryOptions"], None]) -> IngressConnectionList:
        query = tuple(opts) + (
            with_query_param("target_kind", target.kind),
            with_query_param("target_workspace_id", target.workspace_id),
            with_query_param("target_id", target.id),
        )
        value = self._request("GET", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/ingress-connections", query), None)
        return _product_message(value, IngressConnectionList(), "ingress connection data")

    def list_ingress_capabilities(self) -> IngressCapabilityList:
        """Return the provider receive modes implemented by the MOI deployment."""
        value = self._request("GET", f"/workspaces/{_path_id(self._workspace_id)}/ingress-capabilities", None)
        return _product_message(value, IngressCapabilityList(), "ingress capability data")

    def resolve_we_com_qr_binding(self, target: AgentTargetRef, session_token: str = "") -> WeComQRBindingResult:
        """Start or poll a short-lived WeCom QR session. Does not create a connection."""
        body = {"target": {"kind": target.kind, "workspace_id": target.workspace_id, "id": target.id}, "session_token": session_token}
        value = self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/ingress-connections/wecom-qr", body)
        return _product_message(value, WeComQRBindingResult(), "WeCom QR binding data")

    def create_ingress_connection(self, request: IngressConnectionCreateRequest) -> IngressConnection:
        value = self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/ingress-connections", request.body())
        return _product_message(value, IngressConnection(), "ingress connection data")

    def delete_ingress_connection(self, connection_id: str, expected_association_version: int, expected_config_version: int) -> IngressConnection:
        path = f"/workspaces/{_path_id(self._workspace_id)}/ingress-connections/{_path_id(connection_id)}"
        query = (with_query_param("expected_association_version", str(expected_association_version)), with_query_param("expected_config_version", str(expected_config_version)))
        value = self._request("DELETE", _with_query(path, query), None)
        return _product_message(value, IngressConnection(), "ingress connection data")

    def get_ingress_connection(self, connection_id: str) -> IngressConnection:
        value = self._request("GET", f"/workspaces/{_path_id(self._workspace_id)}/ingress-connections/{_path_id(connection_id)}", None)
        return _product_message(value, IngressConnection(), "ingress connection data")

    def update_ingress_connection(self, connection_id: str, request: IngressConnectionUpdateRequest) -> IngressConnection:
        value = self._request("PATCH", f"/workspaces/{_path_id(self._workspace_id)}/ingress-connections/{_path_id(connection_id)}", request.body())
        return _product_message(value, IngressConnection(), "ingress connection data")

    def verify_ingress_connection(self, connection_id: str, request: IngressConnectionVerifyRequest) -> IngressVerificationResult:
        value = self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/ingress-connections/{_path_id(connection_id)}/test", request.body())
        return _ingress_verification_result(value)

    def generate_we_com_callback_secrets(self) -> Any:
        return self._resource("POST", "tools", "/wecom/callback-secrets/generate", None, ())

    def list_team_sessions(self, team_id: str, *opts: Callable[["QueryOptions"], None]) -> AgentTeamSessionListResult:
        """ListTeamSessions through the authenticated product gateway."""
        value = self._request("GET", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/sessions", opts), None)
        return _product_message(value, AgentTeamSessionListResult(), "agent team data")

    def create_team_session(self, team_id: str, request: AgentTeamSessionCreateRequest) -> AgentTeamSession:
        value = self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/sessions", request.body())
        return _product_message(value, AgentTeamSession(), "agent team session data")

    def rename_team_session(self, team_id: str, context_id: str, request: AgentTeamSessionRenameRequest) -> AgentTeamSession:
        value = self._request("PATCH", f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/sessions/{_path_id(context_id)}", request.body())
        return _product_message(value, AgentTeamSession(), "agent team session data")

    def submit_team_message(self, team_id: str, context_id: str, request: AgentTeamMessageRequest) -> AgentTeamSubmitResult:
        value = self._request("POST", f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/sessions/{_path_id(context_id)}/messages", request.body())
        return _product_message(value, AgentTeamSubmitResult(), "agent team submit data")

    def list_team_messages(self, team_id: str, context_id: str, *opts: Callable[["QueryOptions"], None]) -> AgentTeamMessageListResult:
        path = f"/workspaces/{_path_id(self._workspace_id)}/agent-teams/{_path_id(team_id)}/sessions/{_path_id(context_id)}/messages"
        value = self._request("GET", _with_query(path, opts), None)
        return _product_message(value, AgentTeamMessageListResult(), "agent team message data")

    def create_channel_instance(self, provider: str, request: "ChannelInstanceCreateRequest") -> "ChannelInstanceRecord":
        return _channel_instance_record(self._resource("POST", "channels", f"/{_path_id(provider)}/instances", request.body(), ()))

    def list_channel_instances(self, provider: str, *opts: Callable[["QueryOptions"], None]) -> "ChannelInstanceListResult":
        return _channel_instance_list_result(self._resource("GET", "channels", f"/{_path_id(provider)}/instances", None, opts))

    def list_connector_catalog(self) -> "ConnectorCatalogResult":
        return _connector_catalog_result(self._resource("GET", "connector-catalog", "", None, ()))

    def get_channel_instance(self, provider: str, instance_id: str) -> "ChannelInstanceRecord":
        return _channel_instance_record(self._resource("GET", "channels", f"/{_path_id(provider)}/instances/{_path_id(instance_id)}", None, ()))

    def update_channel_instance(self, provider: str, instance_id: str, request: "ChannelInstanceUpdateRequest") -> "ChannelInstanceRecord":
        return _channel_instance_record(self._resource("PATCH", "channels", f"/{_path_id(provider)}/instances/{_path_id(instance_id)}", request.body(), ()))

    def test_channel_configuration(self, provider: str, request: "ChannelInstanceCreateRequest") -> "ChannelInstanceTestResult":
        return _channel_instance_test_result(self._resource("POST", "channels", f"/{_path_id(provider)}/instances/test", request.body(), ()))

    def disable_channel_instance(self, provider: str, instance_id: str) -> "ChannelInstanceRecord":
        return _channel_instance_record(self._resource("DELETE", "channels", f"/{_path_id(provider)}/instances/{_path_id(instance_id)}", None, ()))

    def test_channel_instance(self, provider: str, instance_id: str) -> "ChannelInstanceTestResult":
        return _channel_instance_test_result(self._resource("POST", "channels", f"/{_path_id(provider)}/instances/{_path_id(instance_id)}/test", None, ()))

    def create_callback_rule(self, request: "CallbackRuleCreateRequest") -> "CallbackRuleRecord":
        return _callback_rule_record(self._resource("POST", "callback-rules", "", request.body(), ()))

    def list_callback_rules(self, *opts: Callable[["QueryOptions"], None]) -> "CallbackRuleListResult":
        return _callback_rule_list_result(self._resource("GET", "callback-rules", "", None, opts))

    def get_callback_rule(self, callback_rule_id: str) -> "CallbackRuleRecord":
        return _callback_rule_record(self._resource("GET", "callback-rules", f"/{_path_id(callback_rule_id)}", None, ()))

    def update_callback_rule(self, callback_rule_id: str, request: "CallbackRuleUpdateRequest") -> "CallbackRuleRecord":
        return _callback_rule_record(self._resource("PATCH", "callback-rules", f"/{_path_id(callback_rule_id)}", request.body(), ()))

    def delete_callback_rule(self, callback_rule_id: str) -> "CallbackRuleDeleteResult":
        return _callback_rule_delete_result(self._resource("DELETE", "callback-rules", f"/{_path_id(callback_rule_id)}", None, ()))

    def _resource(
        self,
        method: str,
        resource: str,
        tail_path: str,
        body: Optional[dict[str, Any]],
        opts: tuple[Callable[["QueryOptions"], None], ...],
        *,
        require_envelope: bool = False,
    ) -> Any:
        path = _agent_resource_path(self._workspace_id, resource, tail_path)
        return self._request(method, _with_query(path, opts), body, require_envelope=require_envelope)

    def _agent_upload_payload(self, filename: str, data: bytes, fields: Optional[dict[str, str]] = None) -> tuple[bytes, str]:
        if not filename:
            raise Error("ErrFilenameRequired", "filename is required")
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, fields or {}, [("file", filename, data)])
        return body, f"multipart/form-data; boundary={boundary}"


class MemoryService(WorkspaceScopedService):
    """Legacy route-aligned escape hatch; prefer typed consumer memory handles on legacy servers.

    Deprecated for current MOI: its public API does not serve these routes.
    """

    def retrieve(
        self,
        query: str,
        subject_id: str,
        *,
        top_k: Optional[int] = None,
        session_id: Optional[str] = None,
        session_scope: Optional[str] = None,
        memory_types: Optional[list[str]] = None,
        branch: Optional[str] = None,
    ) -> MemoryListResult:
        """Retrieve memories for one subject via POST /newmoi/memories/retrieve."""
        return _memory_list_result(
            self._request(
                "POST",
                "/memories/retrieve",
                _memory_query_body(query, subject_id, top_k, session_id, session_scope, memory_types, branch),
            )
        )

    def search(
        self,
        query: str,
        subject_id: str,
        *,
        top_k: Optional[int] = None,
        session_id: Optional[str] = None,
        session_scope: Optional[str] = None,
        memory_types: Optional[list[str]] = None,
        branch: Optional[str] = None,
    ) -> MemoryListResult:
        """Search memories for one subject via POST /newmoi/memories/search."""
        return _memory_list_result(
            self._request(
                "POST",
                "/memories/search",
                _memory_query_body(query, subject_id, top_k, session_id, session_scope, memory_types, branch),
            )
        )

    def fulltext_search(
        self,
        query: str,
        subject_id: str,
        *,
        top_k: Optional[int] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[list[str]] = None,
        trust_tier: Optional[str] = None,
        branch: Optional[str] = None,
        extra_metadata_filter: Optional[dict[str, Any]] = None,
    ) -> MemoryListResult:
        """Run pure keyword search with optional exact Metadata filters."""
        _validate_memory_metadata_filter(extra_metadata_filter)
        if top_k is not None and not 0 <= top_k <= 100:
            raise Error("ErrInvalidArgument", "top_k must be between 0 and 100")
        body = _memory_structured_body(
            subject_id,
            session_id=session_id,
            memory_types=memory_types,
            trust_tier=trust_tier,
            branch=branch,
            extra_metadata_filter=extra_metadata_filter,
        )
        if not query or not query.strip():
            raise ErrQueryRequired
        body["query"] = query
        if top_k is not None:
            body["top_k"] = top_k
        return _memory_list_result(self._request("POST", "/memories/fulltext-search", body))

    def query(
        self,
        subject_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[list[str]] = None,
        trust_tier: Optional[str] = None,
        branch: Optional[str] = None,
        extra_metadata_filter: Optional[dict[str, Any]] = None,
    ) -> MemoryListResult:
        """Query exact structured conditions without relevance recall."""
        _validate_memory_metadata_filter(extra_metadata_filter)
        if limit is not None and not 0 <= limit <= 500:
            raise Error("ErrInvalidArgument", "limit must be between 0 and 500")
        body = _memory_structured_body(
            subject_id,
            session_id=session_id,
            memory_types=memory_types,
            trust_tier=trust_tier,
            branch=branch,
            extra_metadata_filter=extra_metadata_filter,
        )
        if limit is not None:
            body["limit"] = limit
        if cursor:
            body["cursor"] = cursor
        return _memory_list_result(self._request("POST", "/memories/query", body))

    def render_profile(self, subject_id: str, *, max_tokens: Optional[int] = None) -> ConsumerProfileRenderResult:
        """Render one subject's consumer profile via GET /newmoi/consumer-profiles/{user_id}/render."""
        if not subject_id or not subject_id.strip():
            raise ErrSubjectRequired
        if max_tokens is not None and max_tokens < 0:
            raise Error("ErrInvalidArgument", "max_tokens must not be negative")
        opts = (with_query_param("max_tokens", str(int(max_tokens))),) if max_tokens else ()
        return _consumer_profile_render_result(
            self._request("GET", _with_query(f"/consumer-profiles/{_path_id(subject_id)}/render", opts))
        )


def _memory_query_body(
    query: str,
    subject_id: str,
    top_k: Optional[int],
    session_id: Optional[str],
    session_scope: Optional[str],
    memory_types: Optional[list[str]],
    branch: Optional[str],
) -> dict[str, Any]:
    if not query or not query.strip():
        raise ErrQueryRequired
    if not subject_id or not subject_id.strip():
        raise ErrSubjectRequired
    if top_k is not None and not 0 <= top_k <= 100:
        raise Error("ErrInvalidArgument", "top_k must be between 0 and 100")
    body: dict[str, Any] = {"query": query, "subject_id": subject_id}
    if top_k is not None:
        body["top_k"] = top_k
    if session_id:
        body["session_id"] = session_id
    if session_scope:
        body["session_scope"] = session_scope
    if memory_types:
        body["memory_types"] = memory_types
    if branch:
        body["branch"] = branch
    return body


def _memory_structured_body(
    subject_id: str,
    *,
    session_id: Optional[str],
    memory_types: Optional[list[str]],
    trust_tier: Optional[str],
    branch: Optional[str],
    extra_metadata_filter: Optional[dict[str, Any]],
) -> dict[str, Any]:
    if not subject_id or not subject_id.strip():
        raise ErrSubjectRequired
    body: dict[str, Any] = {"subject_id": subject_id}
    if session_id:
        body["session_id"] = session_id
    if memory_types:
        body["memory_types"] = memory_types
    if trust_tier:
        body["trust_tier"] = trust_tier
    if branch:
        body["branch"] = branch
    if extra_metadata_filter:
        body["extra_metadata_filter"] = extra_metadata_filter
    return body


def _validate_memory_metadata_filter(extra_metadata_filter: Optional[dict[str, Any]]) -> None:
    if not extra_metadata_filter:
        return
    if len(extra_metadata_filter) > 16:
        raise Error("ErrInvalidArgument", "extra_metadata_filter supports at most 16 fields")
    for key, value in extra_metadata_filter.items():
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", key) is None:
            raise Error("ErrInvalidArgument", "extra_metadata_filter contains an invalid field name")
        if not isinstance(value, (str, int, float, bool)):
            raise Error("ErrInvalidArgument", "extra_metadata_filter values must be string, number, or boolean")
        try:
            encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise Error("ErrInvalidArgument", "extra_metadata_filter values must be finite scalars") from exc
        if len(encoded) > 1024:
            raise Error("ErrInvalidArgument", "extra_metadata_filter value exceeds 1024 encoded bytes")


class ModelService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed provider backend and router handles for user-facing workflows."""

    def create_workspace_llm_backend(self,request: WorkspaceLLMBackendCreateRequest) -> WorkspaceLLMBackend:
        if not isinstance(request,WorkspaceLLMBackendCreateRequest): raise TypeError("request must be WorkspaceLLMBackendCreateRequest")
        body=MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/backends",body),WorkspaceLLMBackend(),"workspace model result")

    def list_workspace_llm_backends(self) -> WorkspaceLLMBackendList:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/backends",None),WorkspaceLLMBackendList(),"workspace model result")

    def get_workspace_llm_backend(self,backend_id: int) -> WorkspaceLLMBackend:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/backends/"+str(backend_id),None),WorkspaceLLMBackend(),"workspace model result")

    def update_workspace_llm_backend(self,backend_id: int,request: WorkspaceLLMBackendUpdateRequest) -> WorkspaceLLMBackend:
        if not isinstance(request,WorkspaceLLMBackendUpdateRequest): raise TypeError("request must be WorkspaceLLMBackendUpdateRequest")
        body=MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/backends/"+str(backend_id),body),WorkspaceLLMBackend(),"workspace model result")

    def delete_workspace_llm_backend(self,backend_id: int) -> None:
        self._request("DELETE",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/backends/"+str(backend_id),None)

    def create_workspace_llm_endpoint(self,backend_id: int,address: str) -> WorkspaceLLMEndpoint:
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/backends/"+str(backend_id)+"/endpoints",{"address":address}),WorkspaceLLMEndpoint(),"workspace model result")

    def workspace_llm_router(self) -> WorkspaceLLMRouterConfigResult:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/router-config",None),WorkspaceLLMRouterConfigResult(),"workspace model result")

    def update_workspace_llm_router(self,request: WorkspaceLLMRouterUpdateRequest) -> WorkspaceLLMRouterConfigResult:
        if not isinstance(request,WorkspaceLLMRouterUpdateRequest): raise TypeError("request must be WorkspaceLLMRouterUpdateRequest")
        body=MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/router-config",body),WorkspaceLLMRouterConfigResult(),"workspace model result")

    def create_workspace_embedding_backend(self,request: WorkspaceLLMBackendCreateRequest) -> WorkspaceLLMBackend:
        if not isinstance(request,WorkspaceLLMBackendCreateRequest): raise TypeError("request must be WorkspaceLLMBackendCreateRequest")
        body=MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/backends",body),WorkspaceLLMBackend(),"workspace model result")

    def list_workspace_embedding_backends(self) -> WorkspaceLLMBackendList:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/backends",None),WorkspaceLLMBackendList(),"workspace model result")

    def get_workspace_embedding_backend(self,backend_id: int) -> WorkspaceLLMBackend:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/backends/"+str(backend_id),None),WorkspaceLLMBackend(),"workspace model result")

    def update_workspace_embedding_backend(self,backend_id: int,request: WorkspaceLLMBackendUpdateRequest) -> WorkspaceLLMBackend:
        if not isinstance(request,WorkspaceLLMBackendUpdateRequest): raise TypeError("request must be WorkspaceLLMBackendUpdateRequest")
        body=MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/backends/"+str(backend_id),body),WorkspaceLLMBackend(),"workspace model result")

    def delete_workspace_embedding_backend(self,backend_id: int) -> None:
        self._request("DELETE",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/backends/"+str(backend_id),None)

    def create_workspace_embedding_endpoint(self,backend_id: int,address: str) -> WorkspaceLLMEndpoint:
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/backends/"+str(backend_id)+"/endpoints",{"address":address}),WorkspaceLLMEndpoint(),"workspace model result")

    def workspace_embedding_router(self) -> WorkspaceLLMRouterConfigResult:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/router-config",None),WorkspaceLLMRouterConfigResult(),"workspace model result")

    def update_workspace_embedding_router(self,request: WorkspaceLLMRouterUpdateRequest) -> WorkspaceLLMRouterConfigResult:
        if not isinstance(request,WorkspaceLLMRouterUpdateRequest): raise TypeError("request must be WorkspaceLLMRouterUpdateRequest")
        body=MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/embeddings"+"/router-config",body),WorkspaceLLMRouterConfigResult(),"workspace model result")


    def list_workspace_llm_endpoints(self, backend_id: int) -> list[WorkspaceLLMEndpoint]:
        return [_product_message(item, WorkspaceLLMEndpoint(), "workspace endpoint") for item in self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm/backends/{backend_id}/endpoints")]

    def set_workspace_llm_endpoint_status(self, backend_id: int, endpoint_id: int, status: int) -> None:
        self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/llm/backends/{backend_id}/endpoints/{endpoint_id}/status",{"status":status})

    def list_workspace_embedding_endpoints(self, backend_id: int) -> list[WorkspaceLLMEndpoint]:
        return [_product_message(item, WorkspaceLLMEndpoint(), "workspace endpoint") for item in self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/embeddings/backends/{backend_id}/endpoints")]

    def set_workspace_embedding_endpoint_status(self, backend_id: int, endpoint_id: int, status: int) -> WorkspaceEndpointMutationResult:
        return _product_message(self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/embeddings/backends/{backend_id}/endpoints/{endpoint_id}/status",{"status":status}),WorkspaceEndpointMutationResult(),"workspace endpoint mutation")

    def list_workspace_llm_models(self) -> ProviderModelListResult:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm/models"),ProviderModelListResult(),"workspace models")

    def workspace_chat_completion(self,request: WorkspaceChatCompletionRequest, *opts: Callable[["QueryOptions"], None]) -> Any:
        if not isinstance(request,WorkspaceChatCompletionRequest): raise TypeError("request must be WorkspaceChatCompletionRequest")
        body = _workspace_chat_completion_body(request)
        return self._request("POST",_with_query(f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/chat/completions",opts),body)

    def workspace_chat_completion_stream(self, request: WorkspaceChatCompletionRequest, *opts: Callable[["QueryOptions"], None]) -> StreamResponse:
        if not isinstance(request, WorkspaceChatCompletionRequest):
            raise TypeError("request must be WorkspaceChatCompletionRequest")
        body = _workspace_chat_completion_body(request)
        body["stream"] = True
        return self._stream("POST", _with_query(f"/workspaces/{_path_id(self._workspace_id)}/llm/chat/completions", opts), body)

    def llm_backends(self) -> "ProviderBackendService":
        return ProviderBackendService(self._client, self._workspace_id, "/llm")

    def embedding_backends(self) -> "ProviderBackendService":
        return ProviderBackendService(self._client, self._workspace_id, "/embedding")

    def parser_backends(self) -> "ProviderBackendService":
        return ProviderBackendService(self._client, self._workspace_id, "/parser")

    def list(self, *opts: Callable[["QueryOptions"], None]) -> ProviderModelListResult:
        return _provider_model_list_result(self._request("GET", _with_query("/models", opts)))

    def list_embedding_models(self) -> ProviderModelListResult:
        return _provider_model_list_result(self._request("GET", "/embedding/models"))

    def setup_llm_backend(
        self,
        name: str,
        address: str,
        models: list[str],
        *opts: Callable[["ProviderBackendOptions"], None],
    ) -> ProviderSetupBackendResult:
        if not name:
            raise ErrNameRequired
        if not address:
            raise ErrAddressRequired
        if not models:
            raise ErrModelsRequired
        body = _provider_backend_body(name, opts)
        body["address"] = address
        body["models"] = models
        return _provider_setup_backend_result(self._request("POST", "/llm/setup", body))

    def setup_llm_backend_raw(self, body: dict[str, Any]) -> ProviderSetupBackendResult:
        return _provider_setup_backend_result(self._request("POST", "/llm/setup", body))

    def probe_llm_models(self, address: str, *opts: Callable[["ProviderBackendOptions"], None]) -> ProviderProbeModelsResult:
        if not address:
            raise ErrAddressRequired
        return _provider_probe_models_result(self._request("POST", "/llm/probe-models", _provider_probe_body(address, opts)))

    def probe_llm_models_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/llm/probe-models", workspace_id=self._workspace_id, body=body)

    def probe_embedding_models(self, address: str, *opts: Callable[["ProviderBackendOptions"], None]) -> ProviderProbeModelsResult:
        if not address:
            raise ErrAddressRequired
        return _provider_probe_models_result(self._request("POST", "/embedding/probe-models", _provider_probe_body(address, opts)))

    def probe_embedding_models_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/embedding/probe-models", workspace_id=self._workspace_id, body=body)

class ProviderBackendService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed provider backend and router handles for user-facing workflows."""

    def __init__(self, client: Client, workspace_id: str, base_path: str) -> None:
        super().__init__(client, workspace_id)
        self._base_path = base_path

    def list(self) -> ProviderBackendListResult:
        data = self._request("GET", self._base_path + "/backends", data_nullable=self._base_path == "/parser")
        if self._base_path == "/parser":
            return _provider_backend_list_from_array(data)
        return _provider_backend_list_result(data)

    def create(self, name: str, *opts: Callable[["ProviderBackendOptions"], None]) -> ProviderBackend:
        if not name:
            raise ErrNameRequired
        body = _provider_backend_body(name, opts)
        if self._base_path == "/parser":
            # Parser CreateParserBackendRequest accepts supported_mime_types; LLM/embedding do not.
            _apply_supported_mime_types(body, opts)
        elif "models" not in body:
            raise ErrModelsRequired
        return _provider_backend(self._request("POST", self._base_path + "/backends", body))

    def create_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", self._base_path + "/backends", workspace_id=self._workspace_id, body=body)

    def get(self, backend_id: str) -> ProviderBackend:
        return _provider_backend(self._request("GET", self._base_path + f"/backends/{_path_id(backend_id)}"))

    def get_result(self, backend_id: str) -> ProductResult:
        return self._client._product_result("GET", self._base_path + f"/backends/{_path_id(backend_id)}", workspace_id=self._workspace_id)

    def update(self, backend_id: str, *opts: Callable[["ProviderBackendUpdateOptions"], None]) -> ProviderBackend:
        return _provider_backend(self._request("PUT", self._base_path + f"/backends/{_path_id(backend_id)}", _provider_backend_update_body(opts)))

    def update_raw(self, backend_id: str, body: dict[str, Any]) -> ProviderBackend:
        return _provider_backend(self._request("PUT", self._base_path + f"/backends/{_path_id(backend_id)}", body))

    def update_result(self, backend_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "PUT",
            self._base_path + f"/backends/{_path_id(backend_id)}",
            workspace_id=self._workspace_id,
            body=body,
        )

    def delete(self, backend_id: str) -> ProviderMutationResult:
        data = self._request("DELETE", self._base_path + f"/backends/{_path_id(backend_id)}")
        if data is None:
            result = ProviderMutationResult()
            result.success = True
            return result
        return _provider_mutation_result(data)

    def delete_result(self, backend_id: str) -> ProductResult:
        return self._client._product_result(
            "DELETE",
            self._base_path + f"/backends/{_path_id(backend_id)}",
            workspace_id=self._workspace_id,
        )

    def create_endpoint(self, backend_id: str, address: str) -> ProviderEndpoint:
        if not address:
            raise ErrAddressRequired
        return _provider_endpoint(self._request("POST", self._base_path + f"/backends/{_path_id(backend_id)}/endpoints", {"address": address}))

    def create_endpoint_result(self, backend_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "POST",
            self._base_path + f"/backends/{_path_id(backend_id)}/endpoints",
            workspace_id=self._workspace_id,
            body=body,
        )

    def list_endpoints(self, backend_id: str) -> ProviderEndpointListResult:
        data = self._request("GET", self._base_path + f"/backends/{_path_id(backend_id)}/endpoints", data_nullable=self._base_path == "/parser")
        if self._base_path == "/parser":
            return _provider_endpoint_list_from_array(data)
        return _provider_endpoint_list_result(data)

    def list_endpoints_result(self, backend_id: str) -> ProductResult:
        return self._client._product_result(
            "GET",
            self._base_path + f"/backends/{_path_id(backend_id)}/endpoints",
            workspace_id=self._workspace_id,
        )

    def set_endpoint_status(self, backend_id: str, endpoint_id: str, status: str) -> ProviderMutationResult:
        backend_path, endpoint_path = _provider_endpoint_path(backend_id, endpoint_id)
        if not status:
            raise ErrStatusRequired
        data = self._request(
            "PUT",
            self._base_path + f"/backends/{backend_path}/endpoints/{endpoint_path}/status",
            {"status": status},
        )
        if data is None:
            result = ProviderMutationResult()
            result.success = True
            return result
        return _provider_mutation_result(data)

    def set_endpoint_status_result(self, backend_id: str, endpoint_id: str, body: dict[str, Any]) -> ProductResult:
        backend_path, endpoint_path = _provider_endpoint_path(backend_id, endpoint_id)
        return self._client._product_result(
            "PUT",
            self._base_path + f"/backends/{backend_path}/endpoints/{endpoint_path}/status",
            workspace_id=self._workspace_id,
            body=body,
        )

    def set_endpoint_status_raw(self, backend_id: str, endpoint_id: str, body: dict[str, Any]) -> ProviderMutationResult:
        backend_path, endpoint_path = _provider_endpoint_path(backend_id, endpoint_id)
        data = self._request(
            "PUT",
            self._base_path + f"/backends/{backend_path}/endpoints/{endpoint_path}/status",
            body,
        )
        if data is None:
            result = ProviderMutationResult()
            result.success = True
            return result
        return _provider_mutation_result(data)

    def router(self) -> ProviderRouterConfig:
        return _provider_router_config(self._request("GET", self._base_path + "/router"))

    def update_router(self, *opts: Callable[["RouterOptions"], None]) -> ProviderRouterConfig:
        return _provider_router_config(self._request("PUT", self._base_path + "/router", _router_body(opts)))

    def probe_backend_models(self, backend_id: str, *opts: Callable[["ProviderBackendOptions"], None]) -> ProviderProbeModelsResult:
        if self._base_path == "/parser":
            raise Error("ErrUnsupportedOperation", "provider kind does not support backend model probe: parser")
        body = _provider_backend_probe_body(opts)
        if "api_key" not in body:
            raise ErrAPIKeyRequired
        return _provider_probe_models_result(self._request("POST", self._base_path + f"/backends/{_path_id(backend_id)}/probe-models", body))

    def probe_backend_models_result(self, backend_id: str, body: Optional[dict[str, Any]] = None) -> ProductResult:
        return self._client._product_result(
            "POST",
            self._base_path + f"/backends/{_path_id(backend_id)}/probe-models",
            workspace_id=self._workspace_id,
            body=body,
        )

class ConnectorService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed connector, import task, export task, and connector file handles for user-facing workflows."""

    def list(self, *opts: Callable[["QueryOptions"], None]) -> ConnectorListResult:
        return _connector_list_result(self._request("GET", _with_query("/connectors/list", opts)))

    def list_result(self, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result("GET", _with_query("/connectors/list", opts), workspace_id=self._workspace_id)

    def get(self, connector_id: str) -> Connector:
        if not connector_id:
            raise ErrConnectorIDRequired
        return _connector(self._connector_post("/connectors/get", {"id": connector_id}))

    def get_raw(self, body: dict[str, Any]) -> Connector:
        return _connector(self._connector_post("/connectors/get", body))

    def get_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/connectors/get", workspace_id=self._workspace_id, body=body)

    def create(
        self,
        name: str,
        source_type: int,
        usage_type: int,
        *opts: Callable[["ConnectorDefinitionOptions"], None],
    ) -> Connector:
        if not name:
            raise ErrNameRequired
        return _connector(self._connector_post("/connectors", _connector_definition_body(name, source_type, usage_type, opts)))

    def create_raw(self, body: dict[str, Any]) -> Connector:
        return _connector(self._connector_post("/connectors", body))

    def create_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/connectors", workspace_id=self._workspace_id, body=body)

    def update(self, connector_id: str, *opts: Callable[["ConnectorUpdateOptions"], None]) -> None:
        if not connector_id:
            raise ErrConnectorIDRequired
        self._request("PUT", f"/connectors/{_path_id(connector_id)}", _connector_update_body(opts))

    def update_raw(self, connector_id: str, body: dict[str, Any]) -> None:
        self._request("PUT", f"/connectors/{_path_id(connector_id)}", body)

    def update_result(self, connector_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "PUT",
            f"/connectors/{_path_id(connector_id)}",
            workspace_id=self._workspace_id,
            body=body,
        )

    def delete(self, connector_id: str) -> None:
        if not connector_id:
            raise ErrConnectorIDRequired
        self._request("DELETE", f"/connectors/{_path_id(connector_id)}")

    def delete_raw(self, connector_id: str) -> None:
        self._request("DELETE", f"/connectors/{_path_id(connector_id)}")

    def delete_result(self, connector_id: str) -> ProductResult:
        return self._client._product_result("DELETE", f"/connectors/{_path_id(connector_id)}", workspace_id=self._workspace_id)

    def validate(
        self,
        name: str,
        source_type: int,
        usage_type: int,
        *opts: Callable[["ConnectorDefinitionOptions"], None],
    ) -> ConnectorValidateResult:
        if not name:
            raise ErrNameRequired
        return _connector_validate_result(self._connector_post("/connectors/validate", _connector_definition_body(name, source_type, usage_type, opts)))

    def probe_rest_draft(self, config: dict[str, Any]) -> ConnectorValidateResult:
        return _connector_validate_result(self._connector_post("/connectors/rest-api/probe", {"config": config}))

    def probe_rest(self, connector_id: str) -> ConnectorValidateResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        return _connector_validate_result(self._request("POST", f"/connectors/{_path_id(connector_id)}/rest-api/probe"))

    def preview_rest(self, connector_id: str, preview: RESTPreview) -> RESTReadResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        data = self._connector_post(f"/connectors/{_path_id(connector_id)}/rest-api/preview", preview.body())
        return _product_message(data, RESTReadResult(), "REST API preview data")

    def files(self, *opts: Callable[["QueryOptions"], None]) -> ConnectorFileListResult:
        return _connector_file_list_result(self._request("GET", _with_query("/connectors/files/list", opts)))

    def upload(self, files: list[tuple[str, str, bytes]], fields: Optional[dict[str, str]] = None) -> UploadResponse:
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, fields or {}, files)
        return _upload_response(self._raw_request("POST", "/connectors/upload", body, f"multipart/form-data; boundary={boundary}"))

    def local_upload(self, files: list[tuple[str, str, bytes]]) -> LocalUploadResult:
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, {}, files)
        return _local_upload_result(self._raw_request("POST", "/connectors/file/upload", body, f"multipart/form-data; boundary={boundary}"))

    def local_upload_raw_result(
        self,
        fields: Optional[dict[str, str]] = None,
        files: Optional[list[tuple[str, str, bytes]]] = None,
    ) -> ProductResult:
        boundary = "moi-product-sdk-" + uuid.uuid4().hex
        body = _multipart_body(boundary, fields or {}, files or [])
        return self._client._raw_product_result(
            "POST",
            "/connectors/file/upload",
            self._workspace_id,
            body,
            f"multipart/form-data; boundary={boundary}",
        )

    def preview_file(self, connector_id: str, uri: str, *opts: Callable[["ConnectorPreviewOptions"], None]) -> PreviewFileResult:
        body = _connector_preview_body(connector_id, uri, opts)
        if not body.get("connector_id") and not body.get("conn_file_id"):
            raise ErrConnectorIDRequired
        return _preview_file_result(self._connector_post("/connectors/file/preview", body))

    def preview_file_raw(self, body: dict[str, Any]) -> PreviewFileResult:
        return _preview_file_result(self._connector_post("/connectors/file/preview", body))

    def preview_file_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/connectors/file/preview",
            workspace_id=self._workspace_id,
            body=body,
        )

    def db_list_databases(self, connector_id: str) -> DBListDatabasesResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        return _db_list_databases_result(self._connector_post("/connectors/db/database/list", {"connector_id": connector_id}))

    def db_list_databases_raw(self, body: dict[str, Any]) -> DBListDatabasesResult:
        return _db_list_databases_result(self._connector_post("/connectors/db/database/list", body))

    def db_list_schemas(self, connector_id: str, database: str) -> DBListSchemasResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not database:
            raise ErrDatabaseRequired
        return _db_list_schemas_result(self._connector_post("/connectors/db/database/schema/list", {"connector_id": connector_id, "database": database}))

    def db_list_schemas_raw(self, body: dict[str, Any]) -> DBListSchemasResult:
        return _db_list_schemas_result(self._connector_post("/connectors/db/database/schema/list", body))

    def db_list_tables(self, connector_id: str, database: str, *opts: Callable[["ConnectorDBOptions"], None]) -> DBListTablesResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not database:
            raise ErrDatabaseRequired
        return _db_list_tables_result(self._connector_post("/connectors/db/database/table/list", _connector_db_body(connector_id, database, opts)))

    def db_list_tables_raw(self, body: dict[str, Any]) -> DBListTablesResult:
        return _db_list_tables_result(self._connector_post("/connectors/db/database/table/list", body))

    def db_source_schema(self, connector_id: str, database: str, table: str, *opts: Callable[["ConnectorDBOptions"], None]) -> DBSourceSchemaResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not database:
            raise ErrDatabaseRequired
        if not table:
            raise ErrTableRequired
        body = _connector_db_body(connector_id, database, opts)
        body["table"] = table
        return _db_source_schema_result(self._connector_post("/connectors/db/schema", body))

    def db_source_schema_raw(self, body: dict[str, Any]) -> DBSourceSchemaResult:
        return _db_source_schema_result(self._connector_post("/connectors/db/schema", body))

    def structured_sources(self) -> StructuredSourceListResult:
        return _structured_source_list_result(self._request("GET", "/connectors/structured/v1/sources"))

    def structured_source_databases(self, connector_id: str, source_type: str) -> StructuredSourceDatabasesResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not source_type:
            raise ErrTypeRequired
        return _structured_source_databases_result(
            self._connector_post(
                "/connectors/structured/v1/source/databases",
                {"connector_id": connector_id, "source_type": source_type},
            )
        )

    def structured_source_schemas(self, connector_id: str, source_type: str, database: str) -> StructuredSourceSchemasResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not source_type:
            raise ErrTypeRequired
        if not database:
            raise ErrDatabaseRequired
        return _structured_source_schemas_result(
            self._connector_post(
                "/connectors/structured/v1/source/schemas",
                {"connector_id": connector_id, "source_type": source_type, "database": database},
            )
        )

    def structured_source_objects(
        self,
        connector_id: str,
        source_type: str,
        database: str,
        schema: str = "",
    ) -> StructuredSourceObjectsResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not source_type:
            raise ErrTypeRequired
        if not database:
            raise ErrDatabaseRequired
        request = StructuredSourceObjectsRequest(connector_id, source_type, database, schema)
        return _structured_source_objects_result(self._connector_post("/connectors/structured/v1/source/objects", request.body()))

    def structured_source_schema(
        self,
        connector_id: str,
        source_type: str,
        database: str = "",
        table: str = "",
        schema: str = "",
        collection: str = "",
        mongo_sample_limit: Optional[int] = None,
        kafka_schema: Optional[StructuredKafkaSchemaSpec] = None,
    ) -> StructuredSourceSchemaResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not source_type:
            raise ErrTypeRequired
        if source_type != "SOURCE_TYPE_KAFKA" and not database:
            raise ErrDatabaseRequired
        if source_type != "SOURCE_TYPE_KAFKA" and not table and not collection:
            raise ErrTableRequired
        source = StructuredSourceRef(
            connector_id=connector_id,
            source_type=source_type,
            database=database,
            schema=schema,
            table=table,
            collection=collection,
        )
        request = StructuredSourceSchemaRequest(connector_id, source, mongo_sample_limit, kafka_schema)
        return _structured_source_schema_result(self._connector_post("/connectors/structured/v1/source/schema", request.body()))

    def structured_source_capability(
        self,
        connector_id: str,
        source_type: str,
        database: str,
        table: str,
        schema: str = "",
    ) -> StructuredSourceCapabilityResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not source_type:
            raise ErrTypeRequired
        if not database:
            raise ErrDatabaseRequired
        if not table:
            raise ErrTableRequired
        source = StructuredSourceRef(
            connector_id=connector_id,
            source_type=source_type,
            database=database,
            schema=schema,
            table=table,
        )
        return _structured_source_capability_result(
            self._connector_post(
                "/connectors/structured/v1/source/capabilities",
                {"connector_id": connector_id, "source": source.body()},
            )
        )

    def structured_source_sample(
        self,
        connector_id: str,
        source_type: str,
        limit: int,
        topic_mode: str,
        topics: Optional[list[str]] = None,
        topic_pattern: str = "",
    ) -> StructuredSourceSampleResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not source_type:
            raise ErrTypeRequired
        if limit <= 0:
            raise Error("ErrLimitRequired", "limit is required")
        sample: dict[str, Any] = {"topic_mode": topic_mode}
        if topics:
            sample["topics"] = topics
        if topic_pattern:
            sample["topic_pattern"] = topic_pattern
        source = StructuredSourceRef(connector_id=connector_id, source_type=source_type, database="")
        return _structured_source_sample_result(
            self._connector_post(
                "/connectors/structured/v1/source/sample",
                {
                    "connector_id": connector_id,
                    "source": source.body(),
                    "limit": limit,
                    "kafka_sample": sample,
                },
            )
        )

    def structured_backfill_start_resolve(
        self,
        connector_id: str,
        source_type: str,
        database: str,
        table: str,
        start_mode: str,
        schema: str = "",
        collection: str = "",
        watermark: Optional[object] = None,
        custom_start_value: Optional[object] = None,
    ) -> StructuredBackfillStartResolveResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not source_type:
            raise ErrTypeRequired
        if not database:
            raise ErrDatabaseRequired
        if not start_mode:
            raise ErrModeRequired
        source = StructuredSourceRef(
            connector_id=connector_id,
            source_type=source_type,
            database=database,
            schema=schema,
            table=table,
            collection=collection,
        )
        request = StructuredBackfillStartResolveRequest(
            connector_id,
            source,
            start_mode,
            watermark,
            custom_start_value,
        )
        return _structured_backfill_start_resolve_result(
            self._connector_post("/connectors/structured/v1/source/backfill-start/resolve", request.body())
        )

    def file_download(self, conn_file_id: str) -> FileDownloadResult:
        if not conn_file_id:
            raise ErrConnectorFileIDRequired
        return _file_download_result(self._connector_post("/connectors/file/download", {"conn_file_id": conn_file_id}))

    def file_stream(self, conn_file_id: str) -> StreamResponse:
        if not conn_file_id:
            raise ErrConnectorFileIDRequired
        path = _with_query("/connectors/file/stream", (with_query_param("conn_file_id", conn_file_id),))
        return self._download("GET", path)

    def file_stream_result(self, conn_file_id: str) -> ProductResult:
        path = _with_query("/connectors/file/stream", (with_query_param("conn_file_id", conn_file_id),))
        return self._client._product_result("GET", path, workspace_id=self._workspace_id)

    def file_delete(self, conn_file_id: str) -> None:
        if not conn_file_id:
            raise ErrConnectorFileIDRequired
        self._connector_post("/connectors/file/delete", {"conn_file_id": conn_file_id})

    def mo_database_list(self, connector_id: str) -> MODatabaseListResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        return _mo_database_list_result(self._connector_post("/connectors/mo/database/list", {"connector_id": connector_id}))

    def mo_database_list_raw(self, body: dict[str, Any]) -> MODatabaseListResult:
        return _mo_database_list_result(self._connector_post("/connectors/mo/database/list", body))

    def mo_database_table_list(self, connector_id: str, database: str) -> MODatabaseTableListResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not database:
            raise ErrDatabaseRequired
        return _mo_database_table_list_result(self._connector_post("/connectors/mo/database/table/list", {"connector_id": connector_id, "database": database}))

    def mo_database_table_list_raw(self, body: dict[str, Any]) -> MODatabaseTableListResult:
        return _mo_database_table_list_result(self._connector_post("/connectors/mo/database/table/list", body))

    def mo_check_table_name(self, connector_id: str, database: str, table: str) -> MOCheckTableNameResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not database:
            raise ErrDatabaseRequired
        if not table:
            raise ErrTableRequired
        return _mo_check_table_name_result(self._connector_post("/connectors/mo/check_table_name", {"connector_id": connector_id, "database": database, "table": table}))

    def mo_check_table_name_raw(self, body: dict[str, Any]) -> MOCheckTableNameResult:
        return _mo_check_table_name_result(self._connector_post("/connectors/mo/check_table_name", body))

    def mo_column_mapping(self, connector_id: str, database: str, table: str, export_columns: dict[str, str]) -> MOColumnMappingResult:
        if not connector_id:
            raise ErrConnectorIDRequired
        if not database:
            raise ErrDatabaseRequired
        if not table:
            raise ErrTableRequired
        return _mo_column_mapping_result(
            self._connector_post(
                "/connectors/mo/column/mapping",
                {"connector_id": connector_id, "database": database, "table": table, "export_columns": export_columns},
            )
        )

    def mo_column_mapping_raw(self, body: dict[str, Any]) -> MOColumnMappingResult:
        return _mo_column_mapping_result(self._connector_post("/connectors/mo/column/mapping", body))

    def task_stats(self) -> ImportTaskStats:
        """Return visible workspace task counts without loading task details."""
        return _product_message(self._request("GET", "/task/stats"), ImportTaskStats(), "import task stats data")

    def tasks(self, *opts: Callable[["QueryOptions"], None]) -> ImportTaskListResult:
        return _import_task_list_result(self._request("GET", _with_query("/task/list", opts)))

    def create_task(
        self,
        spec: "ImportTaskCreateSpec",
        *opts: Callable[["CreateImportTaskOptions"], None],
    ) -> ImportTaskCreateResult:
        return _import_task_create_result(self._connector_post("/task", spec.body(opts)))

    def create_task_raw(self, body: dict[str, Any]) -> ImportTaskCreateResult:
        return _import_task_create_result(self._connector_post("/task", body))

    def create_task_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/task", workspace_id=self._workspace_id, body=body)

    def update_task(self, task_id: str, spec: Optional["ImportTaskUpdateSpec"] = None) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        if spec is None:
            raise ErrSourceConfigRequired
        body: dict[str, Any] = {"task_id": task_id}
        body.update(spec.updates())
        self._connector_post("/task/update", body)

    def update_task_raw(self, body: dict[str, Any]) -> None:
        self._connector_post("/task/update", body)

    def update_task_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/task/update", workspace_id=self._workspace_id, body=body)

    def update_task_from_spec(self, task_id: str, spec: ImportTaskUpdateSpec) -> None:
        self.update_task(task_id, spec)

    def delete_task(self, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post("/task/delete", {"task_id": task_id})

    def delete_task_result(self, task_id: str) -> ProductResult:
        return self._client._product_result("POST", "/task/delete", workspace_id=self._workspace_id, body={"task_id": task_id})

    def pause_task(self, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post("/task/pause", {"task_id": task_id})

    def resume_task(self, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post("/task/resume", {"task_id": task_id})

    def run_task_now(self, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post("/task/run-now", {"task_id": task_id})

    def run_task_full_refresh(self, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post("/task/run-full-refresh", {"task_id": task_id})

    def get_task(self, task_id: str) -> ImportTaskInfoResult:
        if not task_id:
            raise ErrTaskIDRequired
        path = _with_query("/task/get", (with_query_param("task_id", task_id),))
        return _import_task_info_result(self._request("GET", path))

    def get_task_result(self, task_id: str) -> ProductResult:
        path = _with_query("/task/get", (with_query_param("task_id", task_id),))
        return self._client._product_result("GET", path, workspace_id=self._workspace_id)

    def task_files(self, *opts: Callable[["QueryOptions"], None]) -> ImportTaskFileListResult:
        return _import_task_file_list_result(self._request("GET", _with_query("/task/files", opts)))

    def task_runs(self, task_id: str) -> ImportTaskRunListResult:
        if not task_id:
            raise ErrTaskIDRequired
        path = _with_query("/task/runs", (with_query_param("task_id", task_id),))
        return _import_task_run_list_result(self._request("GET", path))

    def retry_task_files(self, task_id: str, *ids: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post("/task/retry", {"task_id": task_id, "ids": list(ids)})

    def retry_task_files_result(self, task_id: str, *ids: str) -> ProductResult:
        if not task_id:
            raise ErrTaskIDRequired
        return self._client._product_result(
            "POST",
            "/task/retry",
            workspace_id=self._workspace_id,
            body={"task_id": task_id, "ids": list(ids)},
        )

    def export_task_stats(self) -> ExportTaskStats:
        return _product_message(self._request("GET", "/export/task/stats"), ExportTaskStats(), "export task stats data")

    def export_tasks(self, *opts: Callable[["ExportTaskListOptions"], None]) -> ExportTaskListResult:
        return _export_task_list_result(self._connector_post("/export/task/list", _export_task_list_body(opts)))

    def export_task_info(self, task_id: str) -> ExportTaskInfo:
        if not task_id:
            raise ErrTaskIDRequired
        return _export_task_info(self._connector_post("/export/task/info", {"id": task_id}))

    def export_task_files(self, task_id: str, *opts: Callable[["ExportTaskFilesOptions"], None]) -> ExportTaskFilesResult:
        if not task_id:
            raise ErrTaskIDRequired
        body = _export_task_files_body(opts)
        body["task_id"] = task_id
        return _export_task_files_result(self._connector_post("/export/task/files", body))

    def delete_export_task(self, task_id: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post("/export/task/delete", {"id": task_id})

    def create_export_task(
        self,
        spec: "ExportTaskCreateSpec",
    ) -> ExportTask:
        return _export_task(self._connector_post("/export/task/create", spec.body()))

    def create_export_task_raw(self, body: dict[str, Any]) -> ExportTask:
        return _export_task(self._connector_post("/export/task/create", body))

    def retry_export_task(self, task_id: str, *file_ids: str) -> None:
        if not task_id:
            raise ErrTaskIDRequired
        self._connector_post(f"/export/task/{_path_id(task_id)}/rerun", {"files": list(file_ids)})

    def export_task_state(self, task_id: str) -> ExportTaskStateResult:
        if not task_id:
            raise ErrTaskIDRequired
        return _export_task_state_result(self._request("GET", f"/export/task/{_path_id(task_id)}/state"))

    def _connector_post(self, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        return self._request("POST", path, body)

class SQLService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed SQL metadata, workbook, query, and statement handles for user-facing workflows."""

    def download_query_result(self, statement_id: str) -> StreamResponse:
        if not statement_id:
            raise ErrStatementIDRequired
        return self._download("POST", "/query/result/download", {"statement_id": statement_id})

    def create_workbook(self, name: str) -> SQLWorkbook:
        return _sql_workbook(self._sql_post("/workbook/create", {"name": name}))

    def create_workbook_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/create", workspace_id=self._workspace_id, body=body)

    def workbooks(self, *opts: Callable[["WorkbookListOptions"], None]) -> SQLWorkbookListResult:
        return _sql_workbook_list_result(self._sql_post("/workbook/list", _workbook_list_body(opts)))

    def workbooks_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/list", workspace_id=self._workspace_id, body=body)

    def update_workbook(self, workbook_id: str, name: str) -> None:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        if not name:
            raise ErrNameRequired
        self._sql_post("/workbook/update", {"workbook_id": workbook_id, "name": name})

    def update_workbook_raw(self, body: dict[str, Any]) -> None:
        self._sql_post("/workbook/update", body)

    def update_workbook_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/update", workspace_id=self._workspace_id, body=body)

    def delete_workbook(self, workbook_id: str) -> None:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        self._sql_post("/workbook/delete", {"workbook_id": workbook_id})

    def delete_workbook_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/delete", workspace_id=self._workspace_id, body=body)

    def workbook_detail(self, workbook_id: str, version_id: str) -> SQLWorkbookDetailResult:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        if not version_id:
            raise ErrVersionIDRequired
        return _sql_workbook_detail_result(self._sql_post("/workbook/detail", {"workbook_id": workbook_id, "version_id": version_id}))

    def workbook_detail_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/detail", workspace_id=self._workspace_id, body=body)

    def workbook_versions(self, workbook_id: str, *opts: Callable[["WorkbookVersionListOptions"], None]) -> SQLWorkbookVersionListResult:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        return _sql_workbook_version_list_result(self._sql_post("/workbook/version/list", _workbook_version_list_body(workbook_id, opts)))

    def workbook_versions_raw(self, body: dict[str, Any]) -> SQLWorkbookVersionListResult:
        return _sql_workbook_version_list_result(self._sql_post("/workbook/version/list", body))

    def create_workbook_version(self, workbook_id: str, sql_content: str) -> SQLWorkbookVersionCreateResult:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        return _sql_workbook_version_create_result(self._sql_post("/workbook/version/create", {"workbook_id": workbook_id, "sql_content": sql_content}))

    def create_workbook_version_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/version/create", workspace_id=self._workspace_id, body=body)

    def update_workbook_version(self, workbook_id: str, version_id: str, sql_content: str) -> None:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        if not version_id:
            raise ErrVersionIDRequired
        self._sql_post(
            "/workbook/version/update",
            {"workbook_id": workbook_id, "version_id": version_id, "sql_content": sql_content},
        )

    def update_workbook_version_raw(self, body: dict[str, Any]) -> None:
        self._sql_post("/workbook/version/update", body)

    def update_workbook_version_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/version/update", workspace_id=self._workspace_id, body=body)

    def save_workbook_version(self, workbook_id: str, version_id: str, sql_content: Optional[str] = None) -> None:
        if not workbook_id:
            raise ErrWorkbookIDRequired
        if not version_id:
            raise ErrVersionIDRequired
        body: dict[str, Any] = {"workbook_id": workbook_id, "version_id": version_id}
        if sql_content is not None:
            body["sql_content"] = sql_content
        self._sql_post("/workbook/version/save", body)

    def save_workbook_version_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/workbook/version/save", workspace_id=self._workspace_id, body=body)

    def meta_databases(self, *opts: Callable[["SQLDatabaseListOptions"], None]) -> SQLDatabaseListResult:
        """List database names; no options preserves the complete name list."""
        options = SQLDatabaseListOptions()
        for opt in opts:
            opt(options)
        body: dict[str, Any] = {}
        if options.page_size is not None:
            body["page_size"] = options.page_size
        if options.page_token is not None:
            body["page_token"] = options.page_token
        if options.search is not None:
            body["search"] = options.search
        if options.name is not None:
            body["name"] = options.name
        return _sql_database_list_result(self._sql_post("/meta/db/info", body))

    def meta_databases_result(self, body: Optional[dict[str, Any]] = None) -> ProductResult:
        return self._client._product_result("POST", "/meta/db/info", workspace_id=self._workspace_id, body=body)

    def meta_db_tree(self) -> SQLDatabaseTreeResult:
        return _sql_database_tree_result(self._sql_post("/meta/db/tree"))

    def meta_db_tree_result(self, body: Optional[dict[str, Any]] = None) -> ProductResult:
        return self._client._product_result("POST", "/meta/db/tree", workspace_id=self._workspace_id, body=body)

    def meta_db_tables(self, db_name: str) -> SQLDatabaseTablesResult:
        if not db_name:
            raise ErrDatabaseRequired
        return _sql_database_tables_result(self._sql_post("/meta/db/table", {"name": db_name}))

    def meta_db_tables_raw(self, body: dict[str, Any]) -> SQLDatabaseTablesResult:
        return _sql_database_tables_result(self._sql_post("/meta/db/table", body))

    def meta_db_tables_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/meta/db/table", workspace_id=self._workspace_id, body=body)

    def meta_table_info(self, db_name: str, table_name: str) -> SQLTableInfoResult:
        if not db_name:
            raise ErrDatabaseRequired
        if not table_name:
            raise ErrTableRequired
        return _sql_table_info_result(self._sql_post("/meta/table/info", {"db_name": db_name, "table_name": table_name}))

    def meta_table_info_raw(self, body: dict[str, Any]) -> SQLTableInfoResult:
        return _sql_table_info_result(self._sql_post("/meta/table/info", body))

    def meta_table_columns(self, db_name: str, table_name: str) -> SQLTableColumnsResult:
        if not db_name:
            raise ErrDatabaseRequired
        if not table_name:
            raise ErrTableRequired
        return _sql_table_columns_result(self._sql_post("/meta/table/column", {"db_name": db_name, "table_name": table_name}))

    def meta_table_columns_raw(self, body: dict[str, Any]) -> SQLTableColumnsResult:
        return _sql_table_columns_result(self._sql_post("/meta/table/column", body))

    def meta_table_column_stats(self, db_name: str, table_name: str) -> SQLTableColumnsResult:
        if not db_name:
            raise ErrDatabaseRequired
        if not table_name:
            raise ErrTableRequired
        return _sql_table_columns_result(self._sql_post("/meta/table/column_stat", {"db_name": db_name, "table_name": table_name}))

    def meta_table_column_stats_raw(self, body: dict[str, Any]) -> SQLTableColumnsResult:
        return _sql_table_columns_result(self._sql_post("/meta/table/column_stat", body))

    def meta_table_ddl(self, db_name: str, table_name: str) -> SQLTableDDLResult:
        if not db_name:
            raise ErrDatabaseRequired
        if not table_name:
            raise ErrTableRequired
        return _sql_table_ddl_result(self._sql_post("/meta/table/ddl", {"db_name": db_name, "table_name": table_name}))

    def meta_table_ddl_raw(self, body: dict[str, Any]) -> SQLTableDDLResult:
        return _sql_table_ddl_result(self._sql_post("/meta/table/ddl", body))

    def drop_meta_database(self, db_name: str) -> None:
        if not db_name:
            raise ErrDatabaseRequired
        self._sql_post("/meta/db/drop", {"db_name": db_name})

    def drop_meta_database_raw(self, body: dict[str, Any]) -> None:
        self._sql_post("/meta/db/drop", body)

    def drop_meta_table(self, db_name: str, table_name: str) -> None:
        if not db_name:
            raise ErrDatabaseRequired
        if not table_name:
            raise ErrTableRequired
        self._sql_post("/meta/table/drop", {"db_name": db_name, "table_name": table_name})

    def drop_meta_table_raw(self, body: dict[str, Any]) -> None:
        self._sql_post("/meta/table/drop", body)

    def drop_meta_view(self, db_name: str, table_name: str) -> None:
        if not db_name:
            raise ErrDatabaseRequired
        if not table_name:
            raise ErrTableRequired
        self._sql_post("/meta/view/drop", {"db_name": db_name, "table_name": table_name})

    def drop_meta_view_raw(self, body: dict[str, Any]) -> None:
        self._sql_post("/meta/view/drop", body)

    def execute_query(self, query: str, *opts: Callable[["SQLQueryOptions"], None]) -> SQLQueryStartResult:
        if not query:
            raise ErrQueryRequired
        return _sql_query_start_result(self._sql_post("/query/execute", _sql_query_body(query, opts)))

    def execute_query_raw(self, body: dict[str, Any]) -> SQLQueryStartResult:
        return _sql_query_start_result(self._sql_post("/query/execute", body))

    def execute_query_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/query/execute", workspace_id=self._workspace_id, body=body)

    def run_query(self, query: str, *opts: Callable[["SQLQueryOptions"], None]) -> SQLQueryResult:
        """Execute once and return the bounded result without polling or replay."""
        if not query:
            raise ErrQueryRequired
        return _sql_query_result(self._sql_post("/query/run", _sql_query_body(query, opts)))

    def describe_query(self, query_id: str) -> SQLQueryOperation:
        if not query_id:
            raise ErrQueryIDRequired
        return _sql_query_operation(self._sql_post("/query/describe", {"query_id": query_id}))

    def describe_query_raw(self, body: dict[str, Any]) -> SQLQueryOperation:
        return _sql_query_operation(self._sql_post("/query/describe", body))

    def describe_query_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/query/describe", workspace_id=self._workspace_id, body=body)

    def kill_query(self, query_id: str) -> None:
        if not query_id:
            raise ErrQueryIDRequired
        self._sql_post("/query/kill", {"query_id": query_id})

    def kill_query_raw(self, body: dict[str, Any]) -> None:
        self._sql_post("/query/kill", body)

    def kill_query_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/query/kill", workspace_id=self._workspace_id, body=body)

    def query_result(self, statement_id: str, *opts: Callable[["SQLResultOptions"], None]) -> SQLQueryResult:
        if not statement_id:
            raise ErrStatementIDRequired
        return _sql_query_result(self._sql_post("/query/result", _sql_result_body(statement_id, opts)))

    def query_result_raw(self, body: dict[str, Any]) -> SQLQueryResult:
        return _sql_query_result(self._sql_post("/query/result", body))

    def query_result_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result("POST", "/query/result", workspace_id=self._workspace_id, body=body)

    def query_history_overview(self, *opts: Callable[["QueryHistoryOverviewOptions"], None]) -> SQLQueryHistoryOverviewResult:
        return _sql_query_history_overview_result(self._sql_post("/query/history/overview", _query_history_overview_body(opts)))

    def query_history(self, *opts: Callable[["QueryHistoryOptions"], None]) -> SQLQueryHistoryResult:
        return _sql_query_history_result(self._sql_post("/query/history", _query_history_body(opts)))

    def query_history_result(self, body: Optional[dict[str, Any]] = None) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/query/history",
            workspace_id=self._workspace_id,
            body=body or {},
        )

    def query_detail(self, statement_id: str, *opts: Callable[["QueryRecordOptions"], None]) -> Optional[SQLStatementRecord]:
        if not statement_id:
            raise ErrStatementIDRequired
        return self._query_detail_result(_query_record_body(statement_id, opts))

    def query_detail_raw(self, body: dict[str, Any]) -> Optional[SQLStatementRecord]:
        return self._query_detail_result(body)

    def _query_detail_result(self, body: dict[str, Any]) -> Optional[SQLStatementRecord]:
        result = self._client._product_result("POST", "/query/detail", workspace_id=self._workspace_id, body=body)
        raw = json.dumps(result.body).encode("utf-8")
        request_id = _request_id(result.headers)
        if result.status >= 400:
            raise _parse_error(result.status, raw, request_id)
        value = _parse_response(raw, request_id, require_envelope=True, data_nullable=True)
        return None if value is None else _sql_statement_record(value)

    def query_detail_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/query/detail",
            workspace_id=self._workspace_id,
            body=body,
        )

    def query_profile(self, statement_id: str, *opts: Callable[["QueryRecordOptions"], None]) -> SQLQueryProfileResult:
        if not statement_id:
            raise ErrStatementIDRequired
        return _sql_query_profile_result(self._sql_post("/query/profile", _query_record_body(statement_id, opts)))

    def query_profile_raw(self, body: dict[str, Any]) -> SQLQueryProfileResult:
        return _sql_query_profile_result(self._sql_post("/query/profile", body))

    def query_profile_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/query/profile",
            workspace_id=self._workspace_id,
            body=body,
        )

    def connect_query_web_socket(self) -> "SQLQueryWebSocket":
        """Open the SQL editor WebSocket; the caller closes the connection."""
        import websocket
        url = self.query_websocket_url() + "?" + urllib.parse.urlencode({"workspace_id":self._workspace_id})
        return SQLQueryWebSocket(websocket.create_connection(url,timeout=self._client._config.timeout,header=self.query_websocket_headers(),subprotocols=self.query_websocket_subprotocols()))

    def query_websocket_url(self) -> str:
        parsed = urllib.parse.urlparse(self._client._base)
        if parsed.scheme == "https":
            scheme = "wss"
        elif parsed.scheme == "http":
            scheme = "ws"
        else:
            raise Error("ErrEndpointSchemeUnsupported", "product endpoint must use http or https")
        path = parsed.path.rstrip("/") + "/query/ws"
        return urllib.parse.urlunparse((scheme, parsed.netloc, path, "", "", ""))

    def query_websocket_headers(self) -> list[str]:
        return _websocket_headers(self._client, self._workspace_id)

    def query_websocket_subprotocols(self) -> list[str]:
        return _websocket_subprotocols(self._client)

    def _sql_post(self, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        return self._request("POST", path, body)

def _dashboard_socket_call(operation: Callable[[], Any]) -> Any:
    import websocket
    try:
        return operation()
    except websocket.WebSocketBadStatusException as exc:
        raw = exc.resp_body.encode() if isinstance(exc.resp_body, str) else exc.resp_body
        raise _parse_error(exc.status_code, raw or b"", _request_id(exc.resp_headers)) from exc
    except (TimeoutError, websocket.WebSocketTimeoutException) as exc:
        raise Error("ErrTimeout", "request timeout") from exc
    except (OSError, websocket.WebSocketException) as exc:
        raise Error("ErrTransportUnavailable", "no response was received from the service") from exc


class DashboardWebSocket:
    """看板协议客户端；错误保留服务端分类和原始关联消息。"""

    def __init__(self, connection: Any):
        self._connection = connection
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()

    def close(self) -> None:
        self._connection.close()

    def ping(self, message_id: str) -> None:
        self._send(message_id, "ping", None)

    def preclose(self, message_id: str) -> None:
        self._send(message_id, "preclose", None)

    def preview_sql(self, message_id: str, dashboard_id: str, chart_id: str, sql_text: str) -> None:
        self._send(message_id, "dashboard_preview_execute", {"dashboard_id": dashboard_id, "chart_id": chart_id, "sql_text": sql_text})

    def create_chart(self, message_id: str, dashboard_id: str, request: DataDashboardChartMutationRequest) -> None:
        if not isinstance(request, DataDashboardChartMutationRequest):
            raise TypeError("request must be DataDashboardChartMutationRequest")
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        body["dashboard_id"] = dashboard_id
        self._send(message_id, "dashboard_chart_create", body)

    def update_chart(self, message_id: str, dashboard_id: str, chart_id: str, request: DataDashboardChartMutationRequest) -> None:
        if not isinstance(request, DataDashboardChartMutationRequest):
            raise TypeError("request must be DataDashboardChartMutationRequest")
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        body.update(dashboard_id=dashboard_id, chart_id=chart_id)
        self._send(message_id, "dashboard_chart_update", body)

    def _send(self, message_id: str, message_type: str, body: Optional[dict[str, Any]]) -> None:
        if not message_id:
            raise ErrIDRequired
        payload = {"id": message_id, "message_type": message_type}
        if body is not None:
            payload["data"] = body
        with self._write_lock:
            _dashboard_socket_call(lambda: self._connection.send(json.dumps(payload)))

    def receive(self, timeout: Optional[float] = None) -> DataDashboardWebSocketMessage:
        with self._read_lock:
            previous = self._connection.gettimeout()
            if timeout is not None:
                self._connection.settimeout(timeout)
            try:
                raw = _dashboard_socket_call(self._connection.recv)
                if not isinstance(raw, str):
                    raise Error("ErrResponseInvalid", "dashboard response must be text")
                frame = json_format.Parse(raw, DataDashboardWebSocketMessage())
            except (json_format.ParseError, ValueError, TypeError) as exc:
                raise Error("ErrResponseInvalid", "dashboard response is invalid") from exc
            finally:
                if timeout is not None:
                    self._connection.settimeout(previous)
        if frame.message_type == DataDashboardWebSocketMessage.error:
            try:
                failure = json_format.ParseDict(dict(frame.data), DataDashboardWebSocketError())
            except (json_format.ParseError, ValueError, TypeError) as exc:
                raise Error("ErrResponseInvalid", "dashboard error response is invalid") from exc
            if not 400 <= failure.status <= 599 or not failure.code or not failure.msg:
                raise Error("ErrResponseInvalid", "dashboard error response is invalid")
            raise Error(failure.code, failure.msg, status=failure.status, data=json.loads(raw))
        if frame.message_type not in (DataDashboardWebSocketMessage.pong, DataDashboardWebSocketMessage.dashboard_preview_result, DataDashboardWebSocketMessage.dashboard_chart_create_result, DataDashboardWebSocketMessage.dashboard_chart_update_result):
            raise Error("ErrResponseInvalid", "dashboard response has an unknown message type")
        return frame


class SQLQueryWebSocket:
    """SQL editor session; the SDK owns commands and protocol decoding."""

    def __init__(self, connection: Any):
        self._connection = connection

    def close(self) -> None:
        self._connection.close()

    def protocols(self) -> list[str]:
        protocol = self._connection.getsubprotocol()
        return [protocol] if protocol else []

    def execute_query(self, message_id: str, query: str, *opts: Callable[["SQLQueryOptions"], None]) -> None:
        if not query:
            raise ErrQueryRequired
        self._send(message_id, SQLQueryWebSocketMessage.query_execute, _sql_query_body(query, opts))

    def kill_query(self, message_id: str, query_id: str) -> None:
        if not query_id:
            raise ErrQueryIDRequired
        self._send(message_id, SQLQueryWebSocketMessage.query_kill, {"query_id": query_id})

    def ping(self, message_id: str) -> None:
        self._send(message_id, SQLQueryWebSocketMessage.ping, None)

    def receive(self, timeout: Optional[float] = None) -> SQLQueryWebSocketMessage:
        previous_timeout = self._connection.gettimeout()
        if timeout is not None:
            self._connection.settimeout(timeout)
        try:
            return json_format.Parse(self._connection.recv(), SQLQueryWebSocketMessage())
        finally:
            if timeout is not None:
                self._connection.settimeout(previous_timeout)

    def _send(self, message_id: str, message_type: int, body: Optional[dict[str, Any]]) -> None:
        message = SQLQueryWebSocketMessage(id=message_id, message_type=message_type)
        payload = json_format.MessageToDict(message, preserving_proto_field_name=True)
        if body is not None:
            # Struct converts integers to floats (limit=1 becomes 1.0), while
            # the SQL request contract requires integer offsets and limits.
            payload["data"] = body
        self._connection.send(json.dumps(payload))


class ComputeService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed compute resource handles for user-facing workflows."""

    def list(self, *opts: Callable[["ListOptions"], None]) -> list[ComputeResource]:
        return _compute_resource_list(self._request("GET", _with_list_query("/compute-resources", opts)))

    def specs(self) -> list[ComputeResourceSpec]:
        return _compute_resource_spec_list(self._request("GET", "/compute-resource-specs"))

    def specs_result(self) -> ProductResult:
        return self._client._product_result("GET", "/compute-resource-specs", workspace_id=self._workspace_id)

    def spec_management_permission(self) -> ComputeResourceSpecManagementPermission:
        return _compute_resource_spec_management_permission(
            self._request("GET", "/compute-resource-specs/management-permission")
        )

    def spec_management_permission_result(self) -> ProductResult:
        return self._client._product_result(
            "GET",
            "/compute-resource-specs/management-permission",
            workspace_id=self._workspace_id,
        )

    def create_spec(
        self,
        spec_id: str,
        kind: str,
        family: str,
        family_name: str,
        family_name_en: str,
        cpu_milli: int,
        memory_mib: int,
        *opts: Callable[["ComputeSpecOptions"], None],
    ) -> ComputeResourceSpec:
        return _compute_resource_spec(
            self._request(
                "POST",
                "/compute-resource-specs",
                _compute_spec_body(spec_id, kind, family, family_name, family_name_en, cpu_milli, memory_mib, opts),
            )
        )

    def create_spec_raw(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/compute-resource-specs", body)

    def create_spec_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/compute-resource-specs",
            workspace_id=self._workspace_id,
            body=body,
        )

    def update_spec(self, spec_id: str, *opts: Callable[["ComputeSpecUpdateOptions"], None]) -> ComputeResourceSpec:
        return _compute_resource_spec(
            self._request("PUT", f"/compute-resource-specs/{_path_id(spec_id)}", _compute_spec_update_body(opts))
        )

    def update_spec_raw(self, spec_id: str, body: dict[str, Any]) -> Any:
        return self._request("PUT", f"/compute-resource-specs/{_path_id(spec_id)}", body)

    def update_spec_result(self, spec_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "PUT",
            f"/compute-resource-specs/{_path_id(spec_id)}",
            workspace_id=self._workspace_id,
            body=body,
        )

    def set_spec_enabled(self, spec_id: str, enabled: bool) -> ComputeResourceSpec:
        return _compute_resource_spec(
            self._request("PATCH", f"/compute-resource-specs/{_path_id(spec_id)}/enabled", {"enabled": enabled})
        )

    def set_spec_enabled_result(self, spec_id: str, enabled: bool) -> ProductResult:
        return self._client._product_result(
            "PATCH",
            f"/compute-resource-specs/{_path_id(spec_id)}/enabled",
            workspace_id=self._workspace_id,
            body={"enabled": enabled},
        )

    def create(
        self,
        name: str,
        spec_id: str,
        cpu: int,
        memory_gib: int,
        *opts: Callable[["ComputeCreateOptions"], None],
    ) -> ComputeResource:
        if not name:
            raise ErrNameRequired
        if not spec_id:
            raise ErrSpecIDRequired
        if cpu == 0:
            raise ErrCPURequired
        if memory_gib == 0:
            raise ErrMemoryRequired
        return _compute_resource(self._request("POST", "/compute-resources", _compute_create_body(name, spec_id, cpu, memory_gib, opts)))

    def create_result(
        self,
        name: str,
        kind: str,
        spec_id: str,
        cpu: int,
        memory_gib: int,
        *opts: Callable[["ComputeCreateOptions"], None],
    ) -> ProductResult:
        """Creates a compute resource from the current Backend request contract."""
        if not name:
            raise ErrNameRequired
        if not kind:
            raise ErrKindRequired
        if not spec_id:
            raise ErrSpecIDRequired
        if cpu == 0:
            raise ErrCPURequired
        if memory_gib == 0:
            raise ErrMemoryRequired
        body = _compute_create_body(name, spec_id, cpu, memory_gib, opts)
        body["kind"] = kind
        return self._client._product_result(
            "POST",
            "/compute-resources",
            workspace_id=self._workspace_id,
            body=body,
        )

    def worker_images(self, *opts: Callable[["QueryOptions"], None]) -> list[WorkerImage]:
        return _worker_image_list(self._request("GET", _with_query("/compute-resources/worker-images", opts)))

    def runtime(self, compute_resource_id: str) -> list[ComputeWorkerRuntime]:
        return _compute_worker_runtime_list(self._request("GET", f"/compute-resources/{_path_id(compute_resource_id)}/runtime", require_envelope=True))

    def workers(self, compute_resource_id: str) -> list[ComputeResourceWorker]:
        return _compute_resource_worker_list(self._request(
            "GET", f"/compute-resources/{_path_id(compute_resource_id)}/workers",
            require_envelope=True, data_nullable=False,
        ))

    def py_deps_limits(self) -> ComputePyDepsLimits:
        return _compute_py_deps_limits(self._request("GET", "/compute-resources/py-deps-limits"))

    def admin_runtime(self, compute_resource_id: str) -> list[ComputeWorkerRuntime]:
        if not compute_resource_id.strip():
            raise ErrIDRequired
        return _compute_worker_runtime_list(self._request("GET", f"/admin/compute-resources/{_path_id(compute_resource_id)}/runtime", require_envelope=True))

    def get(self, resource_id: str) -> ComputeResource:
        return _compute_resource(self._request("GET", f"/compute-resources/{_path_id(resource_id)}"))

    def update(self, resource_id: str, *opts: Callable[["ComputeUpdateOptions"], None]) -> ComputeResource:
        return _compute_resource(self._request("PUT", f"/compute-resources/{_path_id(resource_id)}", _compute_update_body(opts)))

    def adopt_legacy_ownership(self, resource_id: str) -> ComputeResourceOwnership:
        return _compute_resource_ownership(
            self._request("POST", f"/compute-resources/{_path_id(resource_id)}/adopt-legacy-ownership", {})
        )

    def preflight_delete(self, resource_id: str) -> ComputeDeletePreflightResult:
        return _compute_delete_preflight_result(self._request("GET", f"/compute-resources/{_path_id(resource_id)}/preflight-delete"))

    def delete(self, resource_id: str, *opts: Callable[["QueryOptions"], None]) -> None:
        self._request("DELETE", _with_query(f"/compute-resources/{_path_id(resource_id)}", opts))

    def suspend(self, resource_id: str) -> ComputeResource:
        return self._compute_action(resource_id, "suspend")

    def resume(self, resource_id: str) -> ComputeResource:
        return self._compute_action(resource_id, "resume")

    def retry(self, resource_id: str) -> ComputeResource:
        return self._compute_action(resource_id, "retry")

    def _compute_action(self, resource_id: str, action: str) -> ComputeResource:
        return _compute_resource(self._request("POST", f"/compute-resources/{_path_id(resource_id)}/{action}", {}))

    def admin_list(self, *opts: Callable[["ListOptions"], None]) -> AdminComputeResourceListResult:
        return _admin_compute_resource_list_result(self._request("GET", _with_list_query("/admin/compute-resources", opts)))

    def admin_preflight_delete(self, resource_id: str) -> ComputeDeletePreflightResult:
        return _compute_delete_preflight_result(
            self._request("GET", f"/admin/compute-resources/{_path_id(resource_id)}/preflight-delete")
        )

    def admin_update(self, resource_id: str, *opts: Callable[["ComputeUpdateOptions"], None]) -> ComputeResource:
        return _compute_resource(
            self._request("PUT", f"/admin/compute-resources/{_path_id(resource_id)}", _compute_update_body(opts))
        )

    def admin_delete(self, resource_id: str, *opts: Callable[["QueryOptions"], None]) -> None:
        self._request("DELETE", _with_query(f"/admin/compute-resources/{_path_id(resource_id)}", opts))

    def admin_suspend(self, resource_id: str) -> ComputeResource:
        return self._admin_compute_action(resource_id, "suspend")

    def admin_resume(self, resource_id: str) -> ComputeResource:
        return self._admin_compute_action(resource_id, "resume")

    def admin_retry(self, resource_id: str) -> ComputeResource:
        return self._admin_compute_action(resource_id, "retry")

    def _admin_compute_action(self, resource_id: str, action: str) -> ComputeResource:
        return _compute_resource(self._request("POST", f"/admin/compute-resources/{_path_id(resource_id)}/{action}", {}))

class DataShareService(WorkspaceScopedService):
    """Route-aligned escape hatch; prefer typed publish and subscription handles for user-facing workflows."""

    def workspace(self) -> WorkspaceHandle:
        return self._client.workspace(self._workspace_id)

    def publishes(self, *opts: Callable[["QueryOptions"], None]) -> DataSharePublishListResult:
        return _data_share_publish_list_result(self._request("GET", _with_query("/data-share/publishes", opts)))

    def publishes_result(self, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "GET",
            _with_query("/data-share/publishes", opts),
            workspace_id=self._workspace_id,
        )

    def workspace_names(self, ids: list[str]) -> DataShareWorkspaceNameListResult:
        return _data_share_workspace_name_list_result(self._request("POST", "/data-share/workspace-names", {"ids": ids}))

    def workspace_names_result(self, ids: list[str]) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/data-share/workspace-names",
            workspace_id=self._workspace_id,
            body={"ids": ids},
        )

    def resolve_workspace_names(self, ids: list[str]) -> DataShareWorkspaceNameListResult:
        return _data_share_workspace_name_list_result(self._request("POST", "/data-share/workspaces/resolve-names", {"ids": ids}))

    def resolve_workspace_names_result(self, ids: list[str]) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/data-share/workspaces/resolve-names",
            workspace_id=self._workspace_id,
            body={"ids": ids},
        )

    def publish_summary(self) -> PublishSummaryResult:
        return _publish_summary_result(self._request("GET", "/data-share/publishes/summary"))

    def source_tables(
        self,
        source_database_id: str,
        *opts: Callable[["QueryOptions"], None],
    ) -> DataShareSourceTableListResult:
        if not source_database_id:
            raise ErrSourceDatabaseIDRequired
        database_id = _path_id(source_database_id)
        return _data_share_source_table_list_result(
            self._request("GET", _with_query(f"/data-share/source-databases/{database_id}/tables", opts))
        )

    def check_publish_name(self, *opts: Callable[["QueryOptions"], None]) -> CheckNameResult:
        return _check_name_result(self._request("GET", _with_query("/data-share/publishes/check-name", opts)))

    def check_publish_name_result(self, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "GET",
            _with_query("/data-share/publishes/check-name", opts),
            workspace_id=self._workspace_id,
        )

    def create_publish(
        self,
        name: str,
        source_database_id: str,
        table_scope: DataShareScope,
        target_workspace_ids: list[str],
        *opts: Callable[["DataSharePublishOptions"], None],
    ) -> DataSharePublish:
        if not name:
            raise ErrNameRequired
        if not source_database_id:
            raise ErrSourceDatabaseIDRequired
        _validate_data_share_scope(table_scope)
        if not target_workspace_ids:
            raise ErrTargetWorkspaceRequired
        return _data_share_publish(
            self._request(
                "POST",
                "/data-share/publishes",
                _data_share_publish_body(name, source_database_id, table_scope, target_workspace_ids, opts),
            )
        )

    def create_publish_raw(self, body: dict[str, Any]) -> DataSharePublish:
        return _data_share_publish(self._request("POST", "/data-share/publishes", body))

    def create_publish_result(self, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "POST",
            "/data-share/publishes",
            workspace_id=self._workspace_id,
            body=body,
        )

    def update_publish(self, publish_id: str, *opts: Callable[["DataSharePublishUpdateOptions"], None]) -> DataSharePublish:
        return _data_share_publish(self._request("PUT", f"/data-share/publishes/{_path_id(publish_id)}", _data_share_publish_update_body(opts)))

    def update_publish_raw(self, publish_id: str, body: dict[str, Any]) -> DataSharePublish:
        return _data_share_publish(self._request("PUT", f"/data-share/publishes/{_path_id(publish_id)}", body))

    def update_publish_result(self, publish_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "PUT",
            f"/data-share/publishes/{_path_id(publish_id)}",
            workspace_id=self._workspace_id,
            body=body,
        )

    def delete_publish(self, publish_id: str) -> None:
        self._request("DELETE", f"/data-share/publishes/{_path_id(publish_id)}")

    def delete_publish_result(self, publish_id: str) -> ProductResult:
        return self._client._product_result(
            "DELETE",
            f"/data-share/publishes/{_path_id(publish_id)}",
            workspace_id=self._workspace_id,
        )

    def subscriptions(self, *opts: Callable[["QueryOptions"], None]) -> DataShareSubscriptionListResult:
        return _data_share_subscription_list_result(self._request("GET", _with_query("/data-share/subscriptions", opts)))

    def subscriptions_result(self, *opts: Callable[["QueryOptions"], None]) -> ProductResult:
        return self._client._product_result(
            "GET",
            _with_query("/data-share/subscriptions", opts),
            workspace_id=self._workspace_id,
        )

    def subscribe(self, subscription_id: str, sub_name: str) -> DataShareSubscription:
        if not sub_name:
            raise ErrNameRequired
        return self._subscription_action(subscription_id, "subscribe", {"sub_name": sub_name})

    def subscribe_raw(self, subscription_id: str, body: dict[str, Any]) -> DataShareSubscription:
        return self._subscription_action(subscription_id, "subscribe", body)

    def subscribe_result(self, subscription_id: str, body: dict[str, Any]) -> ProductResult:
        return self._client._product_result(
            "POST",
            f"/data-share/subscriptions/{_path_id(subscription_id)}/subscribe",
            workspace_id=self._workspace_id,
            body=body,
        )

    def unsubscribe(self, subscription_id: str) -> None:
        self._request("POST", f"/data-share/subscriptions/{_path_id(subscription_id)}/unsubscribe")

    def unsubscribe_result(self, subscription_id: str) -> ProductResult:
        return self._client._product_result(
            "POST",
            f"/data-share/subscriptions/{_path_id(subscription_id)}/unsubscribe",
            workspace_id=self._workspace_id,
            body={},
        )

    def _subscription_action(self, subscription_id: str, action: str, body: Optional[dict[str, Any]]) -> DataShareSubscription:
        return _data_share_subscription(self._request("POST", f"/data-share/subscriptions/{_path_id(subscription_id)}/{action}", body))

class ListOptions:
    def __init__(self) -> None:
        self.query: dict[str, list[str]] = {}

QueryOptions = ListOptions

def _set_query(options: ListOptions, key: str, value: str) -> None:
    options.query[key] = [value]

def _add_query(options: ListOptions, key: str, value: str) -> None:
    if key not in options.query:
        options.query[key] = []
    options.query[key].append(value)

def with_limit(limit: int) -> Callable[[ListOptions], None]:
    def apply(options: ListOptions) -> None:
        _set_query(options, "limit", str(limit))

    return apply

def with_offset(offset: int) -> Callable[[ListOptions], None]:
    def apply(options: ListOptions) -> None:
        _set_query(options, "offset", str(offset))

    return apply

def with_query_param(key: str, value: str) -> Callable[[QueryOptions], None]:
    def apply(options: QueryOptions) -> None:
        _set_query(options, key, value)

    return apply

def with_query_values(key: str, *values: str) -> Callable[[QueryOptions], None]:
    def apply(options: QueryOptions) -> None:
        for value in values:
            _add_query(options, key, value)

    return apply

def with_delete_data(delete_data: bool) -> Callable[[QueryOptions], None]:
    return with_query_param("delete_data", "true" if delete_data else "false")

def with_page(page: int) -> Callable[[QueryOptions], None]:
    return with_query_param("page", str(page))

def with_page_size(page_size: int) -> Callable[[QueryOptions], None]:
    return with_query_param("page_size", str(page_size))

def with_page_token(page_token: str) -> Callable[[QueryOptions], None]:
    return with_query_param("page_token", page_token)

def with_search(search: str) -> Callable[[QueryOptions], None]:
    return with_query_param("search", search)

def with_workspace_name_filter(name: str) -> Callable[[ListOptions], None]:
    return with_query_param("name", name)

def with_status(status: str) -> Callable[[QueryOptions], None]:
    return with_query_param("status", status)

def with_kind(kind: str) -> Callable[[QueryOptions], None]:
    return with_query_param("kind", kind)

def with_semantic_domain(domain: str) -> Callable[[QueryOptions], None]:
    return with_query_param("domain", domain)

def with_type(type_: str) -> Callable[[QueryOptions], None]:
    return with_query_param("type", type_)

def with_file_id(file_id: str) -> Callable[[QueryOptions], None]:
    return with_query_param("file_id", file_id)

def with_force(force: bool) -> Callable[[QueryOptions], None]:
    return with_query_param("force", "true" if force else "false")

def with_source_node_execution_id(source_node_execution_id: str) -> Callable[[QueryOptions], None]:
    return with_query_param("source_node_execution_id", source_node_execution_id)

class CreateWorkspaceOptions:
    pass

class CatalogListOptions:
    def __init__(self) -> None:
        self.include_stats: Optional[bool] = None
        self.page_size: Optional[int] = None
        self.page_token: Optional[str] = None

def with_catalog_include_stats(include: bool) -> Callable[[CatalogListOptions], None]:
    def apply(options: CatalogListOptions) -> None:
        options.include_stats = include

    return apply


def with_catalog_page_size(size: int) -> Callable[[CatalogListOptions], None]:
    def apply(options: CatalogListOptions) -> None:
        options.page_size = size
    return apply


def with_catalog_page_token(token: str) -> Callable[[CatalogListOptions], None]:
    def apply(options: CatalogListOptions) -> None:
        options.page_token = token
    return apply


class CatalogInfoOptions:
    def __init__(self) -> None:
        self.description: Optional[str] = None

def with_catalog_description(description: str) -> Callable[[CatalogInfoOptions], None]:
    def apply(options: CatalogInfoOptions) -> None:
        options.description = description

    return apply


class CreateTableOptions:
    def __init__(self) -> None:
        self.comment: Optional[str] = None
        self.data_file_url: Optional[str] = None
        self.column_load_options: list[dict[str, Any]] = []

def with_table_comment(comment: str) -> Callable[[CreateTableOptions], None]:
    def apply(options: CreateTableOptions) -> None:
        options.comment = comment

    return apply

def with_table_data_file_url(data_file_url: str) -> Callable[[CreateTableOptions], None]:
    def apply(options: CreateTableOptions) -> None:
        options.data_file_url = data_file_url

    return apply

def with_column_load_option(column: str, data_from: str) -> Callable[[CreateTableOptions], None]:
    def apply(options: CreateTableOptions) -> None:
        options.column_load_options.append({"column": column, "data_from": data_from})

    return apply

class TableLookupOptions:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.database_id: Optional[int] = None
        self.database_name: Optional[str] = None
        self.include_stats: Optional[bool] = None

def with_table_lookup_name(name: str) -> Callable[[TableLookupOptions], None]:
    def apply(options: TableLookupOptions) -> None:
        options.name = name

    return apply

def with_table_lookup_database_id(database_id: int) -> Callable[[TableLookupOptions], None]:
    def apply(options: TableLookupOptions) -> None:
        options.database_id = database_id

    return apply

def with_table_lookup_database_name(database_name: str) -> Callable[[TableLookupOptions], None]:
    """Look up a MatrixOne system table by system database name (mutually exclusive with database_id)."""

    def apply(options: TableLookupOptions) -> None:
        options.database_name = database_name

    return apply

def with_table_lookup_include_stats(include: bool) -> Callable[[TableLookupOptions], None]:
    def apply(options: TableLookupOptions) -> None:
        options.include_stats = include

    return apply

class TableDataOptions:
    def __init__(self) -> None:
        self.page: Optional[int] = None
        self.page_size: Optional[int] = None
        self.name: Optional[str] = None
        self.database_id: Optional[int] = None
        self.database_name: Optional[str] = None
        self.preview_lines: Optional[int] = None
        self.include_total: Optional[bool] = None

def with_table_data_page(page: int) -> Callable[[TableDataOptions], None]:
    def apply(options: TableDataOptions) -> None:
        options.page = page

    return apply

def with_table_data_page_size(page_size: int) -> Callable[[TableDataOptions], None]:
    def apply(options: TableDataOptions) -> None:
        options.page_size = page_size

    return apply

def with_table_data_name(name: str) -> Callable[[TableDataOptions], None]:
    def apply(options: TableDataOptions) -> None:
        options.name = name

    return apply

def with_table_data_database_id(database_id: int) -> Callable[[TableDataOptions], None]:
    def apply(options: TableDataOptions) -> None:
        options.database_id = database_id

    return apply

def with_table_data_database_name(database_name: str) -> Callable[[TableDataOptions], None]:
    """Read sample/preview data for a MatrixOne system table by database name."""

    def apply(options: TableDataOptions) -> None:
        options.database_name = database_name

    return apply

def with_table_preview_lines(preview_lines: int) -> Callable[[TableDataOptions], None]:
    def apply(options: TableDataOptions) -> None:
        options.preview_lines = preview_lines

    return apply

def with_table_data_include_total(include: bool) -> Callable[[TableDataOptions], None]:
    def apply(options: TableDataOptions) -> None:
        options.include_total = include

    return apply

class FileListOptions:
    def __init__(self) -> None:
        self.page: Optional[int] = None
        self.page_size: Optional[int] = None
        self.order: Optional[str] = None
        self.order_by: Optional[str] = None
        self.filters: list[dict[str, Any]] = []

def with_file_list_page(page: int) -> Callable[[FileListOptions], None]:
    def apply(options: FileListOptions) -> None:
        options.page = page

    return apply

def with_file_list_page_size(page_size: int) -> Callable[[FileListOptions], None]:
    def apply(options: FileListOptions) -> None:
        options.page_size = page_size

    return apply

def with_file_list_order(order: str) -> Callable[[FileListOptions], None]:
    def apply(options: FileListOptions) -> None:
        options.order = order

    return apply

def with_file_list_order_by(order_by: str) -> Callable[[FileListOptions], None]:
    def apply(options: FileListOptions) -> None:
        options.order_by = order_by

    return apply

def with_file_list_filter(name: str, *values: str) -> Callable[[FileListOptions], None]:
    def apply(options: FileListOptions) -> None:
        options.filters.append({"name": name, "values": list(values)})

    return apply

def with_fuzzy_file_list_filter(name: str, fuzzy: bool, *values: str) -> Callable[[FileListOptions], None]:
    def apply(options: FileListOptions) -> None:
        options.filters.append({"name": name, "values": list(values), "fuzzy": fuzzy})

    return apply

class DownloadFileOptions:
    def __init__(self) -> None:
        self.as_zip: Optional[bool] = None

def with_file_as_zip(as_zip: bool) -> Callable[[DownloadFileOptions], None]:
    def apply(options: DownloadFileOptions) -> None:
        options.as_zip = as_zip

    return apply

class CreateFolderOptions:
    def __init__(self) -> None:
        self.description: Optional[str] = None

def with_folder_description(description: str) -> Callable[[CreateFolderOptions], None]:
    def apply(options: CreateFolderOptions) -> None:
        options.description = description

    return apply

class UpdateFolderOptions:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.description: Optional[str] = None

def with_folder_name(name: str) -> Callable[[UpdateFolderOptions], None]:
    def apply(options: UpdateFolderOptions) -> None:
        options.name = name

    return apply

def with_updated_folder_description(description: str) -> Callable[[UpdateFolderOptions], None]:
    def apply(options: UpdateFolderOptions) -> None:
        options.description = description

    return apply

class ConnectorDefinitionOptions:
    def __init__(self) -> None:
        self.config: Optional[dict[str, Any]] = None

def with_connector_config(config: dict[str, Any]) -> Callable[[ConnectorDefinitionOptions], None]:
    def apply(options: ConnectorDefinitionOptions) -> None:
        options.config = config

    return apply

class ConnectorUpdateOptions:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.source_type: Optional[int] = None
        self.usage_type: Optional[int] = None
        self.config: Optional[dict[str, Any]] = None

def with_connector_name(name: str) -> Callable[[ConnectorUpdateOptions], None]:
    def apply(options: ConnectorUpdateOptions) -> None:
        options.name = name

    return apply

def with_connector_source_type(source_type: int) -> Callable[[ConnectorUpdateOptions], None]:
    def apply(options: ConnectorUpdateOptions) -> None:
        options.source_type = source_type

    return apply

def with_connector_usage_type(usage_type: int) -> Callable[[ConnectorUpdateOptions], None]:
    def apply(options: ConnectorUpdateOptions) -> None:
        options.usage_type = usage_type

    return apply

def with_connector_update_config(config: dict[str, Any]) -> Callable[[ConnectorUpdateOptions], None]:
    def apply(options: ConnectorUpdateOptions) -> None:
        options.config = config

    return apply

class ConnectorPreviewOptions:
    def __init__(self) -> None:
        self.conn_file_id: Optional[str] = None
        self.sheet_name: Optional[str] = None
        self.is_column_name: Optional[bool] = None
        self.row_start: Optional[int] = None
        self.column_name_row: Optional[int] = None
        self.csv: Optional[dict[str, Any]] = None
        self.file_type: Optional[int] = None

def with_connector_preview_conn_file_id(conn_file_id: str) -> Callable[[ConnectorPreviewOptions], None]:
    def apply(options: ConnectorPreviewOptions) -> None:
        options.conn_file_id = conn_file_id

    return apply

def with_connector_preview_sheet_name(sheet_name: str) -> Callable[[ConnectorPreviewOptions], None]:
    def apply(options: ConnectorPreviewOptions) -> None:
        options.sheet_name = sheet_name

    return apply

def with_connector_preview_column_name(is_column_name: bool) -> Callable[[ConnectorPreviewOptions], None]:
    def apply(options: ConnectorPreviewOptions) -> None:
        options.is_column_name = is_column_name

    return apply

def with_connector_preview_row_start(row_start: int) -> Callable[[ConnectorPreviewOptions], None]:
    def apply(options: ConnectorPreviewOptions) -> None:
        options.row_start = row_start

    return apply

def with_connector_preview_column_name_row(column_name_row: int) -> Callable[[ConnectorPreviewOptions], None]:
    def apply(options: ConnectorPreviewOptions) -> None:
        options.column_name_row = column_name_row

    return apply

def with_connector_preview_csv(separator: str, delimiter: str, is_escape: bool) -> Callable[[ConnectorPreviewOptions], None]:
    def apply(options: ConnectorPreviewOptions) -> None:
        options.csv = {"separator": separator, "delimiter": delimiter, "isEscape": is_escape}

    return apply

def with_connector_preview_file_type(file_type: int) -> Callable[[ConnectorPreviewOptions], None]:
    def apply(options: ConnectorPreviewOptions) -> None:
        options.file_type = file_type

    return apply

class ConnectorDBOptions:
    def __init__(self) -> None:
        self.schema: Optional[str] = None

def with_connector_schema(schema: str) -> Callable[[ConnectorDBOptions], None]:
    def apply(options: ConnectorDBOptions) -> None:
        options.schema = schema

    return apply

class CreateImportTaskOptions:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.volume_id: Optional[str] = None

def with_import_task_name(name: str) -> Callable[[CreateImportTaskOptions], None]:
    def apply(options: CreateImportTaskOptions) -> None:
        options.name = name

    return apply

def with_import_task_volume_id(volume_id: str) -> Callable[[CreateImportTaskOptions], None]:
    def apply(options: CreateImportTaskOptions) -> None:
        options.volume_id = volume_id

    return apply

class ExportTaskListOptions:
    def __init__(self) -> None:
        self.keyword: Optional[str] = None
        self.target_category: Optional[str] = None
        self.limit: Optional[int] = None
        self.offset: Optional[int] = None
        self.connector_name: Optional[str] = None
        self.task_id: Optional[str] = None
        self.order_by: Optional[str] = None
        self.order_direction: Optional[str] = None
        self.statuses: list[int] = []
        self.creator: Optional[str] = None


def with_export_task_keyword(keyword: str) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.keyword = keyword
    return apply


def with_export_task_target_category(category: str) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.target_category = category
    return apply


def with_export_task_limit(limit: int) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.limit = limit

    return apply

def with_export_task_offset(offset: int) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.offset = offset

    return apply

def with_export_task_connector_name(connector_name: str) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.connector_name = connector_name

    return apply

def with_export_task_id(task_id: str) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.task_id = task_id

    return apply

def with_export_task_order_by(order_by: str) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.order_by = order_by

    return apply

def with_export_task_order_direction(order_direction: str) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.order_direction = order_direction

    return apply

def with_export_task_statuses(*statuses: int) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.statuses.extend(statuses)

    return apply

def with_export_task_creator(creator: str) -> Callable[[ExportTaskListOptions], None]:
    def apply(options: ExportTaskListOptions) -> None:
        options.creator = creator

    return apply

class ExportTaskFilesOptions:
    def __init__(self) -> None:
        self.limit: Optional[int] = None
        self.offset: Optional[int] = None
        self.statuses: list[int] = []
        self.order_by: Optional[str] = None
        self.order_direction: Optional[str] = None

def with_export_task_files_limit(limit: int) -> Callable[[ExportTaskFilesOptions], None]:
    def apply(options: ExportTaskFilesOptions) -> None:
        options.limit = limit

    return apply

def with_export_task_files_offset(offset: int) -> Callable[[ExportTaskFilesOptions], None]:
    def apply(options: ExportTaskFilesOptions) -> None:
        options.offset = offset

    return apply

def with_export_task_file_statuses(*statuses: int) -> Callable[[ExportTaskFilesOptions], None]:
    def apply(options: ExportTaskFilesOptions) -> None:
        options.statuses.extend(statuses)

    return apply

def with_export_task_files_order_by(order_by: str) -> Callable[[ExportTaskFilesOptions], None]:
    def apply(options: ExportTaskFilesOptions) -> None:
        options.order_by = order_by

    return apply

def with_export_task_files_order_direction(order_direction: str) -> Callable[[ExportTaskFilesOptions], None]:
    def apply(options: ExportTaskFilesOptions) -> None:
        options.order_direction = order_direction

    return apply

class SQLDatabaseListOptions:
    def __init__(self) -> None:
        self.page_size: Optional[int] = None
        self.page_token: Optional[str] = None
        self.search: Optional[str] = None
        self.name: Optional[str] = None

def with_sql_database_page_size(size: int) -> Callable[[SQLDatabaseListOptions], None]:
    def apply(options: SQLDatabaseListOptions) -> None:
        options.page_size = size

    return apply

def with_sql_database_page_token(token: str) -> Callable[[SQLDatabaseListOptions], None]:
    def apply(options: SQLDatabaseListOptions) -> None:
        options.page_token = token

    return apply

def with_sql_database_search(search: str) -> Callable[[SQLDatabaseListOptions], None]:
    def apply(options: SQLDatabaseListOptions) -> None:
        options.search = search

    return apply

def with_sql_database_name(name: str) -> Callable[[SQLDatabaseListOptions], None]:
    def apply(options: SQLDatabaseListOptions) -> None:
        options.name = name

    return apply

class WorkbookListOptions:
    def __init__(self) -> None:
        self.search: Optional[str] = None
        self.page_size: Optional[int] = None
        self.page_token: Optional[str] = None

def with_workbook_search(search: str) -> Callable[[WorkbookListOptions], None]:
    def apply(options: WorkbookListOptions) -> None:
        options.search = search

    return apply

def with_workbook_page_size(page_size: int) -> Callable[[WorkbookListOptions], None]:
    def apply(options: WorkbookListOptions) -> None:
        options.page_size = page_size

    return apply

def with_workbook_page_token(page_token: str) -> Callable[[WorkbookListOptions], None]:
    def apply(options: WorkbookListOptions) -> None:
        options.page_token = page_token

    return apply

class WorkbookVersionListOptions:
    def __init__(self) -> None:
        self.page_size: Optional[int] = None
        self.page_token: Optional[str] = None

def with_workbook_version_page_size(page_size: int) -> Callable[[WorkbookVersionListOptions], None]:
    def apply(options: WorkbookVersionListOptions) -> None:
        options.page_size = page_size

    return apply

def with_workbook_version_page_token(page_token: str) -> Callable[[WorkbookVersionListOptions], None]:
    def apply(options: WorkbookVersionListOptions) -> None:
        options.page_token = page_token

    return apply

class SQLQueryOptions:
    def __init__(self) -> None:
        self.db_name: Optional[str] = None
        self.sql_type: Optional[str] = None
        self.offset: Optional[int] = None
        self.limit: Optional[int] = None

def with_sql_query_db_name(db_name: str) -> Callable[[SQLQueryOptions], None]:
    def apply(options: SQLQueryOptions) -> None:
        options.db_name = db_name

    return apply

def with_sql_query_type(sql_type: str) -> Callable[[SQLQueryOptions], None]:
    def apply(options: SQLQueryOptions) -> None:
        options.sql_type = sql_type

    return apply

def with_sql_query_offset(offset: int) -> Callable[[SQLQueryOptions], None]:
    def apply(options: SQLQueryOptions) -> None:
        options.offset = offset

    return apply

def with_sql_query_limit(limit: int) -> Callable[[SQLQueryOptions], None]:
    def apply(options: SQLQueryOptions) -> None:
        options.limit = limit

    return apply

class SQLResultOptions:
    def __init__(self) -> None:
        self.offset: Optional[int] = None
        self.limit: Optional[int] = None

def with_sql_result_offset(offset: int) -> Callable[[SQLResultOptions], None]:
    def apply(options: SQLResultOptions) -> None:
        options.offset = offset

    return apply

def with_sql_result_limit(limit: int) -> Callable[[SQLResultOptions], None]:
    def apply(options: SQLResultOptions) -> None:
        options.limit = limit

    return apply

class QueryHistoryOverviewOptions:
    def __init__(self) -> None:
        self.scope: Optional[str] = None
        self.non_user: Optional[bool] = None
        self.start: Optional[str] = None
        self.end: Optional[str] = None
        self.sql_source_type: list[str] = []

def with_query_history_overview_scope(scope: str) -> Callable[[QueryHistoryOverviewOptions], None]:
    """Select self or workspace history under the same read permission."""
    def apply(options: QueryHistoryOverviewOptions) -> None:
        options.scope = scope

    return apply

def with_query_history_overview_non_user(non_user: bool) -> Callable[[QueryHistoryOverviewOptions], None]:
    def apply(options: QueryHistoryOverviewOptions) -> None:
        options.non_user = non_user

    return apply

def with_query_history_overview_start(start: str) -> Callable[[QueryHistoryOverviewOptions], None]:
    def apply(options: QueryHistoryOverviewOptions) -> None:
        options.start = start

    return apply

def with_query_history_overview_end(end: str) -> Callable[[QueryHistoryOverviewOptions], None]:
    def apply(options: QueryHistoryOverviewOptions) -> None:
        options.end = end

    return apply

def with_query_history_overview_sql_source_types(*types: str) -> Callable[[QueryHistoryOverviewOptions], None]:
    def apply(options: QueryHistoryOverviewOptions) -> None:
        options.sql_source_type.extend(types)

    return apply

class QueryHistoryOptions:
    def __init__(self) -> None:
        self.scope: Optional[str] = None
        self.non_user: Optional[bool] = None
        self.status: Optional[str] = None
        self.user: list[str] = []
        self.databases: list[str] = []
        self.statement: Optional[str] = None
        self.query_type: list[str] = []
        self.duration: Optional[int] = None
        self.start: Optional[str] = None
        self.end: Optional[str] = None
        self.statement_id: Optional[str] = None
        self.transaction_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.selected_field: list[str] = []
        self.sql_source_type: list[str] = []
        self.offset: Optional[int] = None
        self.limit: Optional[int] = None
        self.order_by: list[str] = []
        self.order: Optional[str] = None
        self.cu: Optional[int] = None

def with_query_history_scope(scope: str) -> Callable[[QueryHistoryOptions], None]:
    """Select self or workspace history under the same read permission."""
    def apply(options: QueryHistoryOptions) -> None:
        options.scope = scope

    return apply

def with_query_history_non_user(non_user: bool) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.non_user = non_user

    return apply

def with_query_history_status(status: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.status = status

    return apply

def with_query_history_users(*users: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.user.extend(users)

    return apply

def with_query_history_databases(*databases: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.databases.extend(databases)

    return apply

def with_query_history_statement(statement: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.statement = statement

    return apply

def with_query_history_types(*types: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.query_type.extend(types)

    return apply

def with_query_history_min_duration(duration: int) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.duration = duration

    return apply

def with_query_history_start(start: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.start = start

    return apply

def with_query_history_end(end: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.end = end

    return apply

def with_query_history_statement_id(statement_id: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.statement_id = statement_id

    return apply

def with_query_history_transaction_id(transaction_id: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.transaction_id = transaction_id

    return apply

def with_query_history_session_id(session_id: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.session_id = session_id

    return apply

def with_query_history_selected_fields(*fields: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.selected_field.extend(fields)

    return apply

def with_query_history_sql_source_types(*types: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.sql_source_type.extend(types)

    return apply

def with_query_history_offset(offset: int) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.offset = offset

    return apply

def with_query_history_limit(limit: int) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.limit = limit

    return apply

def with_query_history_order_by(*fields: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.order_by.extend(fields)

    return apply

def with_query_history_order(order: str) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.order = order

    return apply

def with_query_history_cu(cu: int) -> Callable[[QueryHistoryOptions], None]:
    def apply(options: QueryHistoryOptions) -> None:
        options.cu = cu

    return apply

class QueryRecordOptions:
    def __init__(self) -> None:
        self.scope: Optional[str] = None
        self.start: Optional[str] = None
        self.end: Optional[str] = None

def with_query_record_scope(scope: str) -> Callable[[QueryRecordOptions], None]:
    """Select self or workspace history under the same read permission."""
    def apply(options: QueryRecordOptions) -> None:
        options.scope = scope

    return apply

def with_query_record_start(start: str) -> Callable[[QueryRecordOptions], None]:
    def apply(options: QueryRecordOptions) -> None:
        options.start = start

    return apply

def with_query_record_end(end: str) -> Callable[[QueryRecordOptions], None]:
    def apply(options: QueryRecordOptions) -> None:
        options.end = end

    return apply

class WorkflowRunOptions:
    def __init__(self) -> None:
        self.input: Optional[dict[str, Any]] = None
        self.replace_saved_defaults = False
        self.trigger_now: Optional[bool] = None

def with_workflow_run_input(input: dict[str, Any]) -> Callable[[WorkflowRunOptions], None]:
    """Set runtime values for workflow run (serialized as JSON field "values")."""

    def apply(options: WorkflowRunOptions) -> None:
        options.input = input

    return apply


def with_workflow_run_values(values: dict[str, Any]) -> Callable[[WorkflowRunOptions], None]:
    """Alias for with_workflow_run_input that matches backend RunWorkflowRequest.values."""

    return with_workflow_run_input(values)


def with_workflow_run_replace_saved_defaults(replace: bool) -> Callable[[WorkflowRunOptions], None]:
    """Replace saved workflow defaults when true."""

    def apply(options: WorkflowRunOptions) -> None:
        options.replace_saved_defaults = replace

    return apply


def with_workflow_run_trigger_now(trigger_now: bool) -> Callable[[WorkflowRunOptions], None]:
    """Set the optional immediate-dispatch control for workflow run creation."""

    def apply(options: WorkflowRunOptions) -> None:
        options.trigger_now = trigger_now

    return apply


class WorkflowHistoryRestoreRequest:
    """Create one reviewable workflow-history restore proposal."""

    def __init__(
        self,
        *,
        context_id: str,
        request_id: str,
        candidate_ref: "WorkflowCandidateRef",
        parent_ref: "WorkflowCandidateRef | None" = None,
    ) -> None:
        if not context_id:
            raise ValueError("context_id is required")
        if not request_id:
            raise ValueError("request_id is required")
        if not isinstance(candidate_ref, WorkflowCandidateRef):
            raise TypeError("candidate_ref is required")
        if parent_ref is not None and not isinstance(parent_ref, WorkflowCandidateRef):
            raise TypeError("parent_ref must be a WorkflowCandidateRef")
        self.context_id = context_id
        self.request_id = request_id
        self.candidate_ref = candidate_ref
        self.parent_ref = parent_ref

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "context_id": self.context_id,
            "request_id": self.request_id,
            "candidate_ref": self.candidate_ref.to_dict(),
        }
        if self.parent_ref is not None:
            body["parent_ref"] = self.parent_ref.to_dict()
        return body


class WorkflowCandidateRef:
    """Reference to one server-owned A2A workflow candidate artifact."""

    def __init__(self, task_id: str, artifact_id: str) -> None:
        if not task_id or not artifact_id:
            raise ValueError("candidate_ref task_id and artifact_id are required")
        self.task_id = task_id
        self.artifact_id = artifact_id

    def to_dict(self) -> dict[str, str]:
        return {"task_id": self.task_id, "artifact_id": self.artifact_id}


class AcceptedWorkflowCandidate:
    """Typed handoff created from one validated server acceptance response."""

    def __init__(self, acceptance: WorkflowCandidateAcceptance) -> None:
        if not isinstance(acceptance, WorkflowCandidateAcceptance):
            raise TypeError("workflow candidate acceptance is required")
        candidate_ref = acceptance.candidate_ref
        candidate = acceptance.candidate
        if not candidate_ref.task_id or not candidate_ref.artifact_id:
            raise ValueError("workflow candidate acceptance identity is required")
        if not acceptance.accepted_at:
            raise ValueError("workflow candidate accepted_at is required")
        if not candidate.ok:
            raise ValueError("workflow candidate acceptance bundle is not successful")
        if candidate.candidate_id != candidate_ref.artifact_id:
            raise ValueError("workflow candidate acceptance candidate_id does not match artifact_id")
        if not candidate.HasField("workflow"):
            raise ValueError("workflow candidate acceptance workflow is required")
        self._acceptance = acceptance
        self._task_id = candidate_ref.task_id
        self._artifact_id = candidate_ref.artifact_id

    @property
    def acceptance(self) -> WorkflowCandidateAcceptance:
        """Return the server acceptance bundle for review and provenance inspection."""

        return self._acceptance

    @property
    def candidate_ref(self) -> WorkflowCandidateRef:
        """Return the exact task/artifact identity accepted by the server."""

        return WorkflowCandidateRef(self._task_id, self._artifact_id)


def accepted_workflow_candidate_from_acceptance(
    acceptance: WorkflowCandidateAcceptance,
) -> AcceptedWorkflowCandidate:
    """Validate a serialized server result and rebuild its typed handoff."""

    return AcceptedWorkflowCandidate(acceptance)


class WorkflowDeployOptions:
    def __init__(self) -> None:
        self.workflow_id: Optional[str] = None
        self.description: Optional[str] = None
        self.execution_mode: Optional[str] = None
        self.cron_expression: Optional[str] = None
        self.source_type: Optional[str] = None
        self.workflow: Optional[dict[str, Any]] = None
        self.input_form: Any = None
        self.form_layout: Any = None
        self.volume_trigger: Optional[dict[str, Any]] = None
        self.dynamic_service: Optional[dict[str, Any]] = None
        self.default_values: Optional[dict[str, Any]] = None
        self.compute_resource_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.notification: Optional[dict[str, Any]] = None

def with_workflow_http_notification(url: str, *workflow_states: str) -> Callable[[WorkflowDeployOptions], None]:
    """Configure terminal HTTP callbacks for COMPLETED, FAILED or CANCELLED."""
    def apply(options: WorkflowDeployOptions) -> None:
        options.notification = {"type": "http", "url": url, "notify_workflow_states": list(workflow_states)}

    return apply

def with_workflow_id(workflow_id: str) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.workflow_id = workflow_id

    return apply

def with_workflow_description(description: str) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.description = description

    return apply

def with_workflow_execution_mode(mode: str) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.execution_mode = mode

    return apply

def with_workflow_cron_expression(expr: str) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.cron_expression = expr

    return apply

def with_workflow_source_type(source_type: str) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.source_type = source_type

    return apply


def with_workflow_mowl(workflow: dict[str, Any]) -> Callable[[WorkflowDeployOptions], None]:
    """Deploy authored native MOWL; pass an empty dsl_yaml to deploy.

    Server-owned accepted candidates must continue to use deploy_candidate.
    """
    def apply(options: WorkflowDeployOptions) -> None:
        if not isinstance(workflow, dict):
            raise ValueError("authored workflow must be a JSON object")
        options.workflow = workflow

    return apply

def with_workflow_input_form(input_form: Any) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.input_form = input_form

    return apply

def with_workflow_form_layout(form_layout: Any) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.form_layout = form_layout

    return apply

def with_workflow_volume_trigger(volume_id: int = 0, enabled: Optional[bool] = None, vars_json: str = "") -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        body: dict[str, Any] = {}
        if volume_id:
            body["volume_id"] = volume_id
        if enabled is not None:
            body["enabled"] = enabled
        if vars_json:
            body["vars_json"] = vars_json
        options.volume_trigger = body

    return apply

def with_workflow_dynamic_service(
    service_name: str = "",
    input_schema: str = "",
    output_schema: str = "",
    result_mode: str = "",
    runtime_spec_json: str = "",
    ui_resource: Optional[dict[str, Any]] = None,
) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        body: dict[str, Any] = {}
        if service_name:
            body["service_name"] = service_name
        if input_schema:
            body["input_schema"] = input_schema
        if output_schema:
            body["output_schema"] = output_schema
        if result_mode:
            body["result_mode"] = result_mode
        if runtime_spec_json:
            body["runtime_spec_json"] = runtime_spec_json
        if ui_resource is not None:
            body["ui_resource"] = ui_resource
        options.dynamic_service = body

    return apply

def with_workflow_default_values(values: dict[str, Any]) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.default_values = values

    return apply

def with_workflow_compute_resource_id(compute_resource_id: str) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.compute_resource_id = compute_resource_id

    return apply

def with_workflow_session_id(session_id: str) -> Callable[[WorkflowDeployOptions], None]:
    def apply(options: WorkflowDeployOptions) -> None:
        options.session_id = session_id

    return apply

class WorkflowUpdateOptions:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.execution_mode: Optional[str] = None
        self.cron_expression: Optional[str] = None
        self.dsl_yaml: Optional[str] = None
        self.input_form: Any = None
        self.form_layout: Any = None
        self.default_values: Optional[dict[str, Any]] = None
        self.volume_trigger: Optional[dict[str, Any]] = None
        self.dynamic_service: Optional[dict[str, Any]] = None

def with_workflow_update_name(name: str) -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        options.name = name

    return apply

def with_workflow_update_description(description: str) -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        options.description = description

    return apply

def with_workflow_update_execution_mode(mode: str) -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        options.execution_mode = mode

    return apply

def with_workflow_update_cron_expression(expr: str) -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        options.cron_expression = expr

    return apply

def with_workflow_update_dsl_yaml(dsl_yaml: str) -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        options.dsl_yaml = dsl_yaml

    return apply


def with_workflow_update_input_form(input_form: Any) -> Callable[[WorkflowUpdateOptions], None]:
    """Set runtime form fields (serialized as JSON field "runtime_fields")."""

    def apply(options: WorkflowUpdateOptions) -> None:
        options.input_form = input_form

    return apply


def with_workflow_update_form_layout(form_layout: Any) -> Callable[[WorkflowUpdateOptions], None]:
    """Set runtime form layout (serialized as JSON field "runtime_layout")."""

    def apply(options: WorkflowUpdateOptions) -> None:
        options.form_layout = form_layout

    return apply


def with_workflow_update_default_values(values: dict[str, Any]) -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        options.default_values = values

    return apply

def with_workflow_update_volume_trigger(volume_id: int = 0, enabled: Optional[bool] = None, vars_json: str = "") -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        body: dict[str, Any] = {}
        if volume_id:
            body["volume_id"] = volume_id
        if enabled is not None:
            body["enabled"] = enabled
        if vars_json:
            body["vars_json"] = vars_json
        options.volume_trigger = body

    return apply

def with_workflow_update_dynamic_service(
    service_name: str = "",
    input_schema: str = "",
    output_schema: str = "",
    result_mode: str = "",
    runtime_spec_json: str = "",
    ui_resource: Optional[dict[str, Any]] = None,
) -> Callable[[WorkflowUpdateOptions], None]:
    def apply(options: WorkflowUpdateOptions) -> None:
        body: dict[str, Any] = {}
        if service_name:
            body["service_name"] = service_name
        if input_schema:
            body["input_schema"] = input_schema
        if output_schema:
            body["output_schema"] = output_schema
        if result_mode:
            body["result_mode"] = result_mode
        if runtime_spec_json:
            body["runtime_spec_json"] = runtime_spec_json
        if ui_resource is not None:
            body["ui_resource"] = ui_resource
        options.dynamic_service = body

    return apply

class WorkflowRerunOptions:
    def __init__(self) -> None:
        self.values: Optional[dict[str, Any]] = None
        self.replace_saved_defaults: bool = False
        self.trigger_now: Optional[bool] = None
        self.config_override: Any = None
        self.expected_rerun_contract_hash: Optional[str] = None
        self.reason: Optional[str] = None

def with_workflow_rerun_values(values: dict[str, Any]) -> Callable[[WorkflowRerunOptions], None]:
    def apply(options: WorkflowRerunOptions) -> None:
        options.values = values

    return apply

def with_workflow_retry_replace_saved_defaults(replace: bool) -> Callable[[WorkflowRerunOptions], None]:
    """Replace saved defaults with retry values; false preserves merge behavior."""
    def apply(options: WorkflowRerunOptions) -> None:
        options.replace_saved_defaults = replace

    return apply

def with_workflow_rerun_trigger_now(trigger_now: bool) -> Callable[[WorkflowRerunOptions], None]:
    def apply(options: WorkflowRerunOptions) -> None:
        options.trigger_now = trigger_now

    return apply

def with_workflow_rerun_config_override(config_override: Any) -> Callable[[WorkflowRerunOptions], None]:
    def apply(options: WorkflowRerunOptions) -> None:
        options.config_override = config_override

    return apply

def with_expected_workflow_rerun_contract_hash(contract_hash: str) -> Callable[[WorkflowRerunOptions], None]:
    def apply(options: WorkflowRerunOptions) -> None:
        options.expected_rerun_contract_hash = contract_hash

    return apply


def with_workflow_rerun_reason(reason: str) -> Callable[[WorkflowRerunOptions], None]:
    def apply(options: WorkflowRerunOptions) -> None:
        options.reason = reason

    return apply

class WorkflowCancelOptions:
    def __init__(self) -> None:
        self.reason: Optional[str] = None

def with_workflow_cancel_reason(reason: str) -> Callable[[WorkflowCancelOptions], None]:
    def apply(options: WorkflowCancelOptions) -> None:
        options.reason = reason

    return apply

class CustomOperatorOptions:
    def __init__(self) -> None:
        self.node_id: Optional[str] = None
        self.kind: Optional[str] = None
        self.language: Optional[str] = None
        self.handler: Optional[str] = None
        self.version: Optional[str] = None
        self.isolation_level: Optional[str] = None
        self.enabled: Optional[bool] = None
        self.code: Optional[str] = None
        self.source_file_id: Optional[str] = None
        self.base_node_id: Optional[str] = None
        self.base_node_version: Optional[str] = None
        self.binding_config: Any = None
        self.catalog_id: Optional[int] = None
        self.database_id: Optional[int] = None

def with_custom_operator_node_id(node_id: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.node_id = node_id

    return apply

def with_custom_operator_kind(kind: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.kind = kind

    return apply

def with_custom_operator_language(language: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.language = language

    return apply

def with_custom_operator_handler(handler: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.handler = handler

    return apply

def with_custom_operator_version(version: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.version = version

    return apply

def with_custom_operator_isolation_level(isolation_level: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.isolation_level = isolation_level

    return apply

def with_custom_operator_enabled(enabled: bool) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.enabled = enabled

    return apply

def with_custom_operator_code(code: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.code = code

    return apply

def with_custom_operator_source_file_id(source_file_id: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.source_file_id = source_file_id

    return apply

def with_custom_operator_base_node_id(base_node_id: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.base_node_id = base_node_id

    return apply

def with_custom_operator_base_node_version(base_node_version: str) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.base_node_version = base_node_version

    return apply

def with_custom_operator_binding_config(binding_config: Any) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.binding_config = binding_config

    return apply

def with_custom_operator_catalog_id(catalog_id: int) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.catalog_id = catalog_id

    return apply

def with_custom_operator_database_id(database_id: int) -> Callable[[CustomOperatorOptions], None]:
    def apply(options: CustomOperatorOptions) -> None:
        options.database_id = database_id

    return apply

class CustomOperatorUpdateOptions:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.kind: Optional[str] = None
        self.language: Optional[str] = None
        self.handler: Optional[str] = None
        self.version: Optional[str] = None
        self.isolation_level: Optional[str] = None
        self.input_schema: Any = None
        self.output_schema: Any = None
        self.enabled: Optional[bool] = None
        self.code: Optional[str] = None
        self.source_file_id: Optional[str] = None
        self.base_node_id: Optional[str] = None
        self.base_node_version: Optional[str] = None
        self.binding_config: Any = None
        self.catalog_id: Optional[int] = None
        self.database_id: Optional[int] = None

def with_custom_operator_update_name(name: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.name = name

    return apply

def with_custom_operator_update_description(description: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.description = description

    return apply

def with_custom_operator_update_kind(kind: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.kind = kind

    return apply

def with_custom_operator_update_language(language: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.language = language

    return apply

def with_custom_operator_update_handler(handler: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.handler = handler

    return apply

def with_custom_operator_update_version(version: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.version = version

    return apply

def with_custom_operator_update_isolation_level(isolation_level: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.isolation_level = isolation_level

    return apply

def with_custom_operator_update_input_schema(input_schema: Any) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.input_schema = input_schema

    return apply

def with_custom_operator_update_output_schema(output_schema: Any) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.output_schema = output_schema

    return apply

def with_custom_operator_update_enabled(enabled: bool) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.enabled = enabled

    return apply

def with_custom_operator_update_code(code: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.code = code

    return apply

def with_custom_operator_update_source_file_id(source_file_id: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.source_file_id = source_file_id

    return apply

def with_custom_operator_update_base_node_id(base_node_id: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.base_node_id = base_node_id

    return apply

def with_custom_operator_update_base_node_version(base_node_version: str) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.base_node_version = base_node_version

    return apply

def with_custom_operator_update_binding_config(binding_config: Any) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.binding_config = binding_config

    return apply

def with_custom_operator_update_catalog_id(catalog_id: int) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.catalog_id = catalog_id

    return apply

def with_custom_operator_update_database_id(database_id: int) -> Callable[[CustomOperatorUpdateOptions], None]:
    def apply(options: CustomOperatorUpdateOptions) -> None:
        options.database_id = database_id

    return apply

class WorkflowTemplateOptions:
    def __init__(self) -> None:
        self.template_key: Optional[str] = None
        self.description: Optional[str] = None
        self.input_form: Optional[str] = None
        self.is_builtin: Optional[bool] = None

def with_workflow_template_key(template_key: str) -> Callable[[WorkflowTemplateOptions], None]:
    def apply(options: WorkflowTemplateOptions) -> None:
        options.template_key = template_key

    return apply

def with_workflow_template_description(description: str) -> Callable[[WorkflowTemplateOptions], None]:
    def apply(options: WorkflowTemplateOptions) -> None:
        options.description = description

    return apply

def with_workflow_template_input_form(input_form: str) -> Callable[[WorkflowTemplateOptions], None]:
    def apply(options: WorkflowTemplateOptions) -> None:
        options.input_form = input_form

    return apply

def with_workflow_template_builtin(is_builtin: bool) -> Callable[[WorkflowTemplateOptions], None]:
    def apply(options: WorkflowTemplateOptions) -> None:
        options.is_builtin = is_builtin

    return apply

class ComputeCreateOptions:
    def __init__(self) -> None:
        self.kind: Optional[str] = None
        self.py_requirements_txt: Optional[str] = None
        self.description: Optional[str] = None
        self.gpu: Optional[int] = None
        self.min_replicas: Optional[int] = None
        self.max_replicas: Optional[int] = None
        self.auto_suspend_minutes: Optional[int] = 10
        self.worker_images: Optional[list[WorkerImageSelection]] = None
        self.go_worker_image_id: Optional[str] = None
        self.python_worker_image_id: Optional[str] = None
        self.platform: Optional[str] = None

def with_compute_kind(kind: str) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.kind = kind
    return apply

def with_compute_py_requirements_txt(requirements: str) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.py_requirements_txt = requirements
    return apply

def with_compute_description(description: str) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.description = description

    return apply

def with_compute_gpu(gpu: int) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.gpu = gpu

    return apply

def with_compute_min_replicas(min_replicas: int) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.min_replicas = min_replicas

    return apply

def with_compute_max_replicas(max_replicas: int) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.max_replicas = max_replicas

    return apply

def with_compute_auto_suspend_minutes(minutes: int) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.auto_suspend_minutes = minutes

    return apply

def with_compute_worker_images(*worker_images: WorkerImageSelection) -> Callable[[ComputeCreateOptions], None]:
    # Catalog accepts only current is_default entries. Omitting this option
    # leaves deployment image resolution entirely to Catalog configuration.
    def apply(options: ComputeCreateOptions) -> None:
        options.worker_images = list(worker_images)

    return apply

def with_compute_go_worker_image_id(image_id: str) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.go_worker_image_id = image_id

    return apply

def with_compute_python_worker_image_id(image_id: str) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.python_worker_image_id = image_id

    return apply

def with_compute_platform(platform: str) -> Callable[[ComputeCreateOptions], None]:
    def apply(options: ComputeCreateOptions) -> None:
        options.platform = platform

    return apply

class ComputeSpecOptions:
    def __init__(self) -> None:
        self.node_placement: Optional[dict[str, Any]] = None
        self.node_placement_set = False
        self.gpu_count: Optional[int] = None
        self.gpu_memory_mib: Optional[int] = None
        self.gpu_cores: Optional[int] = None
        self.credit_per_hour: Optional[float] = None
        self.description: Optional[str] = None
        self.enabled: Optional[bool] = None

class ComputeSpecUpdateOptions(ComputeSpecOptions):
    def __init__(self) -> None:
        super().__init__()
        self.kind: Optional[str] = None
        self.family: Optional[str] = None
        self.family_name: Optional[str] = None
        self.family_name_en: Optional[str] = None
        self.cpu_milli: Optional[int] = None
        self.memory_mib: Optional[int] = None

def with_compute_spec_node_placement(placement: Optional[dict[str, Any]]) -> Callable[[ComputeSpecOptions], None]:
    """Send the placement unchanged; None sends null, omission keeps it absent."""
    def apply(options: ComputeSpecOptions) -> None:
        options.node_placement = placement
        options.node_placement_set = True
    return apply

def with_compute_spec_gpu_count(gpu_count: int) -> Callable[[ComputeSpecOptions], None]:
    def apply(options: ComputeSpecOptions) -> None:
        options.gpu_count = gpu_count

    return apply

def with_compute_spec_gpu_memory_mib(gpu_memory_mib: int) -> Callable[[ComputeSpecOptions], None]:
    def apply(options: ComputeSpecOptions) -> None:
        options.gpu_memory_mib = gpu_memory_mib

    return apply

def with_compute_spec_gpu_cores(gpu_cores: int) -> Callable[[ComputeSpecOptions], None]:
    def apply(options: ComputeSpecOptions) -> None:
        options.gpu_cores = gpu_cores

    return apply

def with_compute_spec_credit_per_hour(credit_per_hour: float) -> Callable[[ComputeSpecOptions], None]:
    def apply(options: ComputeSpecOptions) -> None:
        options.credit_per_hour = credit_per_hour

    return apply

def with_compute_spec_description(description: str) -> Callable[[ComputeSpecOptions], None]:
    def apply(options: ComputeSpecOptions) -> None:
        options.description = description

    return apply

def with_compute_spec_enabled(enabled: bool) -> Callable[[ComputeSpecOptions], None]:
    def apply(options: ComputeSpecOptions) -> None:
        options.enabled = enabled

    return apply

def with_compute_spec_update_kind(kind: str) -> Callable[[ComputeSpecUpdateOptions], None]:
    def apply(options: ComputeSpecUpdateOptions) -> None:
        options.kind = kind

    return apply

def with_compute_spec_update_family(family: str) -> Callable[[ComputeSpecUpdateOptions], None]:
    def apply(options: ComputeSpecUpdateOptions) -> None:
        options.family = family

    return apply

def with_compute_spec_update_family_name(family_name: str) -> Callable[[ComputeSpecUpdateOptions], None]:
    def apply(options: ComputeSpecUpdateOptions) -> None:
        options.family_name = family_name

    return apply

def with_compute_spec_update_family_name_en(family_name_en: str) -> Callable[[ComputeSpecUpdateOptions], None]:
    def apply(options: ComputeSpecUpdateOptions) -> None:
        options.family_name_en = family_name_en

    return apply

def with_compute_spec_update_cpu_milli(cpu_milli: int) -> Callable[[ComputeSpecUpdateOptions], None]:
    def apply(options: ComputeSpecUpdateOptions) -> None:
        options.cpu_milli = cpu_milli

    return apply

def with_compute_spec_update_memory_mib(memory_mib: int) -> Callable[[ComputeSpecUpdateOptions], None]:
    def apply(options: ComputeSpecUpdateOptions) -> None:
        options.memory_mib = memory_mib

    return apply

class ComputeUpdateOptions:
    def __init__(self) -> None:
        self.kind: Optional[str] = None
        self.py_requirements_txt: Optional[str] = None
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.spec_id: Optional[str] = None
        self.cpu: Optional[int] = None
        self.memory_gib: Optional[int] = None
        self.gpu: Optional[int] = None
        self.min_replicas: Optional[int] = None
        self.max_replicas: Optional[int] = None
        self.auto_suspend_minutes: Optional[int] = None
        self.worker_images: Optional[list[WorkerImageSelection]] = None
        self.go_worker_image_id: Optional[str] = None
        self.python_worker_image_id: Optional[str] = None
        self.platform: Optional[str] = None

def with_compute_update_kind(kind: str) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.kind = kind
    return apply

def with_compute_update_py_requirements_txt(requirements: str) -> Callable[[ComputeUpdateOptions], None]:
    """Replace Python worker dependencies; an empty string clears them."""
    def apply(options: ComputeUpdateOptions) -> None:
        options.py_requirements_txt = requirements
    return apply

def with_compute_update_name(name: str) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.name = name

    return apply

def with_compute_update_description(description: str) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.description = description

    return apply

def with_compute_update_spec_id(spec_id: str) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.spec_id = spec_id

    return apply

def with_compute_update_cpu(cpu: int) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.cpu = cpu

    return apply

def with_compute_update_memory_gib(memory_gib: int) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.memory_gib = memory_gib

    return apply

def with_compute_update_gpu(gpu: int) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.gpu = gpu

    return apply

def with_compute_update_min_replicas(min_replicas: int) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.min_replicas = min_replicas

    return apply

def with_compute_update_max_replicas(max_replicas: int) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.max_replicas = max_replicas

    return apply

def with_compute_update_auto_suspend_minutes(minutes: int) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.auto_suspend_minutes = minutes

    return apply

def with_compute_update_worker_images(*worker_images: WorkerImageSelection) -> Callable[[ComputeUpdateOptions], None]:
    # Catalog accepts only current is_default entries. Omitting this option
    # preserves Catalog-driven deployment image resolution for the update.
    def apply(options: ComputeUpdateOptions) -> None:
        options.worker_images = list(worker_images)

    return apply

def with_compute_update_go_worker_image_id(image_id: str) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.go_worker_image_id = image_id

    return apply

def with_compute_update_python_worker_image_id(image_id: str) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.python_worker_image_id = image_id

    return apply

def with_compute_update_platform(platform: str) -> Callable[[ComputeUpdateOptions], None]:
    def apply(options: ComputeUpdateOptions) -> None:
        options.platform = platform

    return apply

class ProviderBackendOptions:
    def __init__(self) -> None:
        self.provider_type: Optional[str] = None
        self.reasoning_control_protocol: Optional[str] = None
        self.api_key: Optional[str] = None
        self.address: Optional[str] = None
        self.timeout_seconds: Optional[int] = None
        self.models: list[str] = []
        self.supported_mime_types: list[str] = []

def with_provider_backend_type(provider_type: str) -> Callable[[ProviderBackendOptions], None]:
    def apply(options: ProviderBackendOptions) -> None:
        options.provider_type = provider_type

    return apply

def with_provider_backend_reasoning_control_protocol(protocol: str) -> Callable[[ProviderBackendOptions], None]:
    def apply(options: ProviderBackendOptions) -> None:
        options.reasoning_control_protocol = protocol

    return apply

def with_provider_backend_api_key(api_key: str) -> Callable[[ProviderBackendOptions], None]:
    def apply(options: ProviderBackendOptions) -> None:
        options.api_key = api_key

    return apply

def with_provider_backend_address(address: str) -> Callable[[ProviderBackendOptions], None]:
    def apply(options: ProviderBackendOptions) -> None:
        options.address = address

    return apply

def with_provider_backend_timeout_seconds(timeout_seconds: int) -> Callable[[ProviderBackendOptions], None]:
    def apply(options: ProviderBackendOptions) -> None:
        options.timeout_seconds = timeout_seconds

    return apply

def with_provider_backend_models(*models: str) -> Callable[[ProviderBackendOptions], None]:
    def apply(options: ProviderBackendOptions) -> None:
        options.models.extend(models)

    return apply

def with_provider_backend_supported_mime_types(*mime_types: str) -> Callable[[ProviderBackendOptions], None]:
    def apply(options: ProviderBackendOptions) -> None:
        options.supported_mime_types.extend(mime_types)

    return apply

class ProviderBackendUpdateOptions:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.api_key: Optional[str] = None
        self.reasoning_control_protocol: Optional[str] = None
        self.timeout_seconds: Optional[int] = None
        self.models: list[str] = []
        self.supported_mime_types: list[str] = []

def with_provider_backend_update_name(name: str) -> Callable[[ProviderBackendUpdateOptions], None]:
    def apply(options: ProviderBackendUpdateOptions) -> None:
        options.name = name

    return apply

def with_provider_backend_update_api_key(api_key: str) -> Callable[[ProviderBackendUpdateOptions], None]:
    def apply(options: ProviderBackendUpdateOptions) -> None:
        options.api_key = api_key

    return apply

def with_provider_backend_update_reasoning_control_protocol(protocol: str) -> Callable[[ProviderBackendUpdateOptions], None]:
    def apply(options: ProviderBackendUpdateOptions) -> None:
        options.reasoning_control_protocol = protocol

    return apply

def with_provider_backend_update_timeout_seconds(timeout_seconds: int) -> Callable[[ProviderBackendUpdateOptions], None]:
    def apply(options: ProviderBackendUpdateOptions) -> None:
        options.timeout_seconds = timeout_seconds

    return apply

def with_provider_backend_update_models(*models: str) -> Callable[[ProviderBackendUpdateOptions], None]:
    def apply(options: ProviderBackendUpdateOptions) -> None:
        options.models.extend(models)

    return apply

def with_provider_backend_update_supported_mime_types(*mime_types: str) -> Callable[[ProviderBackendUpdateOptions], None]:
    def apply(options: ProviderBackendUpdateOptions) -> None:
        options.supported_mime_types.extend(mime_types)

    return apply

class RouterOptions:
    def __init__(self) -> None:
        self.strategy: Optional[str] = None
        self.health_check_interval: Optional[int] = None
        self.max_retries: Optional[int] = None
        self.session_affinity: Optional[bool] = None

def with_router_strategy(strategy: str) -> Callable[[RouterOptions], None]:
    def apply(options: RouterOptions) -> None:
        options.strategy = strategy

    return apply

def with_router_health_check_interval(interval: int) -> Callable[[RouterOptions], None]:
    def apply(options: RouterOptions) -> None:
        options.health_check_interval = interval

    return apply

def with_router_max_retries(max_retries: int) -> Callable[[RouterOptions], None]:
    def apply(options: RouterOptions) -> None:
        options.max_retries = max_retries

    return apply

def with_router_session_affinity(enabled: bool) -> Callable[[RouterOptions], None]:
    def apply(options: RouterOptions) -> None:
        options.session_affinity = enabled

    return apply

class DataSharePublishOptions:
    def __init__(self) -> None:
        self.remark: Optional[str] = None

def with_data_share_remark(remark: str) -> Callable[[DataSharePublishOptions], None]:
    def apply(options: DataSharePublishOptions) -> None:
        options.remark = remark

    return apply

class DataSharePublishUpdateOptions:
    def __init__(self) -> None:
        self.table_scope: Optional[DataShareScope] = None
        self.target_workspace_ids: Optional[list[str]] = None
        self.remark: Optional[str] = None

def with_data_share_update_table_scope(scope: DataShareScope) -> Callable[[DataSharePublishUpdateOptions], None]:
    def apply(options: DataSharePublishUpdateOptions) -> None:
        options.table_scope = scope

    return apply

def with_data_share_update_target_workspace_ids(*workspace_ids: str) -> Callable[[DataSharePublishUpdateOptions], None]:
    def apply(options: DataSharePublishUpdateOptions) -> None:
        if options.target_workspace_ids is None:
            options.target_workspace_ids = []
        options.target_workspace_ids.extend(workspace_ids)

    return apply

def with_data_share_update_remark(remark: str) -> Callable[[DataSharePublishUpdateOptions], None]:
    def apply(options: DataSharePublishUpdateOptions) -> None:
        options.remark = remark

    return apply

@dataclass
class SemanticModelCreateSpec:
    """Creation-only controls; description/tables/files use the existing options."""

    name: str
    preserve_embedding: Optional[bool] = None
    text_send_dimensions: Optional[bool] = None
    image_send_dimensions: Optional[bool] = None
    drawing_structured_enabled: Optional[bool] = None
    drawing_number_policy: Optional[str] = None


class SemanticModelOptions:
    def __init__(self) -> None:
        self.description: Optional[str] = None
        self.tables: Any = None
        self.files: Any = None

def with_semantic_model_description(description: str) -> Callable[[SemanticModelOptions], None]:
    def apply(options: SemanticModelOptions) -> None:
        options.description = description

    return apply

def with_semantic_model_tables(tables: Any) -> Callable[[SemanticModelOptions], None]:
    def apply(options: SemanticModelOptions) -> None:
        options.tables = tables

    return apply

def with_semantic_model_files(files: Any) -> Callable[[SemanticModelOptions], None]:
    def apply(options: SemanticModelOptions) -> None:
        options.files = files

    return apply

class SemanticModelWithSourcesOptions:
    def __init__(self) -> None:
        self.description: Optional[str] = None
        self.target_catalog_id: Optional[int] = None
        self.files: Any = None
        self.image_index_enabled: Optional[bool] = None
        self.source_selections: Optional[list["SemanticModelSourceSelectionInput"]] = None

def with_semantic_model_with_sources_target_catalog_id(catalog_id: int) -> Callable[[SemanticModelWithSourcesOptions], None]:
    def apply(options: SemanticModelWithSourcesOptions) -> None:
        options.target_catalog_id = catalog_id

    return apply

def with_semantic_model_with_sources_source_selections(*selections: "SemanticModelSourceSelectionInput") -> Callable[[SemanticModelWithSourcesOptions], None]:
    def apply(options: SemanticModelWithSourcesOptions) -> None:
        options.source_selections = list(selections)

    return apply

def with_semantic_model_with_sources_description(description: str) -> Callable[[SemanticModelWithSourcesOptions], None]:
    def apply(options: SemanticModelWithSourcesOptions) -> None:
        options.description = description

    return apply

def with_semantic_model_with_sources_files(files: Any) -> Callable[[SemanticModelWithSourcesOptions], None]:
    def apply(options: SemanticModelWithSourcesOptions) -> None:
        options.files = files

    return apply

def with_semantic_model_with_sources_image_index_enabled(enabled: bool) -> Callable[[SemanticModelWithSourcesOptions], None]:
    def apply(options: SemanticModelWithSourcesOptions) -> None:
        options.image_index_enabled = enabled

    return apply

class SemanticModelEmptyOptions:
    def __init__(self) -> None:
        self.description: Optional[str] = None
        self.image_index_enabled: Optional[bool] = None

def with_semantic_model_empty_description(description: str) -> Callable[[SemanticModelEmptyOptions], None]:
    def apply(options: SemanticModelEmptyOptions) -> None:
        options.description = description

    return apply

def with_semantic_model_empty_image_index_enabled(enabled: bool) -> Callable[[SemanticModelEmptyOptions], None]:
    def apply(options: SemanticModelEmptyOptions) -> None:
        options.image_index_enabled = enabled

    return apply

class SemanticModelSourceInput:
    def __init__(
        self,
        source_type: str,
        *,
        file_name: str = "",
        upload_kind: str = "",
        parse_mode: str = "",
        table_config: str = "",
        file_id: str = "",
        volume_id: int = 0,
        table_id: int = 0,
    ) -> None:
        self.source_type = source_type
        self.file_name = file_name
        self.upload_kind = upload_kind
        self.parse_mode = parse_mode
        self.table_config = table_config
        self.file_id = file_id
        self.volume_id = volume_id
        self.table_id = table_id

    def body(self) -> dict[str, Any]:
        body: dict[str, Any] = {"source_type": self.source_type}
        if self.file_name:
            body["file_name"] = self.file_name
        if self.upload_kind:
            body["upload_kind"] = self.upload_kind
        if self.parse_mode:
            body["parse_mode"] = self.parse_mode
        if self.table_config:
            body["table_config"] = self.table_config
        if self.file_id:
            body["file_id"] = self.file_id
        if self.volume_id:
            body["volume_id"] = self.volume_id
        if self.table_id:
            body["table_id"] = self.table_id
        return body

class SemanticModelSourceSelectionFilters:
    def __init__(self, *, table_name: str = "", file_name: str = "", file_ext: Optional[list[str]] = None) -> None:
        self.table_name = table_name
        self.file_name = file_name
        self.file_ext = file_ext or []

    def body(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if self.table_name:
            body["table_name"] = self.table_name
        if self.file_name:
            body["file_name"] = self.file_name
        if self.file_ext:
            body["file_ext"] = self.file_ext
        return body

class SemanticModelSourceSelectionInput:
    def __init__(
        self,
        kind: str,
        *,
        database_id: int = 0,
        volume_id: int = 0,
        all_selected: bool = False,
        selected_table_ids: Optional[list[int]] = None,
        excluded_table_ids: Optional[list[int]] = None,
        selected_file_ids: Optional[list[str]] = None,
        excluded_file_ids: Optional[list[str]] = None,
        filters: Optional[SemanticModelSourceSelectionFilters] = None,
    ) -> None:
        self.kind = kind
        self.database_id = database_id
        self.volume_id = volume_id
        self.all_selected = all_selected
        self.selected_table_ids = selected_table_ids or []
        self.excluded_table_ids = excluded_table_ids or []
        self.selected_file_ids = selected_file_ids or []
        self.excluded_file_ids = excluded_file_ids or []
        self.filters = filters

    def body(self) -> dict[str, Any]:
        body: dict[str, Any] = {"kind": self.kind, "all_selected": self.all_selected}
        if self.database_id:
            body["database_id"] = self.database_id
        if self.volume_id:
            body["volume_id"] = self.volume_id
        if self.selected_table_ids:
            body["selected_table_ids"] = self.selected_table_ids
        if self.excluded_table_ids:
            body["excluded_table_ids"] = self.excluded_table_ids
        if self.selected_file_ids:
            body["selected_file_ids"] = self.selected_file_ids
        if self.excluded_file_ids:
            body["excluded_file_ids"] = self.excluded_file_ids
        if self.filters is not None and self.filters.body():
            body["filters"] = self.filters.body()
        return body

class SemanticModelSourceGovernanceOptions:
    def __init__(self) -> None:
        self.tags: Optional[list[str]] = None
        self.expires_at: Optional[int] = None
        self.clear_expires_at = False
        self.enabled: Optional[bool] = None
        self.force_enabled_after_expiry: Optional[bool] = None

def with_semantic_model_source_tags(*tags: str) -> Callable[[SemanticModelSourceGovernanceOptions], None]:
    def apply(options: SemanticModelSourceGovernanceOptions) -> None:
        options.tags = list(tags)

    return apply

def with_semantic_model_source_expires_at(expires_at: int) -> Callable[[SemanticModelSourceGovernanceOptions], None]:
    def apply(options: SemanticModelSourceGovernanceOptions) -> None:
        options.expires_at = expires_at
        options.clear_expires_at = False

    return apply

def with_semantic_model_source_expires_at_cleared() -> Callable[[SemanticModelSourceGovernanceOptions], None]:
    def apply(options: SemanticModelSourceGovernanceOptions) -> None:
        options.expires_at = None
        options.clear_expires_at = True

    return apply

def with_semantic_model_source_enabled(enabled: bool) -> Callable[[SemanticModelSourceGovernanceOptions], None]:
    def apply(options: SemanticModelSourceGovernanceOptions) -> None:
        options.enabled = enabled

    return apply

def with_semantic_model_source_force_enabled_after_expiry(force: bool) -> Callable[[SemanticModelSourceGovernanceOptions], None]:
    def apply(options: SemanticModelSourceGovernanceOptions) -> None:
        options.force_enabled_after_expiry = force

    return apply

class SemanticModelSegmentBase:
    def __init__(self, if_match: str = "") -> None:
        self.if_match = if_match

class SemanticModelSegmentUpdateInput:
    def __init__(
        self,
        base: SemanticModelSegmentBase,
        *,
        content: Optional[str] = None,
        ocr_text: Optional[str] = None,
        image_description: Optional[str] = None,
    ) -> None:
        self.base = base
        self.content = content
        self.ocr_text = ocr_text
        self.image_description = image_description

class SemanticModelSegmentCreateInput:
    def __init__(
        self,
        base: SemanticModelSegmentBase,
        *,
        level: str = "",
        content: Optional[str] = None,
        ocr_text: Optional[str] = None,
        image_description: Optional[str] = None,
        image_file_id: str = "",
        page_image_file_id: str = "",
        bbox: Any = None,
        metadata: Any = None,
    ) -> None:
        self.base = base
        self.level = level
        self.content = content
        self.ocr_text = ocr_text
        self.image_description = image_description
        self.image_file_id = image_file_id
        self.page_image_file_id = page_image_file_id
        self.bbox = bbox
        self.metadata = metadata

    def body(self) -> dict[str, Any]:
        return _semantic_model_segment_create_body(self)

class SemanticEntryInput:
    def __init__(self, kind: str, key: str, spec: Any, tables: Optional[list[str]] = None, *, domain: str = "") -> None:
        self.kind = kind
        self.key = key
        self.spec = spec
        self.tables = tables or []
        self.domain = domain

    def validate(self) -> None:
        if not self.kind:
            raise ErrKindRequired
        if not self.key:
            raise ErrKeyRequired
        if self.spec is None:
            raise ErrSpecRequired

class LineageRevisionOptions:
    def __init__(self) -> None:
        self.base_revision_id: Optional[str] = None
        self.use_original: Optional[bool] = None
        self.use_current_effective: Optional[bool] = None
        self.expected_effective_set_version: Optional[int] = None
        self.expected_base_content_hash: Optional[str] = None
        self.revision_content_ref: Optional[str] = None
        self.revision_content_hash: Optional[str] = None
        self.revision_content_payload: Optional[str] = None
        self.patch_json: Optional[str] = None

def with_lineage_base_revision_id(base_revision_id: str) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.base_revision_id = base_revision_id

    return apply

def with_lineage_use_original(use_original: bool) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.use_original = use_original

    return apply

def with_lineage_use_current_effective(use_current_effective: bool) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.use_current_effective = use_current_effective

    return apply

def with_lineage_expected_effective_set_version(version: int) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.expected_effective_set_version = version

    return apply

def with_lineage_expected_base_content_hash(content_hash: str) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.expected_base_content_hash = content_hash

    return apply

def with_lineage_revision_content_ref(content_ref: str) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.revision_content_ref = content_ref

    return apply

def with_lineage_revision_content_hash(content_hash: str) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.revision_content_hash = content_hash

    return apply

def with_lineage_revision_content_payload(payload: str) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.revision_content_payload = payload

    return apply

def with_lineage_patch_json(patch_json: str) -> Callable[[LineageRevisionOptions], None]:
    def apply(options: LineageRevisionOptions) -> None:
        options.patch_json = patch_json

    return apply

class LineageRevisionSwitch:
    def __init__(self, block_id: str, effective_revision_id: str = "", use_original: bool = False) -> None:
        self.block_id = block_id
        self.effective_revision_id = effective_revision_id
        self.use_original = use_original

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {"block_id": self.block_id}
        if self.effective_revision_id:
            body["effective_revision_id"] = self.effective_revision_id
        if self.use_original:
            body["use_original"] = self.use_original
        return body

class LineageSwitchOptions:
    def __init__(self) -> None:
        self.expected_effective_set_version: Optional[int] = None

def with_lineage_switch_expected_effective_set_version(version: int) -> Callable[[LineageSwitchOptions], None]:
    def apply(options: LineageSwitchOptions) -> None:
        options.expected_effective_set_version = version

    return apply

class LineageRerunOptions:
    def __init__(self) -> None:
        self.mode: Optional[str] = None
        self.config_override: Any = _JSON_VALUE_UNSET
        self.input_payload_override: Any = _JSON_VALUE_UNSET
        self.vars_payload_override: Any = _JSON_VALUE_UNSET

def with_lineage_rerun_mode(mode: str) -> Callable[[LineageRerunOptions], None]:
    def apply(options: LineageRerunOptions) -> None:
        options.mode = mode

    return apply

def with_lineage_rerun_config_override(config_override: Any) -> Callable[[LineageRerunOptions], None]:
    def apply(options: LineageRerunOptions) -> None:
        options.config_override = config_override

    return apply

def with_lineage_rerun_input_payload_override(input_payload_override: Any) -> Callable[[LineageRerunOptions], None]:
    def apply(options: LineageRerunOptions) -> None:
        options.input_payload_override = input_payload_override

    return apply

def with_lineage_rerun_vars_payload_override(vars_payload_override: Any) -> Callable[[LineageRerunOptions], None]:
    def apply(options: LineageRerunOptions) -> None:
        options.vars_payload_override = vars_payload_override

    return apply

class LineageRevisionRerunOptions:
    def __init__(self) -> None:
        self.mode: Optional[str] = None
        self.source_effective_set_version: Optional[int] = None
        self.selected_revisions_json: Any = _JSON_VALUE_UNSET

def with_lineage_revision_rerun_mode(mode: str) -> Callable[[LineageRevisionRerunOptions], None]:
    def apply(options: LineageRevisionRerunOptions) -> None:
        options.mode = mode

    return apply

def with_lineage_revision_rerun_source_effective_set_version(version: int) -> Callable[[LineageRevisionRerunOptions], None]:
    def apply(options: LineageRevisionRerunOptions) -> None:
        options.source_effective_set_version = version

    return apply

def with_lineage_selected_revisions_json(selected_revisions: Any) -> Callable[[LineageRevisionRerunOptions], None]:
    def apply(options: LineageRevisionRerunOptions) -> None:
        options.selected_revisions_json = selected_revisions

    return apply

class AgentSelector:
    def __init__(self, agent_code: str = "", agent_id: str = "", agent_workspace_id: str = "") -> None:
        self.agent_code = agent_code
        self.agent_id = agent_id
        self.agent_workspace_id = agent_workspace_id

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if self.agent_code:
            body["agent_code"] = self.agent_code
        if self.agent_id:
            body["agent_id"] = self.agent_id
        if self.agent_workspace_id:
            body["agent_workspace_id"] = self.agent_workspace_id
        return body

class A2ARequest:
    """JSON-RPC request; no_wait controls local task following and is never sent."""

    def __init__(self, method: str, id_: Any = None, params: Optional[dict[str, Any]] = None, jsonrpc: str = "2.0", model: str = "", *, no_wait: bool = False) -> None:
        self.jsonrpc = jsonrpc
        self.id = id_
        self.method = method
        self.params = params
        self.model = model
        self.no_wait = no_wait

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.id is not None:
            body["id"] = self.id
        if self.params is not None:
            body["params"] = self.params
        if self.model:
            body["model"] = self.model
        return body

class AgentTextMessage:
    def __init__(
        self,
        text: str,
        message_id: str,
        *,
        request_id: Any = None,
        task_id: str = "",
        context_id: str = "",
        session_id: str = "",
        model: str = "",
        idempotency_key: str = "",
        message_metadata: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        configuration: Optional[dict[str, Any]] = None,
    ) -> None:
        self.text = text
        self.message_id = message_id
        self.request_id = request_id
        self.task_id = task_id
        self.context_id = context_id
        self.session_id = session_id
        self.model = model
        self.idempotency_key = idempotency_key
        self.message_metadata = message_metadata
        self.metadata = metadata
        self.configuration = configuration

    def params(self) -> dict[str, Any]:
        if not self.text:
            raise ErrQueryRequired
        if not self.message_id:
            raise ErrMessageIDRequired
        message: dict[str, Any] = {
            "kind": "message",
            "role": "user",
            "messageId": self.message_id,
            "parts": [{"kind": "text", "text": self.text}],
        }
        if self.task_id:
            message["taskId"] = self.task_id
        if self.context_id:
            message["contextId"] = self.context_id
        if self.message_metadata is not None:
            message["metadata"] = self.message_metadata
        params: dict[str, Any] = {"message": message}
        if self.idempotency_key:
            params["idempotencyKey"] = self.idempotency_key
        if self.model:
            params["model"] = self.model
        metadata = self.metadata
        if self.session_id:
            metadata = {**(metadata or {}), "session_id": self.session_id}
        if metadata is not None:
            params["metadata"] = metadata
        if self.configuration is not None:
            params["configuration"] = self.configuration
        return params

class AgentTaskRequest:
    def __init__(self, task_id: str, request_id: Any = None, after_seq: Optional[int] = None) -> None:
        self.task_id = task_id
        self.request_id = request_id
        self.after_seq = after_seq

    def params(self) -> dict[str, Any]:
        if not self.task_id:
            raise ErrTaskIDRequired
        params: dict[str, Any] = {"id": self.task_id}
        if self.after_seq is not None:
            params["afterSeq"] = self.after_seq
        return params

class AgentInputSubmission:
    def __init__(
        self,
        task_id: str,
        turn_id: str,
        answers: dict[str, list[str]],
        *,
        request_id: Any = None,
        call_id: str = "",
    ) -> None:
        self.task_id = task_id
        self.turn_id = turn_id
        self.answers = answers
        self.request_id = request_id
        self.call_id = call_id

    def params(self) -> dict[str, Any]:
        if not self.task_id:
            raise ErrTaskIDRequired
        if not self.turn_id:
            raise ErrTurnIDRequired
        if not self.answers:
            raise ErrAnswersRequired
        answers: dict[str, Any] = {}
        for key, values in self.answers.items():
            if not values:
                raise ErrAnswersRequired
            answers[key] = {"answers": values}
        params: dict[str, Any] = {
            "taskId": self.task_id,
            "turnId": self.turn_id,
            "answers": answers,
        }
        if self.call_id:
            params["callId"] = self.call_id
        return params

class AgentA2ARequest:
    """Selector plus explicit low-level A2A JSON-RPC request; not an AI task-selection source."""

    def __init__(self, selector: AgentSelector, request: A2ARequest) -> None:
        self.selector = selector
        self.request = request

    def to_dict(self) -> dict[str, Any]:
        body = self.selector.to_dict()
        body.update(self.request.to_dict())
        return body

def _validate_agent_a2a_request(req: AgentA2ARequest, stream: bool) -> None:
    if not req.selector.agent_code and not req.selector.agent_id:
        raise ErrAgentRequired
    if not req.request.method:
        raise ErrMethodRequired
    if req.request.jsonrpc and req.request.jsonrpc != "2.0":
        raise ErrJSONRPCInvalid
    if req.request.method in {A2A_METHOD_STREAM, A2A_METHOD_TASKS_RESUBSCRIBE}:
        if not stream:
            raise ErrMethodInvalid
        return
    if req.request.method in {
        A2A_METHOD_SEND,
        A2A_METHOD_TASKS_GET,
        A2A_METHOD_TASKS_CANCEL,
        A2A_METHOD_INPUT_SUBMIT,
    }:
        if stream:
            raise ErrMethodInvalid
        return
    raise ErrMethodInvalid

class WorkspaceMemberListOptions:
    def __init__(self) -> None:
        self.page: Optional[int] = None
        self.page_size: Optional[int] = None
        self.filters: list[dict[str, Any]] = []

def with_member_page(page: int) -> Callable[[WorkspaceMemberListOptions], None]:
    def apply(options: WorkspaceMemberListOptions) -> None:
        options.page = page

    return apply

def with_member_page_size(page_size: int) -> Callable[[WorkspaceMemberListOptions], None]:
    def apply(options: WorkspaceMemberListOptions) -> None:
        options.page_size = page_size

    return apply

def with_member_filter(name: str, *values: str) -> Callable[[WorkspaceMemberListOptions], None]:
    def apply(options: WorkspaceMemberListOptions) -> None:
        options.filters.append({"name": name, "values": list(values)})

    return apply

class CreateUserOptions:
    def __init__(self) -> None:
        self.email: Optional[str] = None
        self.mobile_number: Optional[str] = None
        self.github_login: Optional[str] = None
        self.description: Optional[str] = None
        self.role_ids: Optional[list[int]] = None
        self.tags: Optional[list[dict[str, Any]]] = None
        self.auto_accept: bool = False

def with_user_email(email: str) -> Callable[[CreateUserOptions], None]:
    def apply(options: CreateUserOptions) -> None:
        options.email = email

    return apply

def with_user_github_login(login: str) -> Callable[[CreateUserOptions], None]:
    def apply(options: CreateUserOptions) -> None:
        options.github_login = login

    return apply

def with_user_auto_accept(auto_accept: bool) -> Callable[[CreateUserOptions], None]:
    def apply(options: CreateUserOptions) -> None:
        options.auto_accept = auto_accept

    return apply

def with_user_mobile_number(mobile_number: str) -> Callable[[CreateUserOptions], None]:
    def apply(options: CreateUserOptions) -> None:
        options.mobile_number = mobile_number

    return apply

def with_user_description(description: str) -> Callable[[CreateUserOptions], None]:
    def apply(options: CreateUserOptions) -> None:
        options.description = description

    return apply

def with_user_role_ids(*role_ids: int) -> Callable[[CreateUserOptions], None]:
    def apply(options: CreateUserOptions) -> None:
        if options.role_ids is None:
            options.role_ids = []
        options.role_ids.extend(role_ids)

    return apply

def with_create_user_tag(id_: int, value: str) -> Callable[[CreateUserOptions], None]:
    def apply(options: CreateUserOptions) -> None:
        if options.tags is None:
            options.tags = []
        options.tags.append({"id": id_, "value": value})

    return apply

class UpdateUserOptions:
    def __init__(self) -> None:
        self.tags: list[dict[str, Any]] = []

def with_user_tag(id_: int, value: str) -> Callable[[UpdateUserOptions], None]:
    def apply(options: UpdateUserOptions) -> None:
        options.tags.append({"id": id_, "value": value})

    return apply


AuditLogOptions = QueryOptions

def with_audit_method(method: str) -> Callable[[AuditLogOptions], None]:
    return with_query_param("method", method)

def with_audit_result(result: str) -> Callable[[AuditLogOptions], None]:
    return with_query_param("result", result)

def with_audit_status_code(status_code: int) -> Callable[[AuditLogOptions], None]:
    return with_query_param("status_code", str(status_code))

def with_audit_start_time(start_time: str) -> Callable[[AuditLogOptions], None]:
    return with_query_param("start_time", start_time)

def with_audit_end_time(end_time: str) -> Callable[[AuditLogOptions], None]:
    return with_query_param("end_time", end_time)

def _add_catalog_list_options(body: dict[str, Any], opts: tuple[Callable[[CatalogListOptions], None], ...]) -> None:
    options = CatalogListOptions()
    for opt in opts:
        opt(options)
    if options.include_stats is not None:
        body["include_stats"] = options.include_stats

    if options.page_size is not None:
        body["page_size"] = options.page_size
    if options.page_token is not None:
        body["page_token"] = options.page_token


def _add_catalog_info_options(body: dict[str, Any], opts: tuple[Callable[[CatalogInfoOptions], None], ...]) -> None:
    options = CatalogInfoOptions()
    for opt in opts:
        opt(options)
    if options.description is not None:
        body["description"] = options.description


def _add_create_table_options(body: dict[str, Any], opts: tuple[Callable[[CreateTableOptions], None], ...]) -> None:
    options = CreateTableOptions()
    for opt in opts:
        opt(options)
    if options.comment is not None:
        body["comment"] = options.comment
    if options.data_file_url is not None:
        body["data_file_url"] = options.data_file_url
    if options.column_load_options:
        body["column_load_options"] = options.column_load_options

def _table_lookup_body(table_id: int, opts: tuple[Callable[[TableLookupOptions], None], ...]) -> dict[str, Any]:
    options = TableLookupOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if table_id:
        body["id"] = table_id
    if options.name is not None:
        body["name"] = options.name
    if options.database_id is not None:
        body["database_id"] = options.database_id
    if options.database_name is not None:
        body["database_name"] = options.database_name
    if options.include_stats is not None:
        body["include_stats"] = options.include_stats
    return body

def _table_data_body(table_id: int, opts: tuple[Callable[[TableDataOptions], None], ...]) -> dict[str, Any]:
    options = TableDataOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if table_id:
        body["id"] = table_id
    if options.page is not None:
        body["page"] = options.page
    if options.page_size is not None:
        body["page_size"] = options.page_size
    if options.name is not None:
        body["name"] = options.name
    if options.database_id is not None:
        body["database_id"] = options.database_id
    if options.database_name is not None:
        body["database_name"] = options.database_name
    if options.preview_lines is not None:
        body["preview_lines"] = options.preview_lines
    if options.include_total is not None:
        body["include_total"] = options.include_total
    return body

def _file_list_body(opts: tuple[Callable[[FileListOptions], None], ...]) -> dict[str, Any]:
    options = FileListOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.page is not None:
        body["page"] = options.page
    if options.page_size is not None:
        body["page_size"] = options.page_size
    if options.order is not None:
        body["order"] = options.order
    if options.order_by is not None:
        body["order_by"] = options.order_by
    if options.filters:
        body["filters"] = options.filters
    return body

def _connector_definition_body(
    name: str,
    source_type: int,
    usage_type: int,
    opts: tuple[Callable[[ConnectorDefinitionOptions], None], ...],
) -> dict[str, Any]:
    options = ConnectorDefinitionOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name, "source_type": source_type, "usage_type": usage_type}
    if options.config is not None:
        body["config"] = options.config
    return body

def _connector_update_body(opts: tuple[Callable[[ConnectorUpdateOptions], None], ...]) -> dict[str, Any]:
    options = ConnectorUpdateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.name is not None:
        body["name"] = options.name
    if options.source_type is not None:
        body["source_type"] = options.source_type
    if options.usage_type is not None:
        body["usage_type"] = options.usage_type
    if options.config is not None:
        body["config"] = options.config
    return body

def _connector_preview_body(
    connector_id: str,
    uri: str,
    opts: tuple[Callable[[ConnectorPreviewOptions], None], ...],
) -> dict[str, Any]:
    options = ConnectorPreviewOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"connector_id": connector_id, "uri": uri}
    if options.conn_file_id is not None:
        body["conn_file_id"] = options.conn_file_id
    if options.sheet_name is not None:
        body["sheet_name"] = options.sheet_name
    if options.is_column_name is not None:
        body["isColumnName"] = options.is_column_name
    if options.row_start is not None:
        body["rowStart"] = options.row_start
    if options.column_name_row is not None:
        body["columnNameRow"] = options.column_name_row
    if options.csv is not None:
        body["csv"] = options.csv
    if options.file_type is not None:
        body["file_type"] = options.file_type
    return body

def _connector_db_body(
    connector_id: str,
    database: str,
    opts: tuple[Callable[[ConnectorDBOptions], None], ...],
) -> dict[str, Any]:
    options = ConnectorDBOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"connector_id": connector_id, "database": database}
    if options.schema is not None:
        body["schema"] = options.schema
    return body

def _export_task_list_body(opts: tuple[Callable[[ExportTaskListOptions], None], ...]) -> dict[str, Any]:
    options = ExportTaskListOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.keyword is not None:
        body["keyword"] = options.keyword
    if options.target_category is not None:
        body["target_category"] = options.target_category
    if options.limit is not None:
        body["limit"] = options.limit
    if options.offset is not None:
        body["offset"] = options.offset
    if options.connector_name is not None:
        body["connector_name"] = options.connector_name
    if options.task_id is not None:
        body["task_id"] = options.task_id
    if options.order_by is not None:
        body["order_by"] = options.order_by
    if options.order_direction is not None:
        body["order_direction"] = options.order_direction
    if options.statuses:
        body["statuses"] = options.statuses
    if options.creator is not None:
        body["creator"] = options.creator
    return body

def _export_task_files_body(opts: tuple[Callable[[ExportTaskFilesOptions], None], ...]) -> dict[str, Any]:
    options = ExportTaskFilesOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.limit is not None:
        body["limit"] = options.limit
    if options.offset is not None:
        body["offset"] = options.offset
    if options.statuses:
        body["statuses"] = options.statuses
    if options.order_by is not None:
        body["order_by"] = options.order_by
    if options.order_direction is not None:
        body["order_direction"] = options.order_direction
    return body

def _workbook_list_body(opts: tuple[Callable[[WorkbookListOptions], None], ...]) -> dict[str, Any]:
    options = WorkbookListOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.search is not None:
        body["search"] = options.search
    if options.page_size is not None:
        body["page_size"] = options.page_size
    if options.page_token is not None:
        body["page_token"] = options.page_token
    return body

def _workbook_version_list_body(
    workbook_id: str,
    opts: tuple[Callable[[WorkbookVersionListOptions], None], ...],
) -> dict[str, Any]:
    options = WorkbookVersionListOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"workbook_id": workbook_id}
    if options.page_size is not None:
        body["page_size"] = options.page_size
    if options.page_token is not None:
        body["page_token"] = options.page_token
    return body

def _sql_query_body(query: str, opts: tuple[Callable[[SQLQueryOptions], None], ...]) -> dict[str, Any]:
    options = SQLQueryOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"query": query}
    if options.db_name is not None:
        body["db_name"] = options.db_name
    if options.sql_type is not None:
        body["sql_type"] = options.sql_type
    if options.offset is not None:
        body["offset"] = options.offset
    if options.limit is not None:
        body["limit"] = options.limit
    return body

def _sql_result_body(statement_id: str, opts: tuple[Callable[[SQLResultOptions], None], ...]) -> dict[str, Any]:
    options = SQLResultOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"statement_id": statement_id}
    if options.offset is not None:
        body["offset"] = options.offset
    if options.limit is not None:
        body["limit"] = options.limit
    return body

def _query_history_overview_body(opts: tuple[Callable[[QueryHistoryOverviewOptions], None], ...]) -> dict[str, Any]:
    options = QueryHistoryOverviewOptions()
    for opt in opts:
        opt(options)
    if options.start is None and options.end is None:
        options.start, options.end = _default_query_history_time_range()
    body: dict[str, Any] = {}
    if options.scope:
        body["scope"] = options.scope
    if options.non_user is not None:
        body["non_user"] = options.non_user
    if options.start is not None:
        body["start"] = options.start
    if options.end is not None:
        body["end"] = options.end
    if options.sql_source_type:
        body["sql_source_type"] = options.sql_source_type
    return body

def _query_history_body(opts: tuple[Callable[[QueryHistoryOptions], None], ...]) -> dict[str, Any]:
    options = QueryHistoryOptions()
    for opt in opts:
        opt(options)
    if options.start is None and options.end is None:
        options.start, options.end = _default_query_history_time_range()
    body: dict[str, Any] = {}
    if options.scope:
        body["scope"] = options.scope
    if options.non_user is not None:
        body["non_user"] = options.non_user
    if options.status is not None:
        body["status"] = options.status
    if options.user:
        body["user"] = options.user
    if options.databases:
        body["databases"] = options.databases
    if options.statement is not None:
        body["statement"] = options.statement
    if options.query_type:
        body["query_type"] = options.query_type
    if options.duration is not None:
        body["duration"] = options.duration
    if options.start is not None:
        body["start"] = options.start
    if options.end is not None:
        body["end"] = options.end
    if options.statement_id is not None:
        body["statement_id"] = options.statement_id
    if options.transaction_id is not None:
        body["transaction_id"] = options.transaction_id
    if options.session_id is not None:
        body["session_id"] = options.session_id
    if options.selected_field:
        body["selected_field"] = options.selected_field
    if options.sql_source_type:
        body["sql_source_type"] = options.sql_source_type
    if options.offset is not None:
        body["offset"] = options.offset
    if options.limit is not None:
        body["limit"] = options.limit
    if options.order_by:
        body["order_by"] = options.order_by
    if options.order is not None:
        body["order"] = options.order
    if options.cu is not None:
        body["cu"] = options.cu
    return body



def _default_query_history_time_range(now: Optional[datetime] = None) -> tuple[str, str]:
    end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    start = end - DEFAULT_QUERY_HISTORY_LOOKBACK
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def _query_record_body(statement_id: str, opts: tuple[Callable[[QueryRecordOptions], None], ...]) -> dict[str, Any]:
    options = QueryRecordOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"statement_id": statement_id}
    if options.scope:
        body["scope"] = options.scope
    if options.start is not None:
        body["start"] = options.start
    if options.end is not None:
        body["end"] = options.end
    return body

def _workflow_deploy_body(name: str, dsl_yaml: str, opts: tuple[Callable[[WorkflowDeployOptions], None], ...]) -> dict[str, Any]:
    options = WorkflowDeployOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name, "dsl_yaml": dsl_yaml}
    if options.workflow is not None:
        if dsl_yaml:
            raise ValueError("manual_mowl deployment does not accept dsl_yaml")
        if options.source_type is not None and options.source_type != "manual_mowl":
            raise ValueError("authored workflow source_type must be manual_mowl")
        del body["dsl_yaml"]
        body["source_type"] = "manual_mowl"
        body["workflow"] = options.workflow
    else:
        if options.source_type is not None and options.source_type != "manual_dsl":
            raise ValueError("DSL workflow source_type must be manual_dsl")
        if not dsl_yaml:
            raise ErrDSLYAMLRequired
    if options.workflow_id is not None:
        body["workflow_id"] = options.workflow_id
    if options.description is not None:
        body["description"] = options.description
    if options.execution_mode is not None:
        body["execution_mode"] = options.execution_mode
    if options.cron_expression is not None:
        body["cron_expression"] = options.cron_expression
    if options.source_type is not None:
        body["source_type"] = options.source_type
    if options.input_form is not None:
        # Product workflow v2 deploy binds runtime form as runtime_fields/runtime_layout.
        body["runtime_fields"] = options.input_form
    if options.form_layout is not None:
        body["runtime_layout"] = options.form_layout
    if options.volume_trigger is not None:
        body["volume_trigger"] = options.volume_trigger
    if options.dynamic_service is not None:
        body["dynamic_service"] = options.dynamic_service
    if options.default_values is not None:
        body["default_values"] = options.default_values
    if options.compute_resource_id is not None:
        body["compute_resource_id"] = options.compute_resource_id
    if options.session_id is not None:
        body["session_id"] = options.session_id
    if options.notification is not None:
        body["notification_config"] = options.notification
    return body


def _workflow_mowl_deploy_body(name: str, workflow: dict[str, Any], opts: tuple[Callable[[WorkflowDeployOptions], None], ...]) -> dict[str, Any]:
    options = WorkflowDeployOptions()
    for opt in opts:
        opt(options)
    if options.source_type is not None and options.source_type != "manual_mowl":
        raise ValueError("MOWL workflow source_type must be manual_mowl")
    body: dict[str, Any] = {"name": name, "source_type": "manual_mowl", "workflow": workflow}
    if options.workflow_id is not None:
        body["workflow_id"] = options.workflow_id
    if options.description is not None:
        body["description"] = options.description
    if options.execution_mode is not None:
        body["execution_mode"] = options.execution_mode
    if options.cron_expression is not None:
        body["cron_expression"] = options.cron_expression
    if options.input_form is not None:
        body["runtime_fields"] = options.input_form
    if options.form_layout is not None:
        body["runtime_layout"] = options.form_layout
    if options.volume_trigger is not None:
        body["volume_trigger"] = options.volume_trigger
    if options.dynamic_service is not None:
        body["dynamic_service"] = options.dynamic_service
    if options.default_values is not None:
        body["default_values"] = options.default_values
    if options.compute_resource_id is not None:
        body["compute_resource_id"] = options.compute_resource_id
    if options.session_id is not None:
        body["session_id"] = options.session_id
    if options.notification is not None:
        body["notification_config"] = options.notification
    return body


def _workflow_mowl_template_body(name: str, workflow: dict[str, Any], opts: tuple[Callable[[WorkflowTemplateOptions], None], ...]) -> dict[str, Any]:
    if not name:
        raise ErrNameRequired
    if not workflow:
        raise ValueError("MOWL workflow graph is required")
    body = _workflow_template_body(name, "", opts)
    del body["dsl_yaml"]
    body["definition_format"] = "mowl"
    body["workflow"] = workflow
    return body


def _workflow_candidate_deploy_body(
    name: str,
    accepted_candidate: AcceptedWorkflowCandidate,
    opts: tuple[Callable[[WorkflowDeployOptions], None], ...],
) -> dict[str, Any]:
    if not isinstance(accepted_candidate, AcceptedWorkflowCandidate):
        raise TypeError("accepted workflow candidate is required")
    options = WorkflowDeployOptions()
    for opt in opts:
        opt(options)
    if options.source_type is not None and options.source_type != "nl2dsl":
        raise ValueError("candidate workflow source_type must be nl2dsl")
    if options.input_form is not None or options.form_layout is not None:
        raise ValueError("candidate workflow deploy does not accept runtime form or layout")
    if options.workflow is not None:
        raise ValueError("candidate workflow deploy does not accept client-authored workflow")
    body: dict[str, Any] = {
        "name": name,
        "source_type": "nl2dsl",
        "candidate_ref": accepted_candidate.candidate_ref.to_dict(),
    }
    if options.workflow_id is not None:
        body["workflow_id"] = options.workflow_id
    if options.description is not None:
        body["description"] = options.description
    if options.execution_mode is not None:
        body["execution_mode"] = options.execution_mode
    if options.cron_expression is not None:
        body["cron_expression"] = options.cron_expression
    if options.volume_trigger is not None:
        body["volume_trigger"] = options.volume_trigger
    if options.dynamic_service is not None:
        body["dynamic_service"] = options.dynamic_service
    if options.default_values is not None:
        body["default_values"] = options.default_values
    if options.compute_resource_id is not None:
        body["compute_resource_id"] = options.compute_resource_id
    if options.notification is not None:
        body["notification_config"] = options.notification
    return body

def _workflow_update_body(opts: tuple[Callable[[WorkflowUpdateOptions], None], ...]) -> dict[str, Any]:
    options = WorkflowUpdateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.name is not None:
        body["name"] = options.name
    if options.description is not None:
        body["description"] = options.description
    if options.execution_mode is not None:
        body["execution_mode"] = options.execution_mode
    if options.cron_expression is not None:
        body["cron_expression"] = options.cron_expression
    if options.dsl_yaml is not None:
        body["dsl_yaml"] = options.dsl_yaml
    if options.input_form is not None:
        body["runtime_fields"] = options.input_form
    if options.form_layout is not None:
        body["runtime_layout"] = options.form_layout
    if options.default_values is not None:
        body["default_values"] = options.default_values
    if options.volume_trigger is not None:
        body["volume_trigger"] = options.volume_trigger
    if options.dynamic_service is not None:
        body["dynamic_service"] = options.dynamic_service
    return body

def _workflow_retry_body(opts: tuple[Callable[[WorkflowRerunOptions], None], ...]) -> dict[str, Any]:
    options = WorkflowRerunOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.values is not None:
        body["values"] = options.values
    if options.replace_saved_defaults:
        body["replace_saved_defaults"] = True
    if options.trigger_now is not None:
        body["trigger_now"] = options.trigger_now
    if options.reason is not None:
        raise Error("ErrUnsupportedOperation", "workflow retry does not support reason; use reason with node rerun instead")
    return body

def _workflow_node_rerun_body(
    mode: str,
    source_node_execution_id: str,
    opts: tuple[Callable[[WorkflowRerunOptions], None], ...],
) -> dict[str, Any]:
    options = WorkflowRerunOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"mode": mode, "source_node_execution_id": source_node_execution_id}
    if options.values is not None:
        body["values"] = options.values
    if options.config_override is not None:
        body["config_override"] = options.config_override
    if options.expected_rerun_contract_hash is not None:
        body["expected_rerun_contract_hash"] = options.expected_rerun_contract_hash
    if options.reason is not None:
        body["reason"] = options.reason
    return body

def _workflow_cancel_body(opts: tuple[Callable[[WorkflowCancelOptions], None], ...]) -> dict[str, Any]:
    options = WorkflowCancelOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.reason is not None:
        body["reason"] = options.reason
    return body

def _workflow_scratch_scope_body(request: WorkflowScratchScope) -> dict[str, Any]:
    body = MessageToDict(request, preserving_proto_field_name=True)
    if request.catalog_id:
        body["catalog_id"] = request.catalog_id
    return body

def _custom_operator_body(
    spec: CustomOperatorSpec,
    opts: tuple[Callable[[CustomOperatorOptions], None], ...],
) -> dict[str, Any]:
    options = CustomOperatorOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {
        "name": spec.name,
        "identifier": spec.identifier,
        "description": spec.description,
        "input_schema": spec.input_schema,
        "output_schema": spec.output_schema,
    }
    for name in (
        "node_id", "kind", "language", "handler", "version", "isolation_level", "enabled", "code",
        "source_file_id", "base_node_id", "base_node_version", "binding_config", "catalog_id", "database_id",
    ):
        value = getattr(spec, name)
        if value is not None:
            body[name] = value
    # Explicit function options override spec fields, including explicit empty
    # values, matching the Go SDK and CLI flag-over-JSON behavior.
    if options.node_id is not None:
        body["node_id"] = options.node_id
    if options.kind is not None:
        body["kind"] = options.kind
    if options.language is not None:
        body["language"] = options.language
    if options.handler is not None:
        body["handler"] = options.handler
    if options.version is not None:
        body["version"] = options.version
    if options.isolation_level is not None:
        body["isolation_level"] = options.isolation_level
    if options.enabled is not None:
        body["enabled"] = options.enabled
    if options.code is not None:
        body["code"] = options.code
    if options.source_file_id is not None:
        body["source_file_id"] = options.source_file_id
    if options.base_node_id is not None:
        body["base_node_id"] = options.base_node_id
    if options.base_node_version is not None:
        body["base_node_version"] = options.base_node_version
    if options.binding_config is not None:
        body["binding_config"] = options.binding_config
    if options.catalog_id is not None:
        body["catalog_id"] = options.catalog_id
    if options.database_id is not None:
        body["database_id"] = options.database_id
    return body

def _custom_operator_update_body(opts: tuple[Callable[[CustomOperatorUpdateOptions], None], ...]) -> dict[str, Any]:
    options = CustomOperatorUpdateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.name is not None:
        body["name"] = options.name
    if options.description is not None:
        body["description"] = options.description
    if options.kind is not None:
        body["kind"] = options.kind
    if options.language is not None:
        body["language"] = options.language
    if options.handler is not None:
        body["handler"] = options.handler
    if options.version is not None:
        body["version"] = options.version
    if options.isolation_level is not None:
        body["isolation_level"] = options.isolation_level
    if options.input_schema is not None:
        body["input_schema"] = options.input_schema
    if options.output_schema is not None:
        body["output_schema"] = options.output_schema
    if options.enabled is not None:
        body["enabled"] = options.enabled
    if options.code is not None:
        body["code"] = options.code
    if options.source_file_id is not None:
        body["source_file_id"] = options.source_file_id
    if options.base_node_id is not None:
        body["base_node_id"] = options.base_node_id
    if options.base_node_version is not None:
        body["base_node_version"] = options.base_node_version
    if options.binding_config is not None:
        body["binding_config"] = options.binding_config
    if options.catalog_id is not None:
        body["catalog_id"] = options.catalog_id
    if options.database_id is not None:
        body["database_id"] = options.database_id
    return body

def _workflow_template_body(name: str, dsl_yaml: str, opts: tuple[Callable[[WorkflowTemplateOptions], None], ...]) -> dict[str, Any]:
    options = WorkflowTemplateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name, "dsl_yaml": dsl_yaml}
    if options.template_key is not None:
        body["template_key"] = options.template_key
    if options.description is not None:
        body["description"] = options.description
    if options.input_form is not None:
        body["runtime_fields"] = options.input_form
    if options.is_builtin is not None:
        body["is_builtin"] = options.is_builtin
    return body

def _compute_create_body(
    name: str,
    spec_id: str,
    cpu: int,
    memory_gib: int,
    opts: tuple[Callable[[ComputeCreateOptions], None], ...],
) -> dict[str, Any]:
    options = ComputeCreateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name, "spec_id": spec_id, "cpu": cpu, "memory_gib": memory_gib}
    if options.kind is not None:
        body["kind"] = options.kind
    if options.py_requirements_txt is not None:
        body["py_requirements_txt"] = options.py_requirements_txt
    if options.description is not None:
        body["description"] = options.description
    if options.gpu is not None:
        body["gpu"] = options.gpu
    if options.min_replicas is not None:
        body["min_replicas"] = options.min_replicas
    if options.max_replicas is not None:
        body["max_replicas"] = options.max_replicas
    if options.auto_suspend_minutes is not None:
        body["auto_suspend_minutes"] = options.auto_suspend_minutes
    if options.worker_images is not None:
        body["worker_images"] = [_compute_worker_image_selection_body(image) for image in options.worker_images]
    if options.go_worker_image_id is not None:
        body["go_worker_image_id"] = options.go_worker_image_id
    if options.python_worker_image_id is not None:
        body["python_worker_image_id"] = options.python_worker_image_id
    if options.platform is not None:
        body["platform"] = options.platform
    return body

def _compute_update_body(opts: tuple[Callable[[ComputeUpdateOptions], None], ...]) -> dict[str, Any]:
    options = ComputeUpdateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.kind is not None:
        body["kind"] = options.kind
    if options.py_requirements_txt is not None:
        body["py_requirements_txt"] = options.py_requirements_txt
    if options.name is not None:
        body["name"] = options.name
    if options.description is not None:
        body["description"] = options.description
    if options.spec_id is not None:
        body["spec_id"] = options.spec_id
    if options.cpu is not None:
        body["cpu"] = options.cpu
    if options.memory_gib is not None:
        body["memory_gib"] = options.memory_gib
    if options.gpu is not None:
        body["gpu"] = options.gpu
    if options.min_replicas is not None:
        body["min_replicas"] = options.min_replicas
    if options.max_replicas is not None:
        body["max_replicas"] = options.max_replicas
    if options.auto_suspend_minutes is not None:
        body["auto_suspend_minutes"] = options.auto_suspend_minutes
    if options.worker_images is not None:
        body["worker_images"] = [_compute_worker_image_selection_body(image) for image in options.worker_images]
    if options.go_worker_image_id is not None:
        body["go_worker_image_id"] = options.go_worker_image_id
    if options.python_worker_image_id is not None:
        body["python_worker_image_id"] = options.python_worker_image_id
    if options.platform is not None:
        body["platform"] = options.platform
    return body

def _compute_worker_image_selection_body(image: WorkerImageSelection) -> dict[str, str]:
    worker_type = str(image.worker_type or "").strip()
    kind = str(image.kind or "").strip()
    if worker_type and kind and worker_type != kind:
        raise ErrWorkerTypeConflict
    worker_type = worker_type or kind
    return {
        "worker_type": worker_type,
        "image_id": image.image_id,
        "platform": image.platform,
    }

def _compute_spec_body(
    spec_id: str,
    kind: str,
    family: str,
    family_name: str,
    family_name_en: str,
    cpu_milli: int,
    memory_mib: int,
    opts: tuple[Callable[[ComputeSpecOptions], None], ...],
) -> dict[str, Any]:
    if not spec_id:
        raise ErrSpecIDRequired
    if not kind:
        raise ErrKindRequired
    if not family:
        raise ErrTypeRequired
    if not family_name:
        raise ErrNameRequired
    if not family_name_en:
        raise ErrNameRequired
    if cpu_milli == 0:
        raise ErrCPURequired
    if memory_mib == 0:
        raise ErrMemoryRequired
    options = ComputeSpecOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {
        "id": spec_id,
        "kind": kind,
        "family": family,
        "family_name": family_name,
        "family_name_en": family_name_en,
        "cpu_milli": cpu_milli,
        "memory_mib": memory_mib,
    }
    _apply_compute_spec_options(body, options)
    return body

def _compute_spec_update_body(opts: tuple[Callable[[ComputeSpecUpdateOptions], None], ...]) -> dict[str, Any]:
    options = ComputeSpecUpdateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.kind is not None:
        body["kind"] = options.kind
    if options.family is not None:
        body["family"] = options.family
    if options.family_name is not None:
        body["family_name"] = options.family_name
    if options.family_name_en is not None:
        body["family_name_en"] = options.family_name_en
    if options.cpu_milli is not None:
        body["cpu_milli"] = options.cpu_milli
    if options.memory_mib is not None:
        body["memory_mib"] = options.memory_mib
    _apply_compute_spec_options(body, options)
    return body

def _apply_compute_spec_options(body: dict[str, Any], options: ComputeSpecOptions) -> None:
    if options.node_placement_set:
        body["node_placement"] = options.node_placement
    if options.gpu_count is not None:
        body["gpu_count"] = options.gpu_count
    if options.gpu_memory_mib is not None:
        body["gpu_memory_mib"] = options.gpu_memory_mib
    if options.gpu_cores is not None:
        body["gpu_cores"] = options.gpu_cores
    if options.credit_per_hour is not None:
        body["credit_per_hour"] = options.credit_per_hour
    if options.description is not None:
        body["description"] = options.description
    if options.enabled is not None:
        body["enabled"] = options.enabled

def _provider_backend_body(name: str, opts: tuple[Callable[[ProviderBackendOptions], None], ...]) -> dict[str, Any]:
    options = ProviderBackendOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name}
    if options.provider_type is not None:
        body["type"] = options.provider_type
    if options.reasoning_control_protocol is not None:
        body["reasoning_control_protocol"] = options.reasoning_control_protocol
    if options.api_key is not None:
        body["api_key"] = options.api_key
    if options.address is not None:
        body["address"] = options.address
    if options.timeout_seconds is not None:
        body["timeout_seconds"] = options.timeout_seconds
    if options.models:
        body["models"] = options.models
    # supported_mime_types is parser-backend only; see _apply_supported_mime_types.
    return body


def _apply_supported_mime_types(
    body: dict[str, Any],
    opts: tuple[Callable[["ProviderBackendOptions"], None], ...],
) -> None:
    options = ProviderBackendOptions()
    for opt in opts:
        opt(options)
    if options.supported_mime_types:
        body["supported_mime_types"] = options.supported_mime_types

def _provider_backend_update_body(opts: tuple[Callable[[ProviderBackendUpdateOptions], None], ...]) -> dict[str, Any]:
    options = ProviderBackendUpdateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.name is not None:
        body["name"] = options.name
    if options.api_key is not None:
        body["api_key"] = options.api_key
    if options.reasoning_control_protocol is not None:
        body["reasoning_control_protocol"] = options.reasoning_control_protocol
    if options.timeout_seconds is not None:
        body["timeout_seconds"] = options.timeout_seconds
    if options.models:
        body["models"] = options.models
    if options.supported_mime_types:
        body["supported_mime_types"] = options.supported_mime_types
    return body

def _provider_probe_body(address: str, opts: tuple[Callable[[ProviderBackendOptions], None], ...]) -> dict[str, Any]:
    options = ProviderBackendOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"address": address}
    if options.api_key is not None:
        body["api_key"] = options.api_key
    return body

def _provider_backend_probe_body(opts: tuple[Callable[[ProviderBackendOptions], None], ...]) -> dict[str, Any]:
    options = ProviderBackendOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.api_key is not None:
        body["api_key"] = options.api_key
    return body

def _router_body(opts: tuple[Callable[[RouterOptions], None], ...]) -> dict[str, Any]:
    options = RouterOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.strategy is not None:
        body["strategy"] = options.strategy
    if options.health_check_interval is not None:
        body["health_check_interval"] = options.health_check_interval
    if options.max_retries is not None:
        body["max_retries"] = options.max_retries
    if options.session_affinity is not None:
        body["session_affinity"] = options.session_affinity
    return body

def _data_share_publish_body(
    name: str,
    source_database_id: str,
    table_scope: DataShareScope,
    target_workspace_ids: list[str],
    opts: tuple[Callable[[DataSharePublishOptions], None], ...],
) -> dict[str, Any]:
    options = DataSharePublishOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {
        "name": name,
        "source_database_id": source_database_id,
        "table_scope": _data_share_scope_body(table_scope),
        "target_workspace_ids": target_workspace_ids,
    }
    if options.remark is not None:
        body["remark"] = options.remark
    return body

def _data_share_publish_update_body(opts: tuple[Callable[[DataSharePublishUpdateOptions], None], ...]) -> dict[str, Any]:
    options = DataSharePublishUpdateOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.table_scope is not None:
        _validate_data_share_scope(options.table_scope)
        body["table_scope"] = _data_share_scope_body(options.table_scope)
    if options.target_workspace_ids is not None:
        body["target_workspace_ids"] = options.target_workspace_ids
    if options.remark is not None:
        body["remark"] = options.remark
    return body

def _validate_data_share_scope(scope: Optional[DataShareScope]) -> None:
    if scope is None or scope.mode not in ("all", "selected"):
        raise ErrTableScopeRequired
    object_ids = list(scope.object_ids)
    if scope.mode == "all" and object_ids:
        raise ErrTableScopeRequired
    if scope.mode == "selected" and (not object_ids or any(not object_id for object_id in object_ids) or len(set(object_ids)) != len(object_ids)):
        raise ErrTableScopeRequired

def _data_share_scope_body(scope: DataShareScope) -> dict[str, Any]:
    body: dict[str, Any] = {"mode": scope.mode}
    if scope.object_ids:
        body["object_ids"] = list(scope.object_ids)
    return body

def _semantic_model_body(name: str, opts: tuple[Callable[[SemanticModelOptions], None], ...]) -> dict[str, Any]:
    options = SemanticModelOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name}
    if options.description is not None:
        body["description"] = options.description
    if options.tables is not None:
        body["tables"] = options.tables
    if options.files is not None:
        body["files"] = options.files
    return body

def _semantic_model_with_sources_body(
    name: str,
    sources: list[SemanticModelSourceInput],
    opts: tuple[Callable[[SemanticModelWithSourcesOptions], None], ...],
) -> dict[str, Any]:
    options = SemanticModelWithSourcesOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name, "sources": _semantic_model_sources_body(sources)}
    if options.target_catalog_id is not None:
        body["target_catalog_id"] = options.target_catalog_id
    if options.description is not None:
        body["description"] = options.description
    if options.files is not None:
        body["files"] = options.files
    if options.image_index_enabled is not None:
        body["image_index_enabled"] = options.image_index_enabled
    if options.source_selections is not None:
        body["source_selections"] = _semantic_model_source_selections_body(options.source_selections)
    return body

def _semantic_model_empty_body(
    name: str,
    opts: tuple[Callable[[SemanticModelEmptyOptions], None], ...],
) -> dict[str, Any]:
    options = SemanticModelEmptyOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"name": name}
    if options.description is not None:
        body["description"] = options.description
    if options.image_index_enabled is not None:
        body["image_index_enabled"] = options.image_index_enabled
    return body

def _semantic_model_sources_body(sources: list[SemanticModelSourceInput]) -> list[dict[str, Any]]:
    return [source.body() for source in sources]

def _semantic_model_source_selections_body(selections: list[SemanticModelSourceSelectionInput]) -> list[dict[str, Any]]:
    return [selection.body() for selection in selections]

def _semantic_model_source_governance_body(
    opts: tuple[Callable[[SemanticModelSourceGovernanceOptions], None], ...],
) -> dict[str, Any]:
    options = SemanticModelSourceGovernanceOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.tags is not None:
        body["tags"] = options.tags
    if options.clear_expires_at:
        body["expires_at"] = None
    elif options.expires_at is not None:
        body["expires_at"] = options.expires_at
    if options.enabled is not None:
        body["enabled"] = options.enabled
    if options.force_enabled_after_expiry is not None:
        body["force_enabled_after_expiry"] = options.force_enabled_after_expiry
    return body

def _semantic_model_segment_base_body(base: SemanticModelSegmentBase) -> dict[str, Any]:
    return {
        "if_match": base.if_match,
    }

def _semantic_model_segment_update_body(input: SemanticModelSegmentUpdateInput) -> dict[str, Any]:
    body = _semantic_model_segment_base_body(input.base)
    if input.content is not None:
        body["content"] = input.content
    if input.ocr_text is not None:
        body["ocr_text"] = input.ocr_text
    if input.image_description is not None:
        body["image_description"] = input.image_description
    return body

def _semantic_model_segment_create_body(input: SemanticModelSegmentCreateInput) -> dict[str, Any]:
    body = _semantic_model_segment_base_body(input.base)
    if input.level:
        body["level"] = input.level
    if input.content is not None:
        body["content"] = input.content
    if input.ocr_text is not None:
        body["ocr_text"] = input.ocr_text
    if input.image_description is not None:
        body["image_description"] = input.image_description
    if input.image_file_id:
        body["image_file_id"] = input.image_file_id
    if input.page_image_file_id:
        body["page_image_file_id"] = input.page_image_file_id
    if input.bbox is not None:
        body["bbox"] = input.bbox
    if input.metadata is not None:
        body["metadata"] = input.metadata
    return body

def _semantic_entry_body(entry: SemanticEntryInput) -> dict[str, Any]:
    body: dict[str, Any] = {"kind": entry.kind, "key": entry.key, "spec": entry.spec}
    if entry.tables:
        body["tables"] = entry.tables
    domain = (entry.domain or "").strip()
    if domain:
        body["domain"] = domain
    return body

def _semantic_import_body(entries: list[SemanticEntryInput]) -> dict[str, Any]:
    return {"entries": [_semantic_entry_body(entry) for entry in entries]}

def _validate_semantic_entry(entry: SemanticEntryInput) -> None:
    if not entry.kind:
        raise ErrKindRequired
    if not entry.key:
        raise ErrKeyRequired
    if entry.spec is None:
        raise ErrSpecRequired

def _lineage_revision_body(opts: tuple[Callable[[LineageRevisionOptions], None], ...]) -> dict[str, Any]:
    options = LineageRevisionOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.base_revision_id is not None:
        body["base_revision_id"] = options.base_revision_id
    if options.use_original is not None:
        body["use_original"] = options.use_original
    if options.use_current_effective is not None:
        body["use_current_effective"] = options.use_current_effective
    if options.expected_effective_set_version is not None:
        body["expected_effective_set_version"] = options.expected_effective_set_version
    if options.expected_base_content_hash is not None:
        body["expected_base_content_hash"] = options.expected_base_content_hash
    if options.revision_content_ref is not None:
        body["revision_content_ref"] = options.revision_content_ref
    if options.revision_content_hash is not None:
        body["revision_content_hash"] = options.revision_content_hash
    if options.revision_content_payload is not None:
        body["revision_content_payload"] = options.revision_content_payload
    if options.patch_json is not None:
        body["patch_json"] = options.patch_json
    return body

def _lineage_switch_body(
    switches: list[LineageRevisionSwitch],
    opts: tuple[Callable[[LineageSwitchOptions], None], ...],
) -> dict[str, Any]:
    options = LineageSwitchOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {"switches": [switch.to_dict() for switch in switches]}
    if options.expected_effective_set_version is not None:
        body["expected_effective_set_version"] = options.expected_effective_set_version
    return body

def _lineage_rerun_body(opts: tuple[Callable[[LineageRerunOptions], None], ...]) -> dict[str, Any]:
    options = LineageRerunOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.mode is not None:
        body["mode"] = options.mode
    if options.config_override is not _JSON_VALUE_UNSET:
        body["config_override"] = options.config_override
    if options.input_payload_override is not _JSON_VALUE_UNSET:
        body["input_payload_override"] = options.input_payload_override
    if options.vars_payload_override is not _JSON_VALUE_UNSET:
        body["vars_payload_override"] = options.vars_payload_override
    return body

def _lineage_revision_rerun_body(opts: tuple[Callable[[LineageRevisionRerunOptions], None], ...]) -> dict[str, Any]:
    options = LineageRevisionRerunOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.mode is not None:
        body["mode"] = options.mode
    if options.source_effective_set_version is not None:
        body["source_effective_set_version"] = options.source_effective_set_version
    if options.selected_revisions_json is not _JSON_VALUE_UNSET:
        body["selected_revisions_json"] = options.selected_revisions_json
    return body

def _validate_assigned_default_role(role_ids: list[int] | None, default_role_id: int) -> None:
    if default_role_id <= 0:
        raise ErrDefaultRoleRequired
    if role_ids is None or default_role_id not in role_ids:
        raise ErrDefaultRoleNotAssigned


def _member_list_body(opts: tuple[Callable[[WorkspaceMemberListOptions], None], ...]) -> dict[str, Any]:
    options = WorkspaceMemberListOptions()
    for opt in opts:
        opt(options)
    body: dict[str, Any] = {}
    if options.page is not None:
        body["page"] = options.page
    if options.page_size is not None:
        body["page_size"] = options.page_size
    if options.filters:
        body["filters"] = options.filters
    return body


def _with_list_query(path: str, opts: tuple[Callable[[ListOptions], None], ...]) -> str:
    return _with_query(path, opts)

def _with_query(path: str, opts: tuple[Callable[[QueryOptions], None], ...]) -> str:
    options = ListOptions()
    for opt in opts:
        opt(options)
    if not options.query:
        return path
    pairs: list[tuple[str, str]] = []
    for key, values in options.query.items():
        for value in values:
            pairs.append((key, value))
    return path + "?" + urllib.parse.urlencode(pairs)

def _path_id(value: str | int) -> str:
    if not value:
        raise ErrIDRequired
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise Error(
            "ErrIDInvalid",
            "id must be a string or integer",
            details={"field": "id", "expected": "string_or_integer", "actual_type": type(value).__name__},
        )
    # Match Go url.PathEscape for one URL path segment. Sub-delims and ':', '@'
    # are legal segment characters; slash, query and fragment delimiters escape.
    return urllib.parse.quote(str(value), safe="$&+:=@")

def _agent_resource_path(workspace_id: str, resource: str, tail_path: str) -> str:
    if not workspace_id:
        raise ErrWorkspaceRequired
    if tail_path and not tail_path.startswith("/"):
        raise ErrPathInvalid
    workspace_path = _path_id(workspace_id)
    resource_path = _path_id(resource)
    return f"/workspaces/{workspace_path}/{resource_path}{tail_path}"

def _workflow_run_path(workflow_id: str, execution_id: str) -> tuple[str, str]:
    return _path_id(workflow_id), _path_id(execution_id)

def _workflow_run_result_path(workflow_id: str, execution_id: str) -> tuple[str, str]:
    if not workflow_id:
        raise ErrWorkflowIDRequired
    if not execution_id:
        raise ErrExecutionIDRequired
    return _workflow_run_path(workflow_id, execution_id)

def _workflow_run_node_path(workflow_id: str, execution_id: str, node_key: str) -> tuple[str, str, str]:
    return _path_id(workflow_id), _path_id(execution_id), _path_id(node_key)

def _workflow_rerun_path(workflow_id: str, execution_id: str, rerun_id: str) -> str:
    workflow_path, execution_path = _workflow_run_path(workflow_id, execution_id)
    return f"/workflow/v2/workflow-apps/{workflow_path}/executions/{execution_path}/reruns/{_path_id(rerun_id)}"

def _artifact_block_path(artifact_id: str, block_id: str) -> tuple[str, str]:
    return _path_id(artifact_id), _path_id(block_id)

def _artifact_node_path(artifact_id: str, node_id: str) -> tuple[str, str]:
    return _path_id(artifact_id), _path_id(node_id)

def _artifact_node_block_path(artifact_id: str, node_id: str, block_id: str) -> tuple[str, str, str]:
    artifact_path, node_path = _artifact_node_path(artifact_id, node_id)
    return artifact_path, node_path, _path_id(block_id)

def _semantic_entry_path(model_id: str, entry_id: str) -> tuple[str, str]:
    return _path_id(model_id), _path_id(entry_id)

def _semantic_model_source_path(model_id: str, source_id: str) -> tuple[str, str]:
    return _path_id(model_id), _path_id(source_id)

def _semantic_model_segment_path(model_id: str, source_id: str, segment_id: str) -> tuple[str, str, str]:
    model_path, source_path = _semantic_model_source_path(model_id, source_id)
    return model_path, source_path, _path_id(segment_id)

def _provider_endpoint_path(backend_id: str, endpoint_id: str) -> tuple[str, str]:
    return _path_id(backend_id), _path_id(endpoint_id)

def _drawing_search_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "drawing search response must be an object")
    if "drawings" not in value or "count" not in value or "diagnostics" not in value:
        raise Error("ErrResponseInvalid", "drawing search response missing required fields")
    drawings = value["drawings"]
    count = value["count"]
    diagnostics = value["diagnostics"]
    if not isinstance(drawings, list):
        raise Error("ErrResponseInvalid", "drawing search drawings must be a list")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise Error("ErrResponseInvalid", "drawing search count must be a non-negative integer")
    if not isinstance(diagnostics, dict):
        raise Error("ErrResponseInvalid", "drawing search diagnostics must be an object")
    return value


def _multipart_file_body(boundary: str, field_name: str, filename: str, data: bytes, content_type: str = "application/octet-stream") -> bytes:
    return _multipart_body(boundary, {}, [(field_name, filename, data)], file_content_type=content_type)

def _multipart_body(boundary: str, fields: dict[str, str], files: list[tuple[str, str, bytes]], *, file_content_type: str = "application/octet-stream") -> bytes:
    if not file_content_type or "\r" in file_content_type or "\n" in file_content_type:
        raise ValueError("invalid multipart file content type")
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{quote(name)}"\r\n\r\n'.encode("utf-8"))
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")
    for field_name, filename, data in files:
        if not filename:
            raise Error("ErrFilenameRequired", "filename is required")
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{quote(field_name)}"; filename="{quote(filename)}"\r\n'
                f"Content-Type: {file_content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        body.extend(data)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body)

def _parse_response(raw: bytes, request_id: str = "", *, require_envelope: bool = False, data_nullable: Optional[bool] = None, status: int = 0) -> Any:
    # An explicit data contract requires a value; only nullable contracts allow null.
    # None retains the existing acknowledgement/raw response contract.
    if not raw:
        if require_envelope or data_nullable is not None:
            raise Error("ErrResponseInvalid", "product response is missing envelope", request_id=request_id, status=status)
        return None
    try:
        data = _decode_body(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        if require_envelope:
            raise Error("ErrResponseInvalid", "product response is not a valid envelope", request_id=request_id, status=status) from err
        raise
    if not _is_product_envelope(data):
        if require_envelope:
            raise Error("ErrResponseInvalid", "product response is missing envelope", request_id=request_id, status=status)
        return data
    code = data.get("code")
    if require_envelope:
        valid_code = (isinstance(code, str) and bool(code)) or (isinstance(code, int) and not isinstance(code, bool))
        if not valid_code or any(key in data and not isinstance(data[key], str) for key in ("msg", "message")):
            raise Error("ErrResponseInvalid", "product response is not a valid envelope", request_id=request_id, status=status)
        _response_error_details(data, request_id, status)
    if code not in (None, 0, 200, "0", "200", "OK", ""):
        raise Error(str(code), data.get("msg") or data.get("message") or "", request_id=request_id, status=status, details=_response_error_details(data, request_id, status), data=data.get("data"))
    if require_envelope and data_nullable is None and not isinstance(data.get("data"), dict):
        raise Error("ErrResponseInvalid", "product response envelope missing data", request_id=request_id, status=status)

    if data_nullable is not None and "data" not in data:
        raise Error("ErrResponseInvalid", "product response envelope missing data", request_id=request_id, status=status)
    if data_nullable is False and data["data"] is None:
        raise Error("ErrResponseInvalid", "product response data must not be null", request_id=request_id, status=status)
    return data.get("data")

def _parse_result_response(raw: bytes, request_id: str = "") -> Any:
    try:
        return _parse_response(raw, request_id)
    except json.JSONDecodeError:
        return _decode_result_body(raw)

def _decode_body(raw: bytes) -> Any:
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))

def _decode_result_body(raw: bytes) -> Any:
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text

def _is_product_envelope(data: Any) -> bool:
    if not isinstance(data, dict) or "code" not in data:
        return False
    return any(key in data for key in ("data", "msg", "message", "details"))

def _response_error_details(data: dict[str, Any], request_id: str, status: int = 0) -> dict[str, Any]:
    details = data.get("details")
    if details is None:
        return {}
    if (not isinstance(details, dict)
            or any(not isinstance(key, str) for key in details)
            or any(key in details and not isinstance(details[key], str) for key in ("reason", "domain", "request_id"))):
        raise Error("ErrResponseInvalid", "product error details are invalid", request_id=request_id, status=status)
    return details

def _read_product_response(response: Any) -> bytes:
    try:
        return response.read()
    except TimeoutError as err:
        raise Error("ErrTimeout", "request timeout", request_id=_request_id(response.headers), status=response.status) from err
    except (OSError, http.client.IncompleteRead) as err:
        raise Error("ErrResponseInvalid", "service response could not be read", request_id=_request_id(response.headers), status=response.status) from err

def _open_product_response(request: Any, timeout: float, *, no_redirect: bool = False, opener: Optional[urllib.request.OpenerDirector] = None) -> Any:
    try:
        if opener is not None:
            return opener.open(request, timeout=timeout)
        if no_redirect:
            return urllib.request.build_opener(_NoBrowserRedirect()).open(request, timeout=timeout)
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as err:
        if no_redirect and 300 <= err.code < 400:
            return err
        raise _parse_error(err.code, _read_product_response(err), _request_id(err.headers)) from err
    except (urllib.error.URLError, OSError) as err:
        reason = err.reason if isinstance(err, urllib.error.URLError) else err
        if isinstance(reason, TimeoutError):
            raise Error("ErrTimeout", "request timeout") from err
        raise Error("ErrTransportUnavailable", "no response was received from the service") from err

def _parse_error(status: int, raw: bytes, request_id: str = "") -> Error:
    invalid = Error("ErrResponseInvalid", "product error response is invalid", request_id=request_id, status=status)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return invalid
    if not isinstance(data, dict):
        return invalid
    if "jsonrpc" in data:
        rpc_error = data.get("error")
        rpc_id = data.get("id")
        valid_id = rpc_id is None or isinstance(rpc_id, str) or type(rpc_id) is int or type(rpc_id) is float and math.isfinite(rpc_id)
        if (data["jsonrpc"] != "2.0" or "id" not in data or not valid_id or "result" in data
                or not isinstance(rpc_error, dict) or type(rpc_error.get("code")) is not int
                or not isinstance(rpc_error.get("message"), str) or not rpc_error["message"]):
            return invalid
        return Error(str(rpc_error["code"]), rpc_error["message"], request_id=request_id, status=status, data=rpc_error.get("data"))
    if "code" not in data and "error_code" not in data and data.get("error") == "policy_denied":
        detail = data.get("detail")
        if status != 403 or not isinstance(detail, str) or not detail:
            return invalid
        # This is the proxy's machine reason, not a Product permission error.
        # Raw diagnostics stay bounded and separate from the safe summary.
        details = {"domain": "sandbox_network", "reason": "policy_denied"}
        if len(detail.encode("utf-8", "surrogatepass")) <= 16 * 1024:
            details["detail"] = detail
        else:
            details["detail_omitted"] = True
        return Error("policy_denied", "sandbox network policy denied the request", request_id=request_id, status=status, details=details)
    if "code" not in data and isinstance(data.get("error"), dict):
        nested = data["error"]
        code = nested.get("code")
        message = nested.get("message")
        owner_request_id = nested.get("request_id", "")
        retryable = nested.get("retryable")
        if (not (isinstance(code, str) and code or type(code) is int)
                or not isinstance(message, str) or not message
                or not isinstance(owner_request_id, str)
                or ("retryable" in nested and type(retryable) is not bool)):
            return invalid
        details = {"retryable": str(retryable).lower()} if "retryable" in nested else {}
        return Error(str(code), message, request_id=request_id or owner_request_id, status=status, details=details)
    if any(key in data and not isinstance(data[key], str) for key in ("msg", "message", "error_code", "error_description")):
        return invalid
    if "code" not in data and "error" in data and not isinstance(data["error"], str):
        return invalid
    try:
        details = _response_error_details(data, request_id, status)
    except Error:
        return invalid
    # Preserve the two published non-Product error envelopes explicitly.
    if data.get("error_code"):
        return Error(data["error_code"], data.get("msg") or data.get("message") or "", request_id=request_id, status=status, details=details, data=data.get("data"))
    if "code" not in data and data.get("error"):
        return Error(str(data.get("code") or _status_code(status)), data.get("error_description") or data.get("message") or data["error"], request_id=request_id, status=status, details=details)
    if not _is_product_envelope(data):
        return invalid
    code = data.get("code")
    message = data.get("msg") or data.get("message")
    if (isinstance(code, bool) or not isinstance(code, (str, int, float))
            or code in (0, 200, "0", "200", "OK", "")
            or not isinstance(message, str) or not message):
        return invalid
    if isinstance(code, float):
        if not code.is_integer():
            return invalid
        code = int(code)
    return Error(str(code), message, request_id=request_id, status=status, details=details, data=data.get("data"))


def _request_id(headers: Any) -> str:
    if headers is None:
        return ""
    value = headers.get("X-Request-ID")
    return value if isinstance(value, str) else ""

def _status_code(status: int) -> str:
    if status == 401:
        return "ErrUnauthorized"
    if status == 403:
        return "ErrForbidden"
    if status == 404:
        return "ErrNotFound"
    if status == 409:
        return "ErrConflict"
    return f"HTTP{status}"

def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]

def _channel_instance_record(value: Any) -> ChannelInstanceRecord:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "channel instance response must be an object")
    return ChannelInstanceRecord(value)

def _channel_instance_list_result(value: Any) -> ChannelInstanceListResult:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "channel instance list response must be an object")
    return ChannelInstanceListResult(value)

def _connector_catalog_result(value: Any) -> ConnectorCatalogResult:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "connector catalog response must be an object")
    return ConnectorCatalogResult(value)

def _channel_instance_test_result(value: Any) -> ChannelInstanceTestResult:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "channel instance test response must be an object")
    return ChannelInstanceTestResult(value)

def _ingress_verification_result(value: Any) -> IngressVerificationResult:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "ingress verification response must be an object")
    probe_keys = {"ok", "status", "last_test_status", "last_tested_at"}
    present = probe_keys & value.keys()
    if len(present) == len(probe_keys):
        return IngressVerificationResult(value, None, _channel_instance_test_result(value))
    if present:
        raise Error("ErrResponseInvalid", "ingress verification probe response is missing required fields")
    return IngressVerificationResult(value, _product_message(value, IngressConnection(), "ingress connection data"), None)

def _callback_rule_match(value: Any) -> CallbackRuleMatch:
    if value is None:
        return CallbackRuleMatch()
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "callback rule match must be an object")
    field_equals = value.get("field_equals")
    return CallbackRuleMatch(
        resource_kinds=_string_list(value.get("resource_kinds")),
        event_types=_string_list(value.get("event_types")),
        event_actions=_string_list(value.get("event_actions")),
        field_equals={key: item for key, item in field_equals.items() if isinstance(key, str) and isinstance(item, str)} if isinstance(field_equals, dict) else {},
    )

def _callback_rule_record(value: Any) -> CallbackRuleRecord:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "callback rule response must be an object")
    return CallbackRuleRecord(value)

def _callback_rule_list_result(value: Any) -> CallbackRuleListResult:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "callback rule list response must be an object")
    return CallbackRuleListResult(value)

def _callback_rule_delete_result(value: Any) -> CallbackRuleDeleteResult:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", "callback rule delete response must be an object")
    return CallbackRuleDeleteResult(value)

def _workspace_list_result(value: Any) -> WorkspaceListResult:
    return _product_message(value, WorkspaceListResult(), "workspace list data")

def _workspace_create_result(value: Any) -> WorkspaceCreateResult:
    return _product_message(value, WorkspaceCreateResult(), "workspace create data")

def _workspace_member_invite_result(value: Any) -> WorkspaceMemberInviteResult:
    return _product_message(value, WorkspaceMemberInviteResult(), "workspace member invite data")

def _workspace_claim_result(value: Any) -> WorkspaceClaimResult:
    return _product_message(value, WorkspaceClaimResult(), "workspace claim data")

def _trigger_file_workflow_result(value: Any) -> TriggerFileWorkflowResult:
    return _product_message(value, TriggerFileWorkflowResult(), "trigger file workflow data")

def _upload_file_result(value: Any) -> UploadFileResult:
    return _product_message(value, UploadFileResult(), "upload file data")

def _runtime_artifact_upload_result(value: Any) -> RuntimeArtifactUploadResult:
    return _product_message(value, RuntimeArtifactUploadResult(), "runtime artifact upload data")

def _runtime_image_analysis_result(value: Any) -> RuntimeImageAnalysisResult:
    return _product_message(value, RuntimeImageAnalysisResult(), "runtime image analysis data")

def _file_info_result(value: Any) -> FileInfoResult:
    return _product_message(value, FileInfoResult(), "file info data")

def _create_folder_result(value: Any) -> CreateFolderResult:
    return _product_message(value, CreateFolderResult(), "create folder data")

def _data_tag_list_result(value: Any) -> DataTagListResult:
    return _product_message(value, DataTagListResult(), "data tag list data")

def _path_result(value: Any) -> PathResult:
    return _product_message(value, PathResult(), "path data")

def _url_result(value: Any) -> URLResult:
    return _product_message(value, URLResult(), "url data")

def _bool_data_result(value: Any) -> BoolDataResult:
    return _product_message(value, BoolDataResult(), "bool data")

def _catalog_nl2sql_run_result(value: Any) -> CatalogNL2SQLRunResult:
    return _product_message(value, CatalogNL2SQLRunResult(), "catalog nl2sql run data")

def _publish_summary_result(value: Any) -> PublishSummaryResult:
    return _product_message(value, PublishSummaryResult(), "publish summary data")

def _check_name_result(value: Any) -> CheckNameResult:
    return _product_message(value, CheckNameResult(), "check name data")

def _compute_resource(value: Any) -> ComputeResource:
    return _product_message(value, ComputeResource(), "compute resource data")

def _compute_resource_ownership(value: Any) -> ComputeResourceOwnership:
    return _product_message(value, ComputeResourceOwnership(), "compute resource ownership data")

def _compute_resource_list(value: Any) -> list[ComputeResource]:
    if not isinstance(value, list):
        raise Error("ErrDecodeFailed", "compute resource list data must be an array")
    return [_compute_resource(item) for item in value]

def _compute_resource_worker_list(value: Any) -> list[ComputeResourceWorker]:
    if not isinstance(value, list):
        raise Error("ErrDecodeFailed", "compute resource workers data must be an array")
    result: list[ComputeResourceWorker] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise Error("ErrResponseInvalid", f"compute resource workers data[{index}] must be an object")
        result.append(
            ComputeResourceWorker(
                instance_id=str(item.get("instance_id") or ""),
                worker_type=str(item.get("worker_type") or ""),
                status=str(item.get("status") or ""),
                py_requirements_sha=str(item.get("py_requirements_sha") or ""),
                py_requirements_status=str(item.get("py_requirements_status") or ""),
                py_requirements_error=str(item.get("py_requirements_error") or ""),
            )
        )
    return result

def _compute_py_deps_limits(value: Any) -> ComputePyDepsLimits:
    if not isinstance(value, dict):
        raise Error("ErrDecodeFailed", "py_deps limits data must be an object")
    allowed = value.get("allowed_index_hosts")
    return ComputePyDepsLimits(
        enabled=bool(value.get("enabled")),
        max_bytes=int(value.get("max_bytes") or 0),
        max_lines=int(value.get("max_lines") or 0),
        allowed_index_hosts=[str(host) for host in allowed] if isinstance(allowed, list) else [],
        pip_index_url=str(value.get("pip_index_url") or ""),
        install_timeout_seconds=int(value.get("install_timeout_seconds") or 0),
    )

def _compute_worker_runtime_list(value: Any) -> list[ComputeWorkerRuntime]:
    if not isinstance(value, dict) or set(value) != {"runtimes"}:
        raise Error("ErrResponseInvalid", "compute worker runtime data must contain only runtimes")
    runtimes = value.get("runtimes")
    if not isinstance(runtimes, list):
        raise Error("ErrResponseInvalid", "compute worker runtime runtimes must be an array")
    result = _product_message(value, ComputeWorkerRuntimeListResult(), "compute worker runtime data")
    decoded = list(result.runtimes)
    for index, runtime in enumerate(decoded):
        _validate_compute_worker_runtime(runtime, index)
    return decoded

def _validate_compute_worker_runtime(runtime: ComputeWorkerRuntime, index: int) -> None:
    for field_name, field_value in (
        ("compute_resource_id", runtime.compute_resource_id),
        ("worker_type", runtime.worker_type),
        ("status", runtime.status),
        ("created_at", runtime.created_at),
        ("updated_at", runtime.updated_at),
    ):
        if not field_value or field_value != field_value.strip():
            raise Error("ErrResponseInvalid", f"compute worker runtime runtimes[{index}] has invalid {field_name}")
    if runtime.desired_replicas < 0 or runtime.current_replicas < 0:
        raise Error("ErrResponseInvalid", f"compute worker runtime runtimes[{index}] has negative replicas")

def _admin_compute_resource(value: Any) -> AdminComputeResource:
    return _product_message(value, AdminComputeResource(), "admin compute resource data")

def _admin_compute_resource_list(value: Any) -> list[AdminComputeResource]:
    if not isinstance(value, list):
        raise Error("ErrDecodeFailed", "admin compute resource list data must be an array")
    return [_admin_compute_resource(item) for item in value]

def _admin_compute_resource_list_result(value: Any) -> AdminComputeResourceListResult:
    return _product_message(value, AdminComputeResourceListResult(), "admin compute resource list data")

def _compute_resource_spec(value: Any) -> ComputeResourceSpec:
    return _product_message(value, ComputeResourceSpec(), "compute resource spec data")

def _compute_resource_spec_list(value: Any) -> list[ComputeResourceSpec]:
    if not isinstance(value, list):
        raise Error("ErrDecodeFailed", "compute resource spec list data must be an array")
    return [_compute_resource_spec(item) for item in value]

def _compute_resource_spec_management_permission(value: Any) -> ComputeResourceSpecManagementPermission:
    return _product_message(value, ComputeResourceSpecManagementPermission(), "compute resource spec management permission data")

def _worker_image(value: Any) -> WorkerImage:
    image = _product_message(value, WorkerImage(), "worker image data")
    if not image.worker_type or image.worker_type != image.worker_type.strip():
        raise Error("ErrResponseInvalid", "worker image data has invalid worker_type")
    if not image.image_key or image.image_key != image.image_key.strip():
        raise Error("ErrResponseInvalid", "worker image data has invalid image_key")
    if not image.type or image.type != image.type.strip() or image.type != image.image_key:
        raise Error("ErrResponseInvalid", "worker image data type must equal image_key")
    return image

def _worker_image_list(value: Any) -> list[WorkerImage]:
    if not isinstance(value, list):
        raise Error("ErrDecodeFailed", "worker image list data must be an array")
    return [_worker_image(item) for item in value]

def _compute_delete_preflight_result(value: Any) -> ComputeDeletePreflightResult:
    return _product_message(value, ComputeDeletePreflightResult(), "compute delete preflight data")

def _provider_backend(value: Any) -> ProviderBackend:
    return _product_message(value, ProviderBackend(), "provider backend data")

def _provider_backend_list_result(value: Any) -> ProviderBackendListResult:
    return _product_message(value, ProviderBackendListResult(), "provider backend list data")

def _provider_backend_list_from_array(value: Any) -> ProviderBackendListResult:
    if value is None:
        return ProviderBackendListResult()
    if isinstance(value, dict):
        return _provider_backend_list_result(value)
    if not isinstance(value, list):
        raise Error("ErrDecodeFailed", "provider backend list data must be an array")
    result = ProviderBackendListResult()
    result.backends.extend(_provider_backend(item) for item in value)
    return result

def _provider_endpoint(value: Any) -> ProviderEndpoint:
    return _product_message(value, ProviderEndpoint(), "provider endpoint data")

def _provider_endpoint_list_result(value: Any) -> ProviderEndpointListResult:
    return _product_message(value, ProviderEndpointListResult(), "provider endpoint list data")

def _provider_endpoint_list_from_array(value: Any) -> ProviderEndpointListResult:
    if value is None:
        return ProviderEndpointListResult()
    if isinstance(value, dict):
        for key in ("endpoints", "list", "items", "data"):
            nested = value.get(key)
            if isinstance(nested, list):
                result = ProviderEndpointListResult()
                result.endpoints.extend(_provider_endpoint(item) for item in nested)
                return result
        return _provider_endpoint_list_result(value)
    if not isinstance(value, list):
        raise Error("ErrDecodeFailed", "provider endpoint list data must be an array")
    result = ProviderEndpointListResult()
    result.endpoints.extend(_provider_endpoint(item) for item in value)
    return result

def _provider_router_config(value: Any) -> ProviderRouterConfig:
    return _product_message(value, ProviderRouterConfig(), "provider router data")

def _provider_model_list_result(value: Any) -> ProviderModelListResult:
    return _product_message(value, ProviderModelListResult(), "provider model list data")

def _provider_probe_models_result(value: Any) -> ProviderProbeModelsResult:
    return _product_message(value, ProviderProbeModelsResult(), "provider probe models data")

def _provider_setup_backend_result(value: Any) -> ProviderSetupBackendResult:
    return _product_message(value, ProviderSetupBackendResult(), "provider setup backend data")

def _provider_mutation_result(value: Any) -> ProviderMutationResult:
    return _product_message(value, ProviderMutationResult(), "provider mutation data")

def _data_share_publish(value: Any) -> DataSharePublish:
    return _product_message(value, DataSharePublish(), "data-share publish data")

def _data_share_source_table_list_result(value: Any) -> DataShareSourceTableListResult:
    return _product_message(value, DataShareSourceTableListResult(), "data-share source table list data")

def _data_share_workspace_name_list_result(value: Any) -> DataShareWorkspaceNameListResult:
    return _product_message(value, DataShareWorkspaceNameListResult(), "data-share workspace name list data")

def _data_share_publish_list_result(value: Any) -> DataSharePublishListResult:
    return _product_message(value, DataSharePublishListResult(), "data-share publish list data")

def _data_share_subscription(value: Any) -> DataShareSubscription:
    return _product_message(value, DataShareSubscription(), "data-share subscription data")

def _data_share_subscription_list_result(value: Any) -> DataShareSubscriptionListResult:
    return _product_message(value, DataShareSubscriptionListResult(), "data-share subscription list data")

def _db_list_databases_result(value: Any) -> DBListDatabasesResult:
    return _product_message(value, DBListDatabasesResult(), "connector database list data")

def _connector_validate_result(value: Any) -> ConnectorValidateResult:
    return _product_message(value, ConnectorValidateResult(), "connector validate data")

def _connector(value: Any) -> Connector:
    return _product_message(value, Connector(), "connector data")

def _connector_list_result(value: Any) -> ConnectorListResult:
    return _product_message(value, ConnectorListResult(), "connector list data")

def _connector_file_list_result(value: Any) -> ConnectorFileListResult:
    return _product_message(value, ConnectorFileListResult(), "connector file list data")

def _upload_response(value: Any) -> UploadResponse:
    return _product_message(value, UploadResponse(), "connector upload data")

def _local_upload_result(value: Any) -> LocalUploadResult:
    return _product_message(value, LocalUploadResult(), "connector local upload data")

def _preview_file_result(value: Any) -> PreviewFileResult:
    return _product_message(value, PreviewFileResult(), "connector file preview data")

def _db_list_schemas_result(value: Any) -> DBListSchemasResult:
    return _product_message(value, DBListSchemasResult(), "connector schema list data")

def _db_list_tables_result(value: Any) -> DBListTablesResult:
    return _product_message(value, DBListTablesResult(), "connector table list data")

def _db_source_schema_result(value: Any) -> DBSourceSchemaResult:
    return _product_message(value, DBSourceSchemaResult(), "connector source schema data")

def _structured_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", f"{label} must be an object")
    return value

def _structured_source_list_result(value: Any) -> StructuredSourceListResult:
    return StructuredSourceListResult(_structured_object(value, "structured source list data"))

def _structured_source_databases_result(value: Any) -> StructuredSourceDatabasesResult:
    return StructuredSourceDatabasesResult(_structured_object(value, "structured source database data"))

def _structured_source_schemas_result(value: Any) -> StructuredSourceSchemasResult:
    return StructuredSourceSchemasResult(_structured_object(value, "structured source schema list data"))

def _structured_source_objects_result(value: Any) -> StructuredSourceObjectsResult:
    return StructuredSourceObjectsResult(_structured_object(value, "structured source object data"))

def _structured_source_schema_result(value: Any) -> StructuredSourceSchemaResult:
    return StructuredSourceSchemaResult(_structured_object(value, "structured source schema data"))

def _structured_source_capability_result(value: Any) -> StructuredSourceCapabilityResult:
    return StructuredSourceCapabilityResult(_structured_object(value, "structured source capability data"))

def _structured_source_sample_result(value: Any) -> StructuredSourceSampleResult:
    return StructuredSourceSampleResult(_structured_object(value, "structured source sample data"))

def _structured_backfill_start_resolve_result(value: Any) -> StructuredBackfillStartResolveResult:
    return StructuredBackfillStartResolveResult(_structured_object(value, "structured backfill start data"))

def _file_download_result(value: Any) -> FileDownloadResult:
    return _product_message(value, FileDownloadResult(), "connector file download data")

def _mo_database_list_result(value: Any) -> MODatabaseListResult:
    return _product_message(value, MODatabaseListResult(), "connector mo database list data")

def _mo_database_table_list_result(value: Any) -> MODatabaseTableListResult:
    return _product_message(value, MODatabaseTableListResult(), "connector mo database table list data")

def _mo_check_table_name_result(value: Any) -> MOCheckTableNameResult:
    return _product_message(value, MOCheckTableNameResult(), "connector mo table name check data")

def _mo_column_mapping_result(value: Any) -> MOColumnMappingResult:
    return _product_message(value, MOColumnMappingResult(), "connector mo column mapping data")

def _import_task_list_result(value: Any) -> ImportTaskListResult:
    return _product_message(value, ImportTaskListResult(), "import task list data")

def _import_task_create_result(value: Any) -> ImportTaskCreateResult:
    return _product_message(value, ImportTaskCreateResult(), "import task create data")

def _import_task_info_result(value: Any) -> ImportTaskInfoResult:
    return _product_message(value, ImportTaskInfoResult(), "import task info data")

def _import_task_file_list_result(value: Any) -> ImportTaskFileListResult:
    return _product_message(value, ImportTaskFileListResult(), "import task file list data")

def _import_task_run_list_result(value: Any) -> ImportTaskRunListResult:
    return _product_message(value, ImportTaskRunListResult(), "import task run list data")

def _export_task(value: Any) -> ExportTask:
    return _product_message(value, ExportTask(), "export task data")


def _export_task_info(value: Any) -> ExportTaskInfo:
    return _product_message(value, ExportTaskInfo(), "export task info data")

def _export_task_list_result(value: Any) -> ExportTaskListResult:
    return _product_message(value, ExportTaskListResult(), "export task list data")

def _export_task_files_result(value: Any) -> ExportTaskFilesResult:
    return _product_message(value, ExportTaskFilesResult(), "export task files data")

def _export_task_state_result(value: Any) -> ExportTaskStateResult:
    return _product_message(value, ExportTaskStateResult(), "export task state data")

def _sql_workbook(value: Any) -> SQLWorkbook:
    return _product_message(value, SQLWorkbook(), "sql workbook data")

def _sql_workbook_list_result(value: Any) -> SQLWorkbookListResult:
    return _product_message(value, SQLWorkbookListResult(), "sql workbook list data")

def _sql_workbook_detail_result(value: Any) -> SQLWorkbookDetailResult:
    return _product_message(value, SQLWorkbookDetailResult(), "sql workbook detail data")

def _sql_workbook_version_list_result(value: Any) -> SQLWorkbookVersionListResult:
    return _product_message(value, SQLWorkbookVersionListResult(), "sql workbook version list data")

def _sql_workbook_version_create_result(value: Any) -> SQLWorkbookVersionCreateResult:
    return _product_message(value, SQLWorkbookVersionCreateResult(), "sql workbook version create data")

def _sql_database_list_result(value: Any) -> SQLDatabaseListResult:
    return _product_message(value, SQLDatabaseListResult(), "sql database list data")

def _sql_database_tree_result(value: Any) -> SQLDatabaseTreeResult:
    return _product_message(value, SQLDatabaseTreeResult(), "sql database tree data")

def _sql_database_tables_result(value: Any) -> SQLDatabaseTablesResult:
    return _product_message(value, SQLDatabaseTablesResult(), "sql database tables data")

def _sql_table_info_result(value: Any) -> SQLTableInfoResult:
    return _product_message(value, SQLTableInfoResult(), "sql table info data")

def _sql_table_columns_result(value: Any) -> SQLTableColumnsResult:
    return _product_message(value, SQLTableColumnsResult(), "sql table columns data")

def _sql_table_ddl_result(value: Any) -> SQLTableDDLResult:
    return _product_message(value, SQLTableDDLResult(), "sql table ddl data")

def _sql_query_start_result(value: Any) -> SQLQueryStartResult:
    return _product_message(value, SQLQueryStartResult(), "sql query start data")

def _sql_query_operation(value: Any) -> SQLQueryOperation:
    return _product_message(value, SQLQueryOperation(), "sql query operation data")

def _sql_query_result(value: Any) -> SQLQueryResult:
    return _product_message(value, SQLQueryResult(), "sql query result data")

def _sql_query_history_overview_result(value: Any) -> SQLQueryHistoryOverviewResult:
    return _product_message(value, SQLQueryHistoryOverviewResult(), "sql query history overview data")

def _sql_query_history_result(value: Any) -> SQLQueryHistoryResult:
    return _product_message(value, SQLQueryHistoryResult(), "sql query history data")

def _sql_statement_record(value: Any) -> SQLStatementRecord:
    return _product_message(value, SQLStatementRecord(), "sql statement record data")

def _sql_query_profile_result(value: Any) -> SQLQueryProfileResult:
    return _product_message(value, SQLQueryProfileResult(), "sql query profile data")

def _workitem_api_service_envelope(value: Any) -> WorkitemAPIServiceEnvelope:
    return _product_message(value, WorkitemAPIServiceEnvelope(), "workitem api service data")

def _workitem_api_service_invoke_envelope(value: Any) -> WorkitemAPIServiceInvokeEnvelope:
    return _product_message(value, WorkitemAPIServiceInvokeEnvelope(), "workitem api service invoke data")

def _dynamic_service_invoke_result(value: Any) -> DynamicServiceInvokeResult:
    return DynamicServiceInvokeResult(value)

def _custom_operator(value: Any) -> CustomOperator:
    return _product_message(value, CustomOperator(), "custom operator data")

def _custom_operator_list_envelope(value: Any) -> CustomOperatorListEnvelope:
    return _product_message(value, CustomOperatorListEnvelope(), "custom operator list data")

def _custom_operator_code_envelope(value: Any) -> CustomOperatorCodeEnvelope:
    return _product_message(value, CustomOperatorCodeEnvelope(), "custom operator code data")

def _custom_operator_source_envelope(value: Any) -> CustomOperatorSourceEnvelope:
    return _product_message(value, CustomOperatorSourceEnvelope(), "custom operator source data")

def _custom_operator_test_envelope(value: Any) -> CustomOperatorTestEnvelope:
    return _product_message(value, CustomOperatorTestEnvelope(), "custom operator test data")

def _workflow_candidate_acceptance(value: Any) -> WorkflowCandidateAcceptance:
    return _product_message(value, WorkflowCandidateAcceptance(), "workflow candidate acceptance data")

def _workflow_deployment_envelope(value: Any) -> WorkflowDeploymentEnvelope:
    return _product_message(value, WorkflowDeploymentEnvelope(), "workflow deployment data")

def _workflow_list_envelope(value: Any) -> WorkflowListEnvelope:
    return _product_message(value, WorkflowListEnvelope(), "workflow list data")

def _workflow_envelope(value: Any) -> WorkflowEnvelope:
    return _product_message(value, WorkflowEnvelope(), "workflow data")

def _workflow_delete_envelope(value: Any) -> WorkflowDeleteEnvelope:
    return _product_message(value, WorkflowDeleteEnvelope(), "workflow delete data")

def _workflow_template_list(value: Any) -> WorkflowTemplateList:
    if not isinstance(value, list):
        raise Error("ErrResponseInvalid", "workflow template list data must be a list")
    out = WorkflowTemplateList()
    for item in value:
        out.templates.append(_workflow_template(item))
    return out

def _workflow_template(value: Any) -> WorkflowTemplate:
    return _product_message(value, WorkflowTemplate(), "workflow template data")

def _workflow_template_delete_envelope(value: Any) -> WorkflowTemplateDeleteEnvelope:
    return _product_message(value, WorkflowTemplateDeleteEnvelope(), "workflow template delete data")

def _lineage_overview(value: Any) -> LineageOverview:
    return _product_message(value, LineageOverview(), "lineage overview data")

def _lineage_artifact_node(value: Any) -> LineageArtifactNode:
    return _product_message(value, LineageArtifactNode(), "lineage artifact node data")

def _lineage_output_blocks(value: Any) -> LineageOutputBlocks:
    return _product_message(value, LineageOutputBlocks(), "lineage output blocks data")

def _lineage_block_revisions(value: Any) -> LineageBlockRevisions:
    return _product_message(value, LineageBlockRevisions(), "lineage block revisions data")

def _lineage_block_revision(value: Any) -> LineageBlockRevision:
    return _product_message(value, LineageBlockRevision(), "lineage block revision data")

def _lineage_effective_revisions(value: Any) -> LineageEffectiveRevisions:
    return _product_message(value, LineageEffectiveRevisions(), "lineage effective revisions data")

def _lineage_rerun(value: Any) -> LineageRerun:
    return _product_message(value, LineageRerun(), "lineage rerun data")

def _workflow_run_envelope(value: Any) -> WorkflowRunEnvelope:
    return _product_message(value, WorkflowRunEnvelope(), "workflow run data")

def _workflow_batch_retry_envelope(value: Any) -> WorkflowBatchRetryEnvelope:
    return _product_message(value, WorkflowBatchRetryEnvelope(), "workflow batch retry data")

def _workflow_execution_list_envelope(value: Any) -> WorkflowExecutionListEnvelope:
    return _product_message(value, WorkflowExecutionListEnvelope(), "workflow execution list data")

def _workflow_execution_envelope(value: Any) -> WorkflowExecutionEnvelope:
    return _product_message(value, WorkflowExecutionEnvelope(), "workflow execution data")

def _workflow_execution_result_envelope(value: Any) -> WorkflowExecutionResultEnvelope:
    return _product_message(value, WorkflowExecutionResultEnvelope(), "workflow execution result data")

def _workflow_file_execution_list(value: Any) -> WorkflowFileExecutionList:
    return _product_message(value, WorkflowFileExecutionList(), "workflow file execution data")

def _workitem_catalog_list(value: Any) -> WorkitemCatalogList:
    return _product_message(value, WorkitemCatalogList(), "workitem catalog data")

def _workitem_catalog_detail(value: Any) -> WorkitemCatalogDetail:
    return _product_message({"item": value}, WorkitemCatalogDetail(), "workitem catalog item data")

def _workflow_import_context_envelope(value: Any) -> WorkflowImportContextEnvelope:
    return _product_message(value, WorkflowImportContextEnvelope(), "workflow import context data")

def _workflow_import_file_list_envelope(value: Any) -> WorkflowImportFileListEnvelope:
    return _product_message(value, WorkflowImportFileListEnvelope(), "workflow import file list data")

def _workflow_execution_node_detail_envelope(value: Any) -> WorkflowExecutionNodeDetailEnvelope:
    return _product_message(value, WorkflowExecutionNodeDetailEnvelope(), "workflow execution node detail data")

def _workflow_rerun_plan_envelope(value: Any) -> WorkflowRerunPlanEnvelope:
    return _product_message(value, WorkflowRerunPlanEnvelope(), "workflow rerun plan data")

def _workflow_rerun_envelope(value: Any) -> WorkflowRerunEnvelope:
    return _product_message(value, WorkflowRerunEnvelope(), "workflow rerun data")

def _workflow_rerun_branch_list_envelope(value: Any) -> WorkflowRerunBranchListEnvelope:
    return _product_message(value, WorkflowRerunBranchListEnvelope(), "workflow rerun branch list data")

def _semantic_model_info(value: Any) -> SemanticModelInfo:
    return _product_message(value, SemanticModelInfo(), "semantic model data")

def _semantic_model_list_result(value: Any) -> SemanticModelListResult:
    return _product_message(value, SemanticModelListResult(), "semantic model list data")

def _semantic_model_tag_list_result(value: Any) -> SemanticModelTagListResult:
    return _product_message(value, SemanticModelTagListResult(), "semantic model tag list data")

def _semantic_entry(value: Any) -> SemanticEntry:
    return _product_message(value, SemanticEntry(), "semantic entry data")

def _semantic_entry_list_result(value: Any) -> SemanticEntryListResult:
    return _product_message(value, SemanticEntryListResult(), "semantic entry list data")

def _semantic_mutation_result(value: Any) -> SemanticMutationResult:
    return _product_message(value, SemanticMutationResult(), "semantic mutation data")

def _semantic_import_result(value: Any) -> SemanticImportResult:
    return _product_message(value, SemanticImportResult(), "semantic import data")

def _semantic_export_result(value: Any) -> SemanticExportResult:
    return _product_message(value, SemanticExportResult(), "semantic export data")

def _semantic_validate_result(value: Any) -> SemanticValidateResult:
    return _product_message(value, SemanticValidateResult(), "semantic validate data")

def _semantic_model_with_sources_result(value: Any) -> SemanticModelWithSourcesResult:
    return _product_message(value, SemanticModelWithSourcesResult(), "semantic model with sources data")

def _semantic_model_empty_result(value: Any) -> SemanticModelEmptyResult:
    return _product_message(value, SemanticModelEmptyResult(), "empty semantic model data")

def _semantic_model_append_sources_result(value: Any) -> SemanticModelAppendSourcesResult:
    return _product_message(value, SemanticModelAppendSourcesResult(), "semantic model append sources data")

def _semantic_model_source_list_result(value: Any) -> SemanticModelSourceListResult:
    return _product_message(value, SemanticModelSourceListResult(), "semantic model source list data")

def _semantic_model_source_selection_preview_result(value: Any) -> SemanticModelSourceSelectionPreviewResult:
    return _product_message(value, SemanticModelSourceSelectionPreviewResult(), "semantic model source selection preview data")

def _semantic_model_source_document(value: Any) -> SemanticModelSourceDocument:
    return _product_message(value, SemanticModelSourceDocument(), "semantic model source document data")

def _semantic_model_source_governance_result(value: Any) -> SemanticModelSourceGovernanceResult:
    return _product_message(value, SemanticModelSourceGovernanceResult(), "semantic model source governance data")

def _semantic_model_segment_mutation_result(value: Any) -> SemanticModelSegmentMutationResult:
    return _product_message(value, SemanticModelSegmentMutationResult(), "semantic model segment mutation data")

def _semantic_model_source_job_list_result(value: Any) -> SemanticModelSourceJobListResult:
    return _product_message(value, SemanticModelSourceJobListResult(), "semantic model source job list data")

def _semantic_model_source_existence_result(value: Any) -> SemanticModelSourceExistenceResult:
    return _product_message(value, SemanticModelSourceExistenceResult(), "semantic model source existence data")

def _health_result(value: Any) -> HealthResult:
    return _product_message(value, HealthResult(), "health data")

def _memory_list_result(value: Any) -> MemoryListResult:
    return _product_message(value, MemoryListResult(), "memory list data")

def _consumer_profile_render_result(value: Any) -> ConsumerProfileRenderResult:
    return _product_message(value, ConsumerProfileRenderResult(), "consumer profile render data")

def _catalog_tree_result(value: Any) -> CatalogTreeResult:
    return _product_message(value, CatalogTreeResult(), "catalog tree data")

def _catalog_list_result(value: Any) -> CatalogListResult:
    return _product_message(value, CatalogListResult(), "catalog list data")

def _id_result(value: Any) -> IDResult:
    return _product_message(value, IDResult(), "id data")

def _catalog_info_result(value: Any) -> CatalogInfoResult:
    return _product_message(value, CatalogInfoResult(), "catalog info data")

def _database_list_result(value: Any) -> DatabaseListResult:
    return _product_message(value, DatabaseListResult(), "database list data")

def _database_info_result(value: Any) -> DatabaseInfoResult:
    return _product_message(value, DatabaseInfoResult(), "database info data")

def _database_children_result(value: Any) -> DatabaseChildrenResult:
    return _product_message(value, DatabaseChildrenResult(), "database children data")

def _database_table_leaves_result(value: Any) -> DatabaseTableLeavesResult:
    return _product_message(value, DatabaseTableLeavesResult(), "database table leaves data")


def _data_dashboard_table_search_result(value: Any) -> DataDashboardTableSearchResult:
    return _product_message(value, DataDashboardTableSearchResult(), "data dashboard table search data")

def _volume_info_result(value: Any) -> VolumeInfoResult:
    return _product_message(value, VolumeInfoResult(), "volume info data")

def _catalog_create_table_result(value: Any) -> CatalogCreateTableResult:
    return _product_message(value, CatalogCreateTableResult(), "catalog create table data")

def _catalog_table_info_result(value: Any) -> CatalogTableInfoResult:
    return _product_message(value, CatalogTableInfoResult(), "catalog table info data")

def _catalog_multi_table_info_result(value: Any) -> CatalogMultiTableInfoResult:
    return _product_message(value, CatalogMultiTableInfoResult(), "catalog multi table info data")

def _catalog_table_data_result(value: Any) -> CatalogTableDataResult:
    return _product_message(value, CatalogTableDataResult(), "catalog table data")

def _catalog_table_overview_result(value: Any) -> CatalogTableOverviewResult:
    return _product_message(value, CatalogTableOverviewResult(), "catalog table overview data")

def _catalog_file_list_result(value: Any) -> CatalogFileListResult:
    return _product_message(value, CatalogFileListResult(), "catalog file list data")

def _catalog_data_asset_resolve_result(value: Any) -> CatalogDataAssetResolveResult:
    return _product_message(value, CatalogDataAssetResolveResult(), "catalog data asset resolve data")

def _catalog_batch_get_data_assets_result(value: Any) -> CatalogBatchGetDataAssetsResult:
    return _product_message(value, CatalogBatchGetDataAssetsResult(), "catalog batch get data assets data")

def _catalog_file_artifact_result(value: Any) -> CatalogFileArtifactResult:
    return _product_message(value, CatalogFileArtifactResult(), "catalog file artifact data")

def _catalog_batch_resolve_file_artifacts_result(value: Any) -> CatalogBatchResolveFileArtifactsResult:
    return _product_message(value, CatalogBatchResolveFileArtifactsResult(), "catalog batch resolve file artifacts data")

def _db_connection_result(value: Any) -> DBConnectionResult:
    return _product_message(value, DBConnectionResult(), "db connection data")

def _current_workspace_principal_result(value: Any) -> CurrentWorkspacePrincipalResult:
    return _product_message(value, CurrentWorkspacePrincipalResult(), "current workspace principal data")


def _workspace_member_list_result(value: Any) -> WorkspaceMemberListResult:
    return _product_message(value, WorkspaceMemberListResult(), "workspace member list data")


def _workspace_member(value: Any) -> WorkspaceMember:
    return _product_message(value, WorkspaceMember(), "workspace member data")

def _audit_log_list_result(value: Any) -> AuditLogListResult:
    return _product_message(value, AuditLogListResult(), "audit log list data")

def _audit_log_overview_result(value: Any) -> AuditLogOverviewResult:
    return _product_message(value, AuditLogOverviewResult(), "audit log overview data")

def _require_iam_request(request: Message, expected_type: type[Message]) -> None:
    if not isinstance(request, expected_type):
        raise Error("ErrRequestRequired", f"{expected_type.__name__} is required")

def _iam_permission_schema_result(value: Any) -> IAMPermissionSchemaResult:
    return _product_message(value, IAMPermissionSchemaResult(), "IAM permission schema data")

def _iam_role_list_result(value: Any) -> IAMRoleListResult:
    return _product_message(value, IAMRoleListResult(), "IAM role list data")


def iam_binding_version_number(result: IAMUserRoleBindingsResult) -> int:
    """Return the numeric CAS version from a typed canonical binding read.

    The raw ``binding-vN`` token remains on ``result.binding_version`` for
    diagnostics. Invalid or non-canonical values are rejected instead of
    silently selecting a CAS version.
    """
    if not isinstance(result, IAMUserRoleBindingsResult):
        raise ErrIAMBindingVersionInvalid
    raw = result.binding_version
    prefix = "binding-v"
    suffix = raw[len(prefix):] if raw.startswith(prefix) else ""
    if (
        not suffix
        or not suffix.isascii()
        or not suffix.isdigit()
        or (len(suffix) > 1 and suffix[0] == "0")
    ):
        raise ErrIAMBindingVersionInvalid
    version = int(suffix)
    if version > (1 << 63) - 1:
        raise ErrIAMBindingVersionInvalid
    return version


def _iam_user_role_bindings_result(value: Any) -> IAMUserRoleBindingsResult:
    return _product_message(value, IAMUserRoleBindingsResult(), "IAM user role bindings data")

def _iam_user_role_bindings_mutation_result(value: Any) -> IAMUserRoleBindingsMutationResult:
    return _product_message(value, IAMUserRoleBindingsMutationResult(), "IAM user role bindings mutation data")

def _iam_role_create_result(value: Any) -> IAMRoleCreateResult:
    return _product_message(value, IAMRoleCreateResult(), "IAM role create data")

def _iam_role_mutation_result(value: Any) -> IAMRoleMutationResult:
    return _product_message(value, IAMRoleMutationResult(), "IAM role mutation data")

def _iam_role_delete_impact_result(value: Any) -> IAMRoleDeleteImpactResult:
    return _product_message(value, IAMRoleDeleteImpactResult(), "IAM role delete impact data")

def _iam_role_permission_view_result(value: Any) -> IAMRolePermissionViewResult:
    return _product_message(value, IAMRolePermissionViewResult(), "IAM role permission view data")

def _iam_object_grants_mutation_result(value: Any) -> IAMObjectGrantsMutationResult:
    return _product_message(value, IAMObjectGrantsMutationResult(), "IAM object grants mutation data")

def _iam_object_permission_view_result(value: Any) -> IAMObjectPermissionViewResult:
    return _product_message(value, IAMObjectPermissionViewResult(), "IAM object permission view data")

def _iam_data_privilege_view_result(value: Any) -> IAMDataPrivilegeViewResult:
    return _product_message(value, IAMDataPrivilegeViewResult(), "IAM data privilege view data")

def _iam_data_privilege_validation_result(value: Any) -> IAMDataPrivilegeValidationResult:
    return _product_message(value, IAMDataPrivilegeValidationResult(), "IAM data privilege validation data")

def _iam_data_privilege_operation_result(value: Any) -> IAMDataPrivilegeOperationResult:
    return _product_message(value, IAMDataPrivilegeOperationResult(), "IAM data privilege operation data")

def _agent_card_result(value: Any) -> AgentCardResult:
    return AgentCardResult(json=json.dumps(value, separators=(",", ":")))

def _plugin_bindings(bindings: Any) -> dict[str, Any]:
    return {name: json_format.MessageToDict(binding, preserving_proto_field_name=True) for name, binding in bindings.items()}

def _agent_a2a_result(value: Any) -> AgentA2AResult:
    return AgentA2AResult(json=json.dumps(value, separators=(",", ":")))

def _product_message(value: Any, message: Message, label: str) -> Any:
    if not isinstance(value, dict):
        raise Error("ErrResponseInvalid", f"{label} must be an object")
    try:
        json_format.ParseDict(value, message, ignore_unknown_fields=False)
    except (json_format.ParseError, TypeError, ValueError) as err:
        raise Error("ErrResponseInvalid", f"{label} invalid: {err}") from err
    return message

def _dashboard_request_body(request: Any) -> dict[str, Any]:
    body = MessageToDict(request, preserving_proto_field_name=True)
    if isinstance(request, DataDashboardMutationRequest) and request.sources:
        body["sources"] = [{"table_id": source.table_id} if source.table_id else {} for source in request.sources]
    elif isinstance(request, DataDashboardChartOrderRequest):
        # The owner requires chart_ids to be an array, including an empty one.
        body["chart_ids"] = list(request.chart_ids)
    return body

class _NoBrowserRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None

class ConversationService(WorkspaceScopedService):
    def create_ui_session(self,request: ConversationUISessionRequest) -> ConversationSession:
        if not isinstance(request,ConversationUISessionRequest): raise TypeError("request must be ConversationUISessionRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST","/sessions",body),ConversationSession(),"conversation result")

    def update_ui_session(self,session_id: int,request: ConversationUISessionRequest) -> ConversationSession:
        if not isinstance(request,ConversationUISessionRequest): raise TypeError("request must be ConversationUISessionRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("PUT","/sessions" + "/"+str(session_id),body),ConversationSession(),"conversation result")

    def get_ui_session(self,session_id: int) -> ConversationSession:
        return _product_message(self._request("GET","/sessions/"+str(session_id),None),ConversationSession(),"conversation result")

    def delete_ui_session(self,session_id: int) -> ConversationMutation:
        return _product_message(self._request("DELETE","/sessions/"+str(session_id)+"",None),ConversationMutation(),"conversation result")

    def pin_ui_session(self,session_id: int) -> ConversationMutation:
        return _product_message(self._request("PUT","/sessions/"+str(session_id)+"/pin",None),ConversationMutation(),"conversation result")

    def unpin_ui_session(self,session_id: int) -> ConversationMutation:
        return _product_message(self._request("DELETE","/sessions/"+str(session_id)+"/pin",None),ConversationMutation(),"conversation result")

    def list_ui_sessions(self,request: ConversationUISessionListRequest) -> ConversationSessionList:
        if not isinstance(request,ConversationUISessionListRequest): raise TypeError("request must be ConversationUISessionListRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST","/sessions/list",body),ConversationSessionList(),"conversation result")

    def list_pinned_ui_sessions(self,request: ConversationUISessionListRequest) -> ConversationSessionList:
        if not isinstance(request,ConversationUISessionListRequest): raise TypeError("request must be ConversationUISessionListRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST","/sessions/pinned/list",body),ConversationSessionList(),"conversation result")

    def list_unpinned_ui_sessions(self,request: ConversationUISessionListRequest) -> ConversationSessionList:
        if not isinstance(request,ConversationUISessionListRequest): raise TypeError("request must be ConversationUISessionListRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST","/sessions/unpinned/list",body),ConversationSessionList(),"conversation result")

    def list_ui_messages(self,request: ConversationUIMessageListRequest) -> list[ConversationUIMessage]:
        if not isinstance(request,ConversationUIMessageListRequest): raise TypeError("request must be ConversationUIMessageListRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        if request.session_id:
            body["session_id"] = request.session_id
        if request.after:
            body["after"] = request.after
        return [_product_message(item,ConversationUIMessage(),"conversation message") for item in self._request("POST","/messages/session/list",body)]

    def get_ui_message(self,message_id: int) -> ConversationUIMessage:
        return _product_message(self._request("GET","/messages/"+str(message_id)+"",None),ConversationUIMessage(),"conversation result")

    def like_ui_message(self,message_id: int) -> ConversationUIMessage:
        return _product_message(self._request("PUT","/messages/"+str(message_id)+"/like",None),ConversationUIMessage(),"conversation result")

    def dislike_ui_message(self,message_id: int) -> ConversationUIMessage:
        return _product_message(self._request("PUT","/messages/"+str(message_id)+"/dislike",None),ConversationUIMessage(),"conversation result")

    def latest_ui_message_id(self,session_id: int) -> ConversationLatestMessageID:
        return _product_message(self._request("GET","/messages/sessions/"+str(session_id)+"/latest",None),ConversationLatestMessageID(),"conversation result")

    def create_session(self,request: ConversationWorkspaceSessionRequest) -> ConversationSession:
        if not isinstance(request,ConversationWorkspaceSessionRequest): raise TypeError("request must be ConversationWorkspaceSessionRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions",body),ConversationSession(),"conversation result")

    def list_sessions(self,*options: Callable[["QueryOptions"], None]) -> ConversationSessionList:
        return _product_message(self._request("GET",_with_query(f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions",options),None),ConversationSessionList(),"conversation result")

    def get_session(self,session_id: int) -> ConversationSession:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"",None),ConversationSession(),"conversation result")

    def update_session(self,session_id: int,request: ConversationWorkspaceSessionRequest) -> ConversationSession:
        if not isinstance(request,ConversationWorkspaceSessionRequest): raise TypeError("request must be ConversationWorkspaceSessionRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"",body),ConversationSession(),"conversation result")

    def delete_session(self,session_id: int) -> None:
        self._request("DELETE",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"",None)

    def modify_response(self, session_id: int, message_id: int, content: str) -> None:
        self._request("PUT",f"/workspaces/{_path_id(self._workspace_id)}/llm/sessions/{session_id}/messages/{message_id}/modify-response",{"modified_response":content})

    def append_modified_response(self, session_id: int, message_id: int, content: str) -> None:
        self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm/sessions/{session_id}/messages/{message_id}/append-modified-response",{"append_content":content})

    def create_message(self,session_id: int,request: ConversationWorkspaceMessageRequest) -> ConversationWorkspaceMessage:
        if not isinstance(request,ConversationWorkspaceMessageRequest): raise TypeError("request must be ConversationWorkspaceMessageRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"/messages",body),ConversationWorkspaceMessage(),"conversation result")

    def list_messages(self,session_id: int,*options: Callable[["QueryOptions"], None]) -> ConversationWorkspaceMessageList:
        return _product_message(self._request("GET",_with_query(f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"/messages",options),None),ConversationWorkspaceMessageList(),"conversation result")

    def get_message(self,message_id: int) -> ConversationWorkspaceMessage:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/messages/"+str(message_id)+"",None),ConversationWorkspaceMessage(),"conversation result")

    def latest_message_id(self,session_id: int) -> ConversationLatestMessageID:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"/messages/latest",None),ConversationLatestMessageID(),"conversation result")

    def create_tag(self,request: ConversationTagRequest) -> ConversationTag:
        if not isinstance(request,ConversationTagRequest): raise TypeError("request must be ConversationTagRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        return _product_message(self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/tags",body),ConversationTag(),"conversation result")

    def list_tags(self,*options: Callable[["QueryOptions"], None]) -> ConversationTagList:
        return _product_message(self._request("GET",_with_query(f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/tags",options),None),ConversationTagList(),"conversation result")

    def delete_tag(self,source: str,name: str) -> None:
        self._request("DELETE",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/tags/"+_path_id(source)+"/"+_path_id(name)+"",None)

    def list_session_tags(self,session_id: int) -> ConversationTagList:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"/tags",None),ConversationTagList(),"conversation result")

    def add_session_tag(self,session_id: int,request: ConversationTagRequest) -> None:
        if not isinstance(request,ConversationTagRequest): raise TypeError("request must be ConversationTagRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"/tags",body)

    def remove_session_tag(self,session_id: int,source: str,name: str) -> None:
        self._request("DELETE",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/sessions/"+str(session_id)+"/tags"+"/"+_path_id(source)+"/"+_path_id(name),None)

    def list_message_tags(self,message_id: int) -> ConversationTagList:
        return _product_message(self._request("GET",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/messages/"+str(message_id)+"/tags",None),ConversationTagList(),"conversation result")

    def add_message_tag(self,message_id: int,request: ConversationTagRequest) -> None:
        if not isinstance(request,ConversationTagRequest): raise TypeError("request must be ConversationTagRequest")
        body = MessageToDict(request,preserving_proto_field_name=True)
        self._request("POST",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/messages/"+str(message_id)+"/tags",body)

    def remove_message_tag(self,message_id: int,source: str,name: str) -> None:
        self._request("DELETE",f"/workspaces/{_path_id(self._workspace_id)}/llm"+"/messages/"+str(message_id)+"/tags"+"/"+_path_id(source)+"/"+_path_id(name),None)


def _workspace_chat_completion_body(request: WorkspaceChatCompletionRequest) -> dict[str, Any]:
    body = MessageToDict(request, preserving_proto_field_name=True)
    # The existing chat API uses a JSON integer selector, including negative
    # platform backend IDs. Protobuf's default int64 JSON encoding is a string.
    if request.HasField("backend_id"):
        body["backend_id"] = request.backend_id
    return body
