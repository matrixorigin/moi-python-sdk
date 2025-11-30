"""Test helpers for MOI Python SDK tests."""

import os
import time
import pytest
from moi import RawClient


# Test configuration from environment variables
# Note: This is a development environment API key, safe to commit to repository
TEST_BASE_URL = os.getenv("MOI_BASE_URL", "https://freetier-01.cn-hangzhou.cluster.cn-dev.matrixone.tech")
TEST_API_KEY = os.getenv("MOI_API_KEY", "JeuCjV_8320G5ACwgPDHo0tJAdkESCrMPnxteLJri8IHb72dPySWkhN6uFWw41-W7qpdH4w3QCG8pJmf")


def get_test_client():
    """Get a test client from environment variables."""
    if not TEST_API_KEY:
        pytest.skip("MOI_API_KEY environment variable not set")
    return RawClient(TEST_BASE_URL, TEST_API_KEY)


def random_name(prefix: str = "test-") -> str:
    """Generate a random name for testing using timestamp."""
    return f"{prefix}{int(time.time() * 1_000_000_000)}"


def random_user_name() -> str:
    """Generate a random user name for testing."""
    return f"sdkuser{int(time.time() * 1_000_000_000)}"


def create_test_catalog(client: RawClient):
    """Create a test catalog and return its ID and cleanup function."""
    resp = client.create_catalog({"name": random_name("sdk-cat-")})
    catalog_id = resp["id"]
    
    def cleanup():
        try:
            client.delete_catalog({"id": catalog_id})
        except Exception:
            pass
    
    return catalog_id, cleanup


def create_test_database(client: RawClient, catalog_id: int):
    """Create a test database and return its ID and cleanup function."""
    resp = client.create_database({
        "name": random_name("sdk-db-"),
        "catalog_id": catalog_id,
    })
    database_id = resp["id"]
    
    def cleanup():
        try:
            client.delete_database({"id": database_id})
        except Exception:
            pass
    
    return database_id, cleanup


def create_test_volume(client: RawClient, database_id: int):
    """Create a test volume and return its ID and cleanup function."""
    resp = client.create_volume({
        "name": random_name("sdk-volume-"),
        "database_id": database_id,
        "description": "sdk helper volume",
    })
    volume_id = resp["id"]
    
    def cleanup():
        try:
            client.delete_volume({"id": volume_id})
        except Exception:
            pass
    
    return volume_id, cleanup


def create_test_table(client: RawClient, database_id: int):
    """Create a test table and return its ID and cleanup function."""
    table_name = random_name("sdk-table-")
    columns = [
        {"name": "id", "type": "int", "is_pk": True},
        {"name": "name", "type": "varchar(255)"},
    ]
    resp = client.create_table({
        "database_id": database_id,
        "name": table_name,
        "columns": columns,
        "comment": "sdk test table",
    })
    table_id = resp["id"]
    
    def cleanup():
        try:
            client.delete_table({"id": table_id})
        except Exception:
            pass
    
    return table_id, cleanup


def create_test_role(client: RawClient, priv_codes: list):
    """Create a test role and return its ID and cleanup function.
    
    Args:
        priv_codes: List of privilege codes (e.g., ['DC2'] for QueryCatalog)
    """
    role_name = f"sdk_role_{int(time.time() * 1_000_000_000)}"
    resp = client.create_role({
        "name": role_name,
        "authority_code_list": priv_codes,
        "obj_authority_code_list": [],
    })
    role_id = resp["id"]
    
    def cleanup():
        try:
            client.delete_role({"id": role_id})
        except Exception:
            pass
    
    return role_id, cleanup

