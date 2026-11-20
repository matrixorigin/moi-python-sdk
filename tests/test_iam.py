import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import moi_product_sdk as sdk


_LOCALHOST_NO_PROXY = ("127.0.0.1", "localhost", "::1")


def _with_localhost_no_proxy(value):
    entries = []
    seen = set()
    for item in (value or "").split(","):
        item = item.strip()
        if item and item not in seen:
            entries.append(item)
            seen.add(item)
    for item in _LOCALHOST_NO_PROXY:
        if item not in seen:
            entries.append(item)
            seen.add(item)
    return ",".join(entries)


class _IAMHandler(BaseHTTPRequestHandler):
    requests = []

    def _handle(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}
        self.__class__.requests.append((self.command, self.path, body))
        data = _response(self.command, self.path.split("?", 1)[0])
        payload = json.dumps({"code": "OK", "msg": "OK", "data": data}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _handle
    do_POST = _handle
    do_PATCH = _handle
    do_PUT = _handle
    do_DELETE = _handle

    def log_message(self, format, *args):
        return


class IAMServiceTest(unittest.TestCase):
    def test_role_delete_ownerships_reads_only_a_page(self):
        def preview(handler):
            _IAMHandler.requests.append((handler.command, handler.path, {}))
            data = {"items": [{"resource_type": "connector", "resource_id": "17", "display_name": "Orders", "ownership_version": 3}], "ownership_version": "set-v1", "next_cursor": "later-key"}
            payload = json.dumps({"code": "OK", "data": data}).encode()
            handler.send_response(200)
            handler.send_header("Content-Length", str(len(payload)))
            handler.end_headers()
            handler.wfile.write(payload)
        with patch.object(_IAMHandler, "do_GET", preview):
            page = self.iam.role_delete_ownerships("5", cursor="next-key", limit=10, transfer_requested=True)
        item, = page.items
        self.assertEqual((item.resource_type, item.resource_id, item.display_name, item.ownership_version), ("connector", "17", "Orders", 3))
        self.assertEqual((page.ownership_version, page.next_cursor), ("set-v1", "later-key"))
        request = urlsplit(_IAMHandler.requests[-1][1])
        self.assertEqual(request.path, "/newmoi/workspaces/ws-1/iam/roles/5/delete-ownerships")
        self.assertEqual(parse_qs(request.query), {"cursor": ["next-key"], "limit": ["10"], "transfer_requested": ["true"]})

    def test_transfer_object_ownership_typed_cas_and_receipt(self):
        request = sdk.IAMObjectOwnershipTransferRequest(target_role_id="7", expected_ownership_version=3, request_id="transfer-1")
        with patch(__name__ + "._response", return_value={
            "workspace_id": "ws-1", "resource_type": "connector", "resource_id": "connector-1",
            "previous_owner_role_id": "5", "owner_role_id": "7", "ownership_version": 4,
            "request_id": "transfer-1", "idempotent_replay": True,
        }):
            result = self.iam.transfer_object_ownership("connector", "connector-1", request)
        self.assertEqual((result.owner_role_id, result.ownership_version, result.idempotent_replay), ("7", 4, True))
        self.assertEqual(_IAMHandler.requests[-1], ("PUT", "/newmoi/workspaces/ws-1/iam/permissions/objects/connector/connector-1/owner", {
            "target_role_id": "7", "expected_ownership_version": 3, "request_id": "transfer-1",
        }))

    def test_inheritance_request_has_no_graph_cas_and_returns_historical_success(self):
        request = sdk.IAMRoleInheritanceMutationRequest(
            parent_role_id="7", expected_child_lifecycle_version=2,
            expected_parent_lifecycle_version=3, request_id="original-request",
        )
        with patch(__name__ + "._response", return_value={
            "child_role_id": "8", "parent_role_id": "7", "idempotent_replay": True,
        }):
            result = self.iam.add_role_inheritance("8", request)
        self.assertEqual((result.child_role_id, result.parent_role_id, result.idempotent_replay), ("8", "7", True))
        self.assertEqual(_IAMHandler.requests[-1], ("POST", "/newmoi/workspaces/ws-1/iam/roles/8/parents", {
            "parent_role_id": "7", "expected_child_lifecycle_version": 2,
            "expected_parent_lifecycle_version": 3, "request_id": "original-request",
        }))

        def pending(handler):
            payload = json.dumps({"code": "ErrIAMInheritancePending", "msg": "本次修改结果尚未确认"}).encode()
            handler.send_response(409)
            handler.send_header("Content-Type", "application/json")
            handler.send_header("Content-Length", str(len(payload)))
            handler.end_headers()
            handler.wfile.write(payload)

        with patch.object(_IAMHandler, "do_DELETE", pending):
            with self.assertRaises(sdk.Error) as raised:
                self.iam.remove_role_inheritance("8", request)
        self.assertEqual(
            (raised.exception.status, raised.exception.code, raised.exception.message),
            (409, "ErrIAMInheritancePending", "本次修改结果尚未确认"),
        )

    def setUp(self):
        self._proxy_env = {key: os.environ.get(key) for key in ("NO_PROXY", "no_proxy")}
        for key, value in self._proxy_env.items():
            os.environ[key] = _with_localhost_no_proxy(value)
        _IAMHandler.requests = []
        self.server = HTTPServer(("127.0.0.1", 0), _IAMHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        endpoint = f"http://127.0.0.1:{self.server.server_port}/newmoi"
        self.client = sdk.Client(endpoint, sdk.with_api_key("user-key"))
        self.iam = self.client.workspace("ws-1").iam()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        for key, value in self._proxy_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_current_principal_capabilities_query_and_response(self):
        for ids in (
            (),
            ("action.role.delete",),
            ("action.role.delete", "action.model.update"),
            ("",),
            ("navigation.roles", "navigation.roles"),
            ("navigation.roles&capability_id=other +/",),
        ):
            with self.subTest(ids=ids):
                result = self.iam.current_principal_capabilities(*ids)
                method, path, body = _IAMHandler.requests[-1]
                parsed = urlsplit(path)
                self.assertEqual((method, parsed.path, body), ("GET", "/newmoi/workspaces/ws-1/iam/me/capabilities", {}))
                self.assertEqual(parse_qs(parsed.query, keep_blank_values=True), {"capability_id": list(ids)} if ids else {})
                self.assertEqual((result.effective_role_id, result.capability_version, result.request_id, result.trace_id), ("7", "v1", "request-1", "trace-1"))
                self.assertEqual([item.capability_id for item in result.items], ["action.model.update", "action.role.delete"])
                update, delete = result.items
                self.assertEqual((update.action_id, update.resource_type, update.allowed, update.all_resources, list(update.resource_ids)), ("model_backend.update", "model_backend", True, False, ["llm:7"]))
                self.assertEqual((delete.allowed, delete.reason_code), (False, "PERMISSION_DENIED"))

    def test_current_principal_capabilities_preserves_server_error(self):
        def respond(handler):
            self.assertEqual(parse_qs(urlsplit(handler.path).query), {"capability_id": ["unknown"]})
            payload = json.dumps({"code": "IAM_ERROR_CODE_PERMISSION_DENIED", "msg": "Permission denied", "data": None}).encode()
            handler.send_response(403)
            handler.send_header("Content-Type", "application/json")
            handler.send_header("X-Request-ID", "public-request")
            handler.send_header("Content-Length", str(len(payload)))
            handler.end_headers()
            handler.wfile.write(payload)

        with patch.object(_IAMHandler, "do_GET", respond):
            with self.assertRaises(sdk.Error) as raised:
                self.iam.current_principal_capabilities("unknown")
        error = raised.exception
        self.assertEqual((error.status, error.code, error.message, error.request_id), (403, "IAM_ERROR_CODE_PERMISSION_DENIED", "Permission denied", "public-request"))

    def test_current_principal_capabilities_unsupported_ids(self):
        for ids, expected_ids in (
            (("future.id", "action.role.create"), ["action.role.create"]),
            (("future.id",), []),
        ):
            with self.subTest(ids=ids):
                data = {
                    "effective_role_id": "7",
                    "items": [{"capability_id": capability_id, "allowed": False, "reason_code": "PERMISSION_DENIED"} for capability_id in expected_ids],
                    "unsupported_capability_ids": ["future.id"],
                }
                with patch(__name__ + "._response", return_value=data):
                    result = self.iam.current_principal_capabilities(*ids)
                self.assertEqual(parse_qs(urlsplit(_IAMHandler.requests[-1][1]).query), {"capability_id": list(ids)})
                self.assertEqual([item.capability_id for item in result.items], expected_ids)
                self.assertEqual(list(result.unsupported_capability_ids), ["future.id"])
                self.assertEqual(result.effective_role_id, "7")

    def test_role_members_preserves_user_display_and_pagination(self):
        page = self.iam.role_members("role-1", sdk.with_query_param("cursor", "user-0"), sdk.with_query_param("limit", "1"))
        self.assertEqual(page.role_id, "role-1")
        self.assertEqual(page.next_cursor, "user-1")
        self.assertEqual(page.request_id, "members-request")
        self.assertEqual(page.trace_id, "members-trace")
        member = page.members[0]
        self.assertEqual(member.user_id, "user-1")
        self.assertEqual(member.display_name, "Alice Chen")
        self.assertEqual(member.email, "alice@example.com")
        self.assertTrue(member.default_role)
        self.assertEqual(member.default_role_version, 4)
        self.assertEqual(member.binding_created_at, 1700000000)
        self.assertEqual(_IAMHandler.requests, [("GET", "/newmoi/workspaces/ws-1/iam/roles/role-1/members?cursor=user-0&limit=1", {})])

    def test_role_delete_ownership_transfer_contract(self):
        bulk_request = sdk.IAMRoleDeleteRequest(reason_code="transfer-delete", expected_lifecycle_version=5, request_id="delete-1")
        bulk_request.ownership_transfer.expected_ownership_version = "ownership-v1"
        bulk_request.ownership_transfer.target_role_id = "role-target"
        per_object_request = sdk.IAMRoleDeleteRequest(reason_code="transfer-delete", expected_lifecycle_version=5, request_id="delete-1")
        per_object_request.ownership_transfer.expected_ownership_version = "ownership-v1"
        per_object_request.ownership_transfer.targets.add(resource_type="workflow", resource_id="workflow-1", target_role_id="role-a")
        per_object_request.ownership_transfer.targets.add(resource_type="table", resource_id="table-1", target_role_id="role-b")
        for request in (bulk_request, per_object_request):
            transfer = request.ownership_transfer
            with self.subTest(transfer=str(transfer)):
                def preview(handler):
                    _IAMHandler.requests.append((handler.command, handler.path, {}))
                    data = {"active_ownership_count": 2, "ownership": {
                        "owned_count": 2, "ownership_version": "ownership-v1", "next_cursor": "cursor-2",
                        "items": [{"resource_type": "workflow", "resource_id": "workflow-1", "display_name": "Order cleaning", "ownership_version": 7}],
                    }}
                    payload = json.dumps({"code": "OK", "data": data}).encode()
                    handler.send_response(200)
                    handler.send_header("Content-Length", str(len(payload)))
                    handler.end_headers()
                    handler.wfile.write(payload)
                with patch.object(_IAMHandler, "do_GET", preview):
                    impact = self.iam.role_delete_impact("role-1", 5, include_ownership=True, ownership_cursor="cursor-1", ownership_limit=1, transfer_requested=True)
                self.assertEqual((impact.ownership.owned_count, impact.ownership.ownership_version, impact.ownership.next_cursor), (2, "ownership-v1", "cursor-2"))
                item = impact.ownership.items[0]
                self.assertEqual((item.resource_type, item.resource_id, item.display_name, item.ownership_version), ("workflow", "workflow-1", "Order cleaning", 7))
                query = _IAMHandler.requests[-1][1]
                self.assertIn("include_ownership=true", query)
                self.assertIn("ownership_cursor=cursor-1", query)
                self.assertIn("ownership_limit=1", query)
                self.assertIn("transfer_requested=true", query)
                self.iam.delete_role("role-1", request)
                body = _IAMHandler.requests[-1][2]
                expected = {"expected_ownership_version": "ownership-v1"}
                if transfer.target_role_id:
                    expected["target_role_id"] = "role-target"
                else:
                    expected["targets"] = [
                        {"resource_type": "workflow", "resource_id": "workflow-1", "target_role_id": "role-a"},
                        {"resource_type": "table", "resource_id": "table-1", "target_role_id": "role-b"},
                    ]
                self.assertEqual(body, {"reason_code": "transfer-delete", "expected_lifecycle_version": 5, "request_id": "delete-1", "ownership_transfer": expected})

    def test_role_write_preserves_public_error_outcomes(self):
        # Outcome fixtures follow abcad03c's role_write_error_test.go.
        cases = [
            (409, "ErrIAMRoleNameExists", "This role name is already in use. Choose another name and submit again."),
            (409, "ErrIAMRoleWriteRolledBack", "The role change was not completed. Your previous settings are unchanged. You can submit again."),
            (500, "ErrIAMRoleWriteFailed", "The role change was not completed and the operation has stopped. Contact an administrator before continuing."),
            (409, "ErrIAMRoleWriteResultUnknown", "The result of this role change is not yet confirmed. Check the current role settings. If you still cannot confirm the result, contact an administrator."),
            (422, "ErrIAMRolePermissionRequired", "Select at least one valid application or data permission before creating the role."),
        ]
        for status, code, message in cases:
            with self.subTest(code=code):
                def respond(handler):
                    payload = json.dumps({"code": code, "msg": message, "data": {"request_id": "body-request"}}).encode()
                    handler.send_response(status)
                    handler.send_header("Content-Type", "application/json")
                    handler.send_header("X-Request-ID", "public-request")
                    handler.send_header("Content-Length", str(len(payload)))
                    handler.end_headers()
                    handler.wfile.write(payload)
                with patch.object(_IAMHandler, "do_POST", respond), patch.object(_IAMHandler, "do_PATCH", respond):
                    for operation in ("create", "update"):
                        with self.assertRaises(sdk.Error) as raised:
                            if operation == "create":
                                self.iam.create_role(sdk.IAMRoleCreateRequest(name="analyst", schema_version="v1", request_id="create-1"))
                            else:
                                self.iam.update_role("role-1", sdk.IAMRoleUpdateRequest(name="analyst", schema_version="v1", request_id="update-1", expected_lifecycle_version=1, expected_policy_version=1))
                        self.assertEqual((raised.exception.status, raised.exception.code, raised.exception.message, raised.exception.request_id), (status, code, message, "public-request"))

    def test_role_write_rejects_old_metadata_response_and_malformed_versions(self):
        for data in (
            {"role": _role(), "idempotent_replay": False},
            {"role_id": "role-1", "role_version": "invalid", "provisioning_state": "ready"},
            {"role_id": "role-1", "data_privilege_version": "invalid", "provisioning_state": "ready"},
            {"role_id": "role-1", "session_invalidation_status": "succeeded", "unknown_outcome": True},
        ):
            with self.subTest(data=data), patch(__name__ + "._response", return_value=data):
                with self.assertRaises(sdk.Error) as raised:
                    self.iam.update_role("role-1", sdk.IAMRoleUpdateRequest(request_id="update-1"))
                self.assertEqual(raised.exception.code, "ErrResponseInvalid")

    def test_typed_role_and_object_grant_routes(self):
        self.assertEqual(self.iam.permission_schema().schema_version, "v1")
        roles = self.iam.roles().roles
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0].system_role_name, "admin")
        created = self.iam.create_role(
            sdk.IAMRoleCreateRequest(
                name="analyst",
                schema_version="v1",
                request_id="create-1",
                statements=[
                    sdk.IAMApplicationPolicyStatement(
                        action_id="workflow.run",
                        resource_type="workflow",
                        scope_mode="all",
                    )
                ],
                data_privilege_mutations=[
                    sdk.IAMDataPrivilegeMutation(
                        operation="grant",
                        action_id="table.query",
                        resource_type="table",
                        resource_id="41",
                        privilege="select",
                        row_column=sdk.IAMDataPrivilegeRowColumnMutation(
                            mode="keep",
                            draft=sdk.IAMDataPrivilegeRowColumnDraft(),
                        ),
                    )
                ],
            )
        )
        self.assertEqual(created.role_id, "role-1")
        self.assertEqual(created.data_privilege_version, 4)
        self.assertFalse(created.idempotent_replay)
        self.assertEqual(created.session_invalidation_status, "succeeded")
        create_body = _IAMHandler.requests[2][2]
        self.assertEqual(create_body["statements"][0]["action_id"], "workflow.run")
        self.assertEqual(create_body["data_privilege_mutations"][0]["resource_id"], "41")
        permission_view = self.iam.role_permission_view("role-1")
        self.assertEqual(permission_view.expected_role_lifecycle_version, 3)
        self.assertEqual(permission_view.lifecycle_state, "disabled")
        self.assertFalse(permission_view.policy_mutation_allowed)
        updated = self.iam.update_role(
            "role-1",
            sdk.IAMRoleUpdateRequest(
                name="renamed", description="updated role", schema_version="v1",
                expected_lifecycle_version=3, expected_policy_version=7,
                expected_data_privilege_version=4, request_id="update-1",
                statements=[sdk.IAMApplicationPolicyStatement(action_id="workflow.run", resource_type="workflow", scope_mode="all")],
                data_privilege_mutations=[sdk.IAMDataPrivilegeMutation(operation="grant", action_id="table.query", resource_type="table", resource_id="table/1", privilege="select")],
            ),
        )
        self.assertIsInstance(updated, sdk.IAMRoleCreateResult)
        self.assertEqual(updated.role_id, "role-1")
        self.assertEqual((updated.role_version, updated.policy_version, updated.data_privilege_version), (4, 8, 5))
        self.assertEqual(updated.provisioning_state, "ready")
        self.assertEqual(updated.provisioning_version, 2)
        self.assertEqual(updated.provisioning_error_code, "")
        self.assertTrue(updated.idempotent_replay)
        self.assertEqual(updated.session_invalidation_status, "succeeded")
        self.assertEqual((updated.request_id, updated.trace_id), ("response-request", "response-trace"))
        self.iam.update_role_lifecycle(
            "role-1",
            sdk.IAMRoleLifecycleRequest(
                target_state="disabled",
                reason_code="test",
                expected_lifecycle_version=4,
                request_id="lifecycle-1",
            ),
        )
        self.iam.role_delete_impact("role-1", 5)
        grant_request = sdk.IAMObjectGrantsMutationRequest(
            schema_version="v1",
            expected_policy_version=7,
            expected_role_lifecycle_version=5,
            request_id="grant-1",
            changes=[sdk.IAMObjectGrantChange(action_id="connector.read")],
        )
        self.assertTrue(
            self.iam.validate_object_grants(
                "connector", "connector-1", "role-1", grant_request
            ).validate_only
        )
        self.iam.apply_object_grants(
            "connector", "connector-1", "role-1", grant_request
        )
        object_view = self.iam.object_permission_view("connector", "connector-1")
        self.assertEqual(object_view.owner.role_lifecycle_state, "disabled")
        self.assertEqual(len(object_view.direct_grants), 1)
        self.assertEqual(len(object_view.all_scope_grants), 1)
        self.assertEqual(object_view.direct_grants[0].role_lifecycle_state, "disabled")
        self.assertEqual(object_view.all_scope_grants[0].role_lifecycle_state, "active")
        self.iam.delete_role(
            "role-1",
            sdk.IAMRoleDeleteRequest(
                reason_code="cleanup",
                expected_lifecycle_version=5,
                request_id="delete-1",
            ),
        )

        self.assertEqual(len(_IAMHandler.requests), 11)
        self.assertEqual(
            _IAMHandler.requests[0][:2],
            ("GET", "/newmoi/workspaces/ws-1/iam/permissions/schema"),
        )
        self.assertEqual(
            _IAMHandler.requests[4][:2],
            ("PATCH", "/newmoi/workspaces/ws-1/iam/roles/role-1"),
        )
        self.assertEqual(
            _IAMHandler.requests[4][2]["expected_lifecycle_version"], 3
        )
        update_body = _IAMHandler.requests[4][2]
        self.assertEqual(update_body["expected_policy_version"], 7)
        self.assertEqual(update_body["expected_data_privilege_version"], 4)
        self.assertEqual(update_body["schema_version"], "v1")
        self.assertEqual(update_body["description"], "updated role")
        self.assertEqual(update_body["statements"][0]["action_id"], "workflow.run")
        self.assertEqual(update_body["data_privilege_mutations"][0]["resource_id"], "table/1")
        self.assertEqual(
            _IAMHandler.requests[6][1],
            "/newmoi/workspaces/ws-1/iam/roles/role-1/delete-impact?expected_lifecycle_version=5",
        )
        self.assertEqual(_IAMHandler.requests[7][2]["expected_policy_version"], 7)
        self.assertIsInstance(
            _IAMHandler.requests[7][2]["expected_role_lifecycle_version"], int
        )

    def test_typed_data_privilege_routes(self):
        request = sdk.IAMDataPrivilegeMutationRequest(
            request_id="request/1",
            expected_data_privilege_version=4,
            mutations=[
                sdk.IAMDataPrivilegeMutation(
                    operation="grant",
                    action_id="table.query",
                    resource_type="table",
                    resource_id="table/1",
                    privilege="select",
                    row_column=sdk.IAMDataPrivilegeRowColumnMutation(
                        mode="set",
                        draft=sdk.IAMDataPrivilegeRowColumnDraft(
                            black_column_list=["secret"],
                            rule_list=[
                                sdk.IAMDataPrivilegeRowRule(
                                    column="id",
                                    relation="and",
                                    expression_list=[
                                        sdk.IAMDataPrivilegeRowExpression(
                                            operator="=", expression=["1"]
                                        )
                                    ],
                                )
                            ],
                        ),
                    ),
                )
            ],
        )

        view = self.iam.data_privileges("role/1")
        self.assertEqual(view.data_privilege_version, 4)
        self.assertEqual(view.items[0].privilege, "select")
        validation = self.iam.validate_data_privileges("role/1", request)
        self.assertTrue(validation.valid)
        self.assertEqual(validation.payload_fingerprint, "fingerprint-1")
        self.assertEqual(
            [(mutation.operation, mutation.resource_id, mutation.row_column.mode)
             for mutation in validation.canonical_mutations],
            [("grant", "table/1", "set")],
        )
        canonical = validation.canonical_mutations[0].row_column.canonical_rule
        self.assertEqual(list(canonical.select_columns), ["id"])
        self.assertEqual(canonical.filters_join, "and")
        self.assertEqual(
            [(row.column, row.operator, list(row.values), row.match_type)
             for row in canonical.filters],
            [("id", "=", ["1"], "")],
        )
        applied = self.iam.apply_data_privileges("role/1", request)
        self.assertEqual(applied.state, "succeeded")
        self.assertEqual(applied.data_privilege_version, 5)
        operation = self.iam.data_privilege_operation("role/1", "request/1")
        self.assertEqual(operation.operation_id, "operation-1")
        self.assertEqual(len(operation.resource_results), 1)
        repaired = self.iam.repair_data_privileges(
            "role/1",
            "request/1:repair",
            sdk.IAMDataPrivilegeRepairRequest(
                request_id="repair-1", expected_data_privilege_version=5
            ),
        )
        self.assertEqual(repaired.state, "succeeded")
        self.assertEqual(repaired.data_privilege_version, 6)

        base = "/newmoi/workspaces/ws-1/iam/roles/role%2F1"
        self.assertEqual(len(_IAMHandler.requests), 5)
        self.assertEqual(
            [(method, path) for method, path, _body in _IAMHandler.requests],
            [
                ("GET", f"{base}/data-privileges"),
                ("POST", f"{base}/data-privileges:validate"),
                ("PUT", f"{base}/data-privileges"),
                ("GET", f"{base}/data-privilege-operations/request%2F1"),
                ("POST", f"{base}/data-privilege-operations/request%2F1:repair"),
            ],
        )
        validate_body = _IAMHandler.requests[1][2]
        self.assertEqual(validate_body["expected_data_privilege_version"], 4)
        self.assertEqual(validate_body["mutations"][0]["resource_id"], "table/1")
        self.assertEqual(validate_body["mutations"][0]["row_column"]["mode"], "set")
        self.assertEqual(_IAMHandler.requests[4][2]["request_id"], "repair-1")

    def test_exact_grant_resource_transport(self):
        request = sdk.IAMApplicationPolicyRequest()
        request.statements.add(action_id="table.grant.query", resource_type="table", resource_id="41", scope_mode="resources", target_action_id="table.query", grant_scope_mode="resources", grant_resource_id="41")
        with patch(__name__ + "._response", return_value={}):
            self.iam.validate_application_policy("role-1", request)
            self.iam.apply_application_policy("role-1", request)
        self.assertEqual(len(_IAMHandler.requests), 2)
        for _method, _path, body in _IAMHandler.requests:
            self.assertEqual(body["statements"][0]["grant_resource_id"], "41")

    def test_contract_result_routes_preserve_explicit_iam_endpoints(self):
        body = {"request_id": "req-1"}

        calls = [
            lambda: self.iam.permission_schema_result(),
            lambda: self.iam.roles_result(),
            lambda: self.iam.create_role_result(body),
            lambda: self.iam.update_role_result("role/1", body),
            lambda: self.iam.update_role_lifecycle_result("role/1", body),
            lambda: self.iam.delete_role_result("role/1", body),
            lambda: self.iam.role_permission_view_result("role/1"),
            lambda: self.iam.validate_application_policy_result("role/1", body),
            lambda: self.iam.apply_application_policy_result("role/1", body),
            lambda: self.iam.list_permission_resources_result(
                resource_type="database",
                action_id="catalog.show_databases",
                parent_id="catalog/1",
                cursor="next",
                q="sales",
                limit=1,
            ),
            lambda: self.iam.batch_describe_permission_resources_result(body),
            lambda: self.iam.object_permission_view_result("connector", "connector/1"),
            lambda: self.iam.validate_object_grants_result(
                "connector", "connector/1", "role/1", body
            ),
            lambda: self.iam.apply_object_grants_result(
                "connector", "connector/1", "role/1", body
            ),
            lambda: self.iam.data_privileges_result("role/1"),
            lambda: self.iam.validate_data_privileges_result("role/1", body),
            lambda: self.iam.apply_data_privileges_result("role/1", body),
            lambda: self.iam.data_privilege_operation_result("role/1", "request/1"),
            lambda: self.iam.repair_data_privileges_result(
                "role/1", "request/1:repair", body
            ),
            lambda: self.iam.role_inheritance_result("role/1"),
            lambda: self.iam.role_inheritance_graph_result("role/1"),
            lambda: self.iam.add_role_inheritance_result("role/1", body),
            lambda: self.iam.remove_role_inheritance_result(
                "role/1", "parent/1", body
            ),
        ]
        expected = [
            ("GET", "/newmoi/workspaces/ws-1/iam/permissions/schema"),
            ("GET", "/newmoi/workspaces/ws-1/iam/roles"),
            ("POST", "/newmoi/workspaces/ws-1/iam/roles"),
            ("PATCH", "/newmoi/workspaces/ws-1/iam/roles/role%2F1"),
            ("PUT", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/lifecycle"),
            ("DELETE", "/newmoi/workspaces/ws-1/iam/roles/role%2F1"),
            ("GET", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/permission-view"),
            ("POST", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/application-policy:validate"),
            ("PUT", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/application-policy"),
            (
                "GET",
                "/newmoi/workspaces/ws-1/iam/permissions/resources?resource_type=database&action_id=catalog.show_databases&parent_id=catalog%2F1&cursor=next&q=sales&limit=1",
            ),
            ("POST", "/newmoi/workspaces/ws-1/iam/permissions/resources:batchDescribe"),
            (
                "GET",
                "/newmoi/workspaces/ws-1/iam/permissions/objects/connector/connector%2F1/permission-view",
            ),
            (
                "POST",
                "/newmoi/workspaces/ws-1/iam/permissions/objects/connector/connector%2F1/roles/role%2F1/grants:validate",
            ),
            (
                "PUT",
                "/newmoi/workspaces/ws-1/iam/permissions/objects/connector/connector%2F1/roles/role%2F1/grants",
            ),
            ("GET", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/data-privileges"),
            ("POST", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/data-privileges:validate"),
            ("PUT", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/data-privileges"),
            (
                "GET",
                "/newmoi/workspaces/ws-1/iam/roles/role%2F1/data-privilege-operations/request%2F1",
            ),
            (
                "POST",
                "/newmoi/workspaces/ws-1/iam/roles/role%2F1/data-privilege-operations/request%2F1:repair",
            ),
            ("GET", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/inheritance"),
            ("GET", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/inheritance-graph"),
            ("POST", "/newmoi/workspaces/ws-1/iam/roles/role%2F1/parents"),
            (
                "DELETE",
                "/newmoi/workspaces/ws-1/iam/roles/role%2F1/parents/parent%2F1",
            ),
        ]

        for invoke in calls:
            invoke()

        self.assertEqual(
            [(method, path) for method, path, _body in _IAMHandler.requests],
            expected,
        )

    def test_permission_resource_typed_methods_preserve_contracts(self):
        with patch(__name__ + "._response", return_value={}):
            self.iam.list_permission_resources(
                "database",
                "database.grant.query",
                "data_privilege",
                sdk.with_query_param("parent_id", "catalog/1"),
                sdk.with_query_param("cursor", "next"),
                sdk.with_query_param("q", "sales"),
                sdk.with_query_param("limit", "1"),
            )
            self.iam.batch_describe_permission_resources(
                "database",
                "database.grant.query",
                "data_privilege",
                ["database/1"],
            )
        list_request = _IAMHandler.requests[0]
        self.assertEqual(list_request[0], "GET")
        for query in (
            "resource_type=database",
            "action_id=database.grant.query",
            "purpose=data_privilege",
            "parent_id=catalog%2F1",
            "cursor=next",
            "q=sales",
            "limit=1",
        ):
            self.assertIn(query, list_request[1])

        self.assertEqual(
            _IAMHandler.requests[1],
            (
                "POST",
                "/newmoi/workspaces/ws-1/iam/permissions/resources:batchDescribe",
                {
                    "resource_type": "database",
                    "resource_ids": ["database/1"],
                    "action_id": "database.grant.query",
                    "purpose": "data_privilege",
                },
            ),
        )

    def test_user_role_bindings_result_uses_canonical_route(self):
        iam = self.client.workspace("ws/1").iam()

        result = iam.user_role_bindings_result("user/2")

        self.assertEqual(result.status, 200)
        self.assertEqual(
            _IAMHandler.requests[-1][:2],
            (
                "GET",
                "/newmoi/workspaces/ws%2F1/iam/users/user%2F2/role-bindings",
            ),
        )

    def test_typed_user_role_bindings_routes_and_cas(self):
        iam = self.client.workspace("ws/1").iam()

        result = iam.user_role_bindings("user/2")
        self.assertEqual(result.user_id, "user/2")
        self.assertEqual(result.binding_version, "binding-v4")
        self.assertEqual(result.roles[0].role_id, "role/viewer")
        expected_binding_version = sdk.iam_binding_version_number(result)
        expected_default_role_version = result.default_role_version

        mutation = iam.put_user_role_bindings(
            "user/2",
            sdk.IAMUserRoleBindingsRequest(
                assigned_role_ids=["role/viewer", "role/editor"],
                default_role_id="role/editor",
                expected_binding_version=expected_binding_version,
                expected_default_role_version=expected_default_role_version,
                request_id="write-1",
            ),
        )
        self.assertEqual(mutation.user_id, "user/2")
        self.assertEqual(mutation.binding_version, 5)
        self.assertEqual(
            _IAMHandler.requests[-1],
            (
                "PUT",
                "/newmoi/workspaces/ws%2F1/iam/users/user%2F2/role-bindings",
                {
                    "assigned_role_ids": ["role/viewer", "role/editor"],
                    "default_role_id": "role/editor",
                    "expected_binding_version": expected_binding_version,
                    "expected_default_role_version": expected_default_role_version,
                    "request_id": "write-1",
                    "clear_default_role": False,
                },
            ),
        )

    def test_iam_binding_version_number_rejects_malformed_read_values(self):
        self.assertEqual(
            sdk.iam_binding_version_number(
                sdk.IAMUserRoleBindingsResult(binding_version="binding-v0")
            ),
            0,
        )
        self.assertEqual(
            sdk.iam_binding_version_number(
                sdk.IAMUserRoleBindingsResult(binding_version="binding-v42")
            ),
            42,
        )
        for value in (
            "",
            "binding-v",
            "v42",
            "binding-v-1",
            "binding-vx",
            "binding-v01",
            "binding-v00",
        ):
            with self.subTest(value=value):
                with self.assertRaises(sdk.Error) as error:
                    sdk.iam_binding_version_number(
                        sdk.IAMUserRoleBindingsResult(binding_version=value)
                    )
                self.assertEqual(error.exception.code, "ErrIAMBindingVersionInvalid")


def _response(method, path):
    if path.endswith("/me/capabilities"):
        return {
            "effective_role_id": "7", "capability_version": "v1", "request_id": "request-1", "trace_id": "trace-1",
            "items": [
                {"capability_id": "action.model.update", "action_id": "model_backend.update", "resource_type": "model_backend", "allowed": True, "all_resources": False, "resource_ids": ["llm:7"]},
                {"capability_id": "action.role.delete", "action_id": "role.delete", "resource_type": "workspace", "allowed": False, "reason_code": "PERMISSION_DENIED", "resource_ids": []},
            ],
        }
    if method == "GET" and path.endswith("/members"):
        return {
            "role_id": "role-1",
            "members": [{"user_id": "user-1", "display_name": "Alice Chen", "email": "alice@example.com", "default_role": True, "default_role_version": 4, "binding_created_at": 1700000000}],
            "next_cursor": "user-1",
            "request_id": "members-request",
            "trace_id": "members-trace",
        }
    if path.endswith("/permissions/schema"):
        return {
            "schema_version": "v1",
            "capabilities": {},
            "resources": [],
            "actions": [],
            "operations": [],
        }
    if method == "GET" and path.endswith("/data-privileges"):
        return {
            "target_role_id": "role/1",
            "data_privilege_version": 4,
            "matrixone_fact_version": "facts-4",
            "items": [
                {
                    "resource_type": "table",
                    "resource_id": "table/1",
                    "action_id": "table.query",
                    "privilege": "select",
                    "ui_config_snapshot": {
                        "black_column_list": ["secret"],
                        "rule_list": [],
                    },
                    "columns": [],
                }
            ],
        }
    if method == "POST" and path.endswith("/data-privileges:validate"):
        return {
            "valid": True,
            "errors": [],
            "warnings": [],
            "payload_fingerprint": "fingerprint-1",
            "canonical_mutations": [{
                "operation": "grant", "resource_id": "table/1",
                "row_column": {"mode": "set", "canonical_rule": {
                    "select_columns": ["id"], "filters_join": "and",
                    "filters": [{"column": "id", "operator": "=", "values": ["1"], "match_type": ""}],
                }},
            }],
        }
    if method == "PUT" and path.endswith("/data-privileges"):
        return _data_privilege_operation(5)
    if method == "GET" and "/data-privilege-operations/" in path:
        return _data_privilege_operation(5)
    if method == "POST" and "/data-privilege-operations/" in path:
        return _data_privilege_operation(6)
    if method == "GET" and path.endswith("/iam/roles"):
        return {
            "roles": [
                {
                    "role_id": "role-admin",
                    "role_name": "Administrator",
                    "system_role": True,
                    "system_role_name": "admin",
                }
            ]
        }
    if method == "GET" and "/iam/users/" in path and path.endswith("/role-bindings"):
        return {
            "user_id": "user/2",
            "roles": [
                {
                    "role_id": "role/viewer",
                    "role_name": "Viewer",
                    "selectable": True,
                }
            ],
            "default_role_id": "role/viewer",
            "default_role_version": 4,
            "binding_version": "binding-v4",
            "request_id": "read-1",
            "trace_id": "trace-1",
        }
    if method == "PUT" and "/iam/users/" in path and path.endswith("/role-bindings"):
        return {
            "user_id": "user/2",
            "assigned_role_ids": ["role/viewer", "role/editor"],
            "default_role_id": "role/editor",
            "binding_version": 5,
            "default_role_version": 5,
            "audit_event_id": "audit-1",
            "idempotent_replay": False,
            "request_id": "write-1",
            "trace_id": "trace-2",
        }
    if (method == "POST" and path.endswith("/iam/roles")) or (method == "PATCH" and path.endswith("/iam/roles/role-1")):
        return {
            "role_id": "role-1",
            "role_version": 4 if method == "PATCH" else 1,
            "policy_version": 8 if method == "PATCH" else 7,
            "data_privilege_version": 5 if method == "PATCH" else 4,
            "provisioning_state": "ready",
            "provisioning_version": 2,
            "provisioning_error_code": "",
            "idempotent_replay": method == "PATCH",
            "session_invalidation_status": "succeeded",
            "request_id": "response-request",
            "trace_id": "response-trace",
        }
    if path.endswith("/permission-view") and "/roles/" in path:
        return {
            "role_id": "role-1",
            "schema_version": "v1",
            "expected_role_lifecycle_version": 3,
            "lifecycle_state": "disabled",
            "policy_mutation_allowed": False,
            "capabilities": {},
            "direct_grants": [],
        }
    if path.endswith("/delete-impact"):
        return {"role": _role(), "blocked": False}
    if path.endswith("/grants:validate"):
        return {
            "workspace_id": "ws-1",
            "resource_type": "connector",
            "resource_id": "connector-1",
            "target_role_id": "role-1",
            "previous_policy_version": 7,
            "policy_version": 7,
            "added_count": 1,
            "validate_only": True,
        }
    if path.endswith("/grants"):
        return {
            "workspace_id": "ws-1",
            "resource_type": "connector",
            "resource_id": "connector-1",
            "target_role_id": "role-1",
            "previous_policy_version": 7,
            "policy_version": 8,
            "added_count": 1,
        }
    if path.endswith("/permission-view"):
        return {
            "workspace_id": "ws-1",
            "resource_type": "connector",
            "resource_id": "connector-1",
            "owner": {"role_id": "role-1", "role_lifecycle_state": "disabled"},
            "capabilities": {},
            "direct_grants": [{"role_id": "role-1", "role_lifecycle_state": "disabled", "action_id": "connector.update", "scope_mode": "resources", "resource_id": "connector-1"}],
            "all_scope_grants": [{"role_id": "role-2", "role_lifecycle_state": "active", "action_id": "connector.read", "scope_mode": "all"}],
        }
    return {"role": _role(), "idempotent_replay": False}


def _data_privilege_operation(version):
    return {
        "request_id": "request/1",
        "operation_id": "operation-1",
        "state": "succeeded",
        "data_privilege_version": version,
        "resource_results": [
            {
                "resource_type": "table",
                "resource_id": "table/1",
                "action_id": "table.query",
                "privilege_key": "select",
                "operation": "grant",
                "state": "succeeded",
            }
        ],
    }

def _role():
    return {
        "workspace_id": "ws-1",
        "role_id": "role-1",
        "role_name": "analyst",
        "lifecycle_state": "active",
        "lifecycle_version": 5,
        "system_role": False,
    }


if __name__ == "__main__":
    unittest.main()
