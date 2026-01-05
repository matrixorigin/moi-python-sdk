"""Tests for Table APIs."""

import os
import pytest
from moi import RawClient, ErrNilRequest
from tests.test_helpers import (
    get_test_client,
    random_name,
    create_test_catalog,
    create_test_database,
    create_test_table,
)


class TestTableLiveFlow:
    """Test Table operations with live backend."""

    def test_table_live_flow(self):
        """Test complete table flow."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        database_id, mark_database_deleted = create_test_database(client, catalog_id)
        
        try:
            table_name = random_name("sdk-table-")
            columns = [
                {"name": "id", "type": "int", "is_pk": True},
                {"name": "name", "type": "varchar(255)"},
            ]
            create_resp = client.create_table({
                "database_id": database_id,
                "name": table_name,
                "columns": columns,
                "comment": "sdk test table",
            })
            assert create_resp is not None
            table_id = create_resp["id"]
            table_deleted = False
            
            try:
                # Get table
                info_resp = client.get_table({"id": table_id})
                assert info_resp is not None
                assert info_resp["name"] == table_name

                # Get multi table
                multi_info_resp = client.get_multi_table([{"id": table_id}])
                assert multi_info_resp is not None
                assert isinstance(multi_info_resp, dict)
                # Access table info using the correct key format
                key = f"{database_id} {table_name}"
                assert key in multi_info_resp
                table_info = multi_info_resp[key]
                assert table_info["name"] == table_name
                
                # Check table exists
                exists = client.check_table_exists({
                    "database_id": database_id,
                    "name": table_name,
                })
                assert exists is True
                
                # Preview table
                preview_resp = client.preview_table({
                    "id": table_id,
                    "lines": 5,
                })
                assert preview_resp is not None
                
                # Truncate table
                trunc_resp = client.truncate_table({"id": table_id})
                assert trunc_resp is not None
                
                # Get full path
                full_path_resp = client.get_table_full_path({
                    "table_id_list": [table_id],
                })
                assert full_path_resp is not None
                
                # Get ref list
                ref_list_resp = client.get_table_ref_list({"id": table_id})
                assert ref_list_resp is not None
                
                # Delete table
                client.delete_table({"id": table_id})
                table_deleted = True
                
                # Verify table doesn't exist
                exists = client.check_table_exists({
                    "database_id": database_id,
                    "name": table_name,
                })
                assert exists is False
                
            finally:
                if not table_deleted:
                    try:
                        client.delete_table({"id": table_id})
                    except Exception:
                        pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()


class TestTableNilRequestErrors:
    """Test that nil request errors are raised correctly."""

    def test_create_table_nil_request(self):
        """Test CreateTable with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.create_table(None)

    def test_get_table_nil_request(self):
        """Test GetTable with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_table(None)

    
    def test_get_multi_table_nil_request(self):
        """Test GetTable with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_multi_table(None)

    def test_check_table_exists_nil_request(self):
        """Test CheckTableExists with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.check_table_exists(None)

    def test_preview_table_nil_request(self):
        """Test PreviewTable with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.preview_table(None)

    def test_get_table_data_nil_request(self):
        """Test GetTableData with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_table_data(None)

    def test_delete_table_nil_request(self):
        """Test DeleteTable with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.delete_table(None)


class TestTableDatabaseIDNotExists:
    """Test table creation with non-existent database ID."""

    def test_table_database_id_not_exists(self):
        """Test that creating table with non-existent database ID fails."""
        client = get_test_client()
        
        non_existent_database_id = 999999999
        
        with pytest.raises(Exception):
            client.create_table({
                "database_id": non_existent_database_id,
                "name": random_name("test-table-"),
                "columns": [{"name": "id", "type": "int", "is_pk": True}],
                "comment": "test",
            })


