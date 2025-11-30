"""Tests for Role APIs."""

import pytest
from moi import RawClient, ErrNilRequest
from tests.test_helpers import get_test_client, create_test_role


class TestRoleLiveFlow:
    """Test Role operations with live backend."""

    def test_role_live_flow(self):
        """Test complete role flow."""
        client = get_test_client()
        
        priv_codes = ["DC2"]  # QueryCatalog
        role_id, mark_role_deleted = create_test_role(client, priv_codes)
        
        try:
            # Get role
            info_resp = client.get_role({"id": role_id})
            assert info_resp is not None
            assert info_resp["id"] == role_id
            
            # Update role info
            obj_priv = {
                "obj_id": "test-catalog",
                "obj_type": "catalog",
                "authority_code_list": [
                    {
                        "code": "DC3",  # UpdateCatalog
                        "rule_list": None,
                    }
                ],
            }
            client.update_role_info({
                "id": role_id,
                "authority_code_list": ["DC2"],  # QueryCatalog
                "obj_authority_code_list": [obj_priv],
                "description": "sdk update",
            })
            
            # Update role status - disable
            client.update_role_status({
                "id": role_id,
                "action": "disable",
            })
            
            # Update role status - enable
            client.update_role_status({
                "id": role_id,
                "action": "enable",
            })
            
            # Delete role
            client.delete_role({"id": role_id})
            mark_role_deleted()
            
        except Exception:
            mark_role_deleted()
            raise


class TestRoleNilRequestErrors:
    """Test that nil request errors are raised correctly."""

    def test_create_role_nil_request(self):
        """Test CreateRole with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.create_role(None)

    def test_delete_role_nil_request(self):
        """Test DeleteRole with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.delete_role(None)

    def test_get_role_nil_request(self):
        """Test GetRole with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_role(None)

    def test_list_roles_nil_request(self):
        """Test ListRoles with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.list_roles(None)

    def test_update_role_info_nil_request(self):
        """Test UpdateRoleInfo with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.update_role_info(None)

    def test_update_role_status_nil_request(self):
        """Test UpdateRoleStatus with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.update_role_status(None)

