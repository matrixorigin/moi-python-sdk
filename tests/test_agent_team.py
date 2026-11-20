import unittest
from unittest.mock import patch

import moi_product_sdk as sdk


class AgentTeamContractTest(unittest.TestCase):
    def test_team_route_kinds(self):
        from moi_product_sdk.routes import route_mappings

        routes = [r for r in route_mappings() if "/agent-teams" in r["path"]]
        self.assertEqual(len(routes), 13)
        for route in routes:
            self.assertNotEqual(route["method"], "ANY")
            self.assertEqual(
                route["kind"], "read" if route["method"] == "GET" else "write"
            )

    def setUp(self):
        self.service = sdk.Client(
            "http://127.0.0.1/newmoi", sdk.with_token("token")
        ).agents("workspace")

    def test_create_member_wire_identity(self):
        request = sdk.AgentTeamCreateRequest(
            name="team",
            members=[sdk.AgentTeamMemberRef(agent_workspace_id="ws", agent_id="agent")],
        )
        with patch.object(
            self.service, "_request", return_value={"id": "team", "version": 7}
        ) as wire:
            team = self.service.create_team(request)
        self.assertEqual((team.id, team.version), ("team", 7))
        self.assertEqual(
            wire.call_args.args[2]["members"],
            [{"agent_workspace_id": "ws", "agent_id": "agent"}],
        )

    def test_patch_preserves_clear_and_disable(self):
        self.assertEqual(
            sdk.AgentTeamUpdateRequest(name="", expected_version=3).body(),
            {"name": "", "expected_version": 3},
        )
        request = sdk.IngressConnectionUpdateRequest(
            enabled=False, agent_model="fast-2", expected_association_version=4, expected_config_version=5
        )
        with patch.object(
            self.service,
            "_request",
            return_value={
                "enabled": False,
                "target": {"kind": "agent", "workspace_id": "system", "id": "momo"},
            },
        ) as wire:
            result = self.service.update_ingress_connection("ingress", request)
        self.assertIs(wire.call_args.args[2]["enabled"], False)
        self.assertEqual(wire.call_args.args[2]["agent_model"], "fast-2")
        self.assertEqual(result.target.id, "momo")

    def test_slack_managed_stream_credentials_are_serialized(self):
        self.assertEqual(
            sdk.IngressManagedStreamConfig(
                app_id="A1", app_token="xapp-test", bot_token="xoxb-test"
            ).body(),
            {
                "app_id": "A1",
                "app_token": "xapp-test",
                "bot_token": "xoxb-test",
            },
        )
        self.assertEqual(
            sdk.IngressConnectionUpdateRequest(
                managed_stream_app_token="xapp-rotated",
                managed_stream_bot_token="xoxb-rotated",
                expected_association_version=4,
                expected_config_version=5,
            ).body()["managed_stream"],
            {"app_token": "xapp-rotated", "bot_token": "xoxb-rotated"},
        )
        legacy_positional = sdk.IngressConnectionUpdateRequest(
            False, "fast", "rotated-secret", 4, 5
        ).body()
        self.assertEqual(legacy_positional["expected_association_version"], 4)
        self.assertEqual(legacy_positional["expected_config_version"], 5)

    def test_feishu_managed_stream_uses_app_secret(self):
        self.assertEqual(
            sdk.IngressManagedStreamConfig(app_id="cli_test", app_secret="feishu-test").body(),
            {"app_id": "cli_test", "app_secret": "feishu-test"},
        )
        self.assertEqual(
            sdk.IngressConnectionUpdateRequest(
                expected_association_version=1, expected_config_version=2,
                managed_stream_app_secret="rotated",
            ).body()["managed_stream"],
            {"app_secret": "rotated"},
        )

    def test_session_identity_is_not_lost(self):
        with patch.object(
            self.service,
            "_request",
            return_value={
                "items": [
                    {
                        "context_id": "context",
                        "astra_session_id": "astra",
                        "created_by_moi_user_id": "user",
                        "last_answering_agent_id": "agent",
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0,
            },
        ):
            result = self.service.list_team_sessions("team")
        self.assertEqual(result.items[0].astra_session_id, "astra")
        self.assertEqual(result.items[0].created_by_moi_user_id, "user")
        self.assertEqual(result.items[0].last_answering_agent_id, "agent")

    def test_list_agent_catalog_cards_is_typed(self):
        with patch.object(
            self.service,
            "_request",
            return_value={
                "items": [{
                    "kind": "team",
                    "id": "team",
                    "workspace_id": "workspace",
                    "name": "Experts",
                    "status": "active",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "actions": ["chat", "manage"],
                }],
                "total": 1,
                "limit": 20,
                "offset": 0,
            },
        ) as wire:
            result = self.service.list_agent_catalog_cards(sdk.with_query_param("limit", "20"))
        self.assertEqual((result.items[0].kind, result.items[0].id), ("team", "team"))
        self.assertIn("limit=20", wire.call_args.args[1])

    def test_verify_ingress_connection_is_server_owned(self):
        request = sdk.IngressConnectionVerifyRequest(4, 5, "https://moi.example/callback")
        with patch.object(
            self.service,
            "_request",
            return_value={"id": "ingress", "channel_instance_id": "channel", "observed_state": "connected", "enabled": True},
        ) as wire:
            result = self.service.verify_ingress_connection("ingress", request)
        self.assertEqual(wire.call_args.args[0], "POST")
        self.assertEqual(wire.call_args.args[2], {"expected_association_version": 4, "expected_config_version": 5, "callback_url": "https://moi.example/callback"})
        self.assertTrue(result.connection.enabled)

    def test_list_ingress_capabilities_is_typed(self):
        with patch.object(
            self.service,
            "_request",
            return_value={
                "items": [{
                    "provider": "wecom",
                    "channel_type": "wecom_ai_bot",
                    "receive_modes": ["managed_stream", "callback"],
                }],
            },
        ) as wire:
            result = self.service.list_ingress_capabilities()
        self.assertEqual(wire.call_args.args[:2], ("GET", "/workspaces/workspace/ingress-capabilities"))
        self.assertEqual(result.items[0].receive_modes, ["managed_stream", "callback"])

    def test_unknown_fields_are_rejected_in_all_shapes(self):
        for method, value in (
            (lambda: self.service.get_team("team"), {"unexpected": 1}),
            (lambda: self.service.list_team_members("team"), [{"unexpected": 1}]),
            (lambda: self.service.list_ingress_connections(sdk.AgentTargetRef(kind="team", workspace_id="workspace", id="team")), {"items": [{"unexpected": 1}]}),
        ):
            with self.subTest(value=value):
                with patch.object(self.service, "_request", return_value=value):
                    with self.assertRaises(sdk.Error):
                        method()
