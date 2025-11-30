"""Tests for Database APIs."""

import pytest
from moi import RawClient, ErrNilRequest
from tests.test_helpers import (
    get_test_client,
    random_name,
    create_test_catalog,
    create_test_database,
)


class TestDatabaseLiveCRUD:
    """Test Database CRUD operations with live backend."""

    def test_database_live_crud(self):
        """Test complete database CRUD flow."""
        client = get_test_client()
        
        # Create catalog first
        catalog_resp = client.create_catalog({"name": random_name("sdk-db-catalog-")})
        catalog_id = catalog_resp["id"]
        catalog_deleted = False
        
        try:
            # Create database
            create_resp = client.create_database({
                "name": random_name("sdk-db-"),
                "catalog_id": catalog_id,
            })
            assert create_resp is not None
            assert create_resp["id"] != 0
            db_id = create_resp["id"]
            db_deleted = False
            
            try:
                # Get database
                info_resp = client.get_database({"id": db_id})
                assert info_resp is not None
                assert info_resp["name"] is not None
                
                # Update database
                client.update_database({
                    "id": db_id,
                    "description": "updated from sdk tests",
                })
                
                # List databases
                list_resp = client.list_databases({"id": catalog_id})
                assert list_resp is not None
                
                # Get children
                children_resp = client.get_database_children({"id": db_id})
                assert children_resp is not None
                
                # Get ref list
                ref_resp = client.get_database_ref_list({"id": db_id})
                assert ref_resp is not None
                
                # Delete database
                client.delete_database({"id": db_id})
                db_deleted = True
                
            finally:
                if not db_deleted:
                    try:
                        client.delete_database({"id": db_id})
                    except Exception:
                        pass
        finally:
            if not catalog_deleted:
                try:
                    client.delete_catalog({"catalog_id": catalog_id})
                except Exception:
                    pass


class TestDatabaseNilRequestErrors:
    """Test that nil request errors are raised correctly."""

    def test_create_database_nil_request(self):
        """Test CreateDatabase with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.create_database(None)

    def test_delete_database_nil_request(self):
        """Test DeleteDatabase with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.delete_database(None)

    def test_update_database_nil_request(self):
        """Test UpdateDatabase with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.update_database(None)

    def test_get_database_nil_request(self):
        """Test GetDatabase with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_database(None)

    def test_list_databases_nil_request(self):
        """Test ListDatabases with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.list_databases(None)

    def test_get_database_children_nil_request(self):
        """Test GetDatabaseChildren with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_database_children(None)

    def test_get_database_ref_list_nil_request(self):
        """Test GetDatabaseRefList with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_database_ref_list(None)


class TestDatabaseCatalogIDNotExists:
    """Test database creation with non-existent catalog ID."""

    def test_database_catalog_id_not_exists(self):
        """Test that creating database with non-existent catalog ID fails."""
        client = get_test_client()
        
        non_existent_catalog_id = 999999999
        
        with pytest.raises(Exception):
            client.create_database({
                "catalog_id": non_existent_catalog_id,
                "database_name": random_name("test-db-"),
                "comment": "test",
            })


class TestDatabaseNameExists:
    """Test database name existence validation."""

    def test_database_name_exists(self):
        """Test that creating a database with duplicate name fails."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        
        try:
            database_name = random_name("sdk-db-")
            create_req = {
                "name": database_name,
                "catalog_id": catalog_id,
                "description": "test database",
            }
            create_resp = client.create_database(create_req)
            assert create_resp is not None
            db_id = create_resp["id"]
            
            try:
                # Try to create another database with the same name
                with pytest.raises(Exception):
                    client.create_database(create_req)
            finally:
                try:
                    client.delete_database({"id": db_id})
                except Exception:
                    pass
        finally:
            mark_catalog_deleted()


class TestDatabaseInvalidName:
    """Test database name validation."""

    def test_database_invalid_name(self):
        """Test that invalid database names are rejected."""
        client = get_test_client()
        
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        
        try:
            test_cases = [
                ("SpecialChars", 'aa"b\''),
                ("Empty", ""),
            ]
            
            for name, database_name in test_cases:
                with pytest.raises(Exception):
                    client.create_database({
                        "name": database_name,
                        "catalog_id": catalog_id,
                        "description": "test",
                    })
        finally:
            mark_catalog_deleted()


class TestDatabaseIDNotExists:
    """Test operations on non-existent database IDs."""

    def test_database_id_not_exists(self):
        """Test operations on non-existent database."""
        client = get_test_client()
        
        non_existent_id = 999999999
        
        # Try to get non-existent database
        with pytest.raises(Exception):
            client.get_database({"id": non_existent_id})
        
        # Try to update non-existent database
        with pytest.raises(Exception):
            client.update_database({
                "id": non_existent_id,
                "description": "test",
            })
        
        # Try to delete non-existent database
        with pytest.raises(Exception):
            client.delete_database({"id": non_existent_id})

