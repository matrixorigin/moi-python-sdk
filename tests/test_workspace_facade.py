import json
import os
import tempfile
import threading
import unittest
import urllib.error
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.parser import BytesParser
from email.policy import default

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client

from loopback_http import _with_localhost_no_proxy


def _lineage_response(method, path):
    path_only = path.split("?", 1)[0]
    if method == "GET" and path_only.endswith("/overview"):
        return {
            "artifact": {"artifact_id": "artifact-1", "root_asset_id": "root-1", "case_id": "case-1", "parsed_file_available": True},
            "workflow": {"workflow_id": "wf-1", "name": "workflow"},
            "workflow_invocation": {"input": {"file_id": "file-1"}, "vars": {}},
            "topology": {"nodes": [{"node_id": "node-1", "label": "Parse"}], "edges": []},
            "entry": {"catalog_file_id": "file-1"},
        }
    if method == "GET" and path_only.endswith("/output-blocks"):
        node_id = "node-1" if "/nodes/" in path_only else ""
        return {"artifact_id": "artifact-1", "node_id": node_id, "blocks": [{"block_id": "block-1"}]}
    if method == "GET" and path_only.endswith("/revisions"):
        node_id = "node-1" if "/nodes/" in path_only else ""
        return {"artifact_id": "artifact-1", "node_id": node_id, "block_id": "block-1", "revisions": [{"revision_id": "rev-1"}]}
    if method == "POST" and path_only.endswith("/revisions"):
        node_id = "node-1" if "/nodes/" in path_only else ""
        return {"artifact_id": "artifact-1", "node_id": node_id, "block_id": "block-1", "revision": {"revision_id": "rev-2"}}
    if method == "POST" and path_only.endswith("/effective-revisions"):
        node_id = "node-1" if "/nodes/" in path_only else ""
        return {"artifact_id": "artifact-1", "node_id": node_id, "effective_set_version": 8}
    if method == "GET" and "/nodes/" in path_only:
        return {"workflow": {"workflow_id": "wf-1"}, "node": {"node_id": "node-1", "label": "Parse"}, "run": {"status": "succeeded", "runtime_input": {}, "runtime_output": {}, "config": {}}}
    if method == "POST" and "/rerun" in path_only:
        return {"artifact_id": "artifact-1", "node_id": "node-1", "node_execution_id": "node-exec-1", "rerun_id": "rerun-1", "branch_id": "branch-1", "case_id": "case-2", "status": "running"}
    return {}


def _compute_resource_payload(status="running"):
    return {
        "id": "compute-1",
        "workspace_id": "ws-created",
        "name": "go-worker",
        "description": "etl",
        "spec_id": "spec-1",
        "cpu": 2,
        "memory_gib": 8,
        "gpu": 0,
        "min_replicas": 1,
        "max_replicas": 3,
        "current_replicas": 1,
        "go_worker_image_id": "go-img-1",
        "python_worker_image_id": "py-img-1",
        "platform": "linux/amd64",
        "auto_suspend_minutes": 0,
        "is_default": False,
        "status": status,
        "status_message": "",
        "created_by": "user-1",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "kind": "task",
        "cpu_milli": 2000,
        "memory_mib": 8192,
        "gpu_count": 0,
        "gpu_memory_mib": 0,
        "gpu_cores": 0,
        "desired_replicas": 2,
        "worker_images": [{"worker_type": "go", "image_id": "go-img-1", "platform": "linux/amd64"}],
        "scale_reason": "activation",
        "last_activation_at": "2026-01-01T00:01:00Z",
        "last_active_at": "2026-01-01T00:02:00Z",
    }


def _provider_backend_payload(backend_id=1, name="openai", backend_type="OPENAI", models=None, supported_mime_types=None):
    return {
        "id": backend_id,
        "name": name,
        "type": backend_type,
        "reasoning_control_protocol": "NONE",
        "timeout_seconds": 30,
        "models": models or [],
        "supported_mime_types": supported_mime_types or [],
        "endpoints": [_provider_endpoint_payload()],
        "created_at": 1710000000,
        "updated_at": 1710000001,
    }


def _provider_endpoint_payload(endpoint_id=1, backend_id=1, address="https://llm.example.test"):
    return {
        "id": endpoint_id,
        "backend_id": backend_id,
        "address": address,
        "status": "ONLINE",
        "created_at": 1710000000,
        "updated_at": 1710000001,
    }


def _alert_receiver_payload(receiver_id="recv-1"):
    return {
        "workspace_id": "ws-created",
        "id": receiver_id,
        "name": "ops",
        "notify_type": 1,
        "email": "ops@example.com",
        "status": 1,
        "created_at": 1710000000,
        "updated_at": 1710000001,
    }


def _alert_template_payload():
    return {
        "expression_id": "expr-1",
        "expression": "metric > $threshold",
        "expression_cn": "metric > threshold",
        "is_default_enabled": True,
        "alert_type": "data_loading",
        "category": 2,
        "level": "critical",
        "args": [{"key": "threshold", "value": "10"}],
        "notification": {
            "interval": {"value": 60, "unit": "minute"},
            "notify_rules": [{"type": "email", "alert_objects": [_alert_receiver_payload()]}],
        },
    }


def _alert_rule_payload():
    return {
        "alert_id": "alert-1",
        "category": 2,
        "alert_config": _alert_template_payload(),
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-02T00:00:00Z",
        "has_new": True,
        "state": "monitoring",
        "complete_expr": "metric > 10",
        "complete_expr_cn": "metric > 10",
    }


def _alert_history_payload():
    return {
        "id": "history-1",
        "rule_id": "alert-1",
        "group_id": "group-1",
        "rule_template_id": "expr-1",
        "rule_expression": "metric > 10",
        "rule_expression_cn": "metric > 10",
        "alert_type": "data_loading",
        "alert_severity": "critical",
        "receivers": [{"id": "recv-1", "name": "ops", "notify_type": 1, "email": "ops@example.com"}],
        "create_at": "2026-06-01T00:00:00Z",
        "is_read": False,
    }


_UNSET = object()


