"""Tests for Task APIs."""

import os
import tempfile
import pytest
from moi import (
    RawClient,
    SDKClient,
    ErrNilRequest,
    new_dedup_config_skip_by_name_and_md5,
    new_dedup_config_skip_by_name,
    new_dedup_config_skip_by_md5,
    DedupBy,
    DedupStrategy,
    new_dedup_config,
)
from tests.test_helpers import (
    get_test_client,
    create_test_catalog,
    create_test_database,
    create_test_volume,
)


class TestGetTask:
    """Test GetTask API."""

    def test_get_task_nil_request(self):
        """Test GetTask with nil request."""
        client = get_test_client()
        
        with pytest.raises(ErrNilRequest):
            client.get_task(None)

    def test_get_task_empty_task_id(self):
        """Test GetTask with empty task ID."""
        client = get_test_client()
        
        with pytest.raises(ValueError) as exc_info:
            client.get_task({"task_id": 0})
        assert "task_id is required" in str(exc_info.value)


@pytest.mark.integration
class TestImportLocalFileToVolumeAndGetTask:
    """Test ImportLocalFileToVolume and GetTask integration."""

    def test_import_local_file_to_volume_and_get_task(self):
        """Test uploading a file to volume and retrieving task information."""
        raw_client = get_test_client()
        sdk_client = SDKClient(raw_client)
        
        # Create test catalog, database, and volume
        catalog_id, catalog_cleanup = create_test_catalog(raw_client)
        try:
            database_id, db_cleanup = create_test_database(raw_client, catalog_id)
            try:
                volume_id, volume_cleanup = create_test_volume(raw_client, database_id)
                try:
                    # Create a temporary test file
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        test_file_name = "test_file.txt"
                        test_file_path = os.path.join(tmp_dir, test_file_name)
                        test_content = "This is a test file for ImportLocalFileToVolume"
                        with open(test_file_path, "w") as f:
                            f.write(test_content)
                        
                        # Upload file to volume using ImportLocalFileToVolume
                        meta = {
                            "filename": test_file_name,
                            "path": test_file_name,
                        }
                        dedup = new_dedup_config_skip_by_name_and_md5()
                        
                        upload_resp = sdk_client.import_local_file_to_volume(
                            test_file_path, volume_id, meta, dedup
                        )
                        assert upload_resp is not None
                        assert upload_resp.get("task_id") is not None, "TaskId should be returned from upload"
                        
                        task_id = upload_resp["task_id"]
                        print(f"Upload successful, task_id: {task_id}")
                        
                        # Get task information using GetTask
                        task_resp = raw_client.get_task({"task_id": task_id})
                        assert task_resp is not None
                        
                        # Verify task information
                        assert str(task_id) == task_resp.get("id"), "Task ID should match"
                        assert task_resp.get("status") is not None, "Task status should be present"
                        assert task_resp.get("created_at") is not None, "CreatedAt should be present"
                        assert volume_id == task_resp.get("volume_id"), "Volume ID should match"
                        
                        print(f"Task retrieved successfully:")
                        print(f"  ID: {task_resp.get('id')}")
                        print(f"  Name: {task_resp.get('name')}")
                        print(f"  Status: {task_resp.get('status')}")
                        print(f"  VolumeID: {task_resp.get('volume_id')}")
                        print(f"  CreatedAt: {task_resp.get('created_at')}")
                finally:
                    volume_cleanup()
            finally:
                db_cleanup()
        finally:
            catalog_cleanup()


