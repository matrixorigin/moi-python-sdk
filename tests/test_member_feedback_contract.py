import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import moi_product_sdk as sdk


class MemberFeedbackContractTest(unittest.TestCase):
    def test_accept_invitation_decodes_public_receipt(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("target-key")).workspace_members("workspace-1")
        with patch.object(service, "_request", return_value={"accepted": True}) as request:
            result = service.accept_invitation("invitation-1")
            self.assertIsInstance(result, sdk.WorkspaceInvitationAcceptResult)
            self.assertTrue(result.accepted)
            request.assert_called_once_with("POST", "/workspaces/invitations/invitation-1/accept", {})
        with patch.object(service, "_request", return_value={"accepted": True, "unexpected": True}), self.assertRaises(sdk.Error):
            service.accept_invitation("invitation-1")

    def test_feedback_admin_paths_and_optional_approval_fields(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_token("admin-token")).agents("workspace-1")
        ticket = {"id": "ticket-1", "submitter_email": "target@example.test"}
        with patch.object(service, "_request", return_value=ticket) as request:
            self.assertEqual(service.admin_feedback_ticket("ticket-1"), ticket)
            request.assert_called_once_with("GET", "/admin/feedback-tickets/ticket-1")
        for update, body in (
            (sdk.FeedbackTicketAdminUpdateRequest(), {}),
            (sdk.FeedbackTicketAdminUpdateRequest(status="closed", admin_reply=""), {"status": "closed", "admin_reply": ""}),
        ):
            with self.subTest(body=body), patch.object(service, "_request", return_value={"reward_event": {"id": "event-1"}}) as request:
                result = service.approve_feedback_reward("ticket-1", update)
                self.assertEqual(result["reward_event"]["id"], "event-1")
                request.assert_called_once_with("POST", "/admin/feedback-tickets/ticket-1/reward-approval", body)

    def test_feedback_github_issue_paths_and_payloads(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_token("admin-token")).agents("workspace-1")
        with patch.object(service, "_request", return_value={"kind": "bug", "title": "draft"}) as request:
            self.assertEqual(service.build_feedback_github_issue_draft("ticket-1", "bug")["title"], "draft")
            request.assert_called_once_with("POST", "/admin/feedback-tickets/ticket-1/github-issue-draft", {"kind": "bug"})
        with patch.object(service, "_request", return_value={"number": 42}) as request:
            self.assertEqual(service.create_feedback_github_issue("ticket-1", "bug", "draft", "details", True)["number"], 42)
            request.assert_called_once_with("POST", "/admin/feedback-tickets/ticket-1/github-issue",
                                            {"kind": "bug", "title": "draft", "body": "details", "retry": True})

    def test_transport_preserves_invited_identity_and_public_errors(self):
        for option, header, value in (
            (sdk.with_api_key("target-key"), "X-api-key", "target-key"),
            (sdk.with_token("target-token"), "Authorization", "Bearer target-token"),
        ):
            client = sdk.Client("http://localhost/newmoi", option)
            for status, code, path, action in (
                (403, "ErrPermissionDenied", "/workspaces/invitations/inv-1/accept", lambda: client.workspace_members("workspace-1").accept_invitation("inv-1")),
                (404, "ErrFeedbackTicketNotFound", "/admin/feedback-tickets/ticket-1", lambda: client.agents("workspace-1").admin_feedback_ticket("ticket-1")),
                (400, "ErrFeedbackRewardSubjectMissing", "/admin/feedback-tickets/ticket-1/reward-approval", lambda: client.agents("workspace-1").approve_feedback_reward("ticket-1", sdk.FeedbackTicketAdminUpdateRequest())),
            ):
                with self.subTest(auth=header, code=code):
                    failure = urllib.error.HTTPError(
                        "http://localhost/newmoi" + path, status, "failure",
                        {"X-Request-ID": "public-request-id"},
                        io.BytesIO(json.dumps({"code": code, "msg": "原始本地化错误"}).encode()),
                    )
                    with patch("urllib.request.urlopen", side_effect=failure) as request, self.assertRaises(sdk.Error) as raised:
                        action()
                    sent = request.call_args.args[0]
                    self.assertEqual(sent.full_url, "http://localhost/newmoi" + path)
                    self.assertEqual(sent.get_header(header), value)
                    self.assertEqual(sent.get_header("X-workspace-id"), "workspace-1")
                    self.assertEqual((raised.exception.status, raised.exception.code, raised.exception.message, raised.exception.request_id),
                                     (status, code, "原始本地化错误", "public-request-id"))


if __name__ == "__main__":
    unittest.main()
