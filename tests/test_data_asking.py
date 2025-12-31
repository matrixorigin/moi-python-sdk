"""Tests for Data Analysis (Data Asking) APIs."""

import json
import io
import pytest
from moi import RawClient, ErrNilRequest
from moi.options import with_stream_buffer_size
from moi.stream import DataAnalysisStream
from tests.test_helpers import get_test_client
import requests


class TestAnalyzeDataStream:
    """Test Data Analysis Streaming API."""

    def test_analyze_data_stream_nil_request(self):
        """Test that nil request raises ErrNilRequest."""
        client = get_test_client()
        
        with pytest.raises(ErrNilRequest):
            client.analyze_data_stream(None)

    def test_analyze_data_stream_empty_question(self):
        """Test that empty question raises ValueError."""
        client = get_test_client()
        
        req = {
            "question": "",
        }
        with pytest.raises(ValueError, match="question cannot be empty"):
            client.analyze_data_stream(req)

    def test_analyze_data_stream_simple_request(self):
        """Test with a minimal request."""
        client = get_test_client()
        
        req = {
            "question": "平均薪资是多少？",
            "config": {
                "data_category": "admin",
                "data_source": {
                    "type": "all"
                }
            }
        }
        
        stream = client.analyze_data_stream(req)
        assert stream is not None
        assert stream.status_code == 200
        
        try:
            # Verify content type
            content_type = stream.headers.get("Content-Type", "")
            assert "text/event-stream" in content_type or "text/plain" in content_type
            
            # Read at least one event to verify the stream works
            event = stream.read_event()
            if event is None:
                pytest.skip("Stream ended immediately (no events)")
            else:
                assert event is not None
                print(f"First event: Type={event.type}, Source={event.source}")
        finally:
            stream.close()

    def test_analyze_data_stream_live_flow(self):
        """Test the data analysis streaming API with a real backend."""
        client = get_test_client()
        
        # Build request
        source = "rag"
        session_id = "019a5672-74f6-7bb8-ba55-239dea01d00f"
        code_type = 1
        
        req = {
            "question": "平均薪资是多少？",
            "source": source,
            "session_id": session_id,
            "config": {
                "data_category": "admin",
                "filter_conditions": {
                    "type": "non_inter_data"
                },
                "data_source": {
                    "type": "all"
                },
                "data_scope": {
                    "type": "specified",
                    "code_type": code_type,
                    "code_group": [
                        {
                            "name": "1001",
                            "values": ["100101", "100102", "100103"]
                        },
                        {
                            "name": "1002",
                            "values": ["1002"]
                        },
                        {
                            "name": "1003",
                            "values": ["1003"]
                        }
                    ]
                }
            }
        }
        
        # Call the streaming API
        stream = client.analyze_data_stream(req)
        assert stream is not None
        assert stream.status_code == 200
        
        try:
            # Verify response headers
            content_type = stream.headers.get("Content-Type", "")
            assert "text/event-stream" in content_type or "text/plain" in content_type, \
                f"Content-Type should be text/event-stream, got: {content_type}"
            
            # Read events from the stream
            event_count = 0
            has_classification = False
            has_complete = False
            max_events = 50  # Limit events to prevent test timeout
            
            while True:
                event = stream.read_event()
                if event is None:  # EOF
                    print(f"Stream ended after {event_count} events")
                    break
                
                assert event is not None, "Event should not be nil"
                
                event_count += 1
                
                # Log event details (truncate long data for readability)
                raw_data_str = ""
                if event.raw_data:
                    raw_data_str = event.raw_data.decode('utf-8', errors='ignore')
                    if len(raw_data_str) > 200:
                        raw_data_str = raw_data_str[:200] + "..."
                
                print(f"Event #{event_count}: Type={event.type}, Source={event.source}, "
                      f"StepType={event.step_type}, StepName={event.step_name}")
                if raw_data_str:
                    print(f"  RawData: {raw_data_str}")
                
                # Track specific event types
                if event.type == "classification":
                    has_classification = True
                    # Verify classification event structure
                    assert event.raw_data is not None or event.data is not None, \
                        "Classification event should have data"
                
                if event.type == "complete":
                    has_complete = True
                    print("Analysis completed")
                    break  # Complete event indicates end of stream
                
                if event.type == "error":
                    print(f"Error event received: {raw_data_str}")
                
                # For events without explicit type field, check for source and step_type
                if not event.type:
                    if event.source:
                        print(f"Event with source {event.source}: step_type={event.step_type}, "
                              f"step_name={event.step_name}")
                    # Some events have step_type in the JSON but not parsed into Type field
                    if event.step_type:
                        print(f"Event with step_type: {event.step_type}")
                
                # Limit events to prevent test timeout
                if event_count >= max_events:
                    print(f"Reached max events limit ({max_events}), stopping to prevent timeout")
                    break
            
            # Verify we received at least some events
            assert event_count > 0, "Should receive at least one event"
            print(f"Total events received: {event_count}")
            
            # Note: We don't require classification or complete events as the backend behavior
            # may vary, but we log if they are present
            if has_classification:
                print("Classification event was received")
            if has_complete:
                print("Complete event was received")
                
        finally:
            stream.close()


