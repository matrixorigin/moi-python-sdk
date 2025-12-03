"""Tests for LLM Proxy APIs."""

import pytest
from moi import RawClient
from tests.test_helpers import get_test_client, random_name


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


class TestLLMSessionMessages:
    """Test LLM Session Messages API."""

    def test_list_llm_session_messages(self):
        """Test listing session messages with optional filtering."""
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
            # Create a message in the session
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
                # List session messages
                # Note: The messages list endpoint does not return original_content and content fields
                # to reduce data transfer. Use get_llm_chat_message to get full message content.
                messages = client.list_llm_session_messages(session_id, {})
                assert messages is not None
                assert len(messages) > 0
                
                found_message = False
                for m in messages:
                    if m["id"] == message_id:
                        found_message = True
                        # Verify message metadata (content fields are not returned by list endpoint)
                        assert m["role"] == message["role"]
                        assert m["status"] == message["status"]
                        assert m["model"] == message["model"]
                        # Content field may be present but should be empty (API returns empty string to reduce data transfer)
                        # The actual content should be retrieved via get_llm_chat_message
                        if "content" in m:
                            assert m["content"] == "", \
                                "Content field should be empty in list response (use get_llm_chat_message for full content)"
                        break
                
                assert found_message, "Created message should be in the session messages list"
                
                # List session messages with role filter
                messages_by_role = client.list_llm_session_messages(session_id, {
                    "role": "user"
                })
                assert messages_by_role is not None
                assert len(messages_by_role) > 0
                
                # Test with after and limit parameters
                # Create another message
                message2 = client.create_llm_chat_message({
                    "user_id": user_id,
                    "session_id": session_id,
                    "source": "sdk-test",
                    "role": "assistant",
                    "content": "Second message",
                    "model": "gpt-4",
                    "status": "success",
                })
                assert message2 is not None
                message2_id = message2["id"]
                
                try:
                    # List messages after message_id (should not include message_id itself)
                    messages_after = client.list_llm_session_messages(session_id, {
                        "after": message_id,
                        "limit": 10
                    })
                    assert messages_after is not None
                    # Should include message2 but not message
                    message_ids = [m["id"] for m in messages_after]
                    assert message_id not in message_ids, \
                        "Messages after should not include the 'after' message ID"
                    if len(messages_after) > 0:
                        # If there are messages, message2 should be included
                        assert message2_id in message_ids or len(messages_after) == 0, \
                            "Messages after should include messages created after the specified ID"
                    
                    # Test limit parameter
                    messages_limited = client.list_llm_session_messages(session_id, {
                        "limit": 1
                    })
                    assert messages_limited is not None
                    assert len(messages_limited) <= 1, \
                        "Limit should restrict the number of returned messages"
                        
                finally:
                    # Cleanup message2
                    try:
                        client.delete_llm_chat_message(message2_id)
                    except Exception:
                        pass
                        
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