@pytest.mark.integration
class TestImportLocalFilesToVolume:
    """Test ImportLocalFilesToVolume API."""

    def test_import_local_files_to_volume_with_metas(self):
        """Test uploading multiple files with provided metadata."""
        raw_client = get_test_client()
        sdk_client = SDKClient(raw_client)
        
        # Create test catalog, database, and volume
        catalog_id, catalog_cleanup = create_test_catalog(raw_client)
        try:
            database_id, db_cleanup = create_test_database(raw_client, catalog_id)
            try:
                volume_id, volume_cleanup = create_test_volume(raw_client, database_id)
                try:
                    # Create temporary test files
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        test_file1 = os.path.join(tmp_dir, "test_file1.txt")
                        test_file2 = os.path.join(tmp_dir, "test_file2.txt")
                        test_content1 = "This is test file 1 for ImportLocalFilesToVolume"
                        test_content2 = "This is test file 2 for ImportLocalFilesToVolume"
                        
                        with open(test_file1, "w") as f:
                            f.write(test_content1)
                        with open(test_file2, "w") as f:
                            f.write(test_content2)
                        
                        # Test with provided metas
                        metas = [
                            {"filename": "test_file1.txt", "path": "test_file1.txt"},
                            {"filename": "test_file2.txt", "path": "test_file2.txt"},
                        ]
                        dedup = new_dedup_config_skip_by_name_and_md5()
                        
                        upload_resp = sdk_client.import_local_files_to_volume(
                            [test_file1, test_file2], volume_id, metas, dedup
                        )
                        assert upload_resp is not None
                        assert upload_resp.get("task_id") is not None, "TaskId should be returned from upload"
                        
                        task_id = upload_resp["task_id"]
                        print(f"Upload successful, task_id: {task_id}")
                finally:
                    volume_cleanup()
            finally:
                db_cleanup()
        finally:
            catalog_cleanup()

    def test_import_local_files_to_volume_auto_metas(self):
        """Test uploading multiple files with auto-generated metadata."""
        raw_client = get_test_client()
        sdk_client = SDKClient(raw_client)
        
        # Create test catalog, database, and volume
        catalog_id, catalog_cleanup = create_test_catalog(raw_client)
        try:
            database_id, db_cleanup = create_test_database(raw_client, catalog_id)
            try:
                volume_id, volume_cleanup = create_test_volume(raw_client, database_id)
                try:
                    # Create temporary test files
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        test_file1 = os.path.join(tmp_dir, "test_file1.txt")
                        test_file2 = os.path.join(tmp_dir, "test_file2.txt")
                        test_content1 = "This is test file 1 for ImportLocalFilesToVolume"
                        test_content2 = "This is test file 2 for ImportLocalFilesToVolume"
                        
                        with open(test_file1, "w") as f:
                            f.write(test_content1)
                        with open(test_file2, "w") as f:
                            f.write(test_content2)
                        
                        # Test with auto-generated metas (None metas)
                        dedup = new_dedup_config_skip_by_name_and_md5()
                        
                        upload_resp = sdk_client.import_local_files_to_volume(
                            [test_file1, test_file2], volume_id, None, dedup
                        )
                        assert upload_resp is not None
                        assert upload_resp.get("task_id") is not None
                        
                        task_id = upload_resp["task_id"]
                        print(f"Upload with auto-generated metas successful, task_id: {task_id}")
                finally:
                    volume_cleanup()
            finally:
                db_cleanup()
        finally:
            catalog_cleanup()