class _Handler(BaseHTTPRequestHandler):
    requests = []
    catalog_created = False
    database_created = False
    drawing_search_data = _UNSET

    def log_message(self, format, *args):
        return

    def do_GET(self):
        self.__class__.requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), None))
        if self.path == "/newmoi/consumer-profiles/subject-1/render":
            self._json({"code": "OK", "msg": "OK", "data": {
                "subject_id": "subject-1", "text": "profile text", "token_estimate": 12, "pending_conflicts": [],
            }})
            return
        if self.path == "/newmoi/semantic-models/101/artifacts/page%20image%2F1/preview":
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Disposition", 'inline; filename="page.png"')
            self.end_headers()
            self.wfile.write(b"png-body")
            return
        if self.path == "/newmoi/connectors/file/stream?conn_file_id=cf-1":
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(b"stream-body")
            return
        if self.path == "/newmoi/workspaces?name=duplicate":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "total": 2,
                        "workspaces": [
                            {"id": "ws-1", "name": "duplicate"},
                            {"id": "ws-2", "name": "duplicate"},
                        ],
                    },
                }
            )
            return
        if self.path == "/newmoi/workspaces/ws-1/iam/users/canonical-user-2/role-bindings":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "user_id": "canonical-user-2",
                        "roles": [{"role_id": "role-20", "role_name": "Editor", "selectable": True}],
                        "default_role_id": "role-20",
                        "default_role_version": 4,
                        "binding_version": "binding-v4",
                        "request_id": "read-1",
                        "trace_id": "trace-1",
                    },
                }
            )
            return
        if self.path.startswith("/newmoi/workspaces"):
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "total": 0,
                        "workspaces": [],
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/healthz":
            self._json({"code": "OK", "msg": "OK", "data": {"status": "ok"}})
            return
        if self.path == "/newmoi/dashboard/task-execution-overview":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "running": 1,
                        "success": 2,
                        "failed": 3,
                        "pending": 4,
                        "total": 10,
                        "window_days": 7,
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/data-assets/asset-1":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "asset": {
                            "asset_id": "asset-1",
                            "name": "orders.csv",
                            "raw_file_id": "file-1",
                            "volume_id": 30,
                            "asset_type": "file",
                            "asset_ref": "file-1",
                            "meta": {"source": "workflow"},
                        },
                        "derivations": [{"kind": "parsed", "source_asset_id": "asset-1", "target_asset_id": "asset-parsed-1"}],
                        "manifest": {"root_asset_id": "asset-1", "source_file_id": "file-1", "parsed_asset_id": "asset-parsed-1"},
                        "assets_by_id": {"asset-1": {"asset_id": "asset-1", "asset_ref": "file-1"}},
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/files/file-1/data-asset":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "asset": {
                            "asset_id": "asset-1",
                            "name": "orders.csv",
                            "raw_file_id": "file-1",
                            "volume_id": 30,
                            "asset_type": "file",
                            "asset_ref": "file-1",
                        },
                        "derivations": [{"kind": "parsed", "target_asset_id": "asset-parsed-1"}],
                        "manifest": {"parsed_file_id": "parsed-file-1", "source_file_id": "file-1"},
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/file-artifacts/file-1":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "file_id": "file-1",
                        "file_exists": True,
                        "has_artifact": True,
                        "source_file_id": "file-1",
                        "root_asset": {"asset_id": "asset-1"},
                    },
                }
            )
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"workflow": {"id": "wf-1", "name": "wf", "source_type": "manual_dsl", "status": "ready", "execution_mode": "one_shot", "dsl_yaml": "workflow:\n  name: wf"}},
                }
            )
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"total": 1, "executions": [{"execution_id": "exec-1", "workflow_id": "wf-1", "status": "running", "execution_mode": "one_shot"}]},
                }
            )
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1":
            self._json({"code": "OK", "msg": "OK", "data": {"execution": {"execution_id": "exec-1", "workflow_id": "wf-1", "status": "running", "execution_mode": "one_shot"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/result":
            self._json({"code": "OK", "msg": "OK", "data": {"result": {"execution_id": "exec-1", "workflow_id": "wf-1", "status": "succeeded", "case_result": "done"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/import-context":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"import_context": {"task_id": "task-1", "run_id": "run-1", "workflow_execution_id": "exec-1", "status": 1}},
                }
            )
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/import-files?kind=output":
            self._json({"code": "OK", "msg": "OK", "data": {"files": [], "total": 0, "total_sum": 0, "total_success": 0, "total_failed": 0}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/nodes/node-1":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "node": {"flow_id": "root", "name": "node-1", "node_key": "node-1", "node_type": "custom", "display_name": "Node 1"},
                        "run": {"status": "succeeded", "runtime_input": {"file_id": "file-1"}, "runtime_output": {"ok": True}, "config": {}},
                    },
                }
            )
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/nodes/node-1/rerun-plan?mode=from_node":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "plan": {
                            "workflow_id": "wf-1",
                            "source_execution_id": "exec-1",
                            "source_case_id": "case-1",
                            "node_key": "node-1",
                            "source_node_execution_id": "node-exec-1",
                            "rerun_contract_hash": "sha256:test-contract",
                            "available_modes": ["continue_from_node"],
                            "validation": {"ok": True},
                        }
                    },
                }
            )
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/rerun-branches":
            self._json({"code": "OK", "msg": "OK", "data": {"reruns": [{"rerun_id": "rerun-1", "branch_id": "branch-1", "case_id": "case-2", "mode": "continue_from_node", "status": "running"}]}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/reruns/rerun-1":
            self._json({"code": "OK", "msg": "OK", "data": {"rerun": {"rerun_id": "rerun-1", "branch_id": "branch-1", "case_id": "case-2", "mode": "continue_from_node", "status": "running"}}})
            return
        if self.path.startswith("/newmoi/lineage/"):
            self._json({"code": "OK", "msg": "OK", "data": _lineage_response(self.command, self.path)})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators/1":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "node_id": "moi:custom.operator:workspace:text_counter", "name": "Text Counter", "identifier": "text_counter", "enabled": True}})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators/1/code":
            self._json({"code": "OK", "msg": "OK", "data": {"source": "def handle(workspace_id, sdk, input): return input"}})
            return
        if self.path == "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service?version=v1":
            self._json({"code": "OK", "msg": "OK", "data": {"service": {"api_service_id": "api_123", "service_name": "operator-api-abc", "version": "v1"}}})
            return
        if self.path == "/newmoi/workflow-templates/1":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "name": "tpl", "dsl_yaml": "workflow:\n  name: tpl"}})
            return
        if self.path == "/newmoi/sessions/1001":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1001, "title": "analysis", "source": "sdk", "user_id": "user-1"}})
            return
        if self.path == "/newmoi/messages/sessions/1001/latest":
            self._json({"code": "OK", "msg": "OK", "data": {"session_id": 1001, "message_id": 1}})
            return
        if self.path == "/newmoi/messages/msg-1":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "session_id": 1001, "source": "explore", "role": "assistant", "content": "done", "status": "success"}})
            return
        if self.path == "/newmoi/semantic-models/101/source-jobs":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "items": [
                            {
                                "job_id": "job-1",
                                "source_id": "source-1",
                                "job_status": "succeeded",
                                "kb_file_id": "kb-file-1",
                                "reconcile_required": True,
                            }
                        ],
                        "total": 1,
                        "reconcile_required": True,
                    },
                }
            )
            return
        if self.path in {
            "/newmoi/semantic-models/101/sources",
            "/newmoi/semantic-models/101/sources?page=2&page_size=20",
        }:
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"items": [], "total": 21, "page": 2, "page_size": 20},
                }
            )
            return
        if self.path == "/newmoi/semantic-models/101/referencing-agents?limit=10&cursor=next":
            self._json({"code": "OK", "msg": "OK", "data": {
                "items": [{"id": "ag_1", "workspace_id": "ws-created", "name": "Agent", "status": "active", "knowledge_base_count": 2}],
                "limit": 10,
            }})
            return
        if self.path == "/newmoi/semantic-models/101":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 101, "name": "orders-model", "description": "orders", "tables": ["orders"], "source_counts": {"files": 2, "tables": 1, "total": 3}, "created_at": 11, "updated_at": 11}})
            return
        if self.path == "/newmoi/semantic-models":
            self._json({"code": "OK", "msg": "OK", "data": {"items": [{"id": 101, "name": "orders-model", "source_counts": {"files": 2, "tables": 1, "total": 3}}], "total": 1, "next_page_token": ""}})
            return
        if self.path == "/newmoi/semantic-models/101/entries?limit=20":
            self._json({"code": "OK", "msg": "OK", "data": {"items": [], "total": 0, "next_page_token": ""}})
            return
        if self.path == "/newmoi/semantic-models/101/entries?domain=rag":
            self._json({"code": "OK", "msg": "OK", "data": {"items": [], "total": 0, "next_page_token": ""}})
            return
        if self.path == "/newmoi/semantic-models/101/export":
            self._json({"code": "OK", "msg": "OK", "data": {"model": {"id": 101, "name": "orders-model", "tables": ["orders"], "created_at": 11, "updated_at": 11}, "entries": []}})
            return
        if self.path == "/newmoi/task/get?task_id=task-1":
            self._json({"code": "OK", "msg": "OK", "data": {"task": {"id": "task-1", "mapping": [{"target_column": "order_id"}], "schedule": {"kind": "hourly"}, "backfill": {"enabled": True}, "structured_load_config": {"source": {"database": "analytics"}, "tables": ["orders"]}}}})
            return
        if self.path == "/newmoi/task/list":
            self._json({"code": "OK", "msg": "OK", "data": {"tasks": [{"id": "task-1", "mapping": [{"target_column": "order_id"}], "schedule": {"kind": "hourly"}, "backfill": {"enabled": True}, "structured_load_config": {"source": {"database": "analytics"}, "tables": ["orders"]}}], "total": 1}})
            return
        if self.path == "/newmoi/task/runs?task_id=task-1":
            self._json({"code": "OK", "msg": "OK", "data": {"runs": []}})
            return
        if self.path == "/newmoi/task/files?task_id=task-1&status=failed":
            self._json({"code": "OK", "msg": "OK", "data": {"files": []}})
            return
        if self.path == "/newmoi/llm/backends":
            self._json({"code": "OK", "msg": "OK", "data": {"backends": [_provider_backend_payload(1, "openai", models=["gpt-4.1"])]}})
            return
        if self.path == "/newmoi/llm/backends/1":
            self._json({"code": "OK", "msg": "OK", "data": _provider_backend_payload(1, "openai", models=["gpt-4.1"])})
            return
        if self.path == "/newmoi/llm/backends/1/endpoints":
            self._json({"code": "OK", "msg": "OK", "data": {"endpoints": [_provider_endpoint_payload(2, 1, "https://llm-2.example.test")]}})
            return
        if self.path == "/newmoi/llm/router":
            self._json({"code": "OK", "msg": "OK", "data": {"strategy": "round_robin", "health_check_interval": 30, "max_retries": 2, "session_affinity": False}})
            return
        if self.path == "/newmoi/parser/router":
            self._json({"code": "OK", "msg": "OK", "data": {"strategy": "single", "health_check_interval": 30, "max_retries": 1, "session_affinity": False}})
            return
        if self.path == "/newmoi/parser/backends/4":
            self._json({"code": "OK", "msg": "OK", "data": _provider_backend_payload(4, "doc-parser", "PARSER", supported_mime_types=["application/pdf"])})
            return
        if self.path == "/newmoi/alerting/receiver?id=recv-1":
            self._json({"code": "OK", "msg": "OK", "data": _alert_receiver_payload()})
            return
        if self.path == "/newmoi/compute-resources":
            self._json({"code": "OK", "msg": "OK", "data": [_compute_resource_payload()]})
            return
        if self.path == "/newmoi/admin/compute-resources?limit=50&offset=0":
            resource = _compute_resource_payload()
            resource["workspace"] = {
                "id": "ws-created",
                "name": "Workspace Created",
                "owner_id": "owner-1",
                "account_name": "account_1",
            }
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "items": [resource],
                        "total": 1,
                        "limit": 50,
                        "offset": 0,
                    },
                }
            )
            return
        if self.path == "/newmoi/compute-resources/worker-images?type=go-worker":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": [
                        {
                            "id": "go-img-1",
                            "worker_type": "go-worker",
                            "image_key": "go-worker",
                            "type": "go-worker",
                            "tag": "v1",
                            "repository": "repo/go-worker",
                            "platform": "linux/amd64",
                            "description": "go worker",
                            "is_default": True,
                            "status": "active",
                            "registered_at": "2026-01-01T00:00:00Z",
                            "updated_at": "2026-01-01T00:00:00Z",
                        }
                    ],
                }
            )
            return
        if self.path == "/newmoi/compute-resources/compute-1":
            self._json({"code": "OK", "msg": "OK", "data": _compute_resource_payload()})
            return
        if self.path == "/newmoi/compute-resources/compute-1/preflight-delete":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "active_tasks": 1,
                        "active_task_ids": ["task-1"],
                        "bound_workflows": 1,
                        "bound_workflow_details": [{"id": "wf-1", "name": "workflow", "node_names": ["node-1"]}],
                    },
                }
            )
            return
        if self.path == "/newmoi/data-share/publishes?name=orders-share":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "list": [
                            {
                                "id": "publish-1",
                                "name": "orders-share",
                                "source_database_id": "101",
                                "mo_database_name": "orders",
                                "table_scope": {"mode": "selected", "object_ids": ["201"]},
                                "obj_display_name": "Orders",
                                "obj_display_path": "Catalog/Orders",
                                "targets": [{"workspace_id": "ws-2", "workspace_name": "Target"}],
                                "permission": "owner",
                                "remark": "daily",
                                "created_by": "user-1",
                                "created_at": "2026-06-01T00:00:00Z",
                                "updated_at": "2026-06-01T00:00:00Z",
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 20,
                    },
                }
            )
            return
        if self.path == "/newmoi/data-share/publishes/summary":
            self._json({"code": "OK", "msg": "OK", "data": {"total": 2, "target_total": 5}})
            return
        if self.path.startswith("/newmoi/data-share/source-databases/101/tables"):
            self._json({"code": "OK", "msg": "OK", "data": {"list": [{"id": "201", "name": "orders"}], "total": 1, "page": 1, "page_size": 20}})
            return
        if self.path == "/newmoi/data-share/publishes/check-name?name=orders-share":
            self._json({"code": "OK", "msg": "OK", "data": {"available": True}})
            return
        if self.path == "/newmoi/data-share/subscriptions?status=pending":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "list": [
                            {
                                "id": "sub-1",
                                "pub_name": "orders-share",
                                "source_database_id": "101",
                                "mo_database_name": "orders",
                                "table_scope": {"mode": "selected", "object_ids": ["201"]},
                                "obj_display_name": "Orders",
                                "obj_display_path": "Catalog/Orders",
                                "source_workspace_id": "ws-source",
                                "source_workspace_name": "Source",
                                "publisher": "alice",
                                "published_at": "2026-06-01T00:00:00Z",
                                "status": "unsubscribed",
                                "created_at": "2026-06-01T00:00:00Z",
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 20,
                    },
                }
            )
            return
        if self.path == "/newmoi/export/task/export-1/state":
            self._json({"code": "OK", "msg": "OK", "data": {"total": 0, "pending": 0, "running": 0, "failed": 0, "completed": 0}})
            return
        if self.path == "/newmoi/user/me/db-connection":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "host": "mo.example.test",
                        "port": 6001,
                        "database": "ws_created",
                        "account_name": "tenant",
                        "username": "u",
                        "password": "p",
                        "session_init_sqls": ["SET ROLE moi_role_2", "SET enable_remap_hint = 1"],
                        "effective_role_id": "2",
                        "effective_role_db_role": "moi_role_2",
                        "effective_role_source": "default_role",
                        "effective_role_version": "role-v1",
                    },
                }
            )
            return
        if self.path.startswith("/newmoi/audit/logs"):
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "items": [
                            {
                                "id": "log-1",
                                "workspace_id": "ws-created",
                                "method": "POST",
                                "path": "/newmoi/catalog/file/create",
                                "status_code": 500,
                                "result": "failed",
                                "created_at": "2026-06-26T00:00:00Z",
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 5,
                    },
                }
            )
            return
        self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or "0")
        raw_body = self.rfile.read(length)
        body = self._request_body(raw_body)
        self.__class__.requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), body))
        if self.path == "/newmoi/workspaces":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "ws-created"}})
            return
        if self.path == "/newmoi/catalog/data-dashboard/table-search":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "items": [
                            {
                                "table_id": 10,
                                "table_name": "orders",
                                "database_id": 20,
                                "database_name": "sales",
                                "catalog_id": 30,
                                "catalog_name": "internal",
                                "description": "orders table",
                                "matched_fields": ["table_name"],
                                "matched_columns": ["order_id"],
                                "metadata_match": True,
                            }
                        ],
                        "total": 2,
                        "next_page_token": "10",
                    },
                }
            )
            return
        if self.path in (
            "/newmoi/memories/retrieve",
            "/newmoi/memories/search",
            "/newmoi/memories/fulltext-search",
            "/newmoi/memories/query",
        ):
            self._json({"code": "OK", "msg": "OK", "data": {"memories": [{
                "memory_id": "m1", "subject_id": "subject-1", "memory_type": "semantic",
                "content": "likes seafood", "trust_tier": "T1", "initial_confidence": 0.9, "is_active": True,
            }]}})
            return
        if self.path == "/newmoi/workspaces/ws-created/users":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/account/detail":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "uid": "user-1",
                        "email": "user@example.test",
                        "firstname": "Ada",
                        "lastname": "Lovelace",
                        "name": "Ada Lovelace",
                    },
                }
            )
            return
        if self.path == "/newmoi/user/me/update_info":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "user-1"}})
            return
        if self.path == "/newmoi/agents/a2a":
            self._json({"code": "OK", "msg": "OK", "data": {"kind": "task", "id": "task-1", "turnId": "turn-1"}})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "node_id": "moi:custom.operator:workspace:text_counter", "name": "Text Counter", "identifier": "text_counter", "enabled": True}})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators/1/test-run":
            self._json({"code": "OK", "msg": "OK", "data": {"test_run": {"operator_id": 1, "node_id": "moi:custom.operator:workspace:text_counter", "version": "v1", "status": "passed", "runtime_input": {"text": "hello"}, "runtime_output": {"length": 5}, "wait_timeout_seconds": 30}}})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators/1/enable":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "node_id": "moi:custom.operator:workspace:text_counter", "name": "Text Counter", "identifier": "text_counter", "enabled": True}})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators/1/disable":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "node_id": "moi:custom.operator:workspace:text_counter", "name": "Text Counter", "identifier": "text_counter", "enabled": False}})
            return
        if self.path == "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service":
            self._json({"code": "OK", "msg": "OK", "data": {"service": {"api_service_id": "api_123", "service_name": "operator-api-abc", "status": "ready"}}})
            return
        if self.path == "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service/enable?version=v1":
            self._json({"code": "OK", "msg": "OK", "data": {"service": {"api_service_id": "api_123", "status": "ready"}}})
            return
        if self.path == "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service/disable?version=v1":
            self._json({"code": "OK", "msg": "OK", "data": {"service": {"api_service_id": "api_123", "status": "disabled"}}})
            return
        if self.path == "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service/invoke":
            self._json({"code": "OK", "msg": "OK", "data": {"result": {"status": "succeeded", "result": {"text": "hello"}}}})
            return
        if self.path == "/newmoi/workflow-templates":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "name": "tpl", "dsl_yaml": "workflow:\n  name: tpl", "template_key": "tpl-key"}})
            return
        if self.path == "/newmoi/semantic-models":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 101, "name": "orders-model", "description": "orders", "tables": ["orders"], "source_counts": {"files": 2, "tables": 1, "total": 3}, "created_at": 11, "updated_at": 11}})
            return
        if self.path == "/newmoi/semantic-models/create-empty":
            self._json({"code": "OK", "msg": "OK", "data": {"model": {"id": 102, "name": "empty-model"}, "data_domain": {"model_id": 102, "catalog_id": 3, "database_id": 11, "raw_volume_id": 12, "processed_volume_id": 13}}})
            return
        if self.path in {
            "/newmoi/semantic-models/local-files/upload",
            "/newmoi/semantic-models/101/local-files/upload",
        }:
            self._json({"code": "OK", "msg": "OK", "data": {"file_id": "file-1"}})
            return
        if self.path == "/newmoi/semantic-models/101/sources":
            self._json({"code": "OK", "msg": "OK", "data": {"sources": [], "jobs": [], "skipped_existing_file_ids": ["file-existing"], "skipped_existing_table_ids": [42]}})
            return
        if self.path == "/newmoi/semantic-models/101/sources/existence":
            self._json({"code": "OK", "msg": "OK", "data": {"file_ids": ["file-1"], "table_ids": [10]}})
            return
        if self.path in {
            "/newmoi/semantic-models/source-selections/preview",
            "/newmoi/semantic-models/101/source-selections/preview",
        }:
            self._json({"code": "OK", "msg": "OK", "data": {"file_count": 140, "table_count": 0, "total_count": 140}})
            return
        if self.path == "/newmoi/catalog/database/table-leaves":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "items": [{"table_id": 10, "table_name": "orders", "database_id": 20}],
                        "total": 2,
                        "next_page_token": "10",
                    },
                }
            )
            return
        if self.path == "/newmoi/semantic-models/101/entries":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 201, "kind": "metric", "key": "revenue", "tables": ["orders"], "spec": {"expr": "sum(amount)"}, "created_at": 12, "updated_at": 12}})
            return
        if self.path == "/newmoi/semantic-models/101/import":
            self._json({"code": "OK", "msg": "OK", "data": {"imported": 1, "model_id": 101}})
            return
        if self.path == "/newmoi/semantic-models/101/validate":
            self._json({"code": "OK", "msg": "OK", "data": {"valid": True}})
            return
        if self.path == "/newmoi/drawings/search":
            data = self.__class__.drawing_search_data
            if data is _UNSET:
                data = {"drawings": [], "count": 0, "diagnostics": {}}
            self._json({"code": "OK", "msg": "OK", "data": data})
            return
        if self.path == "/newmoi/catalog/list":
            catalogs = [{"id": 10, "name": "orders", "display_name": "Orders", "description": "Lake catalog", "display_description": "Catalog shown in the workspace", "allowed_actions": ["catalog.update_catalog"]}] if self.__class__.catalog_created else []
            self._json({"code": "OK", "msg": "OK", "data": {"list": catalogs}})
            return
        if self.path == "/newmoi/catalog/tree":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "tree": [
                            {
                                "id": 10,
                                "type": "catalog",
                                "name": "orders",
                                "display_name": "Orders",
                                "node_list": [
                                    {
                                        "id": "20",
                                        "type": "database",
                                        "name": "raw",
                                        "display_description": "User database leaf",
                                    }
                                ],
                            }
                        ]
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/system/tree":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "tree": [
                            {
                                "id": "system",
                                "type": "catalog",
                                "name": "system",
                                "display_name": "System",
                                "node_list": [
                                    {
                                        "id": "system:database:system",
                                        "type": "database",
                                        "name": "system",
                                        "display_name": "system",
                                        "node_list": [
                                            {
                                                "id": "system:table:system:tables",
                                                "type": "table",
                                                "name": "tables",
                                                "display_description": "System table leaf",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ]
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/create":
            self.__class__.catalog_created = True
            self._json({"code": "OK", "msg": "OK", "data": {"id": 10}})
            return
        if self.path == "/newmoi/catalog/update":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/info":
            self._json({"code": "OK", "msg": "OK", "data": {"catalog": {"id": 10, "name": "orders-renamed", "description": "renamed catalog"}}})
            return
        if self.path == "/newmoi/catalog/ref_list":
            self._json({"code": "OK", "msg": "OK", "data": {"list": [{"ref_id": "db-1", "ref_type": "database"}]}})
            return
        if self.path == "/newmoi/user/tag/list":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"total": 1, "tag_list": [{"id": 7, "name": "tag1", "description": "canonical subject attribute"}]},
                }
            )
            return
        if self.path == "/newmoi/user/tag/create":
            if body.get("name") == "":
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"code": "ErrParamInvalid", "msg": "name is required"}).encode("utf-8"))
                return
            self._json({"code": "OK", "msg": "OK", "data": {"id": 7}})
            return
        if self.path == "/newmoi/user/tag/update":
            self._json({"code": "OK", "msg": "OK", "data": {"id": body.get("id", 7)}})
            return
        if self.path == "/newmoi/user/tag/delete":
            self._json({"code": "OK", "msg": "OK", "data": {"id": body.get("id", 7)}})
            return
        if self.path == "/newmoi/catalog/database/list":
            databases = (
                [
                    {
                        "id": 20,
                        "name": "raw",
                        "display_name": "Raw Data",
                        "display_description": "Raw database",
                        "allowed_actions": ["database.update_database"],
                    }
                ]
                if self.__class__.database_created
                else []
            )
            self._json({"code": "OK", "msg": "OK", "data": {"list": databases}})
            return
        if self.path == "/newmoi/catalog/database/create":
            self.__class__.database_created = True
            self._json({"code": "OK", "msg": "OK", "data": {"id": 20}})
            return
        if self.path == "/newmoi/catalog/database/update":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 20}})
            return
        if self.path == "/newmoi/catalog/database/info":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "database": {
                            "id": 20,
                            "name": "raw_renamed",
                            "display_name": "Raw Data",
                            "description": "renamed database",
                            "display_description": "Renamed database",
                        }
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/database/ref_list":
            self._json({"code": "OK", "msg": "OK", "data": {"list": [{"ref_id": "volume-1", "ref_type": "volume"}]}})
            return
        if self.path == "/newmoi/catalog/database/children":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "list": [
                            {
                                "id": "30",
                                "name": "landing",
                                "display_name": "Landing",
                                "display_description": "Landing volume",
                                "type": "volume",
                                "allowed_actions": ["volume.update"],
                            },
                            {"id": "31", "name": "orders", "type": "table"},
                        ]
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/file/upload":
            self._json({"code": "OK", "msg": "OK", "data": {"file_id": "file-1"}})
            return
        if self.path == "/newmoi/workspaces/ws-created/catalog-files/uploads":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "file_id": "file-private-1",
                        "original_name": "resume.pdf",
                        "size": 3,
                        "md5": "digest",
                        "catalog_file": {
                            "workspace_id": "ws-created",
                            "volume_id": 17,
                            "file_id": "file-private-1",
                            "path": "resume.pdf",
                            "name": "resume.pdf",
                            "size": 3,
                            "md5": "digest",
                        },
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/file/create":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/file/info":
            self._json({"code": "OK", "msg": "OK", "data": {"file_id": "file-1", "file_name": "orders.csv", "size": 16}})
            return
        if self.path == "/newmoi/catalog/file/list":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"total": 1, "list": [{"id": "file-1", "name": "orders.csv", "file_type": "file", "volume_id": "30"}]},
                }
            )
            return
        if self.path == "/newmoi/catalog/file/update":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/file/download":
            self._json({"code": "OK", "msg": "OK", "data": {"downloaded": True}})
            return
        if self.path == "/newmoi/catalog/file/preview_link":
            self._json({"code": "OK", "msg": "OK", "data": {"url": "https://example.test/preview/file-1"}})
            return
        if self.path == "/newmoi/catalog/file/preview_stream":
            self._json({"code": "OK", "msg": "OK", "data": {"previewed": True}})
            return
        if self.path == "/newmoi/catalog/file/preview_excel_stream":
            self._json({"code": "OK", "msg": "OK", "data": {"link": "https://example.test/preview/file-1.xlsx"}})
            return
        if self.path == "/newmoi/catalog/data-assets/batch-get":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "items": [
                            {
                                "asset_id": "asset-1",
                                "raw_file_id": "file-1",
                                "volume_id": 30,
                                "asset_type": "file",
                                "asset_ref": "file-1",
                            }
                        ],
                        "total": 1,
                    },
                }
            )
            return
        if self.path == "/newmoi/catalog/file/trigger_workflow":
            self._json({"code": "OK", "msg": "OK", "data": {"triggered": 1}})
            return
        if self.path == "/newmoi/catalog/file/delete_ref":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/file/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path in {
            "/newmoi/catalog/volume/add_ref_workflow",
            "/newmoi/catalog/volume/remove_ref_workflow",
        }:
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/volume/full_path":
            self._json({"code": "OK", "msg": "OK", "data": {"path": "orders/raw/landing"}})
            return
        if self.path == "/newmoi/catalog/volume/ref_list":
            self._json({"code": "OK", "msg": "OK", "data": {"list": [{"ref_id": "wf-1", "ref_type": "workflow"}]}})
            return
        if self.path == "/newmoi/catalog/volume/update":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 30}})
            return
        if self.path == "/newmoi/catalog/volume/info":
            self._json({"code": "OK", "msg": "OK", "data": {"volume": {"id": 30, "name": "landing_renamed", "description": "renamed volume"}}})
            return
        if self.path == "/newmoi/catalog/volume/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/folder/create":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 31}})
            return
        if self.path == "/newmoi/catalog/folder/update":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/folder/ref_list":
            self._json({"code": "OK", "msg": "OK", "data": {"list": [{"ref_id": "wf-1", "ref_type": "workflow"}]}})
            return
        if self.path == "/newmoi/catalog/folder/clean":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/folder/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/database/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/table/create":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 31}})
            return
        if self.path == "/newmoi/catalog/table/exist":
            self._json({"code": "OK", "msg": "OK", "data": {"data": True}})
            return
        if self.path == "/newmoi/catalog/table/overview":
            self._json({"code": "OK", "msg": "OK", "data": {"tables": [{"name": "orders", "columns": ["id"]}]}})
            return
        if self.path == "/newmoi/catalog/table/info":
            self._json({"code": "OK", "msg": "OK", "data": {"name": "orders", "columns": [{"name": "id", "type": "INT"}]}})
            return
        if self.path == "/newmoi/catalog/table/data":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"data": [["1"]], "columns": [{"name": "id", "type": "INT"}], "total_rows": 1, "page": 2, "page_size": 50},
                }
            )
            return
        if self.path == "/newmoi/catalog/table/preview":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"data": [["1"]], "columns": [{"name": "id", "type": "INT"}], "total_rows": 1, "page": 1, "page_size": 0},
                }
            )
            return
        if self.path == "/newmoi/catalog/table/full_path":
            self._json({"code": "OK", "msg": "OK", "data": {"path": "orders/raw/orders"}})
            return
        if self.path == "/newmoi/catalog/table/truncate":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/table/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/catalog/nl2sql/run_sql":
            self._json({"code": "OK", "msg": "OK", "data": {"columns": ["id", "amount"], "rows": [["1", "42.5"]]}})
            return
        if self.path == "/newmoi/catalog/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/user/create":
            if isinstance(body, dict) and body.get("name") == "unknown":
                self._json({"code": "ErrUserNotFound", "msg": "Invitation account not found"}, status=404)
                return
            self._json({"code": "OK", "msg": "OK", "data": {"id": "canonical-user-2"}})
            return
        if self.path == "/newmoi/user/list":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "total": 2,
                        "user_list": [
                            {
                                "id": "user-1",
                                "iam_user_id": "moi-user-1",
                                "name": "alice",
                                "status": "enabled",
                                "created_at": "2026-08-20T00:00:00Z",
                                "updated_at": "2026-08-20T00:00:00Z",
                                "reserved": False,
                                "role_list": [],
                                "tag_list": [],
                            },
                            {
                                "id": "user-2",
                                "iam_user_id": "moi-user-2",
                                "name": "bob",
                                "status": "pending",
                                "created_at": "2026-08-20T00:00:00Z",
                                "updated_at": "2026-08-20T00:00:00Z",
                                "reserved": False,
                                "role_list": [],
                                "tag_list": [],
                            },
                        ],
                    },
                }
            )
            return
        if self.path == "/newmoi/user/detail_info":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "canonical-user-2", "name": "alice", "status": "enabled"}})
            return
        if self.path == "/newmoi/user/update_info":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/user/update_status":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/user/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/workflow/v2/workflow-deployments":
            self._json({"code": "OK", "msg": "OK", "data": {"workflow": {"id": "wf-1", "name": "wf", "source_type": "manual_dsl", "execution_mode": "one_shot", "status": "ready"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/enable":
            self._json({"code": "OK", "msg": "OK", "data": {"workflow": {"id": "wf-1", "name": "wf", "source_type": "manual_dsl", "execution_mode": "one_shot", "status": "ready"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions":
            self._json({"code": "OK", "msg": "OK", "data": {"workflow_run": {"execution_id": "exec-1", "workflow_id": "wf-1", "status": "running", "execution_mode": "one_shot"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/refresh":
            self._json({"code": "OK", "msg": "OK", "data": {"execution": {"execution_id": "exec-1", "workflow_id": "wf-1", "status": "succeeded", "execution_mode": "one_shot"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/retry":
            self._json({"code": "OK", "msg": "OK", "data": {"workflow_run": {"execution_id": "exec-2", "workflow_id": "wf-1", "status": "running", "execution_mode": "one_shot"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/cancel":
            self._json({"code": "OK", "msg": "OK", "data": {"execution": {"execution_id": "exec-1", "workflow_id": "wf-1", "status": "cancelled", "execution_mode": "one_shot"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/nodes/node-1/reruns":
            self._json({"code": "OK", "msg": "OK", "data": {"rerun": {"rerun_id": "rerun-1", "branch_id": "branch-1", "case_id": "case-2", "mode": "continue_from_node", "status": "running"}}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/reruns/rerun-1/cancel":
            self._json({"code": "OK", "msg": "OK", "data": {"rerun": {"rerun_id": "rerun-1", "branch_id": "branch-1", "case_id": "case-2", "mode": "continue_from_node", "status": "cancelled"}}})
            return
        if self.path.startswith("/newmoi/lineage/"):
            self._json({"code": "OK", "msg": "OK", "data": _lineage_response(self.command, self.path)})
            return
        if self.path == "/newmoi/sessions":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1001, "title": "analysis", "source": "sdk", "user_id": "user-1"}})
            return
        if self.path == "/newmoi/table/overview":
            self._json({"code": "OK", "msg": "OK", "data": {"tables": [{"db_name": "analytics", "table_name": "orders", "col_names": ["id", "amount"]}]}})
            return
        if self.path == "/newmoi/table/database/tables":
            self._json({"code": "OK", "msg": "OK", "data": {"tables": [{"db_name": "analytics", "table_name": "orders", "col_names": ["id", "amount"]}]}})
            return
        if self.path == "/newmoi/table/columns":
            table_name = body.get("table_name") or "orders"
            self._json({"code": "OK", "msg": "OK", "data": {"db_name": "analytics", "table_name": table_name, "col_names": ["id", "amount"]}})
            return
        if self.path == "/newmoi/messages/session/list":
            self._json({"code": "OK", "msg": "OK", "data": {"messages": [{"id": 1, "session_id": 1001, "source": "explore", "role": "assistant", "content": "done", "status": "success"}]}})
            return
        if self.path == "/newmoi/connectors":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "conn-1"}})
            return
        if self.path == "/newmoi/connectors/get":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "conn-1"}})
            return
        if self.path == "/newmoi/connectors/file/preview":
            self._json({"code": "OK", "msg": "OK", "data": {"conn_file_id": "cf-1", "file_type": 1, "rows": []}})
            return
        if self.path == "/newmoi/connectors/file/download":
            self._json({"code": "OK", "msg": "OK", "data": {"url": "https://example.test/cf-1"}})
            return
        if self.path == "/newmoi/connectors/file/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/connectors/db/database/list":
            self._json({"code": "OK", "msg": "OK", "data": {"databases": ["db1"]}})
            return
        if self.path == "/newmoi/connectors/db/database/schema/list":
            self._json({"code": "OK", "msg": "OK", "data": {"schemas": ["public"]}})
            return
        if self.path == "/newmoi/connectors/db/database/table/list":
            self._json({"code": "OK", "msg": "OK", "data": {"tables": ["orders"]}})
            return
        if self.path == "/newmoi/connectors/db/schema":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "columns": [
                            {
                                "name": "id",
                                "data_type": "INT",
                                "mapped_type": "INT64",
                                "is_primary_key": True,
                                "is_nullable": False,
                                "is_auto_incr": True,
                            }
                        ]
                    },
                }
            )
            return
        if self.path == "/newmoi/connectors/mo/database/list":
            self._json({"code": "OK", "msg": "OK", "data": {"databases": ["analytics"]}})
            return
        if self.path == "/newmoi/connectors/mo/database/table/list":
            self._json({"code": "OK", "msg": "OK", "data": {"tables": ["orders"]}})
            return
        if self.path == "/newmoi/connectors/mo/check_table_name":
            self._json({"code": "OK", "msg": "OK", "data": {"exists": False}})
            return
        if self.path == "/newmoi/connectors/mo/column/mapping":
            self._json({"code": "OK", "msg": "OK", "data": {"column_map": {"src_id": ["id"]}, "need_mapping_columns": ["src_id"]}})
            return
        if self.path == "/newmoi/task":
            self._json({"code": "OK", "msg": "OK", "data": {"task_id": "task-1"}})
            return
        if self.path == "/newmoi/task/update":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/task/pause":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/task/resume":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/task/retry":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/task/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/export/task/create":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "export-1"}})
            return
        if self.path == "/newmoi/export/task/info":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "export-1"}})
            return
        if self.path == "/newmoi/export/task/files":
            self._json({"code": "OK", "msg": "OK", "data": {"files": []}})
            return
        if self.path == "/newmoi/export/task/export-1/rerun":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/export/volumes/30/files":
            self._json({"code": "OK", "msg": "OK", "data": {"items": []}})
            return
        if self.path == "/newmoi/export/task/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/llm/probe-models":
            self._json({"code": "OK", "msg": "OK", "data": {"models": ["gpt-4.1"]}})
            return
        if self.path == "/newmoi/llm/backends":
            self._json({"code": "OK", "msg": "OK", "data": _provider_backend_payload(1, "openai", models=["gpt-4.1"])})
            return
        if self.path == "/newmoi/llm/backends/1/endpoints":
            self._json({"code": "OK", "msg": "OK", "data": _provider_endpoint_payload(2, 1, "https://llm-2.example.test")})
            return
        if self.path == "/newmoi/llm/backends/1/probe-models":
            self._json({"code": "OK", "msg": "OK", "data": {"models": ["gpt-4.1"]}})
            return
        if self.path == "/newmoi/llm/setup":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "backend": _provider_backend_payload(5, "setup", models=["gpt-4.1"]),
                        "endpoint": _provider_endpoint_payload(6, 5, "https://setup.example.test"),
                    },
                }
            )
            return
        if self.path == "/newmoi/embedding/probe-models":
            self._json({"code": "OK", "msg": "OK", "data": {"models": ["bge-m3"]}})
            return
        if self.path == "/newmoi/embedding/backends":
            self._json({"code": "OK", "msg": "OK", "data": _provider_backend_payload(3, "bge", "EMBEDDING", models=["bge-m3"])})
            return
        if self.path == "/newmoi/embedding/backends/3/probe-models":
            self._json({"code": "OK", "msg": "OK", "data": {"models": ["bge-m3"]}})
            return
        if self.path == "/newmoi/parser/backends":
            self._json({"code": "OK", "msg": "OK", "data": _provider_backend_payload(4, "doc-parser", "PARSER", supported_mime_types=["application/pdf"])})
            return
        if self.path == "/newmoi/alerting/receiver":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/alerting/workspace/alert/rule/create":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/alerting/workspace/alert/rule/list":
            self._json({"code": "OK", "msg": "OK", "data": {"total": 1, "alerts": [_alert_rule_payload()]}})
            return
        if self.path == "/newmoi/alerting/workspace/alert/rule/update":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/alerting/history/list":
            self._json({"code": "OK", "msg": "OK", "data": {"total": 1, "histories": [_alert_history_payload()]}})
            return
        if self.path == "/newmoi/alerting/history/read/group":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/alerting/workspace/alert/rule/delete":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/compute-resources":
            self._json({"code": "OK", "msg": "OK", "data": _compute_resource_payload()})
            return
        if self.path == "/newmoi/compute-resources/compute-1/adopt-legacy-ownership":
            self._json({"code": "OK", "msg": "OK", "data": {"workspace_id": "ws-created", "resource_type": "compute_resource", "resource_id": "compute-1", "owner_role_id": "role-superadmin", "authorized_role_id": "role-superadmin", "status": "active", "ownership_version": 1}})
            return
        if self.path == "/newmoi/compute-resources/compute-1/suspend":
            self._json({"code": "OK", "msg": "OK", "data": _compute_resource_payload(status="suspended")})
            return
        if self.path == "/newmoi/compute-resources/compute-1/resume":
            self._json({"code": "OK", "msg": "OK", "data": _compute_resource_payload(status="IDLE")})
            return
        if self.path == "/newmoi/compute-resources/compute-1/retry":
            self._json({"code": "OK", "msg": "OK", "data": _compute_resource_payload(status="retrying")})
            return
        if self.path == "/newmoi/data-share/workspace-names":
            self._json({"code": "OK", "msg": "OK", "data": {"workspaces": [{"id": "ws-2", "name": "Target"}]}})
            return
        if self.path == "/newmoi/data-share/workspaces/resolve-names":
            self._json({"code": "OK", "msg": "OK", "data": {"workspaces": [{"id": "cross-user-ws", "name": "Cross User Workspace"}]}})
            return
        if self.path == "/newmoi/data-share/publishes":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "id": "publish-1",
                        "name": "orders-share",
                        "source_database_id": "101",
                        "mo_database_name": "orders",
                        "table_scope": {"mode": "selected", "object_ids": ["201"]},
                        "obj_display_name": "Orders",
                        "obj_display_path": "Catalog/Orders",
                        "targets": [{"workspace_id": "ws-2", "workspace_name": "Target"}],
                        "permission": "owner",
                        "remark": "daily",
                        "created_by": "user-1",
                        "created_at": "2026-06-01T00:00:00Z",
                        "updated_at": "2026-06-01T00:00:00Z",
                    },
                }
            )
            return
        if self.path == "/newmoi/data-share/subscriptions/sub-1/subscribe":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "id": "sub-1",
                        "pub_name": "orders-share",
                        "source_database_id": "101",
                        "mo_database_name": "orders",
                        "table_scope": {"mode": "selected", "object_ids": ["201"]},
                        "source_workspace_id": "ws-source",
                        "source_workspace_name": "Source",
                        "publisher": "alice",
                        "published_at": "2026-06-01T00:00:00Z",
                        "status": "subscribed",
                        "sub_name": "orders-copy",
                        "target_database_id": "301",
                        "subscribed_by": "user-1",
                        "created_at": "2026-06-01T00:00:00Z",
                    },
                }
            )
            return
        if self.path == "/newmoi/data-share/subscriptions/sub-1/unsubscribe":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/workbook/create":
            self._json({"code": "OK", "msg": "OK", "data": {"workbook_id": "wb-1", "name": "analysis"}})
            return
        if self.path == "/newmoi/workbook/list":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "total": 1,
                        "result": [{"workbook_id": "wb-1", "name": "analysis"}],
                        "next_page_token": "workbooks-next",
                    },
                }
            )
            return
        if self.path == "/newmoi/workbook/update":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/workbook/version/list":
            self._json({"code": "OK", "msg": "OK", "data": {"total": 1, "result": [{"id": "ver-1", "name": "v1", "status": "draft"}]}})
            return
        if self.path == "/newmoi/workbook/version/create":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "ver-1", "version": "v1", "status": "draft"}})
            return
        if self.path == "/newmoi/workbook/detail":
            self._json({"code": "OK", "msg": "OK", "data": {"sql_content": "select 1", "created_at": "2026-06-01T00:00:00Z", "updated_at": "2026-06-01T00:00:00Z"}})
            return
        if self.path == "/newmoi/workbook/version/update":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/workbook/version/save":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/workbook/delete":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/query/execute":
            self._json({"code": "OK", "msg": "OK", "data": {"id": "query-1", "query_id": "query-1"}})
            return
        if self.path == "/newmoi/query/describe":
            self._json({"code": "OK", "msg": "OK", "data": {"query_id": "query-1", "created_at": "2026-06-01T00:00:00Z", "statement_id": "stmt-1", "db_name": "db1", "status": "running"}})
            return
        if self.path == "/newmoi/query/kill":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/query/result":
            self._json({"code": "OK", "msg": "OK", "data": {"statement_id": "stmt-1", "status": "success", "offset": 0, "limit": 50, "total": 0, "result": []}})
            return
        if self.path == "/newmoi/query/result/download":
            data = b"c1\n1\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/newmoi/query/detail":
            self._json({"code": "OK", "msg": "OK", "data": {"statement_id": "stmt-1", "status": "Success"}})
            return
        if self.path == "/newmoi/query/profile":
            self._json({"code": "OK", "msg": "OK", "data": {"statement_id": "stmt-1", "profile": {"code": 200, "message": "OK", "success": True}}})
            return
        if self.path == "/newmoi/meta/db/info":
            self._json({"code": "OK", "msg": "OK", "data": {"total": 1, "result": [{"db_name": "db1", "db_owner": "u"}], "next_page_token": "db1"}})
            return
        if self.path == "/newmoi/meta/db/tree":
            self._json({"code": "OK", "msg": "OK", "data": {"db_list": [{"db_name": "db1", "db_owner": "u"}]}})
            return
        if self.path == "/newmoi/meta/db/table":
            self._json({"code": "OK", "msg": "OK", "data": {"db_name": "db1", "tables": {"tables": [{"name": "orders"}], "total": 1}, "views": {"tables": [{"name": "orders_view"}], "total": 1}}})
            return
        if self.path == "/newmoi/meta/table/info":
            self._json({"code": "OK", "msg": "OK", "data": {"columns": [{"name": "id", "data_type": "INT"}], "total": 1, "rows": 10}})
            return
        if self.path == "/newmoi/meta/table/column":
            self._json({"code": "OK", "msg": "OK", "data": {"columns": [{"name": "id", "data_type": "INT"}], "total": 1}})
            return
        if self.path == "/newmoi/meta/table/column_stat":
            self._json({"code": "OK", "msg": "OK", "data": {"columns": [{"name": "id", "data_type": "INT"}], "total": 1}})
            return
        if self.path == "/newmoi/meta/table/ddl":
            self._json({"code": "OK", "msg": "OK", "data": {"create_sql": "CREATE TABLE orders"}})
            return
        if self.path == "/newmoi/meta/table/drop":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/meta/view/drop":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        if self.path == "/newmoi/meta/db/drop":
            self._json({"code": "OK", "msg": "OK", "data": None})
            return
        self.send_error(404)

    def do_PATCH(self):
        length = int(self.headers.get("Content-Length") or "0")
        body = json.loads(self.rfile.read(length) or b"{}")
        self.__class__.requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), body))
        if self.path == "/newmoi/workspaces/ws-created":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {"workflow": {"id": "wf-1", "name": "wf2", "source_type": "manual_dsl", "status": "ready", "execution_mode": "one_shot", "dsl_yaml": "workflow:\n  name: wf"}},
                }
            )
            return
        self.send_error(404)

    def do_PUT(self):
        length = int(self.headers.get("Content-Length") or "0")
        body = json.loads(self.rfile.read(length) or b"{}") if length else None
        self.__class__.requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), body))
        if self.path == "/newmoi/workspaces/ws-1/iam/users/canonical-user-2/role-bindings":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "user_id": "canonical-user-2",
                        "assigned_role_ids": ["role-20"],
                        "default_role_id": "role-20",
                        "binding_version": 5,
                        "default_role_version": 5,
                        "audit_event_id": "audit-1",
                        "idempotent_replay": False,
                        "request_id": "write-1",
                        "trace_id": "trace-2",
                    },
                }
            )
            return
        if self.path == "/newmoi/sessions/1001":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1001, "title": "analysis", "source": "sdk", "user_id": "user-1"}})
            return
        if self.path == "/newmoi/sessions/1001/pin":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1001, "title": "analysis", "source": "sdk", "user_id": "user-1"}})
            return
        if self.path == "/newmoi/messages/msg-1/like":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "session_id": 1001, "source": "explore", "role": "assistant", "content": "done", "status": "success"}})
            return
        if self.path == "/newmoi/messages/msg-1/dislike":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "session_id": 1001, "source": "explore", "role": "assistant", "content": "done", "status": "success"}})
            return
        if self.path == "/newmoi/connectors/conn-1":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators/1":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "node_id": "moi:custom.operator:workspace:text_counter", "name": "Counter", "identifier": "text_counter", "enabled": True}})
            return
        if self.path == "/newmoi/workflow-templates/1":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1, "name": "tpl2", "dsl_yaml": "workflow:\n  name: tpl2", "description": "desc2"}})
            return
        if self.path == "/newmoi/semantic-models/101":
            self._json({"code": "OK", "msg": "OK", "data": {"updated": True}})
            return
        if self.path == "/newmoi/semantic-models/101/entries/201":
            self._json({"code": "OK", "msg": "OK", "data": {"updated": True}})
            return
        if self.path == "/newmoi/llm/backends/1":
            self._json({"code": "OK", "msg": "OK", "data": _provider_backend_payload(1, "openai-prod", models=["gpt-4.1-mini"])})
            return
        if self.path == "/newmoi/llm/backends/1/endpoints/2/status":
            self._json({"code": "OK", "msg": "OK", "data": {"success": True}})
            return
        if self.path == "/newmoi/llm/router":
            self._json({"code": "OK", "msg": "OK", "data": {"strategy": "round_robin", "health_check_interval": 30, "max_retries": 2, "session_affinity": False}})
            return
        if self.path == "/newmoi/embedding/router":
            self._json({"code": "OK", "msg": "OK", "data": {"strategy": "sticky", "health_check_interval": 30, "max_retries": 1, "session_affinity": True}})
            return
        if self.path == "/newmoi/alerting/receiver":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/compute-resources/compute-1":
            self._json({"code": "OK", "msg": "OK", "data": _compute_resource_payload()})
            return
        if self.path == "/newmoi/data-share/publishes/publish-1":
            self._json(
                {
                    "code": "OK",
                    "msg": "OK",
                    "data": {
                        "id": "publish-1",
                        "name": "orders-share",
                        "source_database_id": "101",
                        "mo_database_name": "orders",
                        "table_scope": {"mode": "selected", "object_ids": ["201", "202"]},
                        "targets": [{"workspace_id": "ws-2"}, {"workspace_id": "ws-3"}],
                        "permission": "owner",
                        "remark": "expanded",
                        "created_by": "user-1",
                        "created_at": "2026-06-01T00:00:00Z",
                        "updated_at": "2026-06-02T00:00:00Z",
                    },
                }
            )
            return
        self.send_error(404)

    def do_DELETE(self):
        self.__class__.requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), None))
        if self.path == "/newmoi/workspaces/ws-created":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1":
            self._json({"code": "OK", "msg": "OK", "data": {"deleted": True}})
            return
        if self.path == "/newmoi/workflow/v2/workflow-apps/wf-1":
            self._json({"code": "OK", "msg": "OK", "data": {"deleted": True}})
            return
        if self.path == "/newmoi/workflow/v2/custom-operators/1":
            self._json({"code": "OK", "msg": "OK", "data": {"deleted": True}})
            return
        if self.path == "/newmoi/workflow-templates/1":
            self._json({"code": "OK", "msg": "OK", "data": {"message": "deleted"}})
            return
        if self.path == "/newmoi/sessions/1001/pin":
            self._json({"code": "OK", "msg": "OK", "data": {"id": 1001, "title": "analysis", "source": "sdk", "user_id": "user-1"}})
            return
        if self.path == "/newmoi/messages/msg-1":
            self._json({"code": "OK", "msg": "OK", "data": {"deleted": True}})
            return
        if self.path == "/newmoi/sessions/1001":
            self._json({"code": "OK", "msg": "OK", "data": {"deleted": True}})
            return
        if self.path == "/newmoi/connectors/conn-1":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/semantic-models/101/entries/201":
            self._json({"code": "OK", "msg": "OK", "data": {"deleted": True}})
            return
        if self.path == "/newmoi/semantic-models/101":
            self._json({"code": "OK", "msg": "OK", "data": {"deleted": True}})
            return
        if self.path == "/newmoi/llm/backends/1":
            self._json({"code": "OK", "msg": "OK", "data": {"success": True}})
            return
        if self.path == "/newmoi/alerting/receiver":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/compute-resources/compute-1?force=true":
            self._json({"code": "OK", "msg": "OK"})
            return
        if self.path == "/newmoi/data-share/publishes/publish-1":
            self._json({"code": "OK", "msg": "OK"})
            return
        self.send_error(404)

    def _json(self, value, status=200):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _request_body(self, raw_body):
        content_type = self.headers.get("Content-Type", "")
        if content_type.startswith("multipart/form-data;"):
            message = BytesParser(policy=default).parsebytes(
                b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + raw_body
            )
            part = next(message.iter_parts())
            return {
                "filename": part.get_filename(),
                "data": part.get_payload(decode=True).decode(),
            }
        return json.loads(raw_body or b"{}")


