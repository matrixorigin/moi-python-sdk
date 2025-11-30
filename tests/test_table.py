"""Tests for Table APIs."""

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
            finally:
                try:
                    client.delete_table({"id": table_id})
                except Exception:
                    pass
        finally:
            mark_database_deleted()
            mark_catalog_deleted()

