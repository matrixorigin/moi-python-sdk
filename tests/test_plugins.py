import json
import http.cookiejar
import os
import ssl
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from google.protobuf import json_format
import moi_product_sdk as sdk


# Self-signed localhost fixture, valid through 2126; never used outside tests.
_CALLBACK_CERT = """-----BEGIN CERTIFICATE-----
MIIBmjCCAUGgAwIBAgIUbDK/VVH2g274AnTNvMcNpwrsypMwCgYIKoZIzj0EAwIw
FDESMBAGA1UEAwwJbG9jYWxob3N0MCAXDTI2MTAyODExMDA1MloYDzIxMjYxMDA0
MTEwMDUyWjAUMRIwEAYDVQQDDAlsb2NhbGhvc3QwWTATBgcqhkjOPQIBBggqhkjO
PQMBBwNCAATh31pXwvJLYJyU0MWHM7gDz/t/l48u49k6AdicPo1J8gUN7a3JEVVZ
QQnikx7lUohGLkrCRLzoE9n9GbBCocTuo28wbTAdBgNVHQ4EFgQUQ9jWGEcWexc9
X46iMRWBdAJpQYMwHwYDVR0jBBgwFoAUQ9jWGEcWexc9X46iMRWBdAJpQYMwDwYD
VR0TAQH/BAUwAwEB/zAaBgNVHREEEzARgglsb2NhbGhvc3SHBH8AAAEwCgYIKoZI
zj0EAwIDRwAwRAIgVo9g8hert+Qe1QRQfkG4Px0PWkGvJ1xi9zyXhvdQ8VMCIFqW
Eb2F+KqIjpQECLQTieOIehgXtprC9EfLXQlM/u2D
-----END CERTIFICATE-----
"""
_CALLBACK_KEY = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgGjSCnDRy1px38X99
dumZDEBd2C9afDaKwinODWjm6LyhRANCAATh31pXwvJLYJyU0MWHM7gDz/t/l48u
49k6AdicPo1J8gUN7a3JEVVZQQnikx7lUohGLkrCRLzoE9n9GbBCocTu
-----END PRIVATE KEY-----
"""


class PluginCallbackHandler(BaseHTTPRequestHandler):
    callback_path = "/deployment/api/v1/plugins/oauth/callback/"
    requests = []
    mode = ""

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.__class__.requests.append((self.command, self.path, self.headers, body))
        self.send_response(200)
        self.send_header("Set-Cookie", f"plugin-proof=bound-proof; Path={self.callback_path}; Secure; HttpOnly; SameSite=Lax")
        self.end_headers()
        self.wfile.write(b'{"code":0,"data":{"attempt_id":"attempt"}}')

    def do_GET(self):
        self.__class__.requests.append((self.command, self.path, self.headers, b""))
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query, keep_blank_values=True)
        status, body = 200, b"<html>authorized</html>"
        if self.mode == "malformed":
            status, body = 502, b"RAW-SECRET"
        elif query.get("iss") == ["https://wrong.example.test"]:
            status, body = 400, json.dumps({"code": "PLUGIN_OAUTH_ISSUER_INVALID", "msg": "签发者不匹配。", "details": {"reason": "PLUGIN_OAUTH_ISSUER_INVALID"}}).encode()
        elif "plugin-proof=bound-proof" not in self.headers.get("Cookie", ""):
            status, body = 403, b'{"code":"PLUGIN_OAUTH_STATE_INVALID","msg":"Browser proof is missing.","details":{"reason":"PLUGIN_OAUTH_STATE_INVALID"}}'
        elif query.get("state") == ["redirect"]:
            status, body = 302, b"redirect"
        elif query.get("error") == ["access_denied"]:
            body = b"<html>denied</html>"
        self.send_response(status)
        self.send_header("X-Request-ID", "callback-request")
        if status == 302:
            self.send_header("Location", "/must-not-follow")
        if status == 200:
            self.send_header("Set-Cookie", f"plugin-proof=; Max-Age=0; Path={self.callback_path}; Secure; HttpOnly")
        self.end_headers()
        self.wfile.write(body)


class PluginOAuthCallbackTest(unittest.TestCase):
    product_prefix = "/deployment/newmoi"
    callback_path = "/deployment/api/v1/plugins/oauth/callback/"
    @classmethod
    def setUpClass(cls):
        cls.files = tempfile.TemporaryDirectory()
        cert, key = os.path.join(cls.files.name, "cert.pem"), os.path.join(cls.files.name, "key.pem")
        for path, content in ((cert, _CALLBACK_CERT), (key, _CALLBACK_KEY)):
            with open(path, "w") as file:
                file.write(content)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        cls.tls_context = ssl.create_default_context(cafile=cert)
        cls.server = HTTPServer(("127.0.0.1", 0), PluginCallbackHandler)
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        cls.plain_server = HTTPServer(("127.0.0.1", 0), PluginCallbackHandler)
        cls.threads = [threading.Thread(target=lambda server=server: server.serve_forever(poll_interval=0.01), daemon=True) for server in (cls.server, cls.plain_server)]
        for thread in cls.threads:
            thread.start()

    @classmethod
    def tearDownClass(cls):
        for server in (cls.server, cls.plain_server):
            server.shutdown()
            server.server_close()
        for thread in cls.threads:
            thread.join()
        cls.files.cleanup()

    def setUp(self):
        self.environment = patch.dict(os.environ, {"NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        PluginCallbackHandler.requests, PluginCallbackHandler.mode = [], ""
        PluginCallbackHandler.callback_path = self.callback_path
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), urllib.request.HTTPSHandler(context=self.tls_context))
        self.opener.addheaders.append(("X-Opener-Credential", "opener-secret"))
        # Callback shares the existing process-installed browser opener's jar.
        self.old_opener = urllib.request._opener
        urllib.request.install_opener(self.opener)
        self.addCleanup(lambda: urllib.request.install_opener(self.old_opener))
        self.base = f"https://127.0.0.1:{self.server.server_port}{self.product_prefix}"
        self.client = sdk.Client(self.base, sdk.with_api_key("begin-key"), sdk.with_token("bearer-secret"),
                                 sdk.with_session_cookie("configured-cookie=secret"),
                                 sdk.with_custom_header("X-Workspace-ID", "ws"),
                                 sdk.with_custom_header("X-MOI-Role-ID", "1"),
                                 sdk.with_custom_header("X-MOI-Runtime-Authorization", "runtime-secret"),
                                 sdk.with_custom_header("X-Custom-Credential", "custom-secret"))

    def begin(self):
        self.client.agents("ws").resource_post("plugin-connections", "/pc/oauth", {"initiator": "browser", "expected_version": 1})
        method, path, headers, body = PluginCallbackHandler.requests[-1]
        self.assertEqual((method, path, headers["X-API-Key"], json.loads(body)["initiator"]),
                         ("POST", self.product_prefix + "/workspaces/ws/plugin-connections/pc/oauth", "begin-key", "browser"))

    def complete(self, client, registration_id, request, issuer=""):
        return client.complete_plugin_oauth_callback(registration_id, request, issuer)

    def callback(self, request, issuer="", registration_id="registration"):
        return self.complete(self.client, registration_id, request, issuer)

    def test_callback_uses_fixed_endpoint_encoded_query_and_secure_browser_proof(self):
        self.begin()
        request = sdk.BrowserLoginCallbackRequest(state="state +&%/中文", code="code +&%/?")
        issuer, registration = "https://issuer.example.test/path?x=1&y=2", "reg/ +%?中"
        response = self.callback(request, issuer, registration)
        try:
            self.assertEqual((response.status, response.headers["X-Request-ID"], response.read()), (200, "callback-request", b"<html>authorized</html>"))
        finally:
            response.close()
        method, path, headers, _ = PluginCallbackHandler.requests[-1]
        target = urllib.parse.urlsplit(path)
        self.assertEqual((method, target.path), ("GET", self.callback_path + urllib.parse.quote(registration, safe="$&+:=@")))
        self.assertEqual(urllib.parse.parse_qs(target.query, keep_blank_values=True), {"state": [request.state], "code": [request.code], "error": [""], "iss": [issuer]})
        self.assertEqual(headers["Cookie"], "plugin-proof=bound-proof")
        for header in ("X-API-Key", "Authorization", "X-Workspace-ID", "X-MOI-Role-ID", "X-MOI-Runtime-Authorization", "X-Custom-Credential", "X-Opener-Credential"):
            self.assertIsNone(headers[header])
        # Local handler copies must not reparent the installed opener's handlers.
        for handler in self.opener.handlers:
            self.assertIs(handler.parent, self.opener)
        with self.assertRaises(sdk.Error) as captured:
            self.callback(request, issuer, registration)
        self.assertEqual((captured.exception.code, captured.exception.status), ("PLUGIN_OAUTH_STATE_INVALID", 403))

    def test_proof_is_required_and_secure_cookie_is_not_sent_over_http(self):
        request = sdk.BrowserLoginCallbackRequest(state="state", code="code")
        with self.assertRaises(sdk.Error) as captured:
            self.callback(request)
        self.assertEqual((captured.exception.code, captured.exception.details["reason"]), ("PLUGIN_OAUTH_STATE_INVALID", "PLUGIN_OAUTH_STATE_INVALID"))
        self.begin()
        client = sdk.Client(f"http://127.0.0.1:{self.plain_server.server_port}{self.product_prefix}", sdk.with_unauthenticated())
        with self.assertRaises(sdk.Error) as captured:
            self.complete(client, "registration", request)
        self.assertEqual(captured.exception.code, "PLUGIN_OAUTH_STATE_INVALID")
        self.assertIsNone(PluginCallbackHandler.requests[-1][2]["Cookie"])

    def test_denial_and_redirect_are_returned_without_following(self):
        for state, error, status, body in (("state", "access_denied", 200, b"<html>denied</html>"), ("redirect", "", 302, b"redirect")):
            with self.subTest(state=state):
                self.begin()
                response = self.callback(sdk.BrowserLoginCallbackRequest(state=state, error=error))
                try:
                    self.assertEqual((response.status, response.read()), (status, body))
                    if status == 302:
                        self.assertEqual(response.headers["Location"], "/must-not-follow")
                finally:
                    response.close()
                self.assertEqual(urllib.parse.urlsplit(PluginCallbackHandler.requests[-1][1]).path, self.callback_path + "registration")
                query = urllib.parse.parse_qs(urllib.parse.urlsplit(PluginCallbackHandler.requests[-1][1]).query, keep_blank_values=True)
                self.assertEqual(query, {"state": [state], "code": [""], "error": [error]})

    def test_owner_errors_invalid_response_and_transport_are_preserved(self):
        request = sdk.BrowserLoginCallbackRequest(state="state", code="code")
        with self.assertRaises(sdk.Error) as captured:
            self.callback(request, "https://wrong.example.test")
        failure = captured.exception
        self.assertEqual((failure.code, failure.message, failure.status, failure.request_id, failure.details["reason"]),
                         ("PLUGIN_OAUTH_ISSUER_INVALID", "签发者不匹配。", 400, "callback-request", "PLUGIN_OAUTH_ISSUER_INVALID"))
        PluginCallbackHandler.mode = "malformed"
        with self.assertRaises(sdk.Error) as captured:
            self.callback(request)
        self.assertEqual((captured.exception.code, captured.exception.status, captured.exception.request_id), ("ErrResponseInvalid", 502, "callback-request"))
        self.assertNotIn("RAW-SECRET", str(captured.exception))
        with patch("urllib.request.OpenerDirector.open", side_effect=urllib.error.URLError("RAW-SECRET")):
            with self.assertRaises(sdk.Error) as captured:
                self.callback(request)
        self.assertEqual(captured.exception.code, "ErrTransportUnavailable")
        self.assertNotIn("RAW-SECRET", str(captured.exception))

    def test_request_and_registration_are_validated_before_network(self):
        with self.assertRaises(TypeError):
            self.callback(None)
        for registration in ("", ".", ".."):
            with self.subTest(registration=registration), self.assertRaises(sdk.Error):
                self.callback(sdk.BrowserLoginCallbackRequest(), registration_id=registration)
        self.assertEqual(PluginCallbackHandler.requests, [])

    def test_endpoint_credentials_and_fragment_are_rejected_before_network(self):
        for endpoint in ("https://user:password@example.test/newmoi", "https://user@example.test/newmoi",
                         "https://@example.test/newmoi", "https://example.test/newmoi#fragment"):
            with self.subTest(endpoint=endpoint):
                client = sdk.Client(endpoint, sdk.with_unauthenticated())
                with patch("urllib.request.OpenerDirector.open") as open_response:
                    with self.assertRaises(sdk.Error) as captured:
                        self.complete(client, "registration", sdk.BrowserLoginCallbackRequest(state="state", code="code"))
                    self.assertEqual(captured.exception.code, "ErrPathInvalid")
                    open_response.assert_not_called()
        self.assertEqual(PluginCallbackHandler.requests, [])


class PluginOAuthProductCallbackTest(PluginOAuthCallbackTest):
    product_prefix = "/newmoi"
    callback_path = "/newmoi/api/v1/plugins/oauth/callback/"

    def complete(self, client, registration_id, request, issuer=""):
        return client.complete_plugin_oauth_product_callback(registration_id, request, issuer)


class PluginOAuthCustomProductCallbackTest(PluginOAuthProductCallbackTest):
    product_prefix = "/custom"
    callback_path = "/custom/api/v1/plugins/oauth/callback/"


class PluginHandler(BaseHTTPRequestHandler):
    response = {}
    status = 200
    requests = []

    def log_message(self, *args):
        pass

    def handle_request(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.__class__.requests.append((self.command, self.path.split("?")[0], self.headers, body))
        response = self.__class__.response
        payload = response if isinstance(response, bytes) else json.dumps(response).encode("utf-8")
        self.send_response(self.__class__.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Request-ID", "plugin-request")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PATCH = do_DELETE = handle_request


class PluginControlPlaneTest(unittest.TestCase):
    def test_publication_preserves_localized_display_and_canonical_name(self):
        for name in ("企业微信", "WeCom"):
            with self.subTest(name=name):
                PluginHandler.response = {"code": 0, "data": {"publication": {
                    "name": "wecom", "description": "package metadata",
                    "display_name": name, "display_description": "localized description",
                }}}
                publication = self.client.agents("ws").get_plugin_release("pr_fixture", sdk.with_query_param("namespace", "system")).publication
                self.assertEqual((publication.name, publication.description), ("wecom", "package metadata"))
                self.assertEqual((publication.display_name, publication.display_description), (name, "localized description"))

    def test_setup_selection_is_forwarded_in_install_and_configure(self):
        for selected in ("", "ps_selected"):
            for update in (False, True):
                with self.subTest(selected=selected, update=update):
                    PluginHandler.response = {"code": "OK", "data": {"id": "pi_selected"}}
                    agent = self.client.agents("ws")
                    if update:
                        agent.update_plugin_installation("pi_selected", sdk.PluginUpdateInstallationRequest(
                            setup_operation_id=selected, expected_version=1,
                            release_namespace="system", release_id="pr_fixture"))
                    else:
                        agent.install_plugin(sdk.PluginInstallRequest(setup_operation_id=selected,
                            release_namespace="system", release_id="pr_fixture"))
                    payload = json.loads(PluginHandler.requests[-1][3])
                    if selected:
                        self.assertEqual(selected, payload["setup_operation_id"])
                    else:
                        self.assertNotIn("setup_operation_id", payload)

    def test_mutations_require_valid_success_envelopes(self):
        for raw in [b"", b"null", b"RAW-SECRET", b'{"status":"disconnected"}',
                    b'{"code":null,"data":{}}', b'{"code":true,"data":{}}', b'{"code":"","data":{}}',
                    b'{"code":200.5,"data":{}}', b'{"code":0,"msg":null,"data":{}}',
                    b'{"code":0,"data":null}', b'{"code":0,"data":[]}', b'\xff']:
            a = self.client.agents("ws")
            for operation in [lambda: a.disconnect_plugin_connection("connection", 1),
                              lambda: a.create_plugin_connection(sdk.PluginCreateConnectionRequest())]:
                with self.subTest(raw=raw, operation=operation):
                    PluginHandler.response = raw
                    before = len(PluginHandler.requests)
                    with self.assertRaises(sdk.Error) as captured:
                        operation()
                    failure = captured.exception
                    self.assertEqual((failure.code, failure.status, failure.request_id), ("ErrResponseInvalid", 200, "plugin-request"))
                    self.assertNotIn("RAW-SECRET", str(failure))
                    self.assertEqual(len(PluginHandler.requests), before + 1)

    def test_error_contract_preserves_explicit_locale_and_details(self):
        for locale, message in [("zh-CN", "连接已更新，请刷新后再试。"), ("en-US", "The connection changed. Refresh and try again.")]:
            with self.subTest(locale=locale):
                PluginHandler.status = 409
                PluginHandler.response = {"code": 4, "msg": message, "details": {"reason": "PLUGIN_STATE_CONFLICT", "domain": "moi-core.agent-plugin"}}
                client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("test-user-key"), sdk.with_custom_header("Accept-Language", locale))
                with self.assertRaises(sdk.Error) as captured:
                    client.agents("ws").get_plugin_installation("installation")
                failure = captured.exception
                self.assertEqual((failure.code, failure.status, failure.message, failure.request_id), ("4", 409, message, "plugin-request"))
                self.assertEqual(failure.details["reason"], "PLUGIN_STATE_CONFLICT")
                self.assertEqual(PluginHandler.requests[-1][2]["Accept-Language"], locale)

    def test_invalid_error_envelope_and_unavailable_transport_are_distinct(self):
        from moi_product_sdk.client import _parse_error
        for raw in [b"", b"RAW-SECRET", b"null", b"[]", b'{"msg":"RAW-SECRET"}', b'{"code":4,"msg":"safe","details":{"reason":false}}', b'{"code":0,"msg":"safe"}', b'{"code":4.5,"msg":"safe"}', b'\xff']:
            with self.subTest(raw=raw):
                failure = _parse_error(502, raw, "request-1")
                self.assertEqual((failure.code, failure.status, failure.request_id), ("ErrResponseInvalid", 502, "request-1"))
                self.assertNotIn("RAW-SECRET", str(failure))
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("RAW-SECRET")):
            with self.assertRaises(sdk.Error) as captured:
                self.client.agents("ws").get_plugin_installation("installation")
        self.assertEqual((captured.exception.code, captured.exception.status), ("ErrTransportUnavailable", 0))
        self.assertNotIn("RAW-SECRET", str(captured.exception))
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(os.environ, {"NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"})
        cls.environment.start()
        cls.server = HTTPServer(("127.0.0.1", 0), PluginHandler)
        cls.thread = threading.Thread(target=lambda: cls.server.serve_forever(poll_interval=0.01), daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        cls.environment.stop()

    def setUp(self):
        PluginHandler.requests = []
        PluginHandler.status = 200
        self.client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("test-user-key"))

    def assert_wire_fields(self, expected, actual):
        if isinstance(expected, dict):
            for key, value in expected.items():
                self.assertIn(key, actual)
                self.assert_wire_fields(value, actual[key])
        elif isinstance(expected, list):
            self.assertEqual(len(expected), len(actual))
            for left, right in zip(expected, actual):
                self.assert_wire_fields(left, right)
        elif isinstance(expected, int) and not isinstance(expected, bool) and isinstance(actual, str):
            self.assertEqual(str(expected), actual)
        else:
            self.assertEqual(expected, actual)

    def test_all_typed_control_plane_routes(self):
        a = self.client.agents("ws")
        cases = [
            ("SearchPlugins", "GET", "/newmoi/workspaces/ws/plugin-discovery/search", json.loads("{\"candidates\":[{\"source\":\"system\",\"release\":{\"id\":\"pr_fixture\",\"workspace_id\":\"system\",\"registry\":\"builtin\",\"publisher\":\"matrixorigin\",\"name\":\"example\",\"version\":\"1.0.0\",\"digest\":\"sha256:test\",\"description\":\"Example\",\"published_by\":\"system\",\"created_at\":\"2026-10-08T00:00:00Z\"},\"capabilities\":[{\"capability\":{\"id\":\"operation:read\",\"name\":\"read\",\"description\":\"Read\",\"kind\":\"http\",\"side_effect\":\"read\",\"digest\":\"sha256:test\"},\"capability_ref\":\"pc1.fixture\"}],\"capabilities_truncated\":false}],\"has_more\":true,\"next_cursor\":\"next\"}"), lambda: a.search_plugins(sdk.with_query_param("availability","market"))),
            ("DescribePluginCapability", "GET", "/newmoi/workspaces/ws/plugin-discovery/describe", json.loads("{\"capability\":{\"id\":\"operation:read\",\"name\":\"read\",\"description\":\"Read\",\"kind\":\"http\",\"side_effect\":\"read\",\"digest\":\"sha256:test\"},\"capability_ref\":\"pc1.fixture\",\"input_schema\":{\"type\":\"object\"},\"connections\":[{\"requirement\":\"account\",\"profiles\":[\"oauth\"]}]}"), lambda: a.describe_plugin_capability("pc1.fixture")),
            ("ListPluginReleases", "GET", "/newmoi/workspaces/ws/plugin-releases", json.loads("{\"items\":[{\"id\":\"pr_fixture\",\"workspace_id\":\"system\",\"registry\":\"builtin\",\"publisher\":\"matrixorigin\",\"name\":\"example\",\"version\":\"1.0.0\",\"digest\":\"sha256:test\",\"description\":\"Example\",\"published_by\":\"system\",\"created_at\":\"2026-10-08T00:00:00Z\"}],\"total\":1}"), lambda: a.list_plugin_releases(sdk.with_query_param("namespace","system"))),
            ("GetPluginRelease", "GET", "/newmoi/workspaces/ws/plugin-releases/pr_fixture", json.loads("{\"publication\":{\"id\":\"pr_fixture\",\"workspace_id\":\"system\",\"registry\":\"builtin\",\"publisher\":\"matrixorigin\",\"name\":\"example\",\"version\":\"1.0.0\",\"digest\":\"sha256:test\",\"description\":\"Example\",\"published_by\":\"system\",\"created_at\":\"2026-10-08T00:00:00Z\"},\"manifest\":{\"$schema\":\"plugin-v1\",\"name\":\"example\",\"version\":\"1.0.0\"},\"connections\":{\"requirements\":{}},\"servers\":{\"main\":{\"type\":\"http\",\"url\":\"https://api.example.test/mcp\"}},\"operations\":{},\"skills\":[{\"id\":\"skill:guide\",\"name\":\"guide\",\"description\":\"Guide\",\"path\":\"skills/guide/SKILL.md\",\"digest\":\"sha256:test\"}]}"), lambda: a.get_plugin_release("pr_fixture",sdk.with_query_param("namespace","system"))),
            ("InstallPlugin", "POST", "/newmoi/workspaces/ws/plugin-installations", json.loads("{\"id\":\"pi_1\",\"workspace_id\":\"ws\",\"release_workspace_id\":\"system\",\"release_id\":\"pr_fixture\",\"release_digest\":\"sha256:test\",\"release_name\":\"example\",\"owner_user_id\":\"user\",\"bindings\":{\"account\":{\"connection_id\":\"pc_1\",\"profile\":\"oauth\"}},\"version\":7,\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}"), lambda: a.install_plugin(sdk.PluginInstallRequest(release_namespace="system",release_id="pr_fixture",bindings={"account":sdk.PluginInstallationBinding(connection_id="pc_1",profile="oauth")}))),
            ("ListPluginInstallations", "GET", "/newmoi/workspaces/ws/plugin-installations", json.loads("{\"items\":[{\"id\":\"pi_1\",\"workspace_id\":\"ws\",\"release_workspace_id\":\"system\",\"release_id\":\"pr_fixture\",\"release_digest\":\"sha256:test\",\"release_name\":\"example\",\"owner_user_id\":\"user\",\"bindings\":{\"account\":{\"connection_id\":\"pc_1\",\"profile\":\"oauth\"}},\"version\":7,\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}],\"total\":1}"), lambda: a.list_plugin_installations()),
            ("GetPluginInstallation", "GET", "/newmoi/workspaces/ws/plugin-installations/pi_1", json.loads("{\"id\":\"pi_1\",\"workspace_id\":\"ws\",\"release_workspace_id\":\"system\",\"release_id\":\"pr_fixture\",\"release_digest\":\"sha256:test\",\"release_name\":\"example\",\"owner_user_id\":\"user\",\"bindings\":{\"account\":{\"connection_id\":\"pc_1\",\"profile\":\"oauth\"}},\"version\":7,\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}"), lambda: a.get_plugin_installation("pi_1")),
            ("UpdatePluginInstallation", "PATCH", "/newmoi/workspaces/ws/plugin-installations/pi_1", json.loads("{\"id\":\"pi_1\",\"workspace_id\":\"ws\",\"release_workspace_id\":\"system\",\"release_id\":\"pr_fixture\",\"release_digest\":\"sha256:test\",\"release_name\":\"example\",\"owner_user_id\":\"user\",\"bindings\":{\"account\":{\"connection_id\":\"pc_1\",\"profile\":\"oauth\"}},\"version\":7,\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}"), lambda: a.update_plugin_installation("pi_1",sdk.PluginUpdateInstallationRequest(expected_version=7,release_namespace="system",release_id="pr_fixture",bindings={"account":sdk.PluginInstallationBinding(connection_id="pc_1",profile="oauth")}))),
            ("DeletePluginInstallation", "DELETE", "/newmoi/workspaces/ws/plugin-installations/pi_1", json.loads("{\"status\":\"deleted\"}"), lambda: a.delete_plugin_installation("pi_1",7)),
            ("CreatePluginConnection", "POST", "/newmoi/workspaces/ws/plugin-connections", json.loads("{\"id\":\"pc_1\",\"workspace_id\":\"ws\",\"name\":\"Example\",\"status\":\"active\",\"kind\":\"plugin\",\"endpoint_uri\":\"https://api.example.test\",\"auth_type\":\"oauth2\",\"owner_user_id\":\"user\",\"visibility\":\"private\",\"version\":3,\"config\":{\"provider\":\"example\"},\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}"), lambda: a.create_plugin_connection(sdk.PluginCreateConnectionRequest(release_namespace="system",release_id="pr_fixture",requirement="account",profile="oauth",name="Example"))),
            ("ListPluginConnections", "GET", "/newmoi/workspaces/ws/plugin-connections", json.loads("{\"items\":[{\"id\":\"pc_1\",\"workspace_id\":\"ws\",\"name\":\"Example\",\"status\":\"active\",\"kind\":\"plugin\",\"endpoint_uri\":\"https://api.example.test\",\"auth_type\":\"oauth2\",\"owner_user_id\":\"user\",\"visibility\":\"private\",\"version\":3,\"config\":{\"provider\":\"example\"},\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}],\"total\":1}"), lambda: a.list_plugin_connections()),
            ("GetPluginConnection", "GET", "/newmoi/workspaces/ws/plugin-connections/pc_1", json.loads("{\"id\":\"pc_1\",\"workspace_id\":\"ws\",\"name\":\"Example\",\"status\":\"active\",\"kind\":\"plugin\",\"endpoint_uri\":\"https://api.example.test\",\"auth_type\":\"oauth2\",\"owner_user_id\":\"user\",\"visibility\":\"private\",\"version\":3,\"config\":{\"provider\":\"example\"},\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}"), lambda: a.get_plugin_connection("pc_1")),
            ("UpdatePluginConnection", "PATCH", "/newmoi/workspaces/ws/plugin-connections/pc_1", json.loads("{\"id\":\"pc_1\",\"workspace_id\":\"ws\",\"name\":\"Example\",\"status\":\"active\",\"kind\":\"plugin\",\"endpoint_uri\":\"https://api.example.test\",\"auth_type\":\"oauth2\",\"owner_user_id\":\"user\",\"visibility\":\"private\",\"version\":3,\"config\":{\"provider\":\"example\"},\"created_at\":\"2026-10-08T00:00:00Z\",\"updated_at\":\"2026-10-08T00:00:00Z\"}"), lambda: a.update_plugin_connection("pc_1",sdk.PluginUpdateConnectionRequest(expected_version=3,status="disabled"))),
            ("DeletePluginConnection", "DELETE", "/newmoi/workspaces/ws/plugin-connections/pc_1", json.loads("{\"status\":\"deleted\"}"), lambda: a.delete_plugin_connection("pc_1",3)),
            ("GetPluginAuthorization", "GET", "/newmoi/workspaces/ws/plugin-connections/pc_1/authorization", json.loads("{\"workspace_id\":\"ws\",\"connection_id\":\"pc_1\",\"external_subject\":\"external-user\",\"account_display_name\":\"张小明\",\"status\":\"ready\",\"generation\":2,\"revision\":4,\"connection_version\":3}"), lambda: a.get_plugin_authorization("pc_1")),
            ("StorePluginSecret", "POST", "/newmoi/workspaces/ws/plugin-connections/pc_1/secret", json.loads("{\"workspace_id\":\"ws\",\"connection_id\":\"pc_1\",\"external_subject\":\"external-user\",\"status\":\"ready\",\"generation\":2,\"revision\":4,\"connection_version\":3}"), lambda: a.store_plugin_secret("pc_1",sdk.PluginStoreSecretRequest(expected_version=3,fields={"api_key":"test-only-secret"}))),
            ("BeginPluginOAuth", "POST", "/newmoi/workspaces/ws/plugin-connections/pc_1/oauth", json.loads("{\"attempt_id\":\"oa_1\",\"grant\":\"device_code\",\"authorization_url\":\"https://example.test/device\",\"user_code\":\"ABCD\",\"poll_after\":5,\"expires_at\":\"2026-10-08T00:15:00Z\"}"), lambda: a.begin_plugin_oauth("pc_1",3)),
            ("PollPluginOAuth", "POST", "/newmoi/workspaces/ws/plugin-connections/pc_1/oauth/oa_1/poll", json.loads("{\"attempt_id\":\"oa_1\",\"status\":\"pending\",\"reason\":\"authorization_pending\",\"poll_after\":10}"), lambda: a.poll_plugin_oauth("pc_1","oa_1",3)),
            ("PollPluginOAuthNextAction", "POST", "/newmoi/workspaces/ws/plugin-connections/pc_1/oauth/oa_1/poll", {
                "attempt_id": "oa_1", "status": "pending", "poll_after": 5,
                "next_action": {"attempt_id": "oa_1", "grant": "device_code",
                                "authorization_url": "https://accounts.feishu.cn/oauth/v1/authorize?user_code=ABCD",
                                "user_code": "ABCD", "poll_after": 5, "expires_at": "2026-10-08T00:15:00Z"},
            }, lambda: a.poll_plugin_oauth("pc_1", "oa_1", 3)),
            ("DisconnectPluginConnection", "POST", "/newmoi/workspaces/ws/plugin-connections/pc_1/disconnect", json.loads("{\"status\":\"disconnected\"}"), lambda: a.disconnect_plugin_connection("pc_1",2)),
        ]
        for name, method, path, expected, call in cases:
            with self.subTest(name=name):
                PluginHandler.requests = []
                PluginHandler.response = {"code": "OK", "data": expected}
                value = call()
                actual = json_format.MessageToDict(value, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)
                self.assert_wire_fields(expected, actual)
                self.assertEqual(1, len(PluginHandler.requests))
                sent_method, sent_path, headers, body = PluginHandler.requests[0]
                self.assertEqual((method, path), (sent_method, sent_path))
                self.assertEqual("ws", headers.get("X-Workspace-ID"))
                if body:
                    payload = json.loads(body)
                    if "expected_version" in payload:
                        self.assertIsInstance(payload["expected_version"], int)
                    if name in ("InstallPlugin", "UpdatePluginInstallation"):
                        self.assertEqual({"connection_id": "pc_1", "profile": "oauth"}, payload["bindings"]["account"])
                    if name == "BeginPluginOAuth":
                        self.assertEqual("external", payload["initiator"])

    def test_authorization_error_preserved_without_replay(self):
        for message in ("Connection is busy. Wait and try again.", "连接正在授权中，请稍后再试。"):
            with self.subTest(message=message):
                PluginHandler.requests = []
                PluginHandler.status = 409
                PluginHandler.response = {"code": "PLUGIN_AUTH_IN_PROGRESS", "msg": message, "details": {"reason": "PLUGIN_AUTH_IN_PROGRESS"}}
                with self.assertRaises(sdk.Error) as caught:
                    self.client.agents("ws").poll_plugin_oauth("pc_1", "oa_1", 3)
                self.assertEqual("PLUGIN_AUTH_IN_PROGRESS", caught.exception.code)
                self.assertEqual(message, caught.exception.message)
                self.assertEqual("plugin-request", caught.exception.request_id)
                self.assertEqual("PLUGIN_AUTH_IN_PROGRESS", caught.exception.details["reason"])
                self.assertEqual(1, len(PluginHandler.requests))

    def test_unknown_response_fields_fail_explicitly(self):
        PluginHandler.response = {"code": "OK", "data": {"status": "ready", "provider_secret": "never-a-public-field"}}
        with self.assertRaises(sdk.Error) as caught:
            self.client.agents("ws").get_plugin_authorization("pc_1")
        self.assertEqual("ErrResponseInvalid", caught.exception.code)