class WorkspaceFacadeTest(unittest.TestCase):
    def setUp(self):
        self._proxy_env = {key: os.environ.get(key) for key in ("NO_PROXY", "no_proxy")}
        for key, value in self._proxy_env.items():
            os.environ[key] = _with_localhost_no_proxy(value)
        _Handler.requests = []
        _Handler.catalog_created = False
        _Handler.database_created = False
        _Handler.drawing_search_data = _UNSET
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        for key, value in self._proxy_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_apps_domain_is_not_exposed(self):
        self.assertFalse(hasattr(sdk.Client, "apps"))
        self.assertFalse(hasattr(sdk.WorkspaceHandle, "apps"))
        self.assertFalse(hasattr(sdk_client, "AppService"))
        self.assertFalse(hasattr(sdk_client, "HRScreeningService"))
        self.assertFalse(any(name.startswith("with_hr_screening_") for name in dir(sdk_client)))
        self.assertFalse(any(name.startswith("with_hr_screening_") for name in sdk.__all__))

    def test_dashboard_task_execution_overview_uses_workspace_scope(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        overview = client.dashboard("ws-created").task_execution_overview()

        self.assertEqual(overview.running, 1)
        self.assertEqual(overview.success, 2)
        self.assertEqual(overview.failed, 3)
        self.assertEqual(overview.pending, 4)
        self.assertEqual(overview.total, 10)
        self.assertEqual(overview.window_days, 7)
        self.assertEqual(
            _Handler.requests,
            [
                ("GET", "/newmoi/dashboard/task-execution-overview", "ws-created", None),
            ],
        )

    def test_catalog_search_data_dashboard_tables_uses_workspace_scope(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.catalog("ws-created").search_data_dashboard_tables(
            search="ord", page_size=25, page_token="5"
        )

        self.assertEqual(result.total, 2)
        self.assertEqual(result.next_page_token, "10")
        self.assertEqual(result.items[0].database_name, "sales")
        self.assertEqual(list(result.items[0].matched_columns), ["order_id"])
        self.assertTrue(result.items[0].metadata_match)
        self.assertEqual(
            _Handler.requests,
            [
                (
                    "POST",
                    "/newmoi/catalog/data-dashboard/table-search",
                    "ws-created",
                    {"search": "ord", "page_size": 25, "page_token": "5"},
                ),
            ],
        )

    def test_query_history_bodies_default_to_five_minute_range(self):
        for body in (sdk_client._query_history_body(()), sdk_client._query_history_overview_body(())):
            start = datetime.fromisoformat(body["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(body["end"].replace("Z", "+00:00"))
            self.assertEqual(end - start, sdk_client.DEFAULT_QUERY_HISTORY_LOOKBACK)

        list_body = sdk_client._query_history_body((sdk_client.with_query_history_start("2026-07-29T10:00:00Z"),))
        overview_body = sdk_client._query_history_overview_body(
            (sdk_client.with_query_history_overview_end("2026-07-29T10:00:00Z"),)
        )
        self.assertEqual(list_body, {"start": "2026-07-29T10:00:00Z"})
        self.assertEqual(overview_body, {"end": "2026-07-29T10:00:00Z"})

    def test_query_history_non_user_is_public_and_serialized(self):
        self.assertIs(sdk.with_query_history_non_user, sdk_client.with_query_history_non_user)
        body = sdk_client._query_history_body((sdk.with_query_history_non_user(True),))
        self.assertEqual(body.get("non_user"), True)
        self.assertIn("start", body)
        self.assertIn("end", body)

    def test_private_catalog_upload_uses_workspace_scoped_route(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.catalog("ws-created").upload_private_bytes("resume.pdf", b"pdf")

        self.assertEqual(result.file_id, "file-private-1")
        self.assertEqual(result.catalog_file.workspace_id, "ws-created")
        self.assertEqual(result.catalog_file.volume_id, 17)
        self.assertEqual(
            _Handler.requests,
            [
                (
                    "POST",
                    "/newmoi/workspaces/ws-created/catalog-files/uploads",
                    "ws-created",
                    {"filename": "resume.pdf", "data": "pdf"},
                ),
            ],
        )


    def test_client_never_retries_http(self):
        attempts = []
        original_urlopen = sdk_client.urllib.request.urlopen

        def failing_urlopen(req, timeout=None):
            attempts.append(req.get_method())
            raise urllib.error.URLError("transport unavailable")

        sdk_client.urllib.request.urlopen = failing_urlopen
        try:
            client = sdk.Client("https://product.example.test", sdk.with_api_key("user-key"))
            with self.assertRaises(sdk.Error) as captured:
                client.workspaces().list()
            self.assertEqual(captured.exception.code, "ErrTransportUnavailable")
            self.assertEqual(attempts, ["GET"])

            attempts.clear()
            with self.assertRaises(sdk.Error) as captured:
                client.workspaces().create("workspace")
            self.assertEqual(captured.exception.code, "ErrTransportUnavailable")
            self.assertEqual(attempts, ["POST"])
        finally:
            sdk_client.urllib.request.urlopen = original_urlopen

    def test_client_uses_endpoint_path_as_product_base_path(self):
        seen_paths = []

        class CustomPrefixHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                seen_paths.append(self.path)
                if self.path != "/tenant/moi/workspaces":
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"code":"OK","msg":"OK","data":{"total":0,"workspaces":[]}}')

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), CustomPrefixHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/tenant/moi", sdk.with_api_key("user-key"))
            client.workspaces().list()
            self.assertEqual(seen_paths, ["/tenant/moi/workspaces"])
            self.assertNotIn("/newmoi", seen_paths[0])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_sql_query_websocket_url_uses_endpoint_path_as_product_base_path(self):
        client = sdk.Client("https://product.example.test/tenant/moi", sdk.with_api_key("user-key"))
        got = client.sql("ws-1").query_websocket_url()
        self.assertEqual(got, "wss://product.example.test/tenant/moi/query/ws")
        self.assertNotIn("/newmoi", got)

    def test_ensure_workspace_and_scoped_handle(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.ensure_workspace("analytics")
        self.assertEqual(workspace.id, "ws-created")
        self.assertEqual(workspace.name, "analytics")
        known_workspace = client.workspace("ws-created")
        self.assertEqual(known_workspace.id, "ws-created")

        health = workspace.catalog().health()
        self.assertEqual(health.status, "ok")
        connection = workspace.db_connection()
        self.assertEqual(connection.host, "mo.example.test")
        self.assertEqual(list(connection.session_init_sqls), ["SET ROLE moi_role_2", "SET enable_remap_hint = 1"])
        self.assertEqual(connection.effective_role_id, "2")
        self.assertEqual(connection.effective_role_db_role, "moi_role_2")
        self.assertEqual(list(sdk.DBConnectionResult().session_init_sqls), [])
        self.assertEqual(connection.port, 6001)
        logs = workspace.recent_failed_audit_logs(5)
        self.assertEqual(logs.total, 1)
        self.assertEqual(logs.items[0].result, "failed")
        catalog = workspace.prepare_catalog("orders", sdk.with_catalog_description("lake"))
        self.assertEqual(catalog.id, 10)
        self.assertEqual(catalog.name, "orders")
        volume = workspace.prepare_data_volume("orders", "raw", "landing")
        database = volume._database
        self.assertEqual(database.id, 20)
        self.assertEqual(database.name, "raw")
        self.assertEqual(database._catalog.id, 10)
        self.assertEqual(database._catalog.name, "orders")
        self.assertEqual(volume.id, 30)
        self.assertEqual(volume.name, "landing")
        uploaded = volume.upload_bytes("orders.csv", b"id,name\n1,alice\n")
        self.assertEqual(uploaded.file_id, "file-1")
        with tempfile.NamedTemporaryFile(prefix="local-orders-", suffix=".csv", delete=False) as file_obj:
            local_path = file_obj.name
            file_obj.write(b"id,name\n2,bob\n")
        self.addCleanup(lambda: os.path.exists(local_path) and os.remove(local_path))
        local_uploaded = volume.upload_file(local_path)
        self.assertEqual(local_uploaded.file_id, "file-1")
        file = volume.upload_bytes_handle("orders.csv", b"id,name\n1,alice\n")
        self.assertEqual(file.id, "file-1")
        info = file.info()
        self.assertEqual(info.file_name, "orders.csv")
        triggered = file.trigger_workflows()
        self.assertEqual(triggered.triggered, 1)
        file.delete_ref()
        file.delete()
        local_file = volume.upload_file_handle(local_path)
        self.assertEqual(local_file.id, "file-1")
        volume_preview = volume.upload_bytes_preview("volume-preview.csv", b"id,name\n3,carol\n")
        self.assertEqual(volume_preview.file.id, "file-1")
        self.assertIsNotNone(volume_preview.preview)
        volume_preview.preview.close()
        local_volume_preview = volume.upload_file_preview(local_path)
        self.assertEqual(local_volume_preview.file.id, "file-1")
        self.assertIsNotNone(local_volume_preview.preview)
        local_volume_preview.preview.close()
        named_file = workspace.upload_bytes_to_data_volume("orders", "raw", "landing", "named.csv", b"id,name\n3,carol\n")
        self.assertEqual(named_file.id, "file-1")
        named_local_file = workspace.upload_file_to_data_volume("orders", "raw", "landing", local_path)
        self.assertEqual(named_local_file.id, "file-1")
        previewed = workspace.upload_bytes_preview_to_data_volume("orders", "raw", "landing", "preview.csv", b"id,name\n4,dana\n")
        self.assertEqual(previewed.file.id, "file-1")
        self.assertIsNotNone(previewed.preview)
        previewed.preview.close()
        local_previewed = workspace.upload_file_preview_to_data_volume("orders", "raw", "landing", local_path)
        self.assertEqual(local_previewed.file.id, "file-1")
        self.assertIsNotNone(local_previewed.preview)
        local_previewed.preview.close()
        selected = workspace.prepare_data_volume("orders", "raw", "landing")
        self.assertEqual(selected.id, 30)
        full_path = selected.full_path()
        self.assertEqual(full_path.path, "orders/raw/landing")
        named_full_path = workspace.data_volume_full_path("orders", "raw", "landing")
        self.assertEqual(named_full_path.path, "orders/raw/landing")
        renamed_catalog = selected._database._catalog.rename("orders-renamed", sdk.with_catalog_description("renamed catalog"))
        self.assertIs(renamed_catalog, selected._database._catalog)
        self.assertEqual(renamed_catalog.name, "orders-renamed")
        renamed_database = selected._database.update_description("renamed database")
        self.assertIs(renamed_database, selected._database)
        renamed_volume = selected.rename("landing_renamed", sdk.with_catalog_description("renamed volume"))
        self.assertIs(renamed_volume, selected)
        self.assertEqual(renamed_volume.name, "landing_renamed")
        self.assertEqual(renamed_catalog.info().catalog.name, "orders-renamed")
        self.assertEqual(renamed_database.info().database.name, "raw_renamed")
        self.assertEqual(renamed_volume.info().volume.name, "landing_renamed")
        selected.delete()
        selected._database.delete()
        selected._database._catalog.delete()
        workspace.delete()

        local_name = os.path.basename(local_path)
        expected = [
            ("GET", "/newmoi/workspaces?name=analytics", None, None),
            ("POST", "/newmoi/workspaces", None, {"name": "analytics"}),
            ("GET", "/newmoi/catalog/healthz", "ws-created", None),
            ("GET", "/newmoi/user/me/db-connection", "ws-created", None),
            ("GET", "/newmoi/audit/logs?result=failed&page=1&page_size=5", "ws-created", None),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/create", "ws-created", {"name": "orders", "description": "lake"}),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/create", "ws-created", {"catalog_id": 10, "name": "raw"}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": "orders.csv", "data": "id,name\n1,alice\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": local_name, "data": "id,name\n2,bob\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": "orders.csv", "data": "id,name\n1,alice\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/info", "ws-created", {"file_id": "file-1"}),
            ("POST", "/newmoi/catalog/file/trigger_workflow", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/delete_ref", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/delete", "ws-created", {"id": "file-1", "volume_id": "30"}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": local_name, "data": "id,name\n2,bob\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": "volume-preview.csv", "data": "id,name\n3,carol\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/preview_stream", "ws-created", {"volume_id": "30", "file_id": "file-1"}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": local_name, "data": "id,name\n2,bob\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/preview_stream", "ws-created", {"volume_id": "30", "file_id": "file-1"}),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": "named.csv", "data": "id,name\n3,carol\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": local_name, "data": "id,name\n2,bob\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": "preview.csv", "data": "id,name\n4,dana\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/preview_stream", "ws-created", {"volume_id": "30", "file_id": "file-1"}),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/file/upload", "ws-created", {"filename": local_name, "data": "id,name\n2,bob\n"}),
            ("POST", "/newmoi/catalog/file/create", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/preview_stream", "ws-created", {"volume_id": "30", "file_id": "file-1"}),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/volume/full_path", "ws-created", {"id": 30}),
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/volume/full_path", "ws-created", {"id": 30}),
            ("POST", "/newmoi/catalog/update", "ws-created", {"id": 10, "name": "orders-renamed", "description": "renamed catalog"}),
            ("POST", "/newmoi/catalog/database/update", "ws-created", {"id": 20, "description": "renamed database"}),
            ("POST", "/newmoi/catalog/volume/update", "ws-created", {"id": 30, "name": "landing_renamed", "description": "renamed volume"}),
            ("POST", "/newmoi/catalog/info", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/info", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/volume/info", "ws-created", {"id": "30"}),
            ("POST", "/newmoi/catalog/volume/delete", "ws-created", {"id": 30}),
            ("POST", "/newmoi/catalog/database/delete", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/delete", "ws-created", {"id": 10}),
            ("DELETE", "/newmoi/workspaces/ws-created", None, None),
        ]
        self.assertEqual(_Handler.requests, expected)
        direct_volume = database.prepare_volume("landing")
        self.assertEqual(direct_volume.id, 30)
        self.assertEqual(direct_volume.name, "landing")
        self.assertEqual(_Handler.requests[-1], ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}))

    def test_workspace_member_handle_scopes_requests(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        workspace = client.workspace("ws-1")

        invitation = workspace.invite_member(
            "alice",
            10,
            sdk.with_user_email("alice@example.test"),
            sdk.with_user_role_ids(10),
            sdk.with_user_auto_accept(True),
        )
        self.assertIsInstance(invitation, sdk.WorkspaceMemberInviteResult)
        self.assertEqual(invitation.id, "canonical-user-2")
        self.assertEqual(_Handler.requests, [
            ("POST", "/newmoi/user/create", "ws-1", {"name": "alice", "email": "alice@example.test", "role_id_list": [10], "default_role_id": 10, "auto_accept": True}),
        ])
        # Acceptance is out of band; bind the handle only after active membership is observed.
        user = workspace.member("canonical-user-2")
        self.assertEqual(user.info().id, "canonical-user-2")
        user.update("Alice", "Finance", sdk.with_user_tag(1, "finance"))
        iam = workspace.iam()
        bindings = iam.user_role_bindings("canonical-user-2")
        self.assertEqual(bindings.default_role_id, "role-20")
        expected_binding_version = sdk.iam_binding_version_number(bindings)
        expected_default_role_version = bindings.default_role_version
        updated_bindings = iam.put_user_role_bindings(
            "canonical-user-2",
            sdk.IAMUserRoleBindingsRequest(
                assigned_role_ids=["role-20"],
                default_role_id="role-20",
                expected_binding_version=expected_binding_version,
                expected_default_role_version=expected_default_role_version,
                request_id="write-1",
            ),
        )
        self.assertEqual(updated_bindings.binding_version, 5)
        user.update_status("disable")
        user.delete()

        with self.assertRaises(sdk.Error) as user_error:
            workspace.member("")
        self.assertEqual(user_error.exception.code, "ErrIDRequired")

        with self.assertRaises(sdk.Error) as missing_contact_error:
            workspace.members().invite("missing-contact", 10)
        self.assertEqual(missing_contact_error.exception.code, "ErrInvitationContactRequired")
        with self.assertRaises(sdk.Error) as ambiguous_contact_error:
            workspace.members().invite(
                "ambiguous-contact", 10,
                sdk.with_user_email("alice@example.test"),
                sdk.with_user_mobile_number("13800138000"),
            )
        self.assertEqual(ambiguous_contact_error.exception.code, "ErrInvitationContactConflict")
        with self.assertRaises(sdk.Error) as invalid_mobile_error:
            workspace.members().invite(
                "invalid-mobile", 10,
                sdk.with_user_mobile_number("+8613800138000"),
            )
        self.assertEqual(invalid_mobile_error.exception.code, "ErrInvitationMobileNumberInvalid")
        with self.assertRaises(sdk.Error) as missing_default_error:
            workspace.members().invite(
                "missing-default", 0,
                sdk.with_user_email("alice@example.test"),
                sdk.with_user_role_ids(10),
            )
        self.assertEqual(missing_default_error.exception.code, "ErrDefaultRoleRequired")
        with self.assertRaises(sdk.Error) as unassigned_default_error:
            workspace.members().invite(
                "unassigned-default", 20,
                sdk.with_user_email("alice@example.test"),
                sdk.with_user_role_ids(10),
            )
        self.assertEqual(unassigned_default_error.exception.code, "ErrDefaultRoleNotAssigned")
        with self.assertRaises(sdk.Error) as github_conflict_error:
            workspace.members().invite(
                "github-conflict", 10,
                sdk.with_user_email("alice@example.test"),
                sdk.with_user_github_login("octocat"),
            )
        self.assertEqual(github_conflict_error.exception.code, "ErrInvitationContactConflict")
        with self.assertRaises(sdk.Error) as invalid_github_error:
            workspace.members().invite(
                "invalid-github", 0,
                sdk.with_user_github_login("-octocat"),
            )
        self.assertEqual(invalid_github_error.exception.code, "ErrInvitationGitHubLoginInvalid")
        with self.assertRaises(sdk.Error) as double_prefix_github_error:
            workspace.members().invite(
                "double-prefix-github", 0,
                sdk.with_user_github_login("@@octocat"),
            )
        self.assertEqual(double_prefix_github_error.exception.code, "ErrInvitationGitHubLoginInvalid")
        with self.assertRaises(sdk.Error) as missing_binding_id_error:
            iam.user_role_bindings("")
        self.assertEqual(missing_binding_id_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as invalid_binding_request_error:
            iam.put_user_role_bindings("canonical-user-2", object())
        self.assertEqual(invalid_binding_request_error.exception.code, "ErrRequestRequired")

        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/user/create", "ws-1", {"name": "alice", "email": "alice@example.test", "role_id_list": [10], "default_role_id": 10, "auto_accept": True}),
                ("POST", "/newmoi/user/detail_info", "ws-1", {"id": "canonical-user-2"}),
                ("POST", "/newmoi/user/update_info", "ws-1", {"id": "canonical-user-2", "name": "Alice", "description": "Finance", "tag_list": [{"id": 1, "value": "finance"}]}),
                ("GET", "/newmoi/workspaces/ws-1/iam/users/canonical-user-2/role-bindings", "ws-1", None),
                ("PUT", "/newmoi/workspaces/ws-1/iam/users/canonical-user-2/role-bindings", "ws-1", {"assigned_role_ids": ["role-20"], "default_role_id": "role-20", "expected_binding_version": expected_binding_version, "expected_default_role_version": expected_default_role_version, "request_id": "write-1", "clear_default_role": False}),
                ("POST", "/newmoi/user/update_status", "ws-1", {"id": "canonical-user-2", "action": "disable"}),
                ("POST", "/newmoi/user/delete", "ws-1", {"id": "canonical-user-2"}),
            ],
        )

    def test_github_login_invite_transport(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        workspace = client.workspace("ws-1")

        seated = workspace.invite_member("alice", 10, sdk.with_user_github_login("@OctoCat"), sdk.with_user_role_ids(10))
        self.assertEqual(seated.id, "canonical-user-2")
        with self.assertRaises(sdk.Error) as missing_role:
            workspace.invite_member("no-roles", 0, sdk.with_user_github_login("octocat"))
        self.assertEqual(missing_role.exception.code, "ErrDefaultRoleRequired")
        with self.assertRaises(sdk.Error) as unknown:
            workspace.invite_member("unknown", 10, sdk.with_user_github_login("new-user"), sdk.with_user_role_ids(10))
        self.assertEqual(unknown.exception.code, "ErrUserNotFound")
        self.assertEqual(unknown.exception.status, 404)
        self.assertEqual(unknown.exception.message, "Invitation account not found")
        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/user/create", "ws-1", {"name": "alice", "github_login": "octocat", "role_id_list": [10], "default_role_id": 10}),
                ("POST", "/newmoi/user/create", "ws-1", {"name": "unknown", "github_login": "new-user", "default_role_id": 10, "role_id_list": [10]}),
            ],
        )

    def test_member_list_decodes_pending_invitation(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        users = client.workspace("ws-1").members().members()
        self.assertEqual(users.total, 2)
        self.assertEqual(users.user_list[0].name, "alice")
        self.assertEqual(users.user_list[0].status, "enabled")
        pending = users.user_list[1]
        self.assertEqual(pending.id, "user-2")
        self.assertEqual(pending.iam_user_id, "moi-user-2")
        self.assertEqual(pending.status, "pending")
        self.assertEqual(pending.name, "bob")

    def test_ensure_workspace_rejects_duplicate_workspace_name(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        with self.assertRaises(sdk.Error) as raised:
            client.ensure_workspace("duplicate")

        self.assertEqual(raised.exception.code, "ErrDuplicateName")
        self.assertEqual(len(_Handler.requests), 1)
        self.assertEqual(_Handler.requests[0], ("GET", "/newmoi/workspaces?name=duplicate", None, None))

    def test_workspace_raw_contract_methods_send_caller_body(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        created = client.workspaces().create_raw({"name": "analytics"})

        self.assertEqual(created.id, "ws-created")
        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/workspaces", None, {"name": "analytics"}),
            ],
        )


    def test_catalog_browse_can_skip_child_statistics(self):
        _Handler.catalog_created = True
        _Handler.database_created = True
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        catalogs, _ = client.workspace("ws-created").catalogs(sdk.with_catalog_include_stats(False))
        databases, _ = catalogs[0].databases(sdk.with_catalog_include_stats(False))
        self.assertEqual(len(databases), 1)
        self.assertEqual(_Handler.requests, [
            ("POST", "/newmoi/catalog/list", "ws-created", {"include_stats": False}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10, "include_stats": False}),
        ])


    def test_workspace_catalog_browse_handles_scope_discovered_resources(self):
        _Handler.catalog_created = True
        _Handler.database_created = True
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        catalogs, catalog_list = workspace.catalogs()
        databases, database_list = catalogs[0].databases()
        children = databases[0].children()
        volumes, volume_children = databases[0].volumes()
        tables, table_children = databases[0].tables()
        volume_path = volumes[0].full_path()
        table_path = tables[0].full_path()

        self.assertEqual(len(catalogs), 1)
        self.assertEqual(catalogs[0].id, 10)
        self.assertEqual(catalogs[0].name, "orders")
        self.assertEqual(len(catalog_list.list), 1)
        self.assertEqual(catalog_list.list[0].display_name, "Orders")
        self.assertEqual(catalog_list.list[0].display_description, "Catalog shown in the workspace")
        self.assertEqual(list(catalog_list.list[0].allowed_actions), ["catalog.update_catalog"])
        self.assertEqual(len(databases), 1)
        self.assertEqual(databases[0].id, 20)
        self.assertEqual(databases[0].name, "raw")
        self.assertEqual(len(database_list.list), 1)
        self.assertEqual(database_list.list[0].display_name, "Raw Data")
        self.assertEqual(list(database_list.list[0].allowed_actions), ["database.update_database"])
        self.assertEqual(len(children.list), 2)
        self.assertEqual(children.list[0].display_description, "Landing volume")
        self.assertEqual(list(children.list[0].allowed_actions), ["volume.update"])
        self.assertEqual(len(volumes), 1)
        self.assertEqual(volumes[0].id, 30)
        self.assertEqual(volumes[0].name, "landing")
        self.assertEqual(len(volume_children.list), 2)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].id, 31)
        self.assertEqual(tables[0].name, "orders")
        self.assertEqual(len(table_children.list), 2)
        self.assertEqual(volume_path.path, "orders/raw/landing")
        self.assertEqual(table_path.path, "orders/raw/orders")

        expected = [
            ("POST", "/newmoi/catalog/list", "ws-created", {}),
            ("POST", "/newmoi/catalog/database/list", "ws-created", {"id": 10}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/database/children", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/volume/full_path", "ws-created", {"id": 30}),
            ("POST", "/newmoi/catalog/table/full_path", "ws-created", {"id": 31}),
        ]
        self.assertEqual(_Handler.requests, expected)

    def test_catalog_tree_preserves_numeric_and_string_node_ids(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        tree = client.workspace("ws-created").catalog().tree()

        self.assertEqual(tree.tree[0].id.number_value, 10)
        self.assertEqual(tree.tree[0].display_name, "Orders")
        self.assertEqual(tree.tree[0].node_list[0].id.string_value, "20")
        self.assertEqual(tree.tree[0].node_list[0].display_description, "User database leaf")
        self.assertEqual(_Handler.requests[-1], ("POST", "/newmoi/catalog/tree", "ws-created", {}))

    def test_catalog_system_tree_uses_name_key_nodes(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        tree = client.catalog("ws-created").system_tree()

        self.assertEqual(tree.tree[0].id.string_value, "system")
        self.assertEqual(tree.tree[0].display_name, "System")
        self.assertEqual(tree.tree[0].node_list[0].id.string_value, "system:database:system")
        self.assertEqual(tree.tree[0].node_list[0].node_list[0].id.string_value, "system:table:system:tables")
        self.assertEqual(tree.tree[0].node_list[0].node_list[0].display_description, "System table leaf")
        self.assertEqual(_Handler.requests[-1], ("POST", "/newmoi/catalog/system/tree", "ws-created", {}))
        client.catalog("ws-created").system_tree(include_table_leaves=False, database_name="system")
        self.assertEqual(_Handler.requests[-1], ("POST", "/newmoi/catalog/system/tree", "ws-created", {
            "include_table_leaves": False, "database_name": "system",
        }))

    def test_catalog_system_table_lookup_and_data_use_database_name(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        catalog = client.catalog("ws-created")

        info = catalog.table_info(
            0,
            sdk.with_table_lookup_name("tables"),
            sdk.with_table_lookup_database_name("system"),
        )
        data = catalog.table_data(
            0,
            sdk.with_table_data_name("tables"),
            sdk.with_table_data_database_name("system"),
            sdk.with_table_data_page(1),
            sdk.with_table_data_page_size(20),
        )
        preview = catalog.preview_table(
            0,
            sdk.with_table_data_name("tables"),
            sdk.with_table_data_database_name("system"),
            sdk.with_table_preview_lines(10),
        )

        self.assertEqual(info.name, "orders")
        self.assertEqual(data.total_rows, 1)
        self.assertEqual(preview.total_rows, 1)
        self.assertEqual(
            _Handler.requests[-3:],
            [
                (
                    "POST",
                    "/newmoi/catalog/table/info",
                    "ws-created",
                    {"name": "tables", "database_name": "system"},
                ),
                (
                    "POST",
                    "/newmoi/catalog/table/data",
                    "ws-created",
                    {"name": "tables", "database_name": "system", "page": 1, "page_size": 20},
                ),
                (
                    "POST",
                    "/newmoi/catalog/table/preview",
                    "ws-created",
                    {"name": "tables", "database_name": "system", "preview_lines": 10},
                ),
            ],
        )
        # Package root must re-export the system-table option helpers.
        self.assertIs(sdk.with_table_lookup_database_name, sdk_client.with_table_lookup_database_name)
        self.assertIs(sdk.with_table_data_database_name, sdk_client.with_table_data_database_name)

    def test_product_message_rejects_unknown_response_fields(self):
        with self.assertRaises(sdk.Error) as err:
            sdk_client._catalog_tree_result({"tree": [{"id": 10, "unexpected": True}]})

        self.assertEqual(err.exception.code, "ErrResponseInvalid")

    def test_workspace_catalog_table_handle_scopes_database_and_table(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        catalog = sdk.CatalogHandle(workspace, 10, "orders")
        database = sdk.DatabaseHandle(catalog, 20, "raw")
        columns = [sdk.TableColumn("id", "INT")]

        table, created = database.create_table_from_columns(
            "orders",
            columns,
            sdk.with_table_comment("order table"),
            sdk.with_table_data_file_url("s3://bucket/orders.csv"),
        )
        known = database.table(31)
        exists = database.table_exists("orders")
        overview = database.table_overview()
        info = table.info()
        data = table.data(sdk.with_table_data_page(2), sdk.with_table_data_page_size(50))
        preview = table.preview(sdk.with_table_preview_lines(25))
        path = table.full_path()
        table.truncate()
        table.delete()

        self.assertEqual(table.id, 31)
        self.assertEqual(table.name, "orders")
        self.assertEqual(known.id, 31)
        self.assertEqual(created.id, 31)
        self.assertTrue(exists.data)
        self.assertEqual(overview.tables[0].name, "orders")
        self.assertEqual(info.name, "orders")
        self.assertEqual(data.total_rows, 1)
        self.assertEqual(preview.total_rows, 1)
        self.assertEqual(path.path, "orders/raw/orders")

        expected = [
            (
                "POST",
                "/newmoi/catalog/table/create",
                "ws-created",
                {
                    "database_id": 20,
                    "name": "orders",
                    "columns": [{"name": "id", "type": "INT"}],
                    "comment": "order table",
                    "data_file_url": "s3://bucket/orders.csv",
                },
            ),
            ("POST", "/newmoi/catalog/table/exist", "ws-created", {"database_id": 20, "name": "orders"}),
            ("POST", "/newmoi/catalog/table/overview", "ws-created", {"id": 20}),
            ("POST", "/newmoi/catalog/table/info", "ws-created", {"id": 31}),
            ("POST", "/newmoi/catalog/table/data", "ws-created", {"id": 31, "page": 2, "page_size": 50}),
            ("POST", "/newmoi/catalog/table/preview", "ws-created", {"id": 31, "preview_lines": 25}),
            ("POST", "/newmoi/catalog/table/full_path", "ws-created", {"id": 31}),
            ("POST", "/newmoi/catalog/table/truncate", "ws-created", {"id": 31}),
            ("POST", "/newmoi/catalog/table/delete", "ws-created", {"id": 31}),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as table_error:
            database.table(0)
        self.assertEqual(table_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as create_name_error:
            database.create_table_from_columns("", columns)
        self.assertEqual(create_name_error.exception.code, "ErrNameRequired")
        with self.assertRaises(sdk.Error) as create_columns_error:
            database.create_table_from_columns("orders", [])
        self.assertEqual(create_columns_error.exception.code, "ErrColumnsRequired")
        with self.assertRaises(sdk.Error) as create_column_type_error:
            database.create_table_from_columns("orders", [sdk.TableColumn("id", "")])
        self.assertEqual(create_column_type_error.exception.code, "ErrTypeRequired")

    def test_catalog_run_nl2sql_returns_typed_rows(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.catalog("ws-created").run_nl2sql(20, "select id, amount from orders")

        self.assertEqual(list(result.columns), ["id", "amount"])
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(
            _Handler.requests,
            [
                (
                    "POST",
                    "/newmoi/catalog/nl2sql/run_sql",
                    "ws-created",
                    {"database_id": 20, "sql": "select id, amount from orders"},
                )
            ],
        )
        with self.assertRaises(sdk.Error) as database_error:
            client.catalog("ws-created").run_nl2sql(0, "select 1")
        self.assertEqual(database_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as sql_error:
            client.catalog("ws-created").run_nl2sql(20, "")
        self.assertEqual(sql_error.exception.code, "ErrSQLRequired")

    def test_catalog_data_asset_methods_return_typed_results(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        catalog = client.catalog("ws-created")
        asset = catalog.data_asset("asset-1")
        file_asset = catalog.file_data_asset("file-1")
        batch = catalog.batch_get_data_assets("file-1", "file-2")

        self.assertEqual(asset.asset.asset_id, "asset-1")
        self.assertEqual(asset.asset.meta["source"], "workflow")
        self.assertEqual(asset.derivations[0].target_asset_id, "asset-parsed-1")
        self.assertEqual(asset.manifest.parsed_asset_id, "asset-parsed-1")
        self.assertEqual(asset.assets_by_id["asset-1"].asset_ref, "file-1")
        self.assertEqual(file_asset.asset.raw_file_id, "file-1")
        self.assertEqual(batch.total, 1)
        self.assertEqual(batch.items[0].raw_file_id, "file-1")
        self.assertEqual(
            _Handler.requests,
            [
                ("GET", "/newmoi/catalog/data-assets/asset-1", "ws-created", None),
                ("GET", "/newmoi/catalog/files/file-1/data-asset", "ws-created", None),
                (
                    "POST",
                    "/newmoi/catalog/data-assets/batch-get",
                    "ws-created",
                    {"raw_file_ids": ["file-1", "file-2"]},
                ),
            ],
        )
        with self.assertRaises(sdk.Error) as batch_error:
            catalog.batch_get_data_assets()
        self.assertEqual(batch_error.exception.code, "ErrFileIDsRequired")

    def test_workspace_folder_handle_scopes_volume_folder_lifecycle(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        catalog = sdk.CatalogHandle(workspace, 10, "orders")
        database = sdk.DatabaseHandle(catalog, 20, "raw")
        volume = sdk.VolumeHandle(database, 30, "landing")

        folder, created = volume.create_folder("staging", sdk.with_folder_description("temporary files"))
        known = volume.folder(31)
        renamed = folder.rename("staging-2", sdk.with_updated_folder_description("updated"))
        folder.clean()
        folder.delete()

        self.assertEqual(folder.id, 31)
        self.assertEqual(folder.name, "staging-2")
        self.assertEqual(renamed.name, "staging-2")
        self.assertEqual(known.id, 31)
        self.assertEqual(created.id, 31)

        expected = [
            (
                "POST",
                "/newmoi/catalog/folder/create",
                "ws-created",
                {
                    "parent_volume_id": 30,
                    "database_id": 20,
                    "name": "staging",
                    "description": "temporary files",
                },
            ),
            (
                "POST",
                "/newmoi/catalog/folder/update",
                "ws-created",
                {"id": 31, "name": "staging-2", "description": "updated"},
            ),
            ("POST", "/newmoi/catalog/folder/clean", "ws-created", {"id": 31}),
            ("POST", "/newmoi/catalog/folder/delete", "ws-created", {"id": 31}),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as folder_error:
            volume.folder(0)
        self.assertEqual(folder_error.exception.code, "ErrIDRequired")

    def test_workspace_file_handle_scopes_volume_file_lifecycle(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        catalog = sdk.CatalogHandle(workspace, 10, "orders")
        database = sdk.DatabaseHandle(catalog, 20, "raw")
        volume = sdk.VolumeHandle(database, 30, "landing")
        file = volume.file("file-1")

        files = volume.files(sdk.with_file_list_page_size(25))
        info = file.info()
        download = file.download(sdk.with_file_as_zip(True))
        preview = file.preview()
        triggered = file.trigger_workflows()
        asset = file.data_asset()
        artifact = file.artifact()
        file.delete_ref()
        file.delete()
        download.close()
        preview.close()

        self.assertEqual(files.total, 1)
        self.assertEqual(info.file_name, "orders.csv")
        self.assertEqual(triggered.triggered, 1)
        self.assertEqual(asset.asset.asset_id, "asset-1")
        self.assertEqual(asset.asset.raw_file_id, "file-1")
        self.assertEqual(asset.derivations[0].kind, "parsed")
        self.assertEqual(asset.manifest.parsed_file_id, "parsed-file-1")
        self.assertEqual(artifact.file_id, "file-1")
        self.assertTrue(artifact.has_artifact)

        expected = [
            (
                "POST",
                "/newmoi/catalog/file/list",
                "ws-created",
                {"filters": [{"name": "volume_id", "values": ["30"]}], "page_size": 25},
            ),
            ("POST", "/newmoi/catalog/file/info", "ws-created", {"file_id": "file-1"}),
            ("POST", "/newmoi/catalog/file/download", "ws-created", {"volume_id": "30", "file_id": "file-1", "as_zip": True}),
            ("POST", "/newmoi/catalog/file/preview_stream", "ws-created", {"volume_id": "30", "file_id": "file-1"}),
            ("POST", "/newmoi/catalog/file/trigger_workflow", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("GET", "/newmoi/catalog/files/file-1/data-asset", "ws-created", None),
            ("GET", "/newmoi/catalog/file-artifacts/file-1", "ws-created", None),
            ("POST", "/newmoi/catalog/file/delete_ref", "ws-created", {"volume_id": 30, "file_ids": ["file-1"]}),
            ("POST", "/newmoi/catalog/file/delete", "ws-created", {"id": "file-1", "volume_id": "30"}),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as file_error:
            volume.file("")
        self.assertEqual(file_error.exception.code, "ErrFileIDRequired")

    def test_workflow_retry_preserves_existing_runtime_inputs(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        run = client.workspace("ws-created").workflow("wf-1").run_handle("exec-1")
        for options, expected in [
            ((sdk.with_workflow_rerun_values({"customer": "acme"}), sdk.with_workflow_retry_replace_saved_defaults(True), sdk.with_workflow_rerun_trigger_now(False)),
             {"values": {"customer": "acme"}, "replace_saved_defaults": True, "trigger_now": False}),
            ((sdk.with_workflow_rerun_trigger_now(True),), {"trigger_now": True}),
            ((sdk.with_workflow_retry_replace_saved_defaults(False),), {}),
            ((), {}),
        ]:
            with self.subTest(expected=expected):
                result = run.retry(*options)
                self.assertEqual(result.workflow_run.execution_id, "exec-2")
                self.assertEqual(_Handler.requests[-1], ("POST", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/retry", "ws-created", expected))

    def test_workspace_workflow_handle_scopes_lifecycle(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        workflow, deployed = workspace.deploy_workflow(
            "wf",
            "workflow:\n  name: wf",
            "",
            sdk.with_workflow_description("desc"),
        )
        known_workflow = workspace.workflow("wf-1")
        info = workflow.info()
        updated = workflow.update(sdk.with_workflow_update_name("wf2"))
        enabled = workflow.enable()
        started = workflow.run(
            sdk.with_workflow_run_input({"file_id": "file-1"}),
            sdk.with_workflow_run_replace_saved_defaults(True),
            sdk.with_workflow_run_trigger_now(False),
        )
        runs = workflow.runs()
        run = known_workflow.run_handle("exec-1")
        run_info = run.info()
        refreshed = run.refresh()
        result = run.result()
        import_context = run.import_context()
        import_files = run.import_files(sdk.with_query_param("kind", "output"))
        node = run.node("node-1")
        node_handle = run.node_handle("node-1")
        node_info = node_handle.info()
        rerun_plan = node_handle.rerun_plan(sdk.with_query_param("mode", "from_node"))
        node_rerun = node_handle.create_rerun(
            "continue_from_node",
            "node-exec-1",
            sdk.with_expected_workflow_rerun_contract_hash(rerun_plan.plan.rerun_contract_hash),
            sdk.with_workflow_rerun_reason("fix input"),
        )
        rerun_branches = run.rerun_branches()
        rerun = run.rerun("rerun-1")
        rerun_info = rerun.info()
        rerun_cancelled = rerun.cancel()
        with self.assertRaises(sdk.Error) as retry_reason_error:
            run.retry(sdk.with_workflow_rerun_reason("retry"))
        self.assertEqual(retry_reason_error.exception.code, "ErrUnsupportedOperation")
        retried = run.retry()
        cancelled = run.cancel(sdk.with_workflow_cancel_reason("stop"))
        deleted_run = run.delete()
        deleted_workflow = workflow.delete()

        self.assertEqual(workflow.id, "wf-1")
        self.assertEqual(known_workflow.id, "wf-1")
        self.assertEqual(deployed.workflow.id, "wf-1")
        self.assertEqual(info.workflow.id, "wf-1")
        self.assertEqual(updated.workflow.id, "wf-1")
        self.assertEqual(enabled.workflow.status, "ready")
        self.assertEqual(started.workflow_run.execution_id, "exec-1")
        self.assertEqual(runs.executions[0].execution_id, "exec-1")
        self.assertEqual(run_info.execution.execution_id, "exec-1")
        self.assertEqual(refreshed.execution.status, "succeeded")
        self.assertEqual(result.result.case_result, "done")
        self.assertEqual(import_context.import_context.task_id, "task-1")
        self.assertEqual(import_files.total, 0)
        self.assertEqual(node.node.node_key, "node-1")
        self.assertEqual(node_handle.key, "node-1")
        self.assertEqual(node_info.node.node_key, "node-1")
        self.assertTrue(rerun_plan.plan.validation.ok)
        self.assertEqual(rerun_plan.plan.rerun_contract_hash, "sha256:test-contract")
        self.assertEqual(node_rerun.rerun.rerun_id, "rerun-1")
        self.assertEqual(rerun_branches.reruns[0].rerun_id, "rerun-1")
        self.assertEqual(rerun.id, "rerun-1")
        self.assertEqual(rerun_info.rerun.rerun_id, "rerun-1")
        self.assertEqual(rerun_cancelled.rerun.status, "cancelled")
        self.assertEqual(retried.workflow_run.execution_id, "exec-2")
        self.assertEqual(cancelled.execution.status, "cancelled")
        self.assertTrue(deleted_run.deleted)
        self.assertTrue(deleted_workflow.deleted)

        expected = [
            (
                "POST",
                "/newmoi/workflow/v2/workflow-deployments",
                "ws-created",
                {
                    "name": "wf",
                    "dsl_yaml": "workflow:\n  name: wf",
                    "description": "desc",
                },
            ),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1", "ws-created", None),
            ("PATCH", "/newmoi/workflow/v2/workflow-apps/wf-1", "ws-created", {"name": "wf2"}),
            ("POST", "/newmoi/workflow/v2/workflow-apps/wf-1/enable", "ws-created", {}),
            (
                "POST",
                "/newmoi/workflow/v2/workflow-apps/wf-1/executions",
                "ws-created",
                {"values": {"file_id": "file-1"}, "replace_saved_defaults": True, "trigger_now": False},
            ),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions", "ws-created", None),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1", "ws-created", None),
            ("POST", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/refresh", "ws-created", {}),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/result", "ws-created", None),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/import-context", "ws-created", None),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/import-files?kind=output", "ws-created", None),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/nodes/node-1", "ws-created", None),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/nodes/node-1", "ws-created", None),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/nodes/node-1/rerun-plan?mode=from_node", "ws-created", None),
            (
                "POST",
                "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/nodes/node-1/reruns",
                "ws-created",
                {
                    "mode": "continue_from_node",
                    "source_node_execution_id": "node-exec-1",
                    "expected_rerun_contract_hash": "sha256:test-contract",
                    "reason": "fix input",
                },
            ),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/rerun-branches", "ws-created", None),
            ("GET", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/reruns/rerun-1", "ws-created", None),
            ("POST", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/reruns/rerun-1/cancel", "ws-created", {}),
            ("POST", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/retry", "ws-created", {}),
            ("POST", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1/cancel", "ws-created", {"reason": "stop"}),
            ("DELETE", "/newmoi/workflow/v2/workflow-apps/wf-1/executions/exec-1", "ws-created", None),
            ("DELETE", "/newmoi/workflow/v2/workflow-apps/wf-1", "ws-created", None),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as workflow_error:
            workspace.workflow("")
        self.assertEqual(workflow_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as run_error:
            workflow.run_handle("")
        self.assertEqual(run_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as node_error:
            run.node_handle("")
        self.assertEqual(node_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as rerun_error:
            run.rerun("")
        self.assertEqual(rerun_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as rerun_contract_error:
            node_handle.create_rerun("continue_from_node", "node-exec-1")
        self.assertEqual(rerun_contract_error.exception.code, "ErrRerunContractHashRequired")
        with self.assertRaises(sdk.Error) as blank_rerun_contract_error:
            node_handle.create_rerun(
                "continue_from_node",
                "node-exec-1",
                sdk.with_expected_workflow_rerun_contract_hash(" \t"),
            )
        self.assertEqual(blank_rerun_contract_error.exception.code, "ErrRerunContractHashRequired")

    def test_workspace_agent_handle_scopes_a2a_selector(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        agent_by_code = workspace.agent_by_code("explore")
        by_code = agent_by_code.a2a(
            sdk.A2ARequest(
                sdk.A2A_METHOD_SEND,
                id_="1",
                params={"message": {"parts": [{"kind": "text", "text": "hi"}]}},
            )
        )
        sent_text = agent_by_code.send_text(
            sdk.AgentTextMessage(
                "show revenue",
                "msg-1",
                request_id="req-2",
                session_id="9",
                idempotency_key="idem-1",
                metadata={"source": "sdk-test"},
            )
        )
        stream = agent_by_code.stream_text(sdk.AgentTextMessage("stream revenue", "msg-stream", request_id="req-stream", session_id="10"))
        stream_body = stream.read()
        agent_by_id = workspace.agent_by_id("agent-1")
        by_id = agent_by_id.get_task(sdk.AgentTaskRequest("task-1", request_id="2"))
        canceled = agent_by_id.cancel_task(sdk.AgentTaskRequest("task-1", request_id="3"))
        resubscribed = agent_by_id.resubscribe_task(sdk.AgentTaskRequest("task-1", request_id="4", after_seq=7))
        resubscribed_body = resubscribed.read()
        submitted = agent_by_id.submit_input(
            sdk.AgentInputSubmission(
                "task-1",
                "turn-1",
                {"approval": ["yes"], "regions": ["us", "eu"]},
                request_id="5",
                call_id="call-1",
            )
        )

        self.assertEqual(agent_by_code.selector.agent_code, "explore")
        self.assertEqual(agent_by_id.selector.agent_id, "agent-1")
        self.assertEqual(by_code.json, '{"kind":"task","id":"task-1","turnId":"turn-1"}')
        self.assertEqual(sent_text.json, '{"kind":"task","id":"task-1","turnId":"turn-1"}')
        self.assertEqual(sdk.agent_a2a_task_id(sent_text), "task-1")
        self.assertEqual(sdk.agent_a2a_turn_id(sent_text), "turn-1")
        self.assertIn(b'"kind": "task"', stream_body)
        self.assertEqual(by_id.json, '{"kind":"task","id":"task-1","turnId":"turn-1"}')
        self.assertEqual(canceled.json, '{"kind":"task","id":"task-1","turnId":"turn-1"}')
        self.assertIn(b'"kind": "task"', resubscribed_body)
        self.assertEqual(submitted.json, '{"kind":"task","id":"task-1","turnId":"turn-1"}')
        self.assertEqual(
            _Handler.requests,
            [
                (
                    "POST",
                    "/newmoi/agents/a2a",
                    "ws-created",
                    {
                        "agent_code": "explore",
                        "jsonrpc": "2.0",
                        "id": "1",
                        "method": sdk.A2A_METHOD_SEND,
                        "params": {"message": {"parts": [{"kind": "text", "text": "hi"}]}},
                    },
                ),
                (
                    "POST",
                    "/newmoi/agents/a2a",
                    "ws-created",
                    {
                        "agent_code": "explore",
                        "jsonrpc": "2.0",
                        "id": "req-2",
                        "method": sdk.A2A_METHOD_SEND,
                        "params": {
                            "message": {
                                "kind": "message",
                                "role": "user",
                                "messageId": "msg-1",
                                "parts": [{"kind": "text", "text": "show revenue"}],
                            },
                            "idempotencyKey": "idem-1",
                            "metadata": {"source": "sdk-test", "session_id": "9"},
                        },
                    },
                ),
                (
                    "POST",
                    "/newmoi/agents/a2a",
                    "ws-created",
                    {
                        "agent_code": "explore",
                        "jsonrpc": "2.0",
                        "id": "req-stream",
                        "method": sdk.A2A_METHOD_STREAM,
                        "params": {
                            "message": {
                                "kind": "message",
                                "role": "user",
                                "messageId": "msg-stream",
                                "parts": [{"kind": "text", "text": "stream revenue"}],
                            },
                            "metadata": {"session_id": "10"},
                        },
                    },
                ),
                (
                    "POST",
                    "/newmoi/agents/a2a",
                    "ws-created",
                    {
                        "agent_id": "agent-1",
                        "jsonrpc": "2.0",
                        "id": "2",
                        "method": sdk.A2A_METHOD_TASKS_GET,
                        "params": {"id": "task-1"},
                    },
                ),
                (
                    "POST",
                    "/newmoi/agents/a2a",
                    "ws-created",
                    {
                        "agent_id": "agent-1",
                        "jsonrpc": "2.0",
                        "id": "3",
                        "method": sdk.A2A_METHOD_TASKS_CANCEL,
                        "params": {"id": "task-1"},
                    },
                ),
                (
                    "POST",
                    "/newmoi/agents/a2a",
                    "ws-created",
                    {
                        "agent_id": "agent-1",
                        "jsonrpc": "2.0",
                        "id": "4",
                        "method": sdk.A2A_METHOD_TASKS_RESUBSCRIBE,
                        "params": {"id": "task-1", "afterSeq": 7},
                    },
                ),
                (
                    "POST",
                    "/newmoi/agents/a2a",
                    "ws-created",
                    {
                        "agent_id": "agent-1",
                        "jsonrpc": "2.0",
                        "id": "5",
                        "method": sdk.A2A_METHOD_INPUT_SUBMIT,
                        "params": {
                            "taskId": "task-1",
                            "turnId": "turn-1",
                            "callId": "call-1",
                            "answers": {
                                "approval": {"answers": ["yes"]},
                                "regions": {"answers": ["us", "eu"]},
                            },
                        },
                    },
                ),
            ],
        )
        with self.assertRaises(sdk.Error) as code_error:
            workspace.agent_by_code("")
        self.assertEqual(code_error.exception.code, "ErrAgentRequired")
        with self.assertRaises(sdk.Error) as id_error:
            workspace.agent_by_id("")
        self.assertEqual(id_error.exception.code, "ErrAgentRequired")
        with self.assertRaises(sdk.Error) as input_task_error:
            agent_by_id.submit_input(sdk.AgentInputSubmission("", "turn-1", {"approval": ["yes"]}))
        self.assertEqual(input_task_error.exception.code, "ErrTaskIDRequired")
        with self.assertRaises(sdk.Error) as input_turn_error:
            agent_by_id.submit_input(sdk.AgentInputSubmission("task-1", "", {"approval": ["yes"]}))
        self.assertEqual(input_turn_error.exception.code, "ErrTurnIDRequired")
        with self.assertRaises(sdk.Error) as input_answers_error:
            agent_by_id.submit_input(sdk.AgentInputSubmission("task-1", "turn-1", {}))
        self.assertEqual(input_answers_error.exception.code, "ErrAnswersRequired")
        with self.assertRaises(sdk.Error) as missing_task_id_error:
            sdk.agent_a2a_task_id(sdk.AgentA2AResult(json='{"kind":"task"}'))
        self.assertEqual(missing_task_id_error.exception.code, "ErrResponseInvalid")
        with self.assertRaises(sdk.Error) as missing_turn_id_error:
            sdk.agent_a2a_turn_id(sdk.AgentA2AResult(json='{"kind":"task","id":"task-1"}'))
        self.assertEqual(missing_turn_id_error.exception.code, "ErrResponseInvalid")

    def test_workspace_artifact_handles_scope_lineage_review(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        catalog = sdk.CatalogHandle(workspace, 10, "orders")
        database = sdk.DatabaseHandle(catalog, 20, "raw")
        volume = sdk.VolumeHandle(database, 30, "landing")
        file = volume.file("file-1")
        file_overview = file.lineage_overview(sdk.with_query_param("scope", "latest"))
        artifact = workspace.artifact("artifact-1")
        overview = artifact.overview()
        blocks = artifact.output_blocks()
        block = artifact.block("block-1")
        revisions = block.revisions()
        created_revision = block.create_revision(sdk.with_lineage_revision_content_payload("fixed"), sdk.with_lineage_expected_effective_set_version(7))
        switches = [sdk.LineageRevisionSwitch("block-1", "rev-2")]
        switched = artifact.switch_effective_revisions(switches, sdk.with_lineage_switch_expected_effective_set_version(8))
        node = artifact.node("node-1")
        node_info = node.info()
        node_blocks = node.output_blocks()
        node_block = node.block("node-block-1")
        node_revisions = node_block.revisions()
        node_revision = node_block.create_revision(sdk.with_lineage_use_current_effective(True))
        node_switched = node.switch_effective_revisions(switches)
        rerun = node.rerun(sdk.with_lineage_rerun_mode("from_node"), sdk.with_lineage_rerun_input_payload_override({"id": 1}))
        target_rerun = node.rerun_target_with_revisions(
            "target-1",
            sdk.with_lineage_revision_rerun_mode("selected"),
            sdk.with_lineage_selected_revisions_json({"block-1": "rev-2"}),
            sdk.with_lineage_revision_rerun_source_effective_set_version(9),
        )

        self.assertEqual(file_overview.artifact.artifact_id, "artifact-1")
        self.assertEqual(overview.artifact.artifact_id, "artifact-1")
        self.assertEqual(blocks.artifact_id, "artifact-1")
        self.assertEqual(revisions.block_id, "block-1")
        self.assertEqual(created_revision.block_id, "block-1")
        self.assertEqual(switched.effective_set_version, 8)
        self.assertEqual(node_info.node.node_id, "node-1")
        self.assertEqual(node_blocks.node_id, "node-1")
        self.assertEqual(node_revisions.node_id, "node-1")
        self.assertEqual(node_revision.node_id, "node-1")
        self.assertEqual(node_switched.node_id, "node-1")
        self.assertEqual(rerun.rerun_id, "rerun-1")
        self.assertEqual(target_rerun.rerun_id, "rerun-1")

        expected = [
            ("GET", "/newmoi/lineage/catalog-files/file-1/overview?scope=latest", "ws-created", None),
            ("GET", "/newmoi/lineage/artifacts/artifact-1/overview", "ws-created", None),
            ("GET", "/newmoi/lineage/artifacts/artifact-1/output-blocks", "ws-created", None),
            ("GET", "/newmoi/lineage/artifacts/artifact-1/blocks/block-1/revisions", "ws-created", None),
            (
                "POST",
                "/newmoi/lineage/artifacts/artifact-1/blocks/block-1/revisions",
                "ws-created",
                {"expected_effective_set_version": 7, "revision_content_payload": "fixed"},
            ),
            (
                "POST",
                "/newmoi/lineage/artifacts/artifact-1/effective-revisions",
                "ws-created",
                {"switches": [{"block_id": "block-1", "effective_revision_id": "rev-2"}], "expected_effective_set_version": 8},
            ),
            ("GET", "/newmoi/lineage/artifacts/artifact-1/nodes/node-1", "ws-created", None),
            ("GET", "/newmoi/lineage/artifacts/artifact-1/nodes/node-1/output-blocks", "ws-created", None),
            ("GET", "/newmoi/lineage/artifacts/artifact-1/nodes/node-1/blocks/node-block-1/revisions", "ws-created", None),
            (
                "POST",
                "/newmoi/lineage/artifacts/artifact-1/nodes/node-1/blocks/node-block-1/revisions",
                "ws-created",
                {"use_current_effective": True},
            ),
            (
                "POST",
                "/newmoi/lineage/artifacts/artifact-1/nodes/node-1/effective-revisions",
                "ws-created",
                {"switches": [{"block_id": "block-1", "effective_revision_id": "rev-2"}]},
            ),
            (
                "POST",
                "/newmoi/lineage/artifacts/artifact-1/nodes/node-1/rerun",
                "ws-created",
                {"mode": "from_node", "input_payload_override": {"id": 1}},
            ),
            (
                "POST",
                "/newmoi/lineage/artifacts/artifact-1/nodes/node-1/output-emissions/target-1/rerun-with-revisions",
                "ws-created",
                {
                    "mode": "selected",
                    "selected_revisions_json": {"block-1": "rev-2"},
                    "source_effective_set_version": 9,
                },
            ),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as artifact_error:
            workspace.artifact("")
        self.assertEqual(artifact_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as block_error:
            artifact.block("")
        self.assertEqual(block_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as node_error:
            artifact.node("")
        self.assertEqual(node_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as node_block_error:
            node.block("")
        self.assertEqual(node_block_error.exception.code, "ErrIDRequired")

    def test_custom_operator_spec_body_includes_complete_create_contract(self):
        spec = sdk.CustomOperatorSpec(
            "Text Counter",
            "text_counter",
            "Count text length",
            {"type": "object"},
            {"type": "object"},
            node_id="node-spec",
            kind="python",
            language="python",
            handler="handle",
            version="v1",
            isolation_level="process",
            enabled=False,
            code="def handle(workspace_id, sdk, input): return input",
            source_file_id="source-spec",
            base_node_id="base-spec",
            base_node_version="v0",
            binding_config={"runtime": "sandbox"},
            catalog_id=11,
            database_id=22,
        )
        expected = {
            "name": "Text Counter",
            "identifier": "text_counter",
            "description": "Count text length",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "node_id": "node-spec",
            "kind": "python",
            "language": "python",
            "handler": "handle",
            "version": "v1",
            "isolation_level": "process",
            "enabled": False,
            "code": "def handle(workspace_id, sdk, input): return input",
            "source_file_id": "source-spec",
            "base_node_id": "base-spec",
            "base_node_version": "v0",
            "binding_config": {"runtime": "sandbox"},
            "catalog_id": 11,
            "database_id": 22,
        }
        self.assertEqual(spec.body(()), expected)

        body = spec.body((
            sdk.with_custom_operator_language("python-option"),
            sdk.with_custom_operator_enabled(True),
            sdk.with_custom_operator_catalog_id(33),
        ))
        self.assertEqual(body["language"], "python-option")
        self.assertIs(body["enabled"], True)
        self.assertEqual(body["catalog_id"], 33)

    def test_workspace_workflow_design_handles_scope_operators_and_templates(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        operator_spec = sdk.CustomOperatorSpec(
            "Text Counter",
            "text_counter",
            "Count text length",
            {
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Text to count"}},
                "required": ["text"],
            },
            {
                "type": "object",
                "properties": {"length": {"type": "integer", "description": "Text length"}},
            },
        )
        operator, created_operator = workspace.create_custom_operator_from_spec(
            operator_spec,
            sdk.with_custom_operator_language("python"),
            sdk.with_custom_operator_code("def handle(workspace_id, sdk, input): return {'length': len(input['text'])}"),
            sdk.with_custom_operator_enabled(True),
        )
        known_operator = workspace.custom_operator("1")
        info = operator.info()
        code = operator.code()
        tested = operator.test_with_input(sdk.CustomOperatorTestInput({"text": "hello"}, 30))
        updated_operator = operator.update(sdk.with_custom_operator_update_name("Counter"))
        enabled = operator.enable()
        disabled = operator.disable()
        template, created_template = workspace.create_workflow_template(
            "tpl",
            "workflow:\n  name: tpl",
            sdk.with_workflow_template_key("tpl-key"),
        )
        known_template = workspace.workflow_template("1")
        template_info = template.info()
        updated_template = template.update("tpl2", "workflow:\n  name: tpl2", sdk.with_workflow_template_description("desc2"))
        deleted_template = template.delete()
        deleted_operator = operator.delete()

        self.assertEqual(operator.id, "1")
        self.assertEqual(known_operator.id, "1")
        self.assertEqual(created_operator.id, 1)
        self.assertEqual(info.id, 1)
        self.assertIn("handle", code.source)
        self.assertEqual(tested.test_run.status, "passed")
        self.assertEqual(updated_operator.id, 1)
        self.assertTrue(enabled.enabled)
        self.assertFalse(disabled.enabled)
        self.assertEqual(template.id, "1")
        self.assertEqual(known_template.id, "1")
        self.assertEqual(created_template.id, 1)
        self.assertEqual(template_info.id, 1)
        self.assertEqual(updated_template.id, 1)
        self.assertEqual(deleted_template.message, "deleted")
        self.assertTrue(deleted_operator.deleted)

        self.assertEqual(
            _Handler.requests,
            [
                (
                    "POST",
                    "/newmoi/workflow/v2/custom-operators",
                    "ws-created",
                    {
                        "name": "Text Counter",
                        "identifier": "text_counter",
                        "description": "Count text length",
                        "input_schema": {
                            "type": "object",
                            "properties": {"text": {"type": "string", "description": "Text to count"}},
                            "required": ["text"],
                        },
                        "output_schema": {
                            "type": "object",
                            "properties": {"length": {"type": "integer", "description": "Text length"}},
                        },
                        "language": "python",
                        "code": "def handle(workspace_id, sdk, input): return {'length': len(input['text'])}",
                        "enabled": True,
                    },
                ),
                ("GET", "/newmoi/workflow/v2/custom-operators/1", "ws-created", None),
                ("GET", "/newmoi/workflow/v2/custom-operators/1/code", "ws-created", None),
                ("POST", "/newmoi/workflow/v2/custom-operators/1/test-run", "ws-created", {"input": {"text": "hello"}, "wait_timeout_seconds": 30}),
                ("PUT", "/newmoi/workflow/v2/custom-operators/1", "ws-created", {"name": "Counter"}),
                ("POST", "/newmoi/workflow/v2/custom-operators/1/enable", "ws-created", {}),
                ("POST", "/newmoi/workflow/v2/custom-operators/1/disable", "ws-created", {}),
                ("POST", "/newmoi/workflow-templates", "ws-created", {"name": "tpl", "dsl_yaml": "workflow:\n  name: tpl", "template_key": "tpl-key"}),
                ("GET", "/newmoi/workflow-templates/1", "ws-created", None),
                ("PUT", "/newmoi/workflow-templates/1", "ws-created", {"name": "tpl2", "dsl_yaml": "workflow:\n  name: tpl2", "description": "desc2"}),
                ("DELETE", "/newmoi/workflow-templates/1", "ws-created", None),
                ("DELETE", "/newmoi/workflow/v2/custom-operators/1", "ws-created", None),
            ],
        )
        with self.assertRaises(sdk.Error) as operator_error:
            workspace.custom_operator("")
        self.assertEqual(operator_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as spec_name_error:
            workspace.create_custom_operator_from_spec(sdk.CustomOperatorSpec("", "id", "desc", {}, {}))
        self.assertEqual(spec_name_error.exception.code, "ErrNameRequired")
        with self.assertRaises(sdk.Error) as spec_identifier_error:
            workspace.create_custom_operator_from_spec(sdk.CustomOperatorSpec("name", "", "desc", {}, {}))
        self.assertEqual(spec_identifier_error.exception.code, "ErrIdentifierRequired")
        with self.assertRaises(sdk.Error) as spec_description_error:
            workspace.create_custom_operator_from_spec(sdk.CustomOperatorSpec("name", "id", "", {}, {}))
        self.assertEqual(spec_description_error.exception.code, "ErrDescriptionRequired")
        with self.assertRaises(sdk.Error) as spec_input_error:
            workspace.create_custom_operator_from_spec(sdk.CustomOperatorSpec("name", "id", "desc", None, {}))
        self.assertEqual(spec_input_error.exception.code, "ErrInputSchemaRequired")
        with self.assertRaises(sdk.Error) as spec_output_error:
            workspace.create_custom_operator_from_spec(sdk.CustomOperatorSpec("name", "id", "desc", {}, None))
        self.assertEqual(spec_output_error.exception.code, "ErrOutputSchemaRequired")
        with self.assertRaises(sdk.Error) as test_input_error:
            operator.test_with_input(sdk.CustomOperatorTestInput(None))
        self.assertEqual(test_input_error.exception.code, "ErrPayloadRequired")
        with self.assertRaises(sdk.Error) as result_workflow_error:
            workspace.workflows().get_run_result("", "exec-1")
        self.assertEqual(result_workflow_error.exception.code, "ErrWorkflowIDRequired")
        with self.assertRaises(sdk.Error) as result_execution_error:
            workspace.workflows().get_run_result("wf-1", "")
        self.assertEqual(result_execution_error.exception.code, "ErrExecutionIDRequired")
        with self.assertRaises(sdk.Error) as result_by_id_error:
            workspace.workflows().get_run_result_by_id("")
        self.assertEqual(result_by_id_error.exception.code, "ErrExecutionIDRequired")
        with self.assertRaises(sdk.Error) as result_status_error:
            workspace.workflows().get_run_result_status("", "exec-1")
        self.assertEqual(result_status_error.exception.code, "ErrWorkflowIDRequired")
        with self.assertRaises(sdk.Error) as template_error:
            workspace.workflow_template("")
        self.assertEqual(template_error.exception.code, "ErrIDRequired")

    def test_workspace_workitem_api_service_handle_scopes_lifecycle(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        service = workspace.workitem_api_service("moi:files.read_text", "v1")
        info = service.info()
        published = service.publish(
            sdk.WorkitemAPIServicePublishSpec(
                version="v1",
                service_name="operator-api-abc",
                compute_resource_id="compute-1",
                timeout_seconds=45,
                max_concurrency=3,
                rate_limit_per_min=60,
            )
        )
        enabled = service.enable()
        invoked = service.invoke(sdk.WorkitemAPIServiceInvokeSpec("operator-api-abc", "operator", "v1", {"text": "hello"}))
        disabled = service.disable()

        self.assertEqual(service.node_id, "moi:files.read_text")
        self.assertEqual(service.version, "v1")
        self.assertEqual(info.service.version, "v1")
        self.assertEqual(info.service.api_service_id, "api_123")
        self.assertEqual(published.service.status, "ready")
        self.assertEqual(enabled.service.status, "ready")
        self.assertEqual(invoked.result.status, "succeeded")
        self.assertEqual(disabled.service.status, "disabled")
        self.assertEqual(
            _Handler.requests,
            [
                ("GET", "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service?version=v1", "ws-created", None),
                (
                    "POST",
                    "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service",
                    "ws-created",
                    {
                        "version": "v1",
                        "service_name": "operator-api-abc",
                        "compute_resource_id": "compute-1",
                        "timeout_seconds": 45,
                        "max_concurrency": 3,
                        "rate_limit_per_min": 60,
                    },
                ),
                ("POST", "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service/enable?version=v1", "ws-created", {}),
                (
                    "POST",
                    "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service/invoke",
                    "ws-created",
                    {"service_name": "operator-api-abc", "type": "operator", "version": "v1", "payload": {"text": "hello"}},
                ),
                ("POST", "/newmoi/workflow/v2/workitems/catalog/moi:files.read_text/api-service/disable?version=v1", "ws-created", {}),
            ],
        )
        with self.assertRaises(sdk.Error) as node_error:
            workspace.workitem_api_service("", "v1")
        self.assertEqual(node_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as version_error:
            workspace.workitem_api_service("moi:files.read_text", "")
        self.assertEqual(version_error.exception.code, "ErrVersionRequired")
        with self.assertRaises(sdk.Error) as publish_version_error:
            workspace.workflows().publish_workitem_api_service("moi:files.read_text", sdk.WorkitemAPIServicePublishSpec())
        self.assertEqual(publish_version_error.exception.code, "ErrVersionRequired")
        with self.assertRaises(sdk.Error) as invoke_service_name_error:
            service.invoke(sdk.WorkitemAPIServiceInvokeSpec("", "operator", "v1", {"text": "hello"}))
        self.assertEqual(invoke_service_name_error.exception.code, "ErrServiceNameRequired")
        with self.assertRaises(sdk.Error) as invoke_type_error:
            service.invoke(sdk.WorkitemAPIServiceInvokeSpec("operator-api-abc", "", "v1", {"text": "hello"}))
        self.assertEqual(invoke_type_error.exception.code, "ErrTypeRequired")
        with self.assertRaises(sdk.Error) as invoke_payload_error:
            service.invoke(sdk.WorkitemAPIServiceInvokeSpec("operator-api-abc", "operator", "v1", None))
        self.assertEqual(invoke_payload_error.exception.code, "ErrPayloadRequired")

    def test_workitem_api_service_invoke_validation_details(self):
        cases = [
            (
                "service name",
                sdk.WorkitemAPIServiceInvokeSpec("", "operator", "v1", {}),
                "ErrServiceNameRequired",
                "service_name",
                "required",
                "",
                "published service.service_name",
            ),
            (
                "type",
                sdk.WorkitemAPIServiceInvokeSpec("service", "", "v1", {}),
                "ErrTypeRequired",
                "type",
                "required",
                "operator",
                'use "operator"',
            ),
            (
                "version",
                sdk.WorkitemAPIServiceInvokeSpec("service", "operator", "", {}),
                "ErrVersionRequired",
                "version",
                "required",
                "",
                "published service.version",
            ),
            (
                "payload",
                sdk.WorkitemAPIServiceInvokeSpec("service", "operator", "v1", None),
                "ErrPayloadRequired",
                "payload",
                "required",
                "",
                "not an input wrapper",
            ),
        ]
        for name, spec, code, field, reason, expected, message in cases:
            with self.subTest(name=name):
                with self.assertRaises(sdk.Error) as raised:
                    spec.validate()
                self.assertEqual(raised.exception.code, code)
                self.assertIn(message, raised.exception.message)
                self.assertEqual(raised.exception.details["field"], field)
                self.assertEqual(raised.exception.details["reason"], reason)
                if expected:
                    self.assertEqual(raised.exception.details["expected"], expected)

    def test_workspace_semantic_model_handle_scopes_entries(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        model, created = workspace.create_semantic_model(
            "orders-model",
            sdk.with_semantic_model_description("orders"),
            sdk.with_semantic_model_tables(["orders"]),
        )
        known_model = workspace.semantic_model("101")
        info = model.info()
        updated = model.update("orders-model", sdk.with_semantic_model_files(["file-1"]))
        entries = model.entries(sdk.with_query_param("limit", "20"))
        entry_input = sdk.SemanticEntryInput("metric", "revenue", {"name": "revenue", "source_table": "orders", "metric_type": "aggregate", "aggregation": "SUM", "field": "amount"}, ["orders"])
        entry, entry_created = model.create_entry(entry_input)
        known_entry = model.entry("201")
        entry_updated = entry.update(sdk.SemanticEntryInput("metric", "margin", {"name": "margin", "source_table": "orders", "metric_type": "aggregate", "aggregation": "SUM", "field": "margin"}))
        imported = model.import_entries([sdk.SemanticEntryInput("field_description", "region", {"column": "region"})])
        exported = model.export()
        validated = model.validate()
        deleted_entry = entry.delete()
        deleted_model = model.delete()

        self.assertEqual(model.id, "101")
        self.assertEqual(known_model.id, "101")
        self.assertEqual(created.id, 101)
        self.assertEqual(created.name, "orders-model")
        self.assertEqual(created.source_counts.files, 2)
        self.assertEqual(created.source_counts.tables, 1)
        self.assertEqual(created.source_counts.total, 3)
        self.assertEqual(info.id, 101)
        self.assertEqual(info.description, "orders")
        self.assertEqual(info.source_counts.total, 3)
        self.assertTrue(updated.updated)
        self.assertEqual(entries.total, 0)
        self.assertEqual(len(entries.items), 0)
        self.assertEqual(entry.id, "201")
        self.assertIs(entry.model(), model)
        self.assertEqual(known_entry.id, "201")
        self.assertEqual(entry_created.id, 201)
        self.assertEqual(entry_created.key, "revenue")
        self.assertTrue(entry_updated.updated)
        self.assertEqual(imported.imported, 1)
        self.assertEqual(imported.model_id, 101)
        self.assertEqual(exported.model.id, 101)
        self.assertEqual(len(exported.entries), 0)
        self.assertTrue(validated.valid)
        self.assertTrue(deleted_entry.deleted)
        self.assertTrue(deleted_model.deleted)

        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/semantic-models", "ws-created", {"name": "orders-model", "description": "orders", "tables": ["orders"]}),
                ("GET", "/newmoi/semantic-models/101", "ws-created", None),
                ("PUT", "/newmoi/semantic-models/101", "ws-created", {"name": "orders-model", "files": ["file-1"]}),
                ("GET", "/newmoi/semantic-models/101/entries?limit=20", "ws-created", None),
                (
                    "POST",
                    "/newmoi/semantic-models/101/entries",
                    "ws-created",
                    {"kind": "metric", "key": "revenue", "spec": {"name": "revenue", "source_table": "orders", "metric_type": "aggregate", "aggregation": "SUM", "field": "amount"}, "tables": ["orders"]},
                ),
                (
                    "PUT",
                    "/newmoi/semantic-models/101/entries/201",
                    "ws-created",
                    {"kind": "metric", "key": "margin", "spec": {"name": "margin", "source_table": "orders", "metric_type": "aggregate", "aggregation": "SUM", "field": "margin"}},
                ),
                (
                    "POST",
                    "/newmoi/semantic-models/101/import",
                    "ws-created",
                    {"entries": [{"kind": "field_description", "key": "region", "spec": {"column": "region"}}]},
                ),
                ("GET", "/newmoi/semantic-models/101/export", "ws-created", None),
                ("POST", "/newmoi/semantic-models/101/validate", "ws-created", {}),
                ("DELETE", "/newmoi/semantic-models/101/entries/201", "ws-created", None),
                ("DELETE", "/newmoi/semantic-models/101", "ws-created", None),
            ],
        )
        with self.assertRaises(sdk.Error) as model_error:
            workspace.semantic_model("")
        self.assertEqual(model_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as entry_error:
            model.entry("")
        self.assertEqual(entry_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as entry_kind_error:
            model.create_entry(sdk.SemanticEntryInput("", "revenue", {"expr": "sum(amount)"}))
        self.assertEqual(entry_kind_error.exception.code, "ErrKindRequired")
        with self.assertRaises(sdk.Error) as entry_key_error:
            model.create_entry(sdk.SemanticEntryInput("metric", "", {"expr": "sum(amount)"}))
        self.assertEqual(entry_key_error.exception.code, "ErrKeyRequired")
        with self.assertRaises(sdk.Error) as entry_spec_error:
            model.create_entry(sdk.SemanticEntryInput("metric", "revenue", None))
        self.assertEqual(entry_spec_error.exception.code, "ErrSpecRequired")
        with self.assertRaises(sdk.Error) as update_spec_error:
            entry.update(sdk.SemanticEntryInput("metric", "margin", None))
        self.assertEqual(update_spec_error.exception.code, "ErrSpecRequired")
        with self.assertRaises(sdk.Error) as import_entries_error:
            model.import_entries([])
        self.assertEqual(import_entries_error.exception.code, "ErrEntriesRequired")
        with self.assertRaises(sdk.Error) as import_entry_error:
            model.import_entries([sdk.SemanticEntryInput("field_description", "", {"column": "region"})])
        self.assertEqual(import_entry_error.exception.code, "ErrKeyRequired")

    def test_knowledge_list_parses_source_counts(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.knowledge("ws-created").list()

        self.assertEqual(result.total, 1)
        self.assertEqual(result.items[0].id, 101)
        self.assertIsInstance(result.items[0].source_counts, sdk.SemanticModelSourceCounts)
        self.assertEqual(result.items[0].source_counts.files, 2)
        self.assertEqual(result.items[0].source_counts.tables, 1)
        self.assertEqual(result.items[0].source_counts.total, 3)
        self.assertEqual(_Handler.requests, [("GET", "/newmoi/semantic-models", "ws-created", None)])

    def test_knowledge_list_entries_encodes_semantic_domain(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.knowledge("ws-created").list_entries("101", sdk.with_semantic_domain("rag"))

        self.assertEqual(result.total, 0)
        self.assertEqual(len(result.items), 0)
        self.assertEqual(
            _Handler.requests,
            [("GET", "/newmoi/semantic-models/101/entries?domain=rag", "ws-created", None)],
        )

    def test_knowledge_create_update_import_entries_include_semantic_domain(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        knowledge = client.knowledge("ws-created")

        created = knowledge.create_entry(
            "101",
            sdk.SemanticEntryInput("standard_qa", "q1", {"question": "GMV?"}, domain="rag"),
        )
        updated = knowledge.update_entry(
            "101",
            "201",
            sdk.SemanticEntryInput("standard_qa", "q1", {"question": "GMV total?"}, domain="rag"),
        )
        imported = knowledge.import_entries(
            "101",
            [sdk.SemanticEntryInput("business_rule", "paid", {"content": "paid orders only"}, domain="rag")],
        )

        self.assertEqual(created.id, 201)
        self.assertTrue(updated.updated)
        self.assertEqual(imported.imported, 1)
        self.assertEqual(
            _Handler.requests,
            [
                (
                    "POST",
                    "/newmoi/semantic-models/101/entries",
                    "ws-created",
                    {"kind": "standard_qa", "key": "q1", "spec": {"question": "GMV?"}, "domain": "rag"},
                ),
                (
                    "PUT",
                    "/newmoi/semantic-models/101/entries/201",
                    "ws-created",
                    {"kind": "standard_qa", "key": "q1", "spec": {"question": "GMV total?"}, "domain": "rag"},
                ),
                (
                    "POST",
                    "/newmoi/semantic-models/101/import",
                    "ws-created",
                    {"entries": [{"kind": "business_rule", "key": "paid", "spec": {"content": "paid orders only"}, "domain": "rag"}]},
                ),
            ],
        )

    def test_semantic_model_info_allows_missing_source_counts(self):
        model = sdk_client._semantic_model_info({"id": 101, "name": "orders-model"})

        self.assertEqual(model.id, 101)
        self.assertFalse(model.HasField("source_counts"))

    def test_knowledge_list_source_jobs_parses_view_fields(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        result = client.knowledge("ws-created").list_source_jobs("101")

        self.assertEqual(result.total, 1)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].job_id, "job-1")
        self.assertEqual(result.items[0].job_status, "succeeded")
        self.assertEqual(result.items[0].kb_file_id, "kb-file-1")
        self.assertTrue(result.items[0].reconcile_required)
        self.assertTrue(result.reconcile_required)
        self.assertEqual(_Handler.requests, [("GET", "/newmoi/semantic-models/101/source-jobs", "ws-created", None)])

    def test_knowledge_check_source_existence_uses_typed_contract(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        result = client.knowledge("ws-created").check_source_existence("101", ["file-1", "file-2"], [10, 20])

        self.assertEqual(list(result.file_ids), ["file-1"])
        self.assertEqual(list(result.table_ids), [10])
        self.assertEqual(
            _Handler.requests,
            [("POST", "/newmoi/semantic-models/101/sources/existence", "ws-created", {"file_ids": ["file-1", "file-2"], "table_ids": [10, 20]})],
        )

    def test_knowledge_search_drawings_uses_multipart_without_file_id(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        result = client.knowledge("ws-created").search_drawings(
            42, query="bolt", query_image_bytes=b"png-bytes", query_image_filename="q.png", top_k=3
        )
        self.assertEqual(result.get("count"), 0)
        self.assertEqual(result.get("drawings"), [])
        self.assertEqual(result.get("diagnostics"), {})
        method, path, workspace, body = _Handler.requests[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/newmoi/drawings/search")
        self.assertEqual(workspace, "ws-created")
        self.assertNotIn("query_image_file_id", str(body))

    def test_knowledge_search_drawings_rejects_invalid_response_payloads(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        knowledge = client.knowledge("ws-created")
        invalid_payloads = (
            None,
            [],
            "bad",
            {"count": 0, "diagnostics": {}},
            {"drawings": [], "diagnostics": {}},
            {"drawings": [], "count": 0},
            {"drawings": {}, "count": 0, "diagnostics": {}},
            {"drawings": [], "count": -1, "diagnostics": {}},
            {"drawings": [], "count": True, "diagnostics": {}},
            {"drawings": [], "count": 0, "diagnostics": []},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                _Handler.drawing_search_data = payload
                with self.assertRaises(sdk.Error) as err:
                    knowledge.search_drawings(42, query="bolt")
                self.assertEqual(err.exception.code, "ErrResponseInvalid")

    def test_knowledge_local_file_uploads_use_multipart_routes(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        knowledge = client.knowledge("ws-created")

        created = knowledge.upload_local_file(" report.pdf ", b"create")
        appended = knowledge.upload_model_local_file("101", "notes.txt", b"append")

        self.assertEqual(created.file_id, "file-1")
        self.assertEqual(appended.file_id, "file-1")
        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/semantic-models/local-files/upload", "ws-created", {"filename": "report.pdf", "data": "create"}),
                ("POST", "/newmoi/semantic-models/101/local-files/upload", "ws-created", {"filename": "notes.txt", "data": "append"}),
            ],
        )

    def test_upload_preserves_quoted_and_backslash_filenames(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        knowledge = client.knowledge("ws-created")
        content = "file contents\r\n第二行"
        for filename in ('report.txt', 'report"draft".txt', 'report\\draft.txt',
                         '报告"初稿".txt', 'report\\"draft".txt'):
            for model_id in (None, "101"):
                with self.subTest(filename=filename, model_id=model_id):
                    _Handler.requests = []
                    if model_id is None:
                        result = knowledge.upload_local_file(filename, content.encode())
                        route = "/newmoi/semantic-models/local-files/upload"
                    else:
                        result = knowledge.upload_model_local_file(model_id, filename, content.encode())
                        route = f"/newmoi/semantic-models/{model_id}/local-files/upload"
                    self.assertEqual(result.file_id, "file-1")
                    self.assertEqual(_Handler.requests, [
                        ("POST", route, "ws-created", {"filename": filename, "data": content}),
                    ])

    def test_multipart_preserves_field_names_and_binary_content(self):
        boundary = "quoted-parameter-regression"
        field_name = 'text\\"field'
        file_field = 'file\\"field'
        filename = 'data\\"sample.bin'
        content = b"\x00\xff\r\nfile bytes"
        body = sdk_client._multipart_body(
            boundary, {field_name: 'value "unchanged"\\'},
            [(file_field, filename, content)],
        )
        message = BytesParser(policy=default).parsebytes(
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n\r\n".encode() + body
        )
        parts = list(message.iter_parts())
        self.assertEqual([
            (part.get_param("name", header="Content-Disposition"),
             part.get_filename(), part.get_payload(decode=True))
            for part in parts
        ], [(field_name, None, b'value "unchanged"\\'), (file_field, filename, content)])
        self.assertEqual(parts[1].get_content_type(), "application/octet-stream")

    def test_knowledge_preview_artifact_uses_model_scoped_binary_route(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        preview = client.knowledge("ws-created").preview_artifact("101", "page image/1")
        try:
            self.assertEqual(preview.status, 200)
            self.assertEqual(preview.read(), b"png-body")
        finally:
            preview.close()

        self.assertEqual(
            _Handler.requests,
            [
                (
                    "GET",
                    "/newmoi/semantic-models/101/artifacts/page%20image%2F1/preview",
                    "ws-created",
                    None,
                )
            ],
        )

    def test_knowledge_list_sources_pagination_compatibility(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        knowledge = client.knowledge("ws-created")

        # SemanticModelInfo.id is int64; passing it directly must not leak
        # urllib.parse.quote type errors from URL path construction.
        all_sources = knowledge.list_sources(101)
        page = knowledge.list_sources_page("101", 2, 20)

        self.assertEqual(all_sources.total, 21)
        self.assertEqual(page.page, 2)
        self.assertEqual(page.page_size, 20)
        self.assertEqual(
            _Handler.requests,
            [
                ("GET", "/newmoi/semantic-models/101/sources", "ws-created", None),
                ("GET", "/newmoi/semantic-models/101/sources?page=2&page_size=20", "ws-created", None),
            ],
        )

    def test_knowledge_list_referencing_agents(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        page = client.knowledge("ws-created").list_referencing_agents("101", limit=10, cursor="next")
        self.assertIsInstance(page, sdk.KnowledgeReferencingAgentsPage)
        self.assertEqual(page.items[0].id, "ag_1")
        self.assertEqual(page.items[0].knowledge_base_count, 2)

    def test_knowledge_preview_source_selection_counts_uses_typed_contract(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        knowledge = client.knowledge("ws-created")
        selections = [
            sdk.SemanticModelSourceSelectionInput(
                "volume_files",
                volume_id=42,
                all_selected=True,
                excluded_file_ids=["file-95"],
                filters=sdk.SemanticModelSourceSelectionFilters(file_name="report", file_ext=["pdf"]),
            )
        ]

        create_result = knowledge.preview_source_selection_counts(selections)
        model_result = knowledge.preview_model_source_selection_counts("101", selections)

        self.assertEqual(create_result.total_count, 140)
        self.assertEqual(model_result.file_count, 140)
        body = {
            "source_selections": [
                {
                    "kind": "volume_files",
                    "volume_id": 42,
                    "all_selected": True,
                    "excluded_file_ids": ["file-95"],
                    "filters": {"file_name": "report", "file_ext": ["pdf"]},
                }
            ]
        }
        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/semantic-models/source-selections/preview", "ws-created", body),
                ("POST", "/newmoi/semantic-models/101/source-selections/preview", "ws-created", body),
            ],
        )

    def test_knowledge_append_selections_preserves_duplicate_feedback(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        result = client.knowledge("ws-created").append_sources(
            "101", [], selections=[sdk.SemanticModelSourceSelectionInput("volume_files", volume_id=7, selected_file_ids=["file-existing", "file-new"])],
        )
        self.assertEqual(list(result.skipped_existing_file_ids), ["file-existing"])
        self.assertEqual(list(result.skipped_existing_table_ids), [42])
        self.assertEqual(_Handler.requests, [("POST", "/newmoi/semantic-models/101/sources", "ws-created", {
            "sources": [], "source_selections": [{"kind": "volume_files", "volume_id": 7, "all_selected": False, "selected_file_ids": ["file-existing", "file-new"]}],
        })])

    def test_knowledge_create_with_sources_image_index_enabled_option(self):
        # Public package export used by Storybook / external runners (#14853).
        self.assertTrue(hasattr(sdk, "with_semantic_model_with_sources_image_index_enabled"))
        body = sdk_client._semantic_model_with_sources_body(
            "kb",
            [],
            (sdk.with_semantic_model_with_sources_image_index_enabled(True),),
        )

        self.assertEqual(body["image_index_enabled"], True)

    def test_knowledge_create_empty_uses_typed_contract(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.knowledge("ws-created").create_empty(
            "empty-model",
            sdk.with_semantic_model_empty_description("data-side"),
            sdk.with_semantic_model_empty_image_index_enabled(True),
        )

        self.assertEqual(result.model.id, 102)
        self.assertEqual(result.data_domain.catalog_id, 3)
        self.assertEqual(
            _Handler.requests,
            [("POST", "/newmoi/semantic-models/create-empty", "ws-created", {"name": "empty-model", "description": "data-side", "image_index_enabled": True})],
        )

    def test_semantic_model_source_input_uses_uploaded_file_id(self):
        body = sdk.SemanticModelSourceInput(
            "local_file",
            file_name="manual.pdf",
            file_id="uploaded-file-1",
        ).body()

        self.assertEqual(body["file_id"], "uploaded-file-1")
        self.assertNotIn("content_base64", body)

    def test_catalog_database_table_leaves_uses_pagination_options(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        result = client.catalog("ws-created").database_table_leaves(
            20,
            page_size=25,
            page_token="5",
            search="ord",
        )

        self.assertEqual(result.total, 2)
        self.assertEqual(result.next_page_token, "10")
        self.assertEqual(result.items[0].table_name, "orders")
        self.assertEqual(
            _Handler.requests,
            [("POST", "/newmoi/catalog/database/table-leaves", "ws-created", {"database_id": 20, "page_size": 25, "page_token": "5", "search": "ord"})],
        )

    def test_workspace_connector_handle_scopes_tasks(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        connector, created = workspace.create_connector(
            "oss",
            1,
            2,
            sdk.with_connector_config({"bucket": "b"}),
        )
        known_connector = workspace.connector("conn-1")
        info = connector.info()
        connector.update(sdk.with_connector_name("oss-prod"))
        source_databases = connector.source_databases()
        source_schemas = connector.source_schemas("db1")
        source_tables = connector.source_tables("db1", sdk.with_connector_schema("public"))
        source_schema = connector.source_schema("db1", "orders", sdk.with_connector_schema("public"))
        mo_databases = connector.mo_databases()
        mo_tables = connector.mo_database_tables("analytics")
        checked_table = connector.check_mo_table_name("analytics", "orders")
        column_mapping = connector.mo_column_mapping("analytics", "orders", {"src_id": "id"})
        import_task, imported = connector.create_import_task(
            1,
            {"tables": ["orders"]},
            sdk.with_import_task_name("load orders"),
        )
        file_import_task, _ = connector.create_file_import_task(
            sdk.FileImportTaskSpec(
                1,
                ["oss://bucket/orders.csv"],
                {"mode": 1},
                {"file_types": [1]},
                name="load files",
                volume_id="volume-1",
                unzip_keep_structure=True,
                dedup={"by": ["path"], "strategy": "keep"},
            ),
        )
        known_import = connector.import_task("task-1")
        import_info = import_task.info()
        import_task.update(sdk.ImportTaskUpdateSpec(name="load orders v2"))
        import_task.update_config(
            sdk.ImportTaskUpdateSpec(
                {"mode": 2, "interval": 30},
                name="load orders typed",
                file_filter_config={"file_types": [7]},
                uris=["oss://bucket/orders-v2.csv"],
            )
        )
        import_task.pause()
        import_task.resume()
        runs = import_task.runs()
        files = import_task.files(sdk.with_query_param("status", "failed"))
        import_task.retry_files("file-1")
        export_task, exported = connector.create_export_task(
            "export orders",
            "oss",
            2,
            {"path": "/out"},
            [{"file_id": "file-1", "full_path": ["db", "orders"], "is_raw": True}],
        )
        spec_export_task, _ = connector.create_export_task_from_spec(
            sdk.ExportTaskSpec(
                "export spec orders",
                "oss",
                2,
                sdk.ExportTaskConfig(
                    merge_title_to_text=True,
                    s3_config={"path": "/out/spec", "need_compress": True, "compress_method": "zip"},
                ),
                [sdk.ExportTaskFile("file-2", ["db", "orders", "parsed"], is_raw=True)],
            ),
        )
        known_export = connector.export_task("export-1")
        export_info = export_task.info()
        export_files = export_task.files(sdk.with_export_task_files_limit(10))
        export_task.retry("file-1")
        state = export_task.state()
        export_task.delete()
        import_task.delete()
        connector.delete()
        with self.assertRaises(sdk.Error) as export_name_error:
            connector.create_export_task_from_spec(
                sdk.ExportTaskSpec("", "oss", 2, sdk.ExportTaskConfig(s3_config={"path": "/out"}), [sdk.ExportTaskFile("file-1", ["db"])]),
            )
        self.assertEqual(export_name_error.exception.code, "ErrTaskNameRequired")
        with self.assertRaises(sdk.Error) as export_connector_error:
            connector.create_export_task_from_spec(
                sdk.ExportTaskSpec("export", "", 2, sdk.ExportTaskConfig(s3_config={"path": "/out"}), [sdk.ExportTaskFile("file-1", ["db"])]),
            )
        self.assertEqual(export_connector_error.exception.code, "ErrConnectorIDRequired")
        with self.assertRaises(sdk.Error) as export_type_error:
            connector.create_export_task_from_spec(
                sdk.ExportTaskSpec("export", "oss", 0, sdk.ExportTaskConfig(s3_config={"path": "/out"}), [sdk.ExportTaskFile("file-1", ["db"])]),
            )
        self.assertEqual(export_type_error.exception.code, "ErrTypeRequired")
        with self.assertRaises(sdk.Error) as export_config_error:
            connector.create_export_task_from_spec(sdk.ExportTaskSpec("export", "oss", 2, sdk.ExportTaskConfig(), [sdk.ExportTaskFile("file-1", ["db"])]))
        self.assertEqual(export_config_error.exception.code, "ErrConfigRequired")
        with self.assertRaises(sdk.Error) as export_files_error:
            connector.create_export_task_from_spec(sdk.ExportTaskSpec("export", "oss", 2, sdk.ExportTaskConfig(s3_config={"path": "/out"}), []))
        self.assertEqual(export_files_error.exception.code, "ErrFileIDsRequired")
        with self.assertRaises(sdk.Error) as export_file_id_error:
            connector.create_export_task_from_spec(
                sdk.ExportTaskSpec("export", "oss", 2, sdk.ExportTaskConfig(s3_config={"path": "/out"}), [sdk.ExportTaskFile("", ["db"])]),
            )
        self.assertEqual(export_file_id_error.exception.code, "ErrFileIDRequired")
        with self.assertRaises(sdk.Error) as export_file_path_error:
            connector.create_export_task_from_spec(
                sdk.ExportTaskSpec("export", "oss", 2, sdk.ExportTaskConfig(s3_config={"path": "/out"}), [sdk.ExportTaskFile("file-1", [])]),
            )
        self.assertEqual(export_file_path_error.exception.code, "ErrPathInvalid")
        with self.assertRaises(sdk.Error) as file_import_type_error:
            connector.create_file_import_task(sdk.FileImportTaskSpec(0, ["oss://bucket/orders.csv"], {"mode": 1}, {"file_types": [1]}, name="load", volume_id="volume-1"))
        self.assertEqual(file_import_type_error.exception.code, "ErrTypeRequired")
        sdk.FileImportTaskSpec(1, ["oss://bucket/orders.csv"], {"mode": 1}, {"file_types": [1]}, volume_id="volume-1").validate()
        sdk.FileImportTaskSpec(1, ["oss://bucket/orders.csv"], {"mode": 1}, {"file_types": [1]}, name="load").validate()
        with self.assertRaises(sdk.Error) as file_import_uri_error:
            connector.create_file_import_task(sdk.FileImportTaskSpec(1, [], {"mode": 1}, {"file_types": [1]}, name="load", volume_id="volume-1"))
        self.assertEqual(file_import_uri_error.exception.code, "ErrURLRequired")
        with self.assertRaises(sdk.Error) as file_import_mode_error:
            connector.create_file_import_task(sdk.FileImportTaskSpec(1, ["oss://bucket/orders.csv"], None, {"file_types": [1]}, name="load", volume_id="volume-1"))
        self.assertEqual(file_import_mode_error.exception.code, "ErrModeRequired")
        with self.assertRaises(sdk.Error) as file_import_filter_error:
            connector.create_file_import_task(sdk.FileImportTaskSpec(1, ["oss://bucket/orders.csv"], {"mode": 1}, None, name="load", volume_id="volume-1"))
        self.assertEqual(file_import_filter_error.exception.code, "ErrSourceConfigRequired")

        self.assertEqual(connector.id, "conn-1")
        self.assertEqual(known_connector.id, "conn-1")
        self.assertEqual(created.id, "conn-1")
        self.assertEqual(info.id, "conn-1")
        self.assertEqual(source_databases.databases, ["db1"])
        self.assertEqual(source_schemas.schemas, ["public"])
        self.assertEqual(source_tables.tables, ["orders"])
        self.assertEqual(source_schema.columns[0].name, "id")
        self.assertEqual(source_schema.columns[0].mapped_type, "INT64")
        self.assertTrue(source_schema.columns[0].is_primary_key)
        self.assertFalse(source_schema.columns[0].is_nullable)
        self.assertTrue(source_schema.columns[0].is_auto_incr)
        self.assertEqual(mo_databases.databases, ["analytics"])
        self.assertEqual(mo_tables.tables, ["orders"])
        self.assertFalse(checked_table.exists)
        self.assertEqual([value.string_value for value in column_mapping.column_map["src_id"].values], ["id"])
        self.assertEqual(list(column_mapping.need_mapping_columns), ["src_id"])
        self.assertEqual(import_task.id, "task-1")
        self.assertEqual(file_import_task.id, "task-1")
        self.assertEqual(known_import.id, "task-1")
        self.assertEqual(imported.task_id, "task-1")
        self.assertEqual(import_info.task.id, "task-1")
        self.assertEqual(runs.runs, [])
        self.assertEqual(files.files, [])
        self.assertEqual(export_task.id, "export-1")
        self.assertEqual(spec_export_task.id, "export-1")
        self.assertEqual(known_export.id, "export-1")
        self.assertEqual(exported.id, "export-1")
        self.assertEqual(export_info.id, "export-1")
        self.assertEqual(export_files.files, [])
        self.assertEqual(state.total, 0)

        expected = [
            ("POST", "/newmoi/connectors", "ws-created", {"name": "oss", "source_type": 1, "usage_type": 2, "config": {"bucket": "b"}}),
            ("POST", "/newmoi/connectors/get", "ws-created", {"id": "conn-1"}),
            ("PUT", "/newmoi/connectors/conn-1", "ws-created", {"name": "oss-prod"}),
            ("POST", "/newmoi/connectors/db/database/list", "ws-created", {"connector_id": "conn-1"}),
            ("POST", "/newmoi/connectors/db/database/schema/list", "ws-created", {"connector_id": "conn-1", "database": "db1"}),
            ("POST", "/newmoi/connectors/db/database/table/list", "ws-created", {"connector_id": "conn-1", "database": "db1", "schema": "public"}),
            ("POST", "/newmoi/connectors/db/schema", "ws-created", {"connector_id": "conn-1", "database": "db1", "schema": "public", "table": "orders"}),
            ("POST", "/newmoi/connectors/mo/database/list", "ws-created", {"connector_id": "conn-1"}),
            ("POST", "/newmoi/connectors/mo/database/table/list", "ws-created", {"connector_id": "conn-1", "database": "analytics"}),
            ("POST", "/newmoi/connectors/mo/check_table_name", "ws-created", {"connector_id": "conn-1", "database": "analytics", "table": "orders"}),
            (
                "POST",
                "/newmoi/connectors/mo/column/mapping",
                "ws-created",
                {"connector_id": "conn-1", "database": "analytics", "table": "orders", "export_columns": {"src_id": "id"}},
            ),
            (
                "POST",
                "/newmoi/task",
                "ws-created",
                {"source_connector_id": "conn-1", "config_type": 1, "source_config": {"tables": ["orders"]}, "name": "load orders"},
            ),
            (
                "POST",
                "/newmoi/task",
                "ws-created",
                {
                    "source_connector_id": "conn-1",
                    "config_type": 1,
                    "source_config": {
                        "common_file_task_config": {
                            "uris": ["oss://bucket/orders.csv"],
                            "load_mode_config": {"mode": 1},
                            "file_filter_config": {"file_types": [1]},
                            "unzip_keep_structure": True,
                            "dedup": {"by": ["path"], "strategy": "keep"},
                        }
                    },
                    "name": "load files",
                    "volume_id": "volume-1",
                },
            ),
            ("GET", "/newmoi/task/get?task_id=task-1", "ws-created", None),
            ("POST", "/newmoi/task/update", "ws-created", {"task_id": "task-1", "name": "load orders v2"}),
            (
                "POST",
                "/newmoi/task/update",
                "ws-created",
                {
                    "task_id": "task-1",
                    "name": "load orders typed",
                    "load_mode_config": {"mode": 2, "interval": 30},
                    "file_filter_config": {"file_types": [7]},
                    "uris": ["oss://bucket/orders-v2.csv"],
                },
            ),
            ("POST", "/newmoi/task/pause", "ws-created", {"task_id": "task-1"}),
            ("POST", "/newmoi/task/resume", "ws-created", {"task_id": "task-1"}),
            ("GET", "/newmoi/task/runs?task_id=task-1", "ws-created", None),
            ("GET", "/newmoi/task/files?task_id=task-1&status=failed", "ws-created", None),
            ("POST", "/newmoi/task/retry", "ws-created", {"task_id": "task-1", "ids": ["file-1"]}),
            (
                "POST",
                "/newmoi/export/task/create",
                "ws-created",
                {
                    "task_name": "export orders",
                    "connector_id": "conn-1",
                    "connector_name": "oss",
                    "type": 2,
                    "config": {"path": "/out"},
                    "files": [{"file_id": "file-1", "full_path": ["db", "orders"], "is_raw": True}],
                },
            ),
            (
                "POST",
                "/newmoi/export/task/create",
                "ws-created",
                {
                    "task_name": "export spec orders",
                    "connector_id": "conn-1",
                    "connector_name": "oss",
                    "type": 2,
                    "config": {"merge_title_to_text": True, "s3_config": {"path": "/out/spec", "need_compress": True, "compress_method": "zip"}},
                    "files": [{"file_id": "file-2", "full_path": ["db", "orders", "parsed"], "is_raw": True}],
                },
            ),
            ("POST", "/newmoi/export/task/info", "ws-created", {"id": "export-1"}),
            ("POST", "/newmoi/export/task/files", "ws-created", {"limit": 10, "task_id": "export-1"}),
            ("POST", "/newmoi/export/task/export-1/rerun", "ws-created", {"files": ["file-1"]}),
            ("GET", "/newmoi/export/task/export-1/state", "ws-created", None),
            ("POST", "/newmoi/export/task/delete", "ws-created", {"id": "export-1"}),
            ("POST", "/newmoi/task/delete", "ws-created", {"task_id": "task-1"}),
            ("DELETE", "/newmoi/connectors/conn-1", "ws-created", None),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as connector_error:
            workspace.connector("")
        self.assertEqual(connector_error.exception.code, "ErrConnectorIDRequired")
        with self.assertRaises(sdk.Error) as import_error:
            connector.import_task("")
        self.assertEqual(import_error.exception.code, "ErrTaskIDRequired")
        with self.assertRaises(sdk.Error) as export_error:
            connector.export_task("")
        self.assertEqual(export_error.exception.code, "ErrTaskIDRequired")
        with self.assertRaises(sdk.Error) as empty_update_error:
            import_task.update_config(sdk.ImportTaskUpdateSpec())
        self.assertEqual(empty_update_error.exception.code, "ErrSourceConfigRequired")
        with self.assertRaises(sdk.Error) as empty_uri_update_error:
            import_task.update_config(sdk.ImportTaskUpdateSpec(uris=[]))
        self.assertEqual(empty_uri_update_error.exception.code, "ErrURLRequired")

    def test_import_task_structured_load_config_decodes_strictly(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        connectors = client.workspace("ws-created").connectors()

        info = connectors.get_task("task-1")
        tasks = connectors.tasks()

        self.assertEqual(info.task.structured_load_config.fields["source"].struct_value.fields["database"].string_value, "analytics")
        self.assertEqual(tasks.tasks[0].structured_load_config.fields["tables"].list_value.values[0].string_value, "orders")
        for task in (info.task, tasks.tasks[0]):
            self.assertEqual(task.mapping.values[0].struct_value.fields["target_column"].string_value, "order_id")
            self.assertEqual(task.schedule.fields["kind"].string_value, "hourly")
            self.assertTrue(task.backfill.fields["enabled"].bool_value)
        self.assertEqual(
            _Handler.requests,
            [
                ("GET", "/newmoi/task/get?task_id=task-1", "ws-created", None),
                ("GET", "/newmoi/task/list", "ws-created", None),
            ],
        )

    def test_workspace_connector_file_handle_scopes_temporary_file_lifecycle(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        connector = workspace.connector("conn-1")
        connector_file = connector.file("cf-1")
        known_file = workspace.connector_file("cf-1")
        preview = connector_file.preview(sdk.with_connector_preview_row_start(2))
        download = connector_file.download()
        stream = known_file.stream()
        try:
            stream_body = stream.read()
        finally:
            stream.close()
        known_file.delete()

        self.assertEqual(connector_file.id, "cf-1")
        self.assertEqual(known_file.id, "cf-1")
        self.assertEqual(preview.conn_file_id, "cf-1")
        self.assertEqual(download.url, "https://example.test/cf-1")
        self.assertEqual(stream_body, b"stream-body")
        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/connectors/file/preview", "ws-created", {"connector_id": "conn-1", "uri": "", "conn_file_id": "cf-1", "rowStart": 2}),
                ("POST", "/newmoi/connectors/file/download", "ws-created", {"conn_file_id": "cf-1"}),
                ("GET", "/newmoi/connectors/file/stream?conn_file_id=cf-1", "ws-created", None),
                ("POST", "/newmoi/connectors/file/delete", "ws-created", {"conn_file_id": "cf-1"}),
            ],
        )

        with self.assertRaises(sdk.Error) as workspace_file_error:
            workspace.connector_file("")
        self.assertEqual(workspace_file_error.exception.code, "ErrConnectorFileIDRequired")
        with self.assertRaises(sdk.Error) as connector_file_error:
            connector.file("")
        self.assertEqual(connector_file_error.exception.code, "ErrConnectorFileIDRequired")
        known_preview = known_file.preview()
        self.assertEqual(known_preview.conn_file_id, "cf-1")

    def test_workspace_model_provider_handle_scopes_backend_and_router(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        llm = workspace.llm_provider()
        backends = llm.backends()
        probed = llm.probe_address("https://llm.example.test", sdk.with_provider_backend_api_key("sk"))
        backend, created = llm.create_backend(
            "openai",
            sdk.with_provider_backend_address("https://llm.example.test"),
            sdk.with_provider_backend_models("gpt-4.1"),
        )
        known_backend = workspace.llm_backend("1")
        info = backend.info()
        updated = backend.update(
            sdk.with_provider_backend_update_name("openai-prod"),
            sdk.with_provider_backend_update_models("gpt-4.1-mini"),
        )
        endpoint = backend.create_endpoint("https://llm-2.example.test")
        endpoints = backend.endpoints()
        status = backend.set_endpoint_status("2", "disabled")
        backend_probed = backend.probe_models(sdk.with_provider_backend_api_key("sk"))
        router = llm.router()
        router_info = router.info()
        router_updated = router.update(sdk.with_router_strategy("round_robin"), sdk.with_router_max_retries(2))
        deleted = backend.delete()
        setup_backend, setup = workspace.setup_llm_backend(
            "setup",
            "https://setup.example.test",
            ["gpt-4.1"],
        )
        embedding = workspace.embedding_provider()
        embedding_probed = embedding.probe_address("https://embedding.example.test", sdk.with_provider_backend_api_key("sk"))
        embedding_backend, embedding_created = embedding.create_backend(
            "bge",
            sdk.with_provider_backend_models("bge-m3"),
        )
        known_embedding = workspace.embedding_backend("3")
        embedding_backend_probed = embedding_backend.probe_models(sdk.with_provider_backend_api_key("sk"))
        embedding_router = embedding.router().update(sdk.with_router_session_affinity(True))
        parser = workspace.parser_provider()
        parser_backend, parser_created = parser.create_backend(
            "doc-parser",
            sdk.with_provider_backend_supported_mime_types("application/pdf"),
        )
        known_parser = workspace.parser_backend("4")
        parser_router = parser.router().info()
        parser_info = parser_backend.info()

        self.assertEqual(llm.kind, "llm")
        self.assertEqual([item.id for item in backends.backends], [1])
        self.assertEqual(list(probed.models), ["gpt-4.1"])
        self.assertEqual(backend.id, "1")
        self.assertIs(backend.provider(), llm)
        self.assertEqual(known_backend.id, "1")
        self.assertEqual(created.id, 1)
        self.assertEqual(info.id, 1)
        self.assertEqual(updated.id, 1)
        self.assertEqual(endpoint.id, 2)
        self.assertEqual([item.id for item in endpoints.endpoints], [2])
        self.assertTrue(status.success)
        self.assertEqual(list(backend_probed.models), ["gpt-4.1"])
        self.assertIs(router.provider(), llm)
        self.assertEqual(router_info.strategy, "round_robin")
        self.assertEqual(router_updated.strategy, "round_robin")
        self.assertTrue(deleted.success)
        self.assertEqual(setup_backend.id, "5")
        self.assertEqual(setup.backend.id, 5)
        self.assertEqual(list(embedding_probed.models), ["bge-m3"])
        self.assertEqual(embedding_backend.id, "3")
        self.assertEqual(embedding_created.id, 3)
        self.assertEqual(known_embedding.id, "3")
        self.assertEqual(list(embedding_backend_probed.models), ["bge-m3"])
        self.assertEqual(embedding_router.strategy, "sticky")
        self.assertEqual(parser_backend.id, "4")
        self.assertEqual(parser_created.id, 4)
        self.assertEqual(known_parser.id, "4")
        self.assertEqual(parser_router.strategy, "single")
        self.assertEqual(parser_info.id, 4)

        expected = [
            ("GET", "/newmoi/llm/backends", "ws-created", None),
            ("POST", "/newmoi/llm/probe-models", "ws-created", {"address": "https://llm.example.test", "api_key": "sk"}),
            (
                "POST",
                "/newmoi/llm/backends",
                "ws-created",
                {"name": "openai", "address": "https://llm.example.test", "models": ["gpt-4.1"]},
            ),
            ("GET", "/newmoi/llm/backends/1", "ws-created", None),
            ("PUT", "/newmoi/llm/backends/1", "ws-created", {"name": "openai-prod", "models": ["gpt-4.1-mini"]}),
            ("POST", "/newmoi/llm/backends/1/endpoints", "ws-created", {"address": "https://llm-2.example.test"}),
            ("GET", "/newmoi/llm/backends/1/endpoints", "ws-created", None),
            ("PUT", "/newmoi/llm/backends/1/endpoints/2/status", "ws-created", {"status": "disabled"}),
            ("POST", "/newmoi/llm/backends/1/probe-models", "ws-created", {"api_key": "sk"}),
            ("GET", "/newmoi/llm/router", "ws-created", None),
            ("PUT", "/newmoi/llm/router", "ws-created", {"strategy": "round_robin", "max_retries": 2}),
            ("DELETE", "/newmoi/llm/backends/1", "ws-created", None),
            (
                "POST",
                "/newmoi/llm/setup",
                "ws-created",
                {"name": "setup", "address": "https://setup.example.test", "models": ["gpt-4.1"]},
            ),
            ("POST", "/newmoi/embedding/probe-models", "ws-created", {"address": "https://embedding.example.test", "api_key": "sk"}),
            ("POST", "/newmoi/embedding/backends", "ws-created", {"name": "bge", "models": ["bge-m3"]}),
            ("POST", "/newmoi/embedding/backends/3/probe-models", "ws-created", {"api_key": "sk"}),
            ("PUT", "/newmoi/embedding/router", "ws-created", {"session_affinity": True}),
            ("POST", "/newmoi/parser/backends", "ws-created", {"name": "doc-parser", "supported_mime_types": ["application/pdf"]}),
            ("GET", "/newmoi/parser/router", "ws-created", None),
            ("GET", "/newmoi/parser/backends/4", "ws-created", None),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as parser_probe:
            parser.probe_address("https://parser.example.test")
        self.assertEqual(parser_probe.exception.code, "ErrUnsupportedOperation")
        with self.assertRaises(sdk.Error) as create_error:
            llm.create_backend("", sdk.with_provider_backend_models("gpt"))
        self.assertEqual(create_error.exception.code, "ErrNameRequired")
        with self.assertRaises(sdk.Error) as endpoint_address_error:
            backend.create_endpoint("")
        self.assertEqual(endpoint_address_error.exception.code, "ErrAddressRequired")
        with self.assertRaises(sdk.Error) as endpoint_id_error:
            backend.set_endpoint_status("", "disabled")
        self.assertEqual(endpoint_id_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as endpoint_status_error:
            backend.set_endpoint_status("2", "")
        self.assertEqual(endpoint_status_error.exception.code, "ErrStatusRequired")
        with self.assertRaises(sdk.Error) as known_error:
            workspace.llm_backend("")
        self.assertEqual(known_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as setup_error:
            workspace.setup_llm_backend("", "https://setup.example.test", ["gpt"])
        self.assertEqual(setup_error.exception.code, "ErrNameRequired")
        with self.assertRaises(sdk.Error) as setup_address_error:
            workspace.setup_llm_backend("setup", "", ["gpt"])
        self.assertEqual(setup_address_error.exception.code, "ErrAddressRequired")
        with self.assertRaises(sdk.Error) as setup_models_error:
            workspace.setup_llm_backend("setup", "https://setup.example.test", [])
        self.assertEqual(setup_models_error.exception.code, "ErrModelsRequired")


    def test_workspace_compute_resource_handle_scopes_lifecycle(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        worker_images = [
            sdk.WorkerImageSelection(worker_type="go-worker", image_id="go-img-1", platform="linux/amd64"),
            sdk.WorkerImageSelection(worker_type="python-worker", image_id="python-img-1", platform="linux/amd64"),
            sdk.WorkerImageSelection(worker_type="java-worker", image_id="java-img-1", platform="linux/amd64"),
            sdk.WorkerImageSelection(worker_type="custom-tool-worker", image_id="tool-img-1", platform="linux/amd64"),
        ]
        resource, created = workspace.create_compute_resource(
            "go-worker",
            "spec-1",
            2,
            8,
            sdk.with_compute_description("etl"),
            sdk.with_compute_min_replicas(1),
            sdk.with_compute_max_replicas(3),
            sdk.with_compute_worker_images(*worker_images),
        )
        resources = workspace.compute().list()
        images = workspace.compute().worker_images(sdk.with_query_param("type", "go-worker"))
        known = workspace.compute_resource("compute-1")
        info = resource.info()
        updated = resource.update(
            sdk.with_compute_update_name("go-worker-prod"),
            sdk.with_compute_update_cpu(4),
            sdk.with_compute_update_memory_gib(16),
            sdk.with_compute_update_auto_suspend_minutes(20),
            sdk.with_compute_update_worker_images(*worker_images),
        )
        ownership = resource.adopt_legacy_ownership()
        suspended = resource.suspend()
        resumed = resource.resume()
        retried = resource.retry()
        preflight = resource.preflight_delete()
        resource.delete(sdk.with_force(True))

        self.assertEqual(resource.id, "compute-1")
        self.assertEqual(known.id, "compute-1")
        self.assertEqual(created.id, "compute-1")
        self.assertEqual(created.cpu, 2)
        self.assertEqual(resources[0].id, "compute-1")
        self.assertEqual(images[0].id, "go-img-1")
        self.assertEqual(images[0].type, "go-worker")
        self.assertEqual(info.id, "compute-1")
        self.assertEqual(info.workspace_id, "ws-created")
        self.assertEqual(updated.id, "compute-1")
        self.assertEqual(ownership.resource_id, "compute-1")
        self.assertEqual(ownership.owner_role_id, "role-superadmin")
        self.assertEqual(ownership.ownership_version, 1)
        self.assertEqual(suspended.status, "suspended")
        self.assertEqual(resumed.status, "IDLE")
        self.assertEqual(retried.status, "retrying")
        self.assertEqual(preflight.active_tasks, 1)
        self.assertEqual(preflight.bound_workflow_details[0].node_names[0], "node-1")

        expected = [
            (
                "POST",
                "/newmoi/compute-resources",
                "ws-created",
                {"name": "go-worker", "spec_id": "spec-1", "cpu": 2, "memory_gib": 8, "description": "etl", "min_replicas": 1, "max_replicas": 3, "auto_suspend_minutes": 10, "worker_images": [
                    {"worker_type": image.worker_type, "image_id": image.image_id, "platform": image.platform}
                    for image in worker_images
                ]},
            ),
            ("GET", "/newmoi/compute-resources", "ws-created", None),
            ("GET", "/newmoi/compute-resources/worker-images?type=go-worker", "ws-created", None),
            ("GET", "/newmoi/compute-resources/compute-1", "ws-created", None),
            ("PUT", "/newmoi/compute-resources/compute-1", "ws-created", {"name": "go-worker-prod", "cpu": 4, "memory_gib": 16, "auto_suspend_minutes": 20, "worker_images": [
                {"worker_type": image.worker_type, "image_id": image.image_id, "platform": image.platform}
                for image in worker_images
            ]}),
            ("POST", "/newmoi/compute-resources/compute-1/adopt-legacy-ownership", "ws-created", {}),
            ("POST", "/newmoi/compute-resources/compute-1/suspend", "ws-created", {}),
            ("POST", "/newmoi/compute-resources/compute-1/resume", "ws-created", {}),
            ("POST", "/newmoi/compute-resources/compute-1/retry", "ws-created", {}),
            ("GET", "/newmoi/compute-resources/compute-1/preflight-delete", "ws-created", None),
            ("DELETE", "/newmoi/compute-resources/compute-1?force=true", "ws-created", None),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as known_error:
            workspace.compute_resource("")
        self.assertEqual(known_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as create_error:
            workspace.create_compute_resource("", "spec-1", 1, 1)
        self.assertEqual(create_error.exception.code, "ErrNameRequired")

    def test_workspace_consumer_memory_handle_scopes_retrieve_and_profile(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        handle = workspace.consumer_memory("subject-1")
        self.assertEqual(handle.id, "subject-1")

        retrieved = handle.retrieve("seafood allergy")
        fulltext = handle.fulltext_search(
            sdk.ConsumerMemoryFulltextSearchInput(
                "seafood", extra_metadata_filter={"department": "sales"}
            )
        )
        structured = handle.query(
            sdk.ConsumerMemoryStructuredQueryInput(extra_metadata_filter={"urgent": True})
        )
        profile = handle.render_profile()

        self.assertEqual(len(retrieved.memories), 1)
        self.assertEqual(retrieved.memories[0].memory_id, "m1")
        self.assertEqual(fulltext.memories[0].memory_id, "m1")
        self.assertEqual(structured.memories[0].memory_id, "m1")
        self.assertEqual(profile.subject_id, "subject-1")
        self.assertEqual(profile.text, "profile text")
        self.assertEqual(profile.token_estimate, 12)

        self.assertEqual(_Handler.requests, [
            ("POST", "/newmoi/memories/retrieve", "ws-created", {"query": "seafood allergy", "subject_id": "subject-1"}),
            (
                "POST",
                "/newmoi/memories/fulltext-search",
                "ws-created",
                {"subject_id": "subject-1", "extra_metadata_filter": {"department": "sales"}, "query": "seafood"},
            ),
            (
                "POST",
                "/newmoi/memories/query",
                "ws-created",
                {"subject_id": "subject-1", "extra_metadata_filter": {"urgent": True}},
            ),
            ("GET", "/newmoi/consumer-profiles/subject-1/render", "ws-created", None),
        ])

        with self.assertRaises(sdk.Error) as subject_error:
            workspace.consumer_memory("")
        self.assertEqual(subject_error.exception.code, "ErrSubjectRequired")

        with self.assertRaises(sdk.Error) as metadata_error:
            sdk.ConsumerMemoryFulltextSearchInput(
                "seafood", extra_metadata_filter={"nested": {"value": 1}}
            ).validate()
        self.assertEqual(metadata_error.exception.code, "ErrInvalidArgument")

        with self.assertRaises(sdk.Error) as limit_error:
            sdk.ConsumerMemoryStructuredQueryInput(limit=501).validate()
        self.assertEqual(limit_error.exception.code, "ErrInvalidArgument")

    def test_compute_worker_image_selection_body_canonicalizes_legacy_kind(self):
        self.assertEqual(
            sdk_client._compute_worker_image_selection_body(
                sdk.WorkerImageSelection(kind="legacy-worker", image_id="legacy-image:v1", platform="linux/amd64")
            ),
            {"worker_type": "legacy-worker", "image_id": "legacy-image:v1", "platform": "linux/amd64"},
        )
        self.assertEqual(
            sdk_client._compute_worker_image_selection_body(
                sdk.WorkerImageSelection(worker_type="document-worker", image_id="gpu-v2:v1", platform="linux/amd64")
            ),
            {"worker_type": "document-worker", "image_id": "gpu-v2:v1", "platform": "linux/amd64"},
        )
        with self.assertRaises(sdk.Error) as conflict:
            sdk_client._compute_worker_image_selection_body(
                sdk.WorkerImageSelection(kind="legacy-worker", worker_type="document-worker")
            )
        self.assertEqual(conflict.exception.code, "ErrWorkerTypeConflict")

    def test_compute_runtime_preserves_http_error_status_and_code(self):
        requests = []

        class RuntimeErrorHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                return

            def do_GET(self):
                requests.append((self.path, self.headers.get("X-Workspace-ID")))
                status = int(self.path.rsplit("/", 2)[-2])
                body = json.dumps({"code": f"RUNTIME_{status}", "msg": "runtime request failed", "data": None}).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = HTTPServer(("127.0.0.1", 0), RuntimeErrorHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            service = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key")).compute("ws-created")
            calls = [
                (400, lambda: service.runtime(compute_resource_id="400")),
                (403, lambda: service.runtime(compute_resource_id="403")),
                (404, lambda: service.admin_runtime(compute_resource_id="404")),
                (500, lambda: service.admin_runtime(compute_resource_id="500")),
            ]
            for status, call in calls:
                with self.assertRaises(sdk.Error) as failure:
                    call()
                self.assertEqual(failure.exception.status, status)
                self.assertEqual(failure.exception.code, f"RUNTIME_{status}")
            self.assertEqual(
                requests,
                [
                    ("/newmoi/compute-resources/400/runtime", "ws-created"),
                    ("/newmoi/compute-resources/403/runtime", "ws-created"),
                    ("/newmoi/admin/compute-resources/404/runtime", "ws-created"),
                    ("/newmoi/admin/compute-resources/500/runtime", "ws-created"),
                ],
            )
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_compute_admin_list_decodes_catalog_fields_strictly(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.compute("ws-created").admin_list(sdk.with_limit(50), sdk.with_offset(0))

        self.assertEqual(result.total, 1)
        self.assertEqual(result.limit, 50)
        self.assertEqual(result.offset, 0)
        self.assertEqual(len(result.items), 1)
        resource = result.items[0]
        self.assertEqual(resource.id, "compute-1")
        self.assertEqual(resource.kind, "task")
        self.assertEqual(resource.cpu_milli, 2000)
        self.assertEqual(resource.memory_mib, 8192)
        self.assertEqual(resource.desired_replicas, 2)
        self.assertEqual(resource.worker_images[0].image_id, "go-img-1")
        self.assertEqual(resource.scale_reason, "activation")
        self.assertEqual(resource.last_activation_at, "2026-01-01T00:01:00Z")
        self.assertEqual(resource.last_active_at, "2026-01-01T00:02:00Z")
        self.assertEqual(resource.workspace.id, "ws-created")
        self.assertEqual(resource.workspace.account_name, "account_1")
        self.assertEqual(
            _Handler.requests,
            [("GET", "/newmoi/admin/compute-resources?limit=50&offset=0", "ws-created", None)],
        )

    def test_compute_create_result_preserves_current_backend_contract(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        body = {
            "name": "go-worker",
            "kind": "task",
            "spec_id": "spec-1",
            "cpu": 2,
            "memory_gib": 8,
            "auto_suspend_minutes": 10,
        }

        result = client.compute("ws-created").create_result("go-worker", "task", "spec-1", 2, 8)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.data["id"], "compute-1")
        self.assertEqual(
            _Handler.requests,
            [("POST", "/newmoi/compute-resources", "ws-created", body)],
        )

    def test_workspace_data_share_handle_scopes_publish_and_subscription(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        publishes = workspace.data_share().publishes(sdk.with_query_param("name", "orders-share"))
        workspace_names = workspace.data_share().workspace_names(["ws-2"])
        resolved_workspace_names = workspace.data_share().resolve_workspace_names(["cross-user-ws"])
        summary = workspace.data_share_summary()
        source_tables = workspace.data_share_source_tables("101", sdk.with_query_param("page", "2"))
        checked_name = workspace.data_share().check_publish_name(sdk.with_query_param("name", "orders-share"))
        publish, created = workspace.create_data_share_publish(
            "orders-share",
            "101",
            sdk.DataShareScope(mode="selected", object_ids=["201"]),
            ["ws-2"],
            sdk.with_data_share_remark("daily"),
        )
        known_publish = workspace.data_share_publish("publish-1")
        updated = publish.update(
            sdk.with_data_share_update_table_scope(sdk.DataShareScope(mode="selected", object_ids=["201", "202"])),
            sdk.with_data_share_update_target_workspace_ids("ws-2", "ws-3"),
            sdk.with_data_share_update_remark("expanded"),
        )
        subscriptions = workspace.data_share().subscriptions(sdk.with_query_param("status", "pending"))
        subscription = workspace.data_share_subscription("sub-1")
        subscribed = subscription.subscribe("orders-copy")
        subscription.unsubscribe()
        publish.delete()

        self.assertEqual(publishes.total, 1)
        self.assertEqual(publishes.list[0].id, "publish-1")
        self.assertEqual(publishes.list[0].obj_display_name, "Orders")
        self.assertEqual(publishes.list[0].obj_display_path, "Catalog/Orders")
        self.assertEqual(publishes.list[0].targets[0].workspace_id, "ws-2")
        self.assertEqual(workspace_names.workspaces[0].name, "Target")
        self.assertEqual(resolved_workspace_names.workspaces[0].name, "Cross User Workspace")
        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.target_total, 5)
        self.assertEqual(source_tables.total, 1)
        self.assertEqual(source_tables.list[0].id, "201")
        self.assertEqual(source_tables.list[0].name, "orders")
        self.assertTrue(checked_name.available)
        self.assertEqual(publish.id, "publish-1")
        self.assertEqual(known_publish.id, "publish-1")
        self.assertEqual(created.id, "publish-1")
        self.assertEqual(created.source_database_id, "101")
        self.assertEqual(created.mo_database_name, "orders")
        self.assertEqual(list(created.table_scope.object_ids), ["201"])
        self.assertEqual(created.obj_display_name, "Orders")
        self.assertEqual(created.obj_display_path, "Catalog/Orders")
        self.assertEqual(created.targets[0].workspace_id, "ws-2")
        self.assertEqual(updated.id, "publish-1")
        self.assertEqual(updated.remark, "expanded")
        self.assertEqual(len(updated.targets), 2)
        self.assertEqual(subscriptions.total, 1)
        self.assertEqual(subscriptions.list[0].id, "sub-1")
        self.assertEqual(subscriptions.list[0].obj_display_name, "Orders")
        self.assertEqual(subscriptions.list[0].obj_display_path, "Catalog/Orders")
        self.assertEqual(subscription.id, "sub-1")
        self.assertEqual(subscribed.id, "sub-1")
        self.assertEqual(subscribed.status, "subscribed")
        self.assertEqual(subscribed.target_database_id, "301")

        expected = [
            ("GET", "/newmoi/data-share/publishes?name=orders-share", "ws-created", None),
            ("POST", "/newmoi/data-share/workspace-names", "ws-created", {"ids": ["ws-2"]}),
            ("POST", "/newmoi/data-share/workspaces/resolve-names", "ws-created", {"ids": ["cross-user-ws"]}),
            ("GET", "/newmoi/data-share/publishes/summary", "ws-created", None),
            ("GET", "/newmoi/data-share/source-databases/101/tables?page=2", "ws-created", None),
            ("GET", "/newmoi/data-share/publishes/check-name?name=orders-share", "ws-created", None),
            (
                "POST",
                "/newmoi/data-share/publishes",
                "ws-created",
                {
                    "name": "orders-share",
                    "source_database_id": "101",
                    "table_scope": {"mode": "selected", "object_ids": ["201"]},
                    "target_workspace_ids": ["ws-2"],
                    "remark": "daily",
                },
            ),
            (
                "PUT",
                "/newmoi/data-share/publishes/publish-1",
                "ws-created",
                {"table_scope": {"mode": "selected", "object_ids": ["201", "202"]}, "target_workspace_ids": ["ws-2", "ws-3"], "remark": "expanded"},
            ),
            ("GET", "/newmoi/data-share/subscriptions?status=pending", "ws-created", None),
            ("POST", "/newmoi/data-share/subscriptions/sub-1/subscribe", "ws-created", {"sub_name": "orders-copy"}),
            ("POST", "/newmoi/data-share/subscriptions/sub-1/unsubscribe", "ws-created", {}),
            ("DELETE", "/newmoi/data-share/publishes/publish-1", "ws-created", None),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as publish_error:
            workspace.data_share_publish("")
        self.assertEqual(publish_error.exception.code, "ErrIDRequired")
        with self.assertRaises(sdk.Error) as create_publish_error:
            workspace.create_data_share_publish("", "101", sdk.DataShareScope(mode="selected", object_ids=["201"]), ["ws-2"])
        self.assertEqual(create_publish_error.exception.code, "ErrNameRequired")
        with self.assertRaises(sdk.Error) as subscription_error:
            workspace.data_share_subscription("")
        self.assertEqual(subscription_error.exception.code, "ErrIDRequired")

    def test_workspace_data_share_publish_all_tables_uses_explicit_scope(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        publish, created = workspace.create_data_share_publish(
            "orders-db-share",
            "101",
            sdk.DataShareScope(mode="all"),
            ["ws-2"],
        )

        self.assertEqual(publish.id, "publish-1")
        self.assertEqual(created.id, "publish-1")
        self.assertEqual(
            _Handler.requests[-1],
            (
                "POST",
                "/newmoi/data-share/publishes",
                "ws-created",
                {
                    "name": "orders-db-share",
                    "source_database_id": "101",
                    "table_scope": {"mode": "all"},
                    "target_workspace_ids": ["ws-2"],
                },
            ),
        )

    def test_workspace_sql_handles_scope_workbook_query_and_statement(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        workbook, created = workspace.create_sql_workbook("analysis")
        known_workbook = workspace.sql_workbook("wb-1")
        renamed = workbook.rename("analysis v2")
        versions = workbook.versions(sdk.with_workbook_version_page_size(10))
        version, version_created = workbook.create_version("select 1")
        known_version = workbook.version("ver-1")
        version_info = version.info()
        version_updated = version.update("select 2")
        version_saved = version.save("select 3")
        query, started = workspace.execute_sql("select 1", sdk.with_sql_query_db_name("db1"), sdk.with_sql_query_limit(100))
        known_query = workspace.sql_query("query-1")
        described = query.describe()
        killed = query.kill()
        statement = workspace.sql_statement("stmt-1")
        result = statement.result(sdk.with_sql_result_limit(50))
        detail = statement.detail(sdk.with_query_record_start("2026-06-01 00:00:00"))
        profile = statement.profile(sdk.with_query_record_end("2026-06-02 00:00:00"))
        deleted = workbook.delete()

        self.assertEqual(workbook.id, "wb-1")
        self.assertEqual(known_workbook.id, "wb-1")
        self.assertEqual(created.workbook_id, "wb-1")
        self.assertIsNone(renamed)
        self.assertEqual(versions.total, 1)
        self.assertEqual(version.id, "ver-1")
        self.assertIs(version.workbook(), workbook)
        self.assertEqual(known_version.id, "ver-1")
        self.assertEqual(version_created.id, "ver-1")
        self.assertEqual(version_info.sql_content, "select 1")
        self.assertIsNone(version_updated)
        self.assertIsNone(version_saved)
        self.assertEqual(query.id, "query-1")
        self.assertEqual(known_query.id, "query-1")
        self.assertEqual(started.query_id, "query-1")
        self.assertEqual(described.status, "running")
        self.assertIsNone(killed)
        self.assertEqual(statement.id, "stmt-1")
        self.assertEqual(result.total, 0)
        self.assertEqual(detail.statement_id, "stmt-1")
        self.assertEqual(profile.profile.code, 200)
        self.assertIsNone(deleted)

        expected = [
            ("POST", "/newmoi/workbook/create", "ws-created", {"name": "analysis"}),
            ("POST", "/newmoi/workbook/update", "ws-created", {"workbook_id": "wb-1", "name": "analysis v2"}),
            ("POST", "/newmoi/workbook/version/list", "ws-created", {"workbook_id": "wb-1", "page_size": 10}),
            ("POST", "/newmoi/workbook/version/create", "ws-created", {"workbook_id": "wb-1", "sql_content": "select 1"}),
            ("POST", "/newmoi/workbook/detail", "ws-created", {"workbook_id": "wb-1", "version_id": "ver-1"}),
            ("POST", "/newmoi/workbook/version/update", "ws-created", {"workbook_id": "wb-1", "version_id": "ver-1", "sql_content": "select 2"}),
            ("POST", "/newmoi/workbook/version/save", "ws-created", {"workbook_id": "wb-1", "version_id": "ver-1", "sql_content": "select 3"}),
            ("POST", "/newmoi/query/execute", "ws-created", {"query": "select 1", "db_name": "db1", "limit": 100}),
            ("POST", "/newmoi/query/describe", "ws-created", {"query_id": "query-1"}),
            ("POST", "/newmoi/query/kill", "ws-created", {"query_id": "query-1"}),
            ("POST", "/newmoi/query/result", "ws-created", {"statement_id": "stmt-1", "limit": 50}),
            ("POST", "/newmoi/query/detail", "ws-created", {"statement_id": "stmt-1", "start": "2026-06-01 00:00:00"}),
            ("POST", "/newmoi/query/profile", "ws-created", {"statement_id": "stmt-1", "end": "2026-06-02 00:00:00"}),
            ("POST", "/newmoi/workbook/delete", "ws-created", {"workbook_id": "wb-1"}),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as workbook_error:
            workspace.sql_workbook("")
        self.assertEqual(workbook_error.exception.code, "ErrWorkbookIDRequired")
        with self.assertRaises(sdk.Error) as version_error:
            workbook.version("")
        self.assertEqual(version_error.exception.code, "ErrVersionIDRequired")
        with self.assertRaises(sdk.Error) as query_error:
            workspace.sql_query("")
        self.assertEqual(query_error.exception.code, "ErrQueryIDRequired")
        with self.assertRaises(sdk.Error) as statement_error:
            workspace.sql_statement("")
        self.assertEqual(statement_error.exception.code, "ErrStatementIDRequired")

    def test_sql_workbooks_use_cursor_pagination(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        result = client.sql("ws-created").workbooks(
            sdk.with_workbook_search("ana"),
            sdk.with_workbook_page_size(20),
            sdk.with_workbook_page_token("cursor=="),
        )

        self.assertEqual(result.next_page_token, "workbooks-next")
        self.assertEqual(
            _Handler.requests[-1],
            (
                "POST",
                "/newmoi/workbook/list",
                "ws-created",
                {"search": "ana", "page_size": 20, "page_token": "cursor=="},
            ),
        )
    def test_sql_database_pagination_options_and_cursor(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        metadata = client.workspace("ws-created").sql_metadata()
        metadata.databases()
        page = metadata.databases(
            sdk.with_sql_database_page_size(10),
            sdk.with_sql_database_page_token("previous"),
            sdk.with_sql_database_search("sales"),
            sdk.with_sql_database_name("sales.data`2026"),
        )
        self.assertEqual(page.next_page_token, "db1")
        self.assertEqual(page.result[0].db_name, "db1")
        self.assertEqual(_Handler.requests, [
            ("POST", "/newmoi/meta/db/info", "ws-created", {}),
            ("POST", "/newmoi/meta/db/info", "ws-created", {"page_size": 10, "page_token": "previous", "search": "sales", "name": "sales.data`2026"}),
        ])

    def test_workspace_sql_metadata_handle_scopes_database_and_table(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))

        workspace = client.workspace("ws-created")
        metadata = workspace.sql_metadata()
        databases = metadata.databases()
        tree = metadata.tree()
        database = metadata.database("db1")
        tables = database.tables()
        table = database.table("orders")
        info = table.info()
        columns = table.columns()
        stats = table.column_stats()
        ddl = table.ddl()
        dropped_table = table.drop_table()
        view = database.table("orders_view")
        dropped_view = view.drop_view()
        dropped_database = database.drop()

        self.assertEqual(databases.total, 1)
        self.assertEqual(len(tree.db_list), 1)
        self.assertEqual(database.name, "db1")
        self.assertEqual(tables.db_name, "db1")
        self.assertEqual(table.name, "orders")
        self.assertEqual(info.rows, 10)
        self.assertEqual(columns.total, 1)
        self.assertEqual(stats.total, 1)
        self.assertEqual(ddl.create_sql, "CREATE TABLE orders")
        self.assertIsNone(dropped_table)
        self.assertIsNone(dropped_view)
        self.assertIsNone(dropped_database)

        expected = [
            ("POST", "/newmoi/meta/db/info", "ws-created", {}),
            ("POST", "/newmoi/meta/db/tree", "ws-created", {}),
            ("POST", "/newmoi/meta/db/table", "ws-created", {"name": "db1"}),
            ("POST", "/newmoi/meta/table/info", "ws-created", {"db_name": "db1", "table_name": "orders"}),
            ("POST", "/newmoi/meta/table/column", "ws-created", {"db_name": "db1", "table_name": "orders"}),
            ("POST", "/newmoi/meta/table/column_stat", "ws-created", {"db_name": "db1", "table_name": "orders"}),
            ("POST", "/newmoi/meta/table/ddl", "ws-created", {"db_name": "db1", "table_name": "orders"}),
            ("POST", "/newmoi/meta/table/drop", "ws-created", {"db_name": "db1", "table_name": "orders"}),
            ("POST", "/newmoi/meta/view/drop", "ws-created", {"db_name": "db1", "table_name": "orders_view"}),
            ("POST", "/newmoi/meta/db/drop", "ws-created", {"db_name": "db1"}),
        ]
        self.assertEqual(_Handler.requests, expected)

        with self.assertRaises(sdk.Error) as database_error:
            metadata.database("")
        self.assertEqual(database_error.exception.code, "ErrDatabaseRequired")
        with self.assertRaises(sdk.Error) as table_error:
            database.table("")
        self.assertEqual(table_error.exception.code, "ErrTableRequired")

    def test_workspace_member_tag_methods_use_canonical_routes(self):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("user-key"))
        members = client.workspace("ws-created").members()

        created = members.create_user_tag("tag1")
        tags = members.user_tags()
        updated = members.update_user_tag(7, "tag2")
        deleted = members.delete_user_tag(7)

        self.assertEqual(created.id, 7)
        self.assertEqual(tags.total, 1)
        self.assertEqual(tags.tag_list[0].name, "tag1")
        self.assertEqual(tags.tag_list[0].description, "canonical subject attribute")
        self.assertEqual(updated.id, 7)
        self.assertEqual(deleted.id, 7)
        self.assertEqual(
            _Handler.requests,
            [
                ("POST", "/newmoi/user/tag/create", "ws-created", {"name": "tag1"}),
                ("POST", "/newmoi/user/tag/list", "ws-created", {}),
                ("POST", "/newmoi/user/tag/update", "ws-created", {"id": 7, "name": "tag2"}),
                ("POST", "/newmoi/user/tag/delete", "ws-created", {"id": 7}),
            ],
        )

    def test_workspace_member_result_types_are_public_exports(self):
        for name in (
            "CurrentWorkspacePrincipalResult",
            "WorkspaceMember",
            "WorkspaceMemberInviteResult",
            "WorkspaceMemberListResult",
        ):
            self.assertIn(name, sdk.__all__)

    def test_agent_channel_instance_requests_use_unified_contract(self):
        client = sdk.Client("https://product.example.test/newmoi", sdk.with_api_key("user-key"))
        service = client.agents("ws-created")
        calls = []

        def resource(method, resource_name, tail_path, body, opts):
            calls.append((method, resource_name, tail_path, body, opts))
            if tail_path.endswith("/test"):
                return {
                    "instance": {"id": "channel-1", "provider": "wecom", "channel_type": "wecom_mail"},
                    "ok": True,
                    "status": "succeeded",
                }
            return {"id": "channel-1", "provider": "wecom", "channel_type": "wecom_mail"}

        service._resource = resource
        create_request = sdk.ChannelInstanceCreateRequest(
            "wecom_mail",
            name="mail",
            config={"smtp_host": "smtp.example.test"},
            secrets={"password": "secret"},
        )
        update_request = sdk.ChannelInstanceUpdateRequest(secrets={"password": "next"}, expected_version=2)

        created = service.create_channel_instance("wecom", create_request)
        updated = service.update_channel_instance("wecom", "channel-1", update_request)
        tested = service.test_channel_configuration("wecom", create_request)

        self.assertEqual(created.id, "channel-1")
        self.assertEqual(updated.channel_type, "wecom_mail")
        self.assertTrue(tested.ok)
        self.assertEqual(
            calls,
            [
                (
                    "POST",
                    "channels",
                    "/wecom/instances",
                    {
                        "channel_type": "wecom_mail",
                        "name": "mail",
                        "config": {"smtp_host": "smtp.example.test"},
                        "secrets": {"password": "secret"},
                    },
                    (),
                ),
                (
                    "PATCH",
                    "channels",
                    "/wecom/instances/channel-1",
                    {"secrets": {"password": "next"}, "expected_version": 2},
                    (),
                ),
                (
                    "POST",
                    "channels",
                    "/wecom/instances/test",
                    {
                        "channel_type": "wecom_mail",
                        "name": "mail",
                        "config": {"smtp_host": "smtp.example.test"},
                        "secrets": {"password": "secret"},
                    },
                    (),
                ),
            ],
        )

    def test_compute_sdk_rejects_invalid_worker_runtime_and_image_identity(self):
        with self.assertRaises(sdk.Error) as runtime_error:
            sdk_client._compute_worker_runtime_list(
                {
                    "runtimes": [
                        {
                            "worker_type": "python-worker",
                            "status": "ACTIVE",
                            "desired_replicas": 1,
                            "current_replicas": 1,
                            "created_at": "2026-08-11T10:30:00Z",
                            "updated_at": "2026-08-11T10:32:08Z",
                        }
                    ]
                }
            )
        self.assertEqual(runtime_error.exception.code, "ErrResponseInvalid")

        with self.assertRaises(sdk.Error) as image_error:
            sdk_client._worker_image_list(
                [
                    {
                        "id": "img-1",
                        "worker_type": "document-worker",
                        "image_key": "gpu-v2",
                        "type": "gpu-v1",
                    }
                ]
            )
        self.assertEqual(image_error.exception.code, "ErrResponseInvalid")


if __name__ == "__main__":
    unittest.main()