class TestImportLocalFilesToVolumeErrors:
    """Test error cases for ImportLocalFilesToVolume."""

    def test_import_local_files_to_volume_empty_paths(self):
        """Test ImportLocalFilesToVolume with empty file paths."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        with pytest.raises(ValueError) as exc_info:
            sdk_client.import_local_files_to_volume([], "123456", None, None)
        assert "at least one file path is required" in str(exc_info.value)

    def test_import_local_files_to_volume_empty_volume_id(self):
        """Test ImportLocalFilesToVolume with empty volume ID."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        with pytest.raises(ValueError) as exc_info:
            sdk_client.import_local_files_to_volume(["/path/to/file.txt"], "", None, None)
        assert "volume_id is required" in str(exc_info.value)

    def test_import_local_files_to_volume_mismatched_metas(self):
        """Test ImportLocalFilesToVolume with mismatched metas length."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        metas = [{"filename": "file1.txt", "path": "file1.txt"}]
        with pytest.raises(ValueError) as exc_info:
            sdk_client.import_local_files_to_volume(
                ["/path/to/file1.txt", "/path/to/file2.txt"], "123456", metas, None
            )
        assert "metas array length" in str(exc_info.value)

    def test_import_local_files_to_volume_empty_file_path(self):
        """Test ImportLocalFilesToVolume with empty file path in array."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        with pytest.raises(ValueError) as exc_info:
            sdk_client.import_local_files_to_volume(
                ["", "/path/to/file2.txt"], "123456", None, None
            )
        assert "file_path[0] is empty" in str(exc_info.value)

    def test_import_local_file_to_volume_empty_path(self):
        """Test ImportLocalFileToVolume with empty file path."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        with pytest.raises(ValueError) as exc_info:
            sdk_client.import_local_file_to_volume("", "123456", {"filename": "test.txt"}, None)
        assert "file_path is required" in str(exc_info.value)

    def test_import_local_file_to_volume_empty_volume_id(self):
        """Test ImportLocalFileToVolume with empty volume ID."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        with pytest.raises(ValueError) as exc_info:
            sdk_client.import_local_file_to_volume("/path/to/file.txt", "", {"filename": "test.txt"}, None)
        assert "volume_id is required" in str(exc_info.value)

    def test_import_local_file_to_volume_empty_meta_filename(self):
        """Test ImportLocalFileToVolume with empty meta filename."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        with pytest.raises(ValueError) as exc_info:
            sdk_client.import_local_file_to_volume("/path/to/file.txt", "123456", {}, None)
        assert "meta.filename is required" in str(exc_info.value)

    def test_import_local_file_to_volume_file_not_found(self):
        """Test ImportLocalFileToVolume with non-existent file."""
        from moi import RawClient, SDKClient
        
        raw_client = RawClient("http://example.com", "test-key")
        sdk_client = SDKClient(raw_client)
        
        with pytest.raises(FileNotFoundError):
            sdk_client.import_local_file_to_volume(
                "/nonexistent/file.txt", "123456", {"filename": "test.txt"}, None
            )


class TestDedupConfigHelpers:
    """Test DedupConfig helper functions."""

    def test_new_dedup_config(self):
        """Test new_dedup_config helper function."""
        # Test with name and MD5
        dedup = new_dedup_config([DedupBy.NAME, DedupBy.MD5], DedupStrategy.SKIP)
        assert dedup is not None
        assert dedup.by == [DedupBy.NAME, DedupBy.MD5]
        assert dedup.strategy == DedupStrategy.SKIP
        
        # Test with name only
        dedup = new_dedup_config([DedupBy.NAME], DedupStrategy.SKIP)
        assert dedup is not None
        assert dedup.by == [DedupBy.NAME]
        assert dedup.strategy == DedupStrategy.SKIP
        
        # Test with empty list (should return None)
        dedup = new_dedup_config([], DedupStrategy.SKIP)
        assert dedup is None
        
        # Test with replace strategy
        dedup = new_dedup_config([DedupBy.MD5], DedupStrategy.REPLACE)
        assert dedup is not None
        assert dedup.by == [DedupBy.MD5]
        assert dedup.strategy == DedupStrategy.REPLACE

    def test_new_dedup_config_skip_by_name_and_md5(self):
        """Test new_dedup_config_skip_by_name_and_md5 convenience function."""
        dedup = new_dedup_config_skip_by_name_and_md5()
        assert dedup is not None
        assert dedup.by == [DedupBy.NAME, DedupBy.MD5]
        assert dedup.strategy == DedupStrategy.SKIP

    def test_new_dedup_config_skip_by_name(self):
        """Test new_dedup_config_skip_by_name convenience function."""
        dedup = new_dedup_config_skip_by_name()
        assert dedup is not None
        assert dedup.by == [DedupBy.NAME]
        assert dedup.strategy == DedupStrategy.SKIP

    def test_new_dedup_config_skip_by_md5(self):
        """Test new_dedup_config_skip_by_md5 convenience function."""
        dedup = new_dedup_config_skip_by_md5()
        assert dedup is not None
        assert dedup.by == [DedupBy.MD5]
        assert dedup.strategy == DedupStrategy.SKIP

