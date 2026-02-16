import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Set a fake DATABASE_URL to prevent startup errors
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ALGORITHM"] = "HS256"


@pytest.fixture
def mock_db_connection():
    """Create a mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Mock the execute method to return the cursor
    mock_conn.execute.return_value = mock_cursor
    mock_conn.commit.return_value = None
    mock_conn.close.return_value = None

    return mock_conn


@pytest.fixture
def client(mock_db_connection):
    """Create a test client with mocked database."""
    # Patch the database functions before importing the app
    with patch('main.get_db_connection', return_value=mock_db_connection):
        with patch('main.init_db'):  # Skip database initialization
            # Import here to ensure patches are applied
            from main import app

            with TestClient(app) as test_client:
                yield test_client


@pytest.fixture
def auth_token():
    """Create a test JWT token without database interaction."""
    from main import create_access_token
    return create_access_token(data={"sub": "admin"})