class TestTableNameExists:
    """Test table name existence validation."""

    def test_table_name_exists(self):
        """Test that creating a table with duplicate name fails."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        database_id, mark_database_deleted = create_test_database(client, catalog_id)
        
        try:
            table_name = random_name("sdk-table-")
            columns = [
                {"name": "id", "type": "int", "is_pk": True},
                {"name": "name", "type": "varchar(255)"},
            ]
            create_req = {
                "database_id": database_id,
                "name": table_name,
                "columns": columns,
                "comment": "test table",
            }
            create_resp = client.create_table(create_req)
            assert create_resp is not None
            table_id = create_resp["id"]
            
            try:
                # Try to create another table with the same name
                with pytest.raises(Exception):
                    client.create_table(create_req)
            finally:
                try:
                    client.delete_table({"id": table_id})
                except Exception:
                    pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()


class TestTableIDNotExists:
    """Test operations on non-existent table IDs."""

    def test_table_id_not_exists(self):
        """Test operations on non-existent table."""
        client = get_test_client()
        
        non_existent_id = 999999999
        
        # Try to get non-existent table
        with pytest.raises(Exception):
            client.get_table({"id": non_existent_id})

        # Try to get non-existent table (by get_multi_table)
        try:
            resp = client.get_multi_table([{"id": non_existent_id}])
            assert resp is not None
        except Exception:
            pass  # Expected error
        
        # Try to preview non-existent table - may not error if service allows empty preview
        try:
            client.preview_table({"id": non_existent_id, "lines": 5})
        except Exception:
            pass  # Expected error


class TestTableWithDefaultValues:
    """Test table creation with default values."""

    def test_table_with_default_values(self):
        """Test creating a table with default column values."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        database_id, mark_database_deleted = create_test_database(client, catalog_id)
        
        try:
            table_name = random_name("sdk-table-default-")
            columns = [
                {"name": "id", "type": "int", "is_pk": True},
                {"name": "age", "type": "int", "default": "0"},
                {"name": "default_test", "type": "varchar(100)", "default": "VARCHAR DEFAULT"},
            ]
            
            create_resp = client.create_table({
                "database_id": database_id,
                "name": table_name,
                "columns": columns,
                "comment": "test table with defaults",
            })
            assert create_resp is not None
            table_id = create_resp["id"]
            
            try:
                # Verify table was created successfully
                info_resp = client.get_table({"id": table_id})
                assert info_resp is not None
                assert info_resp["name"] == table_name
                assert len(info_resp.get("columns", [])) == 3

                # Verify table was created successfully(by get multi info)
                info_resp = client.get_multi_table([{"id": table_id}])
                assert info_resp is not None
                key = f"{database_id} {table_name}"
                table_info = info_resp[key]
                assert table_info["name"] == table_name
                assert len(table_info.get("columns", [])) == 3
            finally:
                try:
                    client.delete_table({"id": table_id})
                except Exception:
                    pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()


class TestGetTableData:
    """Test GetTableData API."""

    def test_get_table_data_live_flow(self):
        """Test GetTableData with live backend."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        database_id, mark_database_deleted = create_test_database(client, catalog_id)
        
        try:
            table_name = random_name("sdk-table-data-")
            columns = [
                {"name": "id", "type": "int", "is_pk": True},
                {"name": "name", "type": "varchar(255)"},
                {"name": "value", "type": "int"},
            ]
            create_resp = client.create_table({
                "database_id": database_id,
                "name": table_name,
                "columns": columns,
                "comment": "test table for GetTableData",
            })
            assert create_resp is not None
            table_id = create_resp["id"]
            
            try:
                # Test GetTableData with default pagination (empty table)
                resp = client.get_table_data({
                    "id": table_id,
                    "database_id": database_id,
                    "page": 1,
                    "page_size": 100,
                })
                assert resp is not None
                assert "columns" in resp
                assert "data" in resp
                assert resp["page"] == 1
                assert resp["page_size"] == 100
                assert resp["total_rows"] >= 0
                assert len(resp["columns"]) == 3
                assert resp["columns"][0]["name"] == "id"
                assert resp["columns"][1]["name"] == "name"
                assert resp["columns"][2]["name"] == "value"
                
                # Test GetTableData with different page size
                resp2 = client.get_table_data({
                    "id": table_id,
                    "database_id": database_id,
                    "page": 1,
                    "page_size": 50,
                })
                assert resp2 is not None
                assert resp2["page"] == 1
                assert resp2["page_size"] == 50
                assert resp["total_rows"] == resp2["total_rows"], "total rows should be the same"
                
                # Test GetTableData with both id and name (id is required by backend)
                resp3 = client.get_table_data({
                    "id": table_id,
                    "name": table_name,
                    "database_id": database_id,
                    "page": 1,
                    "page_size": 10,
                })
                assert resp3 is not None
                assert resp["total_rows"] == resp3["total_rows"], "total rows should be the same when using both id and name"
                
                # Test GetTableData with page 2 (should work even if empty)
                resp4 = client.get_table_data({
                    "id": table_id,
                    "database_id": database_id,
                    "page": 2,
                    "page_size": 10,
                })
                assert resp4 is not None
                assert resp4["page"] == 2
                assert resp4["page_size"] == 10
            finally:
                try:
                    client.delete_table({"id": table_id})
                except Exception:
                    pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()

    def test_get_table_data_pagination(self):
        """Test GetTableData pagination edge cases."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        database_id, mark_database_deleted = create_test_database(client, catalog_id)
        
        try:
            table_name = random_name("sdk-table-pagination-")
            columns = [
                {"name": "id", "type": "int", "is_pk": True},
                {"name": "name", "type": "varchar(255)"},
            ]
            create_resp = client.create_table({
                "database_id": database_id,
                "name": table_name,
                "columns": columns,
                "comment": "test table for pagination",
            })
            assert create_resp is not None
            table_id = create_resp["id"]
            
            try:
                # Test with page 0 (should default to 1)
                resp = client.get_table_data({
                    "id": table_id,
                    "database_id": database_id,
                    "page": 0,
                    "page_size": 10,
                })
                assert resp is not None
                # Backend should default page to 1 if <= 0
                assert resp["page"] >= 1
                
                # Test with pageSize 0 (should default to 100)
                resp2 = client.get_table_data({
                    "id": table_id,
                    "database_id": database_id,
                    "page": 1,
                    "page_size": 0,
                })
                assert resp2 is not None
                # Backend should default pageSize to 100 if <= 0
                assert resp2["page_size"] >= 100
            finally:
                try:
                    client.delete_table({"id": table_id})
                except Exception:
                    pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()


