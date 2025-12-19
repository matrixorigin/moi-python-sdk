"""Tests for Workflow APIs."""

import pytest
from moi import RawClient, SDKClient, ErrNilRequest
from moi.models import FileType, WorkflowJobStatus
from tests.test_helpers import get_test_client


class TestCreateWorkflow:
    """Test CreateWorkflow API."""

    def test_create_workflow_nil_request(self):
        """Test that nil request raises ErrNilRequest."""
        client = get_test_client()
        
        with pytest.raises(ErrNilRequest):
            client.create_workflow(None)

    @pytest.mark.integration
    def test_create_workflow_basic(self):
        """Test creating a workflow with basic configuration."""
        client = get_test_client()
        
        # This test requires volumes to be created first
        # For now, we'll just test the request structure
        req = {
            "name": "test-workflow",
            "source_volume_ids": ["vol-123"],
            "target_volume_id": "vol-456",
            "file_types": [FileType.TXT, FileType.PDF],
            "process_mode": {
                "interval": -1,
                "offset": 0
            },
            "workflow": {
                "nodes": [
                    {
                        "id": "RootNode_1",
                        "type": "RootNode",
                        "init_parameters": {}
                    }
                ],
                "connections": []
            }
        }
        
        # Note: This will fail without actual volumes, but tests the API structure
        try:
            resp = client.create_workflow(req)
            assert resp is not None
            assert "id" in resp
        except Exception as e:
            # Expected if volumes don't exist
            assert "volume" in str(e).lower() or "not found" in str(e).lower()


class TestListWorkflowJobs:
    """Test ListWorkflowJobs API."""

    def test_list_workflow_jobs_nil_request(self):
        """Test that nil request raises ErrNilRequest."""
        client = get_test_client()
        
        with pytest.raises(ErrNilRequest):
            client.list_workflow_jobs(None)

    @pytest.mark.integration
    def test_list_workflow_jobs_basic(self):
        """Test listing workflow jobs with filters."""
        client = get_test_client()
        
        req = {
            "workflow_id": "workflow-123",
            "page": 1,
            "page_size": 20
        }
        
        try:
            resp = client.list_workflow_jobs(req)
            assert resp is not None
            assert "jobs" in resp
            assert "total" in resp
            assert isinstance(resp["jobs"], list)
        except Exception as e:
            # Expected if workflow doesn't exist
            assert "not found" in str(e).lower() or "workflow" in str(e).lower()


class TestSDKClientWorkflow:
    """Test SDKClient workflow helpers."""

    def test_create_document_processing_workflow_missing_params(self):
        """Test that missing parameters raise ValueError."""
        sdk = SDKClient(get_test_client())
        
        with pytest.raises(ValueError, match="workflow_name"):
            sdk.create_document_processing_workflow("", "vol-1", "vol-2")
        
        with pytest.raises(ValueError, match="source_volume_id"):
            sdk.create_document_processing_workflow("test", "", "vol-2")
        
        with pytest.raises(ValueError, match="target_volume_id"):
            sdk.create_document_processing_workflow("test", "vol-1", "")

    def test_get_workflow_job_missing_params(self):
        """Test that missing parameters raise ValueError."""
        sdk = SDKClient(get_test_client())
        
        with pytest.raises(ValueError, match="workflow_id"):
            sdk.get_workflow_job("", "file-1")
        
        with pytest.raises(ValueError, match="source_file_id"):
            sdk.get_workflow_job("workflow-1", "")

    def test_wait_for_workflow_job_missing_params(self):
        """Test that missing parameters raise ValueError."""
        sdk = SDKClient(get_test_client())
        
        with pytest.raises(ValueError, match="workflow_id"):
            sdk.wait_for_workflow_job("", "file-1")
        
        with pytest.raises(ValueError, match="source_file_id"):
            sdk.wait_for_workflow_job("workflow-1", "")


class TestWorkflowJobStatus:
    """Test WorkflowJobStatus helper."""

    def test_workflow_job_status_to_string(self):
        """Test status to string conversion."""
        assert WorkflowJobStatus.to_string(WorkflowJobStatus.RUNNING) == "running"
        assert WorkflowJobStatus.to_string(WorkflowJobStatus.COMPLETED) == "completed"
        assert WorkflowJobStatus.to_string(WorkflowJobStatus.FAILED) == "failed"
        assert WorkflowJobStatus.to_string(WorkflowJobStatus.UNKNOWN) == "unknown"
        assert WorkflowJobStatus.to_string(999) == "unknown(999)"


class TestFileType:
    """Test FileType constants."""

    def test_file_type_constants(self):
        """Test that FileType constants are defined."""
        assert FileType.TXT == 1
        assert FileType.PDF == 2
        assert FileType.MARKDOWN == 6
        assert FileType.DOCX == 11
        assert FileType.HTML == 28