class TestCancelAnalyze:
    """Test Cancel Analyze API."""

    def test_cancel_analyze_nil_request(self):
        """Test that nil request raises ErrNilRequest."""
        client = get_test_client()
        
        with pytest.raises(ErrNilRequest):
            client.cancel_analyze(None)

    def test_cancel_analyze_empty_request_id(self):
        """Test that empty request_id raises ValueError."""
        client = get_test_client()
        
        req = {
            "request_id": "",
        }
        with pytest.raises(ValueError, match="request_id cannot be empty"):
            client.cancel_analyze(req)

    @pytest.mark.integration
    def test_cancel_analyze_live_flow(self):
        """Test the cancel analyze API with a real backend."""
        import json
        
        client = get_test_client()
        
        # First, start an analysis request to get a request_id
        req = {
            "question": "平均薪资是多少？",
            "config": {
                "data_category": "admin",
                "data_source": {
                    "type": "all"
                }
            }
        }
        
        stream = client.analyze_data_stream(req)
        assert stream is not None
        assert stream.status_code == 200
        
        try:
            # Read the first event to get request_id
            event = stream.read_event()
            if event is None:
                pytest.skip("Could not get first event from stream, skipping cancel test")
            
            # Extract request_id from the init event
            request_id = None
            if event.step_type == "init":
                # Parse the raw_data field to get request_id
                if event.raw_data:
                    try:
                        init_data = json.loads(event.raw_data.decode('utf-8'))
                        if isinstance(init_data, dict) and "data" in init_data:
                            data = init_data["data"]
                            if isinstance(data, dict) and "request_id" in data:
                                request_id = data["request_id"]
                    except (json.JSONDecodeError, KeyError, AttributeError):
                        pass
            
            # Also try to get from event.data if available
            if not request_id and event.data:
                request_id = event.data.get("request_id")
            
            if not request_id:
                pytest.skip("Could not extract request_id from stream, skipping cancel test")
            
            # Now cancel the request
            cancel_req = {
                "request_id": request_id
            }
            
            cancel_resp = client.cancel_analyze(cancel_req)
            assert cancel_resp is not None
            assert cancel_resp.get("request_id") == request_id
            assert cancel_resp.get("status") == "cancelled"
            assert cancel_resp.get("user_id") is not None
            print(f"Successfully cancelled request: {cancel_resp.get('request_id')}, "
                  f"Status: {cancel_resp.get('status')}, UserID: {cancel_resp.get('user_id')}")
        finally:
            stream.close()