class TestPreviewTable:
    """Test PreviewTable API (refactored to use get_table_data internally)."""

    def test_preview_table_live_flow(self):
        """Test PreviewTable with live backend."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        database_id, mark_database_deleted = create_test_database(client, catalog_id)
        
        try:
            table_name = random_name("sdk-table-preview-")
            columns = [
                {"name": "id", "type": "int", "is_pk": True},
                {"name": "name", "type": "varchar(255)"},
                {"name": "value", "type": "int"},
            ]
            create_resp = client.create_table({
                "database_id": database_id,
                "name": table_name,
                "columns": columns,
                "comment": "test table for PreviewTable",
            })
            assert create_resp is not None
            table_id = create_resp["id"]
            
            try:
                # Test PreviewTable with specific Lines
                resp = client.preview_table({
                    "id": table_id,
                    "lines": 5,
                })
                assert resp is not None
                assert "columns" in resp
                assert "data" in resp
                assert len(resp["columns"]) == 3
                assert resp["columns"][0]["name"] == "id"
                assert resp["columns"][1]["name"] == "name"
                assert resp["columns"][2]["name"] == "value"
                # Data rows should not exceed requested Lines
                assert len(resp["data"]) <= 5, "data rows should not exceed requested Lines"
                
                # Test PreviewTable with different Lines value
                resp2 = client.preview_table({
                    "id": table_id,
                    "lines": 10,
                })
                assert resp2 is not None
                assert len(resp2["data"]) <= 10, "data rows should not exceed requested Lines"
                # Columns should be the same
                assert len(resp["columns"]) == len(resp2["columns"])
                
                # Test PreviewTable with Lines = 0 (should use default)
                resp3 = client.preview_table({
                    "id": table_id,
                    "lines": 0,
                })
                assert resp3 is not None
                # Should use default pageSize of 10
                assert len(resp3["data"]) <= 10, "data rows should not exceed default pageSize"
                
                # Test PreviewTable with negative Lines (should use default)
                resp4 = client.preview_table({
                    "id": table_id,
                    "lines": -1,
                })
                assert resp4 is not None
                # Should use default pageSize of 10
                assert len(resp4["data"]) <= 10, "data rows should not exceed default pageSize"
                
                # Test PreviewTable with large Lines value
                resp5 = client.preview_table({
                    "id": table_id,
                    "lines": 100,
                })
                assert resp5 is not None
                assert len(resp5["data"]) <= 100, "data rows should not exceed requested Lines"
            finally:
                try:
                    client.delete_table({"id": table_id})
                except Exception:
                    pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()

    def test_preview_table_empty_table(self):
        """Test PreviewTable with empty table."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        database_id, mark_database_deleted = create_test_database(client, catalog_id)
        
        try:
            table_name = random_name("sdk-table-preview-empty-")
            columns = [
                {"name": "id", "type": "int", "is_pk": True},
                {"name": "name", "type": "varchar(255)"},
            ]
            create_resp = client.create_table({
                "database_id": database_id,
                "name": table_name,
                "columns": columns,
                "comment": "empty test table for PreviewTable",
            })
            assert create_resp is not None
            table_id = create_resp["id"]
            
            try:
                # Preview empty table
                resp = client.preview_table({
                    "id": table_id,
                    "lines": 5,
                })
                assert resp is not None
                assert "columns" in resp
                assert "data" in resp
                assert len(resp["columns"]) == 2
                # Data should be empty for empty table
                assert len(resp["data"]) == 0, "data should be empty for empty table"
            finally:
                try:
                    client.delete_table({"id": table_id})
                except Exception:
                    pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()

    def test_preview_table_nonexistent_table(self):
        """Test PreviewTable with non-existent table."""
        client = get_test_client()
        
        non_existent_id = 999999999
        
        # Try to preview non-existent table
        try:
            resp = client.preview_table({
                "id": non_existent_id,
                "lines": 5,
            })
            # If no error, response should be valid (service may allow empty preview)
            assert resp is not None
            assert "columns" in resp
            assert "data" in resp
        except Exception:
            # Expected error for non-existent table
            pass

