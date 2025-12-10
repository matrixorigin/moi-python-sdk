"""Tests for client cloning functionality."""

import pytest
from moi import RawClient, SDKClient, ErrAPIKeyRequired


class TestRawClientWithSpecialUser:
    """Test RawClient.with_special_user method."""

    def test_with_special_user_with_valid_api_key(self):
        """Test WithSpecialUser with valid API key."""
        original = RawClient("https://api.example.com", "original-key-123")
        
        new_api_key = "new-api-key-123"
        cloned = original.with_special_user(new_api_key)
        
        assert cloned is not None
        assert cloned is not original
        
        # Verify API key is different
        assert cloned._api_key == new_api_key
        assert original._api_key != cloned._api_key
        
        # Verify other fields are the same
        assert original._base_url == cloned._base_url
        assert original._user_agent == cloned._user_agent
        assert original._timeout == cloned._timeout
        assert original._http_client == cloned._http_client  # Should share the same HTTP client

    def test_with_special_user_with_empty_api_key(self):
        """Test WithSpecialUser with empty API key raises ValueError."""
        original = RawClient("https://api.example.com", "original-key-123")
        
        with pytest.raises(ValueError) as exc_info:
            original.with_special_user("")
        assert "API key is required" in str(exc_info.value)

    def test_with_special_user_with_whitespace_only_api_key(self):
        """Test WithSpecialUser with whitespace-only API key raises ValueError."""
        original = RawClient("https://api.example.com", "original-key-123")
        
        with pytest.raises(ValueError) as exc_info:
            original.with_special_user("   ")
        assert "API key is required" in str(exc_info.value)


class TestSDKClientWithSpecialUser:
    """Test SDKClient.with_special_user method."""

    def test_with_special_user_with_valid_api_key(self):
        """Test WithSpecialUser with valid API key."""
        original_raw = RawClient("https://api.example.com", "original-key-123")
        original = SDKClient(original_raw)
        
        new_api_key = "new-api-key-456"
        cloned = original.with_special_user(new_api_key)
        
        assert cloned is not None
        assert cloned is not original
        assert cloned.raw is not original.raw
        
        # Verify cloned SDKClient has new API key
        assert cloned.raw._api_key == new_api_key
        assert original.raw._api_key != cloned.raw._api_key
        
        # Verify other fields are the same
        assert original.raw._base_url == cloned.raw._base_url
        assert original.raw._user_agent == cloned.raw._user_agent
        assert original.raw._timeout == cloned.raw._timeout

    def test_with_special_user_with_empty_api_key(self):
        """Test WithSpecialUser with empty API key raises ValueError."""
        original_raw = RawClient("https://api.example.com", "original-key-123")
        original = SDKClient(original_raw)
        
        with pytest.raises(ValueError) as exc_info:
            original.with_special_user("")
        assert "API key is required" in str(exc_info.value)

