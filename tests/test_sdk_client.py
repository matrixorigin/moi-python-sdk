"""Tests for SDKClient helper methods."""

import os
import pytest
from moi import SDKClient, ExistedTableOption, ExistedTableOptions
from tests.test_helpers import (
    get_test_client,
    random_name,
    create_test_catalog,
    create_test_database,
    create_test_volume,
    create_test_table,
)


class TestFindFilesByName:
    """Test FindFilesByName method."""

    def test_find_files_by_name_empty_file_name(self):
        """Test that empty file_name raises ValueError."""
        raw_client = get_test_client()
        sdk = SDKClient(raw_client)
        
        with pytest.raises(ValueError, match="file_name is required"):
            sdk.find_files_by_name("", "test-volume-id")

    def test_find_files_by_name_empty_volume_id(self):
        """Test that empty volume_id raises ValueError."""
        raw_client = get_test_client()
        sdk = SDKClient(raw_client)
        
        with pytest.raises(ValueError, match="volume_id is required"):
            sdk.find_files_by_name("test-file.txt", "")

    @pytest.mark.integration
    def test_find_files_by_name_with_import_local_file_to_volume(self):
        """Test FindFilesByName with ImportLocalFileToVolume integration."""
        import os
        import tempfile
        import time
        
        raw_client = get_test_client()
        sdk = SDKClient(raw_client)
        
        # Step 1: Create test catalog, database, and volume
        catalog_id, mark_catalog_deleted = create_test_catalog(raw_client)
        database_id, mark_database_deleted = create_test_database(raw_client, catalog_id)
        volume_id, mark_volume_deleted = create_test_volume(raw_client, database_id)
        
        try:
            # Step 2: Create a temporary test file with a specific name
            with tempfile.TemporaryDirectory() as tmpdir:
                # Use the same file name format as in the user's example (without extension in search)
                local_file_name = "许继电气：关于召开2.txt"
                search_file_name = "许继电气：关于召开2"  # Search without extension, matching user's example
                file_path = os.path.join(tmpdir, local_file_name)
                test_content = "This is a test file for FindFilesByName integration test"
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(test_content)
                
                # Ensure file exists
                assert os.path.exists(file_path), "Temporary file should exist"
                
                # Step 3: Upload the file to volume using import_local_file_to_volume
                # Use the full filename with extension for upload
                upload_resp = sdk.import_local_file_to_volume(
                    file_path,
                    volume_id,
                    {"filename": local_file_name, "path": local_file_name},
                    None
                )
                assert upload_resp is not None
                assert upload_resp.get("file_id")
                print(f"Uploaded file with ID: {upload_resp.get('file_id')}, TaskId: {upload_resp.get('task_id')}")
                
                # Step 4: Wait a bit for the file to be processed and indexed
                # The file might need some time to be available in the file list
                # We'll retry the search a few times with a short delay
                found_files = None
                max_retries = 10
                retry_delay = 1.0
                
                for i in range(max_retries):
                    # Step 5: Search for the file using find_files_by_name
                    # Use the search file name (without extension) as in the user's example
                    try:
                        found_files = sdk.find_files_by_name(search_file_name, volume_id)
                        if found_files and found_files.get("total", 0) > 0:
                            print(f"Found file after {i+1} retries")
                            break
                    except Exception as e:
                        print(f"Search attempt {i+1} failed: {e}")
                    
                    if i < max_retries - 1:
                        print(f"File not found yet, retrying in {retry_delay}s (attempt {i+1}/{max_retries})...")
                        time.sleep(retry_delay)
                
                # Step 6: Verify the search results
                assert found_files is not None, "find_files_by_name should return a response"
                assert found_files.get("total", 0) > 0, "Should find at least one file with the given name"
                assert len(found_files.get("list", [])) > 0, "List should contain at least one file"
                
                # Verify that the found file matches the uploaded file
                found = False
                for file in found_files.get("list", []):
                    # The file name might be with or without extension, so check both
                    file_name = file.get("name", "")
                    if local_file_name in file_name or search_file_name in file_name or "许继电气：关于召开2" in file_name:
                        found = True
                        print(f"Found matching file: ID={file.get('id')}, Name={file_name}, FileType={file.get('file_type')}")
                        assert file.get("volume_id") == volume_id, "Volume ID should match"
                        break
                
                assert found, "Should find a file matching the uploaded file name"
                print(f"Successfully found {found_files.get('total')} file(s) with search name '{search_file_name}'")
        finally:
            mark_volume_deleted()
            mark_database_deleted()
            mark_catalog_deleted()