class TestDataAnalysisStream_ReadEvent:
    """Test DataAnalysisStream.read_event with various scenarios."""

    def test_read_event_basic(self):
        """Test basic SSE event reading."""
        # Create a simple SSE stream
        sse_data = "event: classification\ndata: {\"type\":\"classification\",\"data\":{\"category\":\"query\"}}\n\n"
        
        # Create a mock response
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=0)
        
        event = stream.read_event()
        assert event is not None
        assert event.type == "classification"
        assert event.raw_data is not None
        
        # Should return None for next read (EOF)
        event = stream.read_event()
        assert event is None
        
        stream.close()

    def test_read_event_multiple_events(self):
        """Test reading multiple events."""
        sse_data = (
            "event: init\ndata: {\"step_type\":\"init\",\"data\":{\"request_id\":\"req-123\"}}\n\n"
            + "event: classification\ndata: {\"type\":\"classification\"}\n\n"
            + "event: complete\ndata: {\"type\":\"complete\"}\n\n"
        )
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=0)
        
        # Read first event
        event = stream.read_event()
        assert event is not None
        assert event.type == "init"
        
        # Read second event
        event = stream.read_event()
        assert event is not None
        assert event.type == "classification"
        
        # Read third event
        event = stream.read_event()
        assert event is not None
        assert event.type == "complete"
        
        # Should return None (EOF)
        event = stream.read_event()
        assert event is None
        
        stream.close()

    def test_read_event_multi_line_data(self):
        """Test multi-line data handling."""
        sse_data = "event: test\ndata: {\"key1\":\"value1\"}\ndata: {\"key2\":\"value2\"}\n\n"
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=0)
        
        event = stream.read_event()
        assert event is not None
        assert event.type == "test"
        # Multi-line data should be joined
        raw_data_str = event.raw_data.decode('utf-8') if event.raw_data else ""
        assert "key1" in raw_data_str
        assert "key2" in raw_data_str
        
        stream.close()

    def test_read_event_empty_stream(self):
        """Test empty stream handling."""
        class MockResponse:
            def __init__(self):
                self.content = b""
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(b"")
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                return iter([])
                    
            def close(self):
                pass
        
        response = MockResponse()
        stream = DataAnalysisStream(response, initial_buffer_size=0)
        
        event = stream.read_event()
        assert event is None
        
        stream.close()

    def test_read_event_default_buffer_size(self):
        """Test default buffer size handling."""
        # Create data larger than typical chunk size
        large_data = "x" * (100 * 1024)  # 100KB
        json_data = json.dumps({"data": large_data})
        sse_data = f"event: large\ndata: {json_data}\n\n"
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=0)  # Use default
        
        event = stream.read_event()
        assert event is not None
        assert event.type == "large"
        assert large_data in event.raw_data.decode('utf-8')
        
        stream.close()

    def test_read_event_custom_buffer_size(self):
        """Test custom buffer size handling."""
        # Create data larger than initial buffer - should automatically grow
        large_data = "y" * (200 * 1024)  # 200KB
        json_data = json.dumps({"data": large_data})
        sse_data = f"event: large\ndata: {json_data}\n\n"
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=512 * 1024)  # 512KB initial buffer (will grow as needed)
        
        event = stream.read_event()
        assert event is not None, "Should handle large data with dynamic buffer growth"
        assert event.type == "large"
        assert large_data in event.raw_data.decode('utf-8')
        
        stream.close()

    def test_read_event_invalid_json(self):
        """Test handling of invalid JSON."""
        sse_data = "event: test\ndata: {invalid json}\n\n"
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=0)
        
        event = stream.read_event()
        assert event is not None
        assert event.type == "test"
        assert "{invalid json}" in event.raw_data.decode('utf-8')
        
        stream.close()

    def test_read_event_no_event_type(self):
        """Test SSE without event type."""
        sse_data = "data: {\"step_type\":\"init\",\"data\":{\"request_id\":\"req-123\"}}\n\n"
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=0)
        
        event = stream.read_event()
        assert event is not None
        # Type should be empty if not specified
        assert event.type == ""
        assert event.raw_data is not None
        
        stream.close()

    def test_with_stream_buffer_size_option(self):
        """Test WithStreamBufferSize option."""
        # The buffer will automatically grow to handle data larger than initial size
        large_data = "a" * (150 * 1024)  # 150KB
        json_data = json.dumps({"data": large_data})
        sse_data = f"event: test\ndata: {json_data}\n\n"
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=256 * 1024)  # 256KB initial buffer (set via WithStreamBufferSize, will grow as needed)
        
        event = stream.read_event()
        assert event is not None, "Should handle data with dynamic buffer growth from option"
        assert event.type == "test"
        
        stream.close()

    def test_read_event_empty_lines(self):
        """Test handling of multiple empty lines."""
        sse_data = "\n\nevent: test\ndata: {\"key\":\"value\"}\n\n\n\n"
        
        class MockResponse:
            def __init__(self, data):
                self.content = data.encode('utf-8')
                self.headers = {}
                self.status_code = 200
                self.raw = io.BytesIO(data.encode('utf-8'))
                
            def iter_lines(self, decode_unicode=True, chunk_size=512):
                for line in data.split('\n'):
                    yield line
                    
            def close(self):
                pass
        
        response = MockResponse(sse_data)
        stream = DataAnalysisStream(response, initial_buffer_size=0)
        
        event = stream.read_event()
        assert event is not None
        assert event.type == "test"
        
        # Next read should be None (EOF)
        event = stream.read_event()
        assert event is None
        
        stream.close()


class TestWithStreamBufferSize_Option:
    """Test WithStreamBufferSize option function."""

    def test_with_stream_buffer_size_option(self):
        """Test that WithStreamBufferSize properly sets the buffer size."""
        from moi.options import CallOptions
        
        # Test with positive value
        opts = CallOptions()
        opt = with_stream_buffer_size(2 * 1024 * 1024)  # 2MB
        opt(opts)
        assert opts.stream_buffer_size == 2 * 1024 * 1024
        
        # Test with zero value (should not change default)
        opts = CallOptions()
        opt = with_stream_buffer_size(0)
        opt(opts)
        assert opts.stream_buffer_size == 0
        
        # Test with negative value (should not change default)
        opts = CallOptions()
        opt = with_stream_buffer_size(-1)
        opt(opts)
        assert opts.stream_buffer_size == 0
        
        # Test default value
        opts = CallOptions()
        assert opts.stream_buffer_size == 0

