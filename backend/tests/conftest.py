import pytest


@pytest.fixture
def mock_redis():
    """In-memory dict simulating Redis for cache tests."""
    return {}


@pytest.fixture
def tenant_a_context():
    """Standard test context for tenant-a."""
    return {"tenant_id": "tenant-a", "property_id": "prop-001"}


@pytest.fixture
def tenant_b_context():
    """Standard test context for tenant-b."""
    return {"tenant_id": "tenant-b", "property_id": "prop-001"}
