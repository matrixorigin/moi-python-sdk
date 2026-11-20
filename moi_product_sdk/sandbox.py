from __future__ import annotations

from typing import Callable

from google.protobuf import json_format

from ._proto.product.agent_pb2 import (
    AgentSandbox, SandboxCreateRequest, SandboxNetworkRequest,
    SandboxQuotaRequest, SandboxQuota, SandboxQuotaStatus, SandboxEgressEndpoint,
    SandboxAdminListResult, SandboxTerminalToken, SandboxAdminWorkspace, SandboxSSHSession,
)
from .client import ListOptions, WorkspaceScopedService, _path_id, _product_message, _with_query
from .errors import Error


class SandboxService(WorkspaceScopedService):
    """Manage workspace sandboxes through the product API."""

    def connect_terminal(self, sandbox_id: str, token: str, cols: int = 80, rows: int = 24) -> "SandboxTerminal":
        import websocket
        from urllib.parse import urlencode, urlsplit, urlunsplit
        endpoint = urlsplit(self._client._product_url(f"/agent-sandboxes/{_path_id(sandbox_id)}/terminal/ws"))
        target = urlunsplit(("wss" if endpoint.scheme == "https" else "ws", endpoint.netloc, endpoint.path, urlencode({"token":token,"cols":cols,"rows":rows}), ""))
        return SandboxTerminal(websocket.create_connection(target, timeout=self._client._config.timeout))

    def admin_get(self, sandbox_id: str) -> AgentSandbox:
        return _product_message(self._request("GET", f"/admin/agent-sandboxes/{_path_id(sandbox_id)}"), AgentSandbox(), "sandbox data")

    def admin_update_quota(self, workspace_id: str, request: SandboxQuotaRequest) -> SandboxQuota:
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(self._request("PATCH", f"/admin/workspaces/{_path_id(workspace_id)}/sandbox-quota", body), SandboxQuota(), "sandbox quota data")

    def create_ssh_session(self, sandbox_id: str) -> SandboxSSHSession:
        return _product_message(self._request("POST", f"/agent-sandboxes/{_path_id(sandbox_id)}/ssh-session"), SandboxSSHSession(), "sandbox SSH session data")

    def admin_list(self, *options: Callable[[ListOptions], None]) -> SandboxAdminListResult:
        return _product_message(self._request("GET", _with_query("/admin/agent-sandboxes", options)), SandboxAdminListResult(), "sandbox admin list data")

    def admin_delete(self, sandbox_id: str) -> None:
        self._request("DELETE", f"/admin/agent-sandboxes/{_path_id(sandbox_id)}")

    def admin_update_network(self, sandbox_id: str, request: SandboxNetworkRequest) -> AgentSandbox:
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(self._request("PATCH", f"/admin/agent-sandboxes/{_path_id(sandbox_id)}/network", body), AgentSandbox(), "sandbox data")

    def terminal_token(self, sandbox_id: str) -> SandboxTerminalToken:
        return _product_message(self._request("GET", f"/agent-sandboxes/{_path_id(sandbox_id)}/terminal"), SandboxTerminalToken(), "sandbox terminal token data")

    def create(self, request: SandboxCreateRequest) -> AgentSandbox:
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(self._request("POST", "/agent-sandboxes", body), AgentSandbox(), "sandbox data")

    def list(self) -> list[AgentSandbox]:
        data = self._request("GET", "/agent-sandboxes")
        if not isinstance(data, list):
            raise Error("ErrResponseInvalid", "sandbox list data must be an array")
        return [_product_message(item, AgentSandbox(), "sandbox data") for item in data]

    def get(self, sandbox_id: str) -> AgentSandbox:
        return _product_message(self._request("GET", f"/agent-sandboxes/{_path_id(sandbox_id)}"), AgentSandbox(), "sandbox data")

    def delete(self, sandbox_id: str) -> None:
        self._request("DELETE", f"/agent-sandboxes/{_path_id(sandbox_id)}")

    def update_network(self, sandbox_id: str, request: SandboxNetworkRequest) -> AgentSandbox:
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(self._request("PATCH", f"/agent-sandboxes/{_path_id(sandbox_id)}/network", body), AgentSandbox(), "sandbox data")

    def get_quota(self, *opts: Callable[[ListOptions], None]) -> SandboxQuotaStatus:
        return _product_message(self._request("GET", _with_query("/agent-sandboxes/quota", opts)), SandboxQuotaStatus(), "sandbox quota data")

    def update_quota(self, request: SandboxQuotaRequest) -> SandboxQuota:
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(self._request("PATCH", "/agent-sandboxes/quota", body), SandboxQuota(), "sandbox quota data")

class SandboxTerminal:
    def __init__(self, connection):
        self._connection = connection

    def close(self) -> None:
        # Match the Go SDK: send the close frame and release the socket without
        # waiting for a peer that may already have stopped reading.
        self._connection.close(timeout=0)

    def write_input(self, data: bytes) -> None:
        self._connection.send_binary(data)

    def receive(self) -> bytes:
        data = self._connection.recv()
        return data.encode() if isinstance(data, str) else data

    def resize(self, cols: int, rows: int) -> None:
        import json
        self._connection.send(json.dumps({"type":"resize","cols":cols,"rows":rows}))
