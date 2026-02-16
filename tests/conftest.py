import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["DATABASE_URL"] = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/todo_test"
    )
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ALGORITHM"] = "HS256"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Import here to ensure env vars are set
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_token(client):
    """Get an authentication token for testing protected endpoints."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
