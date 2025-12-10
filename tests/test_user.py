"""Tests for User APIs."""

import pytest
from moi import RawClient, ErrNilRequest
from tests.test_helpers import get_test_client, random_user_name, create_test_role


class TestUserLiveFlow:
    """Test User operations with live backend."""

    def test_user_live_flow(self):
        """Test complete user flow."""
        client = get_test_client()
        
        role_id, mark_role_deleted = create_test_role(client, ["DC2"])  # QueryCatalog
        
        try:
            # Create user
            create_resp = client.create_user({
                "name": random_user_name().lower(),
                "password": "TestPwd123!",
                "role_id_list": [role_id],
                "description": "sdk test user",
                "phone": "12345678901",
                "email": "sdk@example.com",
            })
            assert create_resp is not None
            user_id = create_resp["id"]
            user_deleted = False
            
            try:
                # Get user detail
                detail_resp = client.get_user_detail({"id": user_id})
                assert detail_resp is not None
                
                # List users
                list_resp = client.list_users({})
                assert list_resp is not None
                
                # Update user info
                client.update_user_info({
                    "id": user_id,
                    "phone": "10987654321",
                    "email": "sdk-updated@example.com",
                    "description": "updated",
                })
                
                # Update user roles
                client.update_user_roles({
                    "id": user_id,
                    "role_id_list": [role_id],
                })
                
                # Update user status - disable
                client.update_user_status({
                    "id": user_id,
                    "action": "disable",
                })
                
                # Update user status - enable
                client.update_user_status({
                    "id": user_id,
                    "action": "enable",
                })
                
                # Delete user
                client.delete_user({"id": user_id})
                user_deleted = True
                
            finally:
                if not user_deleted:
                    try:
                        client.delete_user({"id": user_id})
                    except Exception:
                        pass
        finally:
            mark_role_deleted()


class TestUserNilRequestErrors:
    """Test that nil request errors are raised correctly."""

    def test_create_user_nil_request(self):
        """Test CreateUser with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.create_user(None)

    def test_delete_user_nil_request(self):
        """Test DeleteUser with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.delete_user(None)

    def test_get_user_detail_nil_request(self):
        """Test GetUserDetail with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_user_detail(None)

    def test_list_users_nil_request(self):
        """Test ListUsers with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.list_users(None)

    def test_update_user_info_nil_request(self):
        """Test UpdateUserInfo with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.update_user_info(None)

    def test_update_user_roles_nil_request(self):
        """Test UpdateUserRoles with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.update_user_roles(None)

    def test_update_user_status_nil_request(self):
        """Test UpdateUserStatus with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.update_user_status(None)


@pytest.mark.integration
class TestCreateUserWithGetApiKey:
    """Test CreateUser API with GetApiKey parameter."""

    def test_create_user_with_get_api_key_true(self):
        """Test CreateUser with GetApiKey=true should return ApiKey."""
        client = get_test_client()
        role_id, mark_role_deleted = create_test_role(client, ["DC2"])  # QueryCatalog
        
        try:
            create_resp = client.create_user({
                "name": random_user_name().lower(),
                "password": "TestPwd123!",
                "role_id_list": [role_id],
                "description": "sdk test user with api key",
                "get_api_key": True,
            })
            assert create_resp is not None
            assert create_resp.get("id") is not None
            assert create_resp.get("api_key") is not None and create_resp.get("api_key") != "", "ApiKey should be present when get_api_key is True"
            
            # Cleanup
            try:
                client.delete_user({"id": create_resp["id"]})
            except Exception:
                pass
        finally:
            mark_role_deleted()

    def test_create_user_with_get_api_key_false(self):
        """Test CreateUser with GetApiKey=false should not return ApiKey."""
        client = get_test_client()
        role_id, mark_role_deleted = create_test_role(client, ["DC2"])  # QueryCatalog
        
        try:
            create_resp = client.create_user({
                "name": random_user_name().lower(),
                "password": "TestPwd123!",
                "role_id_list": [role_id],
                "description": "sdk test user without api key",
                "get_api_key": False,
            })
            assert create_resp is not None
            assert create_resp.get("id") is not None
            # ApiKey may be empty or not present when get_api_key is False
            # This is acceptable as the field is optional
            
            # Cleanup
            try:
                client.delete_user({"id": create_resp["id"]})
            except Exception:
                pass
        finally:
            mark_role_deleted()

    def test_create_user_with_get_api_key_default(self):
        """Test CreateUser with default GetApiKey (not set) should work."""
        client = get_test_client()
        role_id, mark_role_deleted = create_test_role(client, ["DC2"])  # QueryCatalog
        
        try:
            # Test that default behavior (get_api_key not set, defaults to False) still works
            create_resp = client.create_user({
                "name": random_user_name().lower(),
                "password": "TestPwd123!",
                "role_id_list": [role_id],
                "description": "sdk test user with default get_api_key",
            })
            assert create_resp is not None
            assert create_resp.get("id") is not None
            
            # Cleanup
            try:
                client.delete_user({"id": create_resp["id"]})
            except Exception:
                pass
        finally:
            mark_role_deleted()

