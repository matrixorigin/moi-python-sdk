"""Tests for LLM Proxy APIs."""

import os
import pytest
from moi import RawClient


def get_test_client():
    """Get a test client from environment variables."""
    base_url = os.getenv("MOI_BASE_URL", "http://localhost:8080")
    api_key = os.getenv("MOI_API_KEY", "")
    if not api_key:
        pytest.skip("MOI_API_KEY environment variable not set")
    return RawClient(base_url, api_key)


def random_name(prefix: str = "test-") -> str:
    """Generate a random name for testing."""
    import random
    import string
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}{suffix}"


class TestLLMSessionLatestMessage:
    """Test LLM Session Latest Message API."""

    def test_get_llm_session_latest_message(self):
        """Test getting the latest message regardless of status."""
        client = get_test_client()
        
        # Create a session
        user_id = random_name("user-")
        session = client.create_llm_session({
            "title": random_name("sdk-session-"),
            "source": "sdk-test",
            "user_id": user_id,
        })
        assert session is not None
        session_id = session["id"]
        
        try:
            # Create a message with success status
            message1 = client.create_llm_chat_message({
                "user_id": user_id,
                "session_id": session_id,
                "source": "sdk-test",
                "role": "user",
                "content": "First message",
                "model": "gpt-4",
                "status": "success",
            })
            assert message1 is not None
            message1_id = message1["id"]
            
            try:
                # Create a message with failed status
                message2 = client.create_llm_chat_message({
                    "user_id": user_id,
                    "session_id": session_id,
                    "source": "sdk-test",
                    "role": "user",
                    "content": "Second message",
                    "model": "gpt-4",
                    "status": "failed",
                })
                assert message2 is not None
                message2_id = message2["id"]
                
                try:
                    # Get latest completed message (should return message1 with success status)
                    latest_completed = client.get_llm_session_latest_completed_message(session_id)
                    assert latest_completed is not None
                    assert latest_completed["session_id"] == session_id
                    assert latest_completed["message_id"] == message1_id, \
                        "Latest completed should be message1 (success)"
                    
                    # Get latest message (regardless of status, should return message2 as it's the latest)
                    latest = client.get_llm_session_latest_message(session_id)
                    assert latest is not None
                    assert latest["session_id"] == session_id
                    assert latest["message_id"] == message2_id, \
                        "Latest message (any status) should be message2 (the most recent)"
                    
                finally:
                    # Cleanup message2
                    try:
                        client.delete_llm_chat_message(message2_id)
                    except Exception:
                        pass
                        
            finally:
                # Cleanup message1
                try:
                    client.delete_llm_chat_message(message1_id)
                except Exception:
                    pass
                    
        finally:
            # Cleanup session
            try:
                client.delete_llm_session(session_id)
            except Exception:
                pass

    def test_get_llm_session_latest_message_in_session_messages_flow(self):
        """Test latest message API in the context of session messages flow."""
        client = get_test_client()
        
        # Create a session
        user_id = random_name("user-")
        session = client.create_llm_session({
            "title": random_name("sdk-session-"),
            "source": "sdk-test",
            "user_id": user_id,
        })
        assert session is not None
        session_id = session["id"]
        
        try:
            # Create a message
            message = client.create_llm_chat_message({
                "user_id": user_id,
                "session_id": session_id,
                "source": "sdk-test",
                "role": "user",
                "content": "Test message",
                "model": "gpt-4",
                "status": "success",
            })
            assert message is not None
            message_id = message["id"]
            
            try:
                # Get latest completed message
                latest_completed = client.get_llm_session_latest_completed_message(session_id)
                assert latest_completed is not None
                assert latest_completed["session_id"] == session_id
                assert latest_completed["message_id"] == message_id
                
                # Get latest message (regardless of status)
                latest = client.get_llm_session_latest_message(session_id)
                assert latest is not None
                assert latest["session_id"] == session_id
                assert latest["message_id"] == message_id
                
            finally:
                # Cleanup message
                try:
                    client.delete_llm_chat_message(message_id)
                except Exception:
                    pass
                    
        finally:
            # Cleanup session
            try:
                client.delete_llm_session(session_id)
            except Exception:
                pass