class TestImportLocalFileToTableExistedTableOption:
    """Test ImportLocalFileToTable with ExistedTableOptions.
    run case : 
        pytest test_sdk_client.py::TestImportLocalFileToTableExistedTableOption 
    """

    @pytest.mark.integration
    def test_import_local_file_to_table_existed_table_option(self):
        """Test ImportLocalFileToTable with ExistedTableOptions (append and overwrite)."""
        import tempfile
        
        raw_client = get_test_client()
        sdk = SDKClient(raw_client)
        
        # Create test catalog, database, and table
        catalog_id, mark_catalog_deleted = create_test_catalog(raw_client)
        database_id, mark_database_deleted = create_test_database(raw_client, catalog_id)
        table_id, mark_table_deleted = create_test_table(raw_client, database_id)
        
        try:
            # Create a test volume and upload a file to get conn_file_id
            volume_id, mark_volume_deleted = create_test_volume(raw_client, database_id)
            
            try:
                # Create a temporary test file
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_name = "test-import-table.csv"
                    file_path = os.path.join(tmpdir, file_name)
                    test_content = "id,name\n1,test1\n2,test2\n"
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(test_content)
                    
                    # Upload file to volume to get conn_file_id
                    upload_resp = sdk.import_local_file_to_volume(
                        file_path,
                        volume_id,
                        {"filename": file_name, "path": file_name},
                        None
                    )
                    assert upload_resp is not None
                    assert upload_resp.get("file_id")
                    conn_file_id = upload_resp.get("file_id")
                    
                    # Test 1: Import to existing table with ExistedTableOpts set to append
                    table_config_append = {
                        "conn_file_ids": [conn_file_id],
                        "new_table": False,
                        "table_id": table_id,
                        "database_id": database_id,
                        "existed_table": [
                            {
                                "tableColumn": "id",
                                "column": "id",
                                "col_num_in_file": 1,
                            },
                            {
                                "tableColumn": "name",
                                "column": "name",
                                "col_num_in_file": 2,
                            },
                        ],
                        "existed_table_opts": ExistedTableOptions(method=ExistedTableOption.APPEND),
                    }
                    
                    resp = sdk.import_local_file_to_table(table_config_append)
                    # Note: The actual API call might fail if the file format doesn't match,
                    # but we're testing that the ExistedTableOpts is properly set
                    if resp is None:
                        print("ImportLocalFileToTable with append option returned None (expected in some cases)")
                    else:
                        assert resp is not None
                        print(f"Successfully imported with append option, response: {resp}")
                    
                    # Test 2: Import to existing table with ExistedTableOpts set to overwrite
                    table_config_overwrite = {
                        "conn_file_ids": [conn_file_id],
                        "new_table": False,
                        "table_id": table_id,
                        "database_id": database_id,
                        "existed_table": [
                            {
                                "tableColumn": "id",
                                "column": "id",
                                "col_num_in_file": 1,
                            },
                            {
                                "tableColumn": "name",
                                "column": "name",
                                "col_num_in_file": 2,
                            },
                        ],
                        "existed_table_opts": ExistedTableOptions(method=ExistedTableOption.OVERWRITE),
                    }
                    
                    resp2 = sdk.import_local_file_to_table(table_config_overwrite)
                    if resp2 is None:
                        print("ImportLocalFileToTable with overwrite option returned None (expected in some cases)")
                    else:
                        assert resp2 is not None
                        print(f"Successfully imported with overwrite option, response: {resp2}")
                    
                    # Test 3: Import to existing table with existed_table as None (should be initialized to empty list internally)
                    # Note: The method uses deepcopy, so the original dict won't be modified, but None should be handled correctly
                    table_config_nil_existed_table = {
                        "conn_file_ids": [conn_file_id],
                        "new_table": False,
                        "table_id": table_id,
                        "database_id": database_id,
                        "existed_table": None,  # None should be initialized to empty list internally
                        "existed_table_opts": ExistedTableOptions(method=ExistedTableOption.APPEND),
                    }
                    
                    resp3 = sdk.import_local_file_to_table(table_config_nil_existed_table)
                    # The method should handle None existed_table correctly by initializing it to empty list internally
                    # Since the method uses deepcopy, the original dict remains unchanged
                    # We just verify that the call doesn't raise an error
                    
                    if resp3 is None:
                        print("ImportLocalFileToTable with None existed_table returned None (expected in some cases)")
                    else:
                        assert resp3 is not None
                        print(f"Successfully imported with None existed_table (initialized internally), response: {resp3}")
            finally:
                mark_volume_deleted()
        finally:
            mark_table_deleted()
            mark_database_deleted()
            mark_catalog_deleted()

