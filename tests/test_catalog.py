"""Tests for Catalog APIs."""

import pytest
from moi import RawClient, ErrNilRequest
from tests.test_helpers import (
    get_test_client,
    random_name,
    create_test_catalog,
    create_test_database,
    create_test_table,
)


class TestCatalogLiveCRUD:
    """Test Catalog CRUD operations with live backend."""

    def test_catalog_live_crud(self):
        """Test complete catalog CRUD flow."""
        client = get_test_client()
        
        # Create
        create_req = {"name": random_name("sdk-catalog-")}
        create_resp = client.create_catalog(create_req)
        assert create_resp is not None
        assert create_resp["id"] != 0
        catalog_id = create_resp["id"]
        
        try:
            # Get
            info_resp = client.get_catalog({"id": catalog_id})
            assert info_resp is not None
            assert info_resp["name"] == create_req["name"]
            
            # Update
            updated_name = random_name("sdk-catalog-updated-")
            client.update_catalog({
                "id": catalog_id,
                "name": updated_name,
            })
            
            # Verify update
            info_resp = client.get_catalog({"id": catalog_id})
            assert info_resp["name"] == updated_name
            
            # List
            list_resp = client.list_catalogs()
            assert list_resp is not None
            
            # Get tree
            tree_resp = client.get_catalog_tree()
            assert tree_resp is not None
            
            # Get ref list
            ref_resp = client.get_catalog_ref_list({"id": catalog_id})
            assert ref_resp is not None
            
            # Delete
            client.delete_catalog({"id": catalog_id})
            
        except Exception:
            # Cleanup on error
            try:
                client.delete_catalog({"id": catalog_id})
            except Exception:
                pass
            raise


class TestCatalogNilRequestErrors:
    """Test that nil request errors are raised correctly."""

    def test_create_catalog_nil_request(self):
        """Test CreateCatalog with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.create_catalog(None)

    def test_delete_catalog_nil_request(self):
        """Test DeleteCatalog with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.delete_catalog(None)

    def test_update_catalog_nil_request(self):
        """Test UpdateCatalog with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.update_catalog(None)

    def test_get_catalog_nil_request(self):
        """Test GetCatalog with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_catalog(None)

    def test_get_catalog_ref_list_nil_request(self):
        """Test GetCatalogRefList with nil request."""
        client = RawClient("http://example.com", "test-key")
        with pytest.raises(ErrNilRequest):
            client.get_catalog_ref_list(None)


class TestCatalogNameExists:
    """Test catalog name existence validation."""

    def test_catalog_name_exists(self):
        """Test that creating a catalog with duplicate name fails."""
        client = get_test_client()
        
        catalog_name = random_name("sdk-catalog-")
        create_req = {
            "name": catalog_name,
            "description": "test catalog",
        }
        create_resp = client.create_catalog(create_req)
        assert create_resp is not None
        catalog_id = create_resp["id"]
        
        try:
            # Try to create another catalog with the same name
            try:
                client.create_catalog(create_req)
                assert False, "Should have raised an error for duplicate name"
            except Exception as e:
                # Expected error
                assert e is not None
        finally:
            # Cleanup
            try:
                client.delete_catalog({"id": catalog_id})
            except Exception:
                pass


class TestCatalogInvalidName:
    """Test catalog name validation."""

    def test_catalog_invalid_name(self):
        """Test that invalid catalog names are rejected."""
        client = get_test_client()
        
        test_cases = [
            ("TooLong", "a" * 300),
            ("SpecialChars", '"aa\''),
            ("Empty", ""),
        ]
        
        for name, catalog_name in test_cases:
            with pytest.raises(Exception):
                client.create_catalog({
                    "name": catalog_name,
                    "description": "test",
                })


class TestCatalogIDNotExists:
    """Test operations on non-existent catalog IDs."""

    def test_catalog_id_not_exists(self):
        """Test operations on non-existent catalog."""
        client = get_test_client()
        
        non_existent_id = 999999999
        
        # Try to get non-existent catalog
        with pytest.raises(Exception):
            client.get_catalog({"id": non_existent_id})
        
        # Try to update non-existent catalog
        with pytest.raises(Exception):
            client.update_catalog({
                "id": non_existent_id,
                "name": random_name("test-"),
            })
        
        # Try to delete non-existent catalog
        with pytest.raises(Exception):
            client.delete_catalog({"id": non_existent_id})


class TestCatalogTreeWithDatabaseAndTable:
    """Test catalog tree with database and table."""

    def test_catalog_tree_with_database_and_table(self):
        """Test that catalog tree includes created database and table."""
        client = get_test_client()
        
        # Create catalog
        catalog_id, mark_catalog_deleted = create_test_catalog(client)
        
        try:
            # Create database
            database_id, mark_database_deleted = create_test_database(client, catalog_id)
            
            try:
                # Create table
                table_id, mark_table_deleted = create_test_table(client, database_id)
                
                try:
                    # Get catalog tree
                    tree_resp = client.get_catalog_tree()
                    assert tree_resp is not None
                    assert len(tree_resp.get("tree", [])) > 0
                    
                    # Find our catalog in the tree
                    catalog_id_str = str(catalog_id)
                    database_id_str = str(database_id)
                    table_id_str = str(table_id)
                    
                    found_catalog = False
                    found_database = False
                    found_table = False
                    
                    for catalog_node in tree_resp["tree"]:
                        if catalog_node["id"] == catalog_id_str:
                            found_catalog = True
                            
                            # Check for database
                            for db_node in catalog_node.get("node_list", []):
                                if db_node["id"] == database_id_str:
                                    found_database = True
                                    
                                    # Check for table
                                    for table_node in db_node.get("node_list", []):
                                        if table_node["id"] == table_id_str:
                                            found_table = True
                                            break
                                    break
                            break
                    
                    assert found_catalog, "catalog should be found in tree"
                    assert found_database, "database should be found in tree"
                    assert found_table, "table should be found in tree"
                    
                finally:
                    mark_table_deleted()
            finally:
                mark_database_deleted()
        finally:
            mark_catalog_deleted()

