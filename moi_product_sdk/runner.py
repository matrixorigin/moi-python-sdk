from __future__ import annotations

from google.protobuf import json_format

from ._proto.product.agent_pb2 import AgentRunner, RunnerCreateRequest
from .client import WorkspaceScopedService, _path_id, _product_message
from .errors import Error


class RunnerService(WorkspaceScopedService):
    """Manage workspace runners through the product API."""

    def create(self, name: str) -> AgentRunner:
        request = RunnerCreateRequest(name=name)
        body = json_format.MessageToDict(request, preserving_proto_field_name=True)
        return _product_message(
            self._request("POST", "/agent-runners/custom", body),
            AgentRunner(),
            "runner data",
        )

    def list(self) -> list[AgentRunner]:
        data = self._request("GET", "/agent-runners")
        if not isinstance(data, list):
            raise Error("ErrResponseInvalid", "runner list data must be an array")
        return [_product_message(item, AgentRunner(), "runner data") for item in data]

    def get(self, runner_id: str) -> AgentRunner:
        return _product_message(
            self._request("GET", f"/agent-runners/{_path_id(runner_id)}"),
            AgentRunner(),
            "runner data",
        )

    def refresh(self, runner_id: str) -> AgentRunner:
        return _product_message(
            self._request("POST", f"/agent-runners/{_path_id(runner_id)}/refresh-token"),
            AgentRunner(),
            "runner data",
        )

    def delete(self, runner_id: str) -> None:
        self._request("DELETE", f"/agent-runners/{_path_id(runner_id)}")
