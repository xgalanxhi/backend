import pytest
from unittest.mock import patch


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Todo API is running"


def test_login_success(client, mock_db_connection):
    """Test successful login."""
    # Mock the database to return a valid user
    mock_cursor = mock_db_connection.execute.return_value
    mock_cursor.fetchone.return_value = {
        "username": "admin",
        "password": "admin123"
    }

    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client, mock_db_connection):
    """Test login with invalid credentials."""
    # Mock the database to return a user with different password
    mock_cursor = mock_db_connection.execute.return_value
    mock_cursor.fetchone.return_value = {
        "username": "admin",
        "password": "admin123"
    }

    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_user_not_found(client, mock_db_connection):
    """Test login with non-existent user."""
    # Mock the database to return None (user not found)
    mock_cursor = mock_db_connection.execute.return_value
    mock_cursor.fetchone.return_value = None

    response = client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "password"}
    )
    assert response.status_code == 401


def test_get_todos_unauthorized(client):
    """Test getting todos without authentication."""
    response = client.get("/api/todos")
    assert response.status_code == 403


def test_get_todos_authorized(client, auth_token, mock_db_connection):
    """Test getting todos with valid authentication."""
    # Mock the database responses
    mock_cursor = mock_db_connection.execute.return_value

    # First call: get user by username
    # Second call: get todos
    mock_cursor.fetchone.side_effect = [
        {"id": "1", "username": "admin", "password": "admin123"},  # User lookup
    ]
    mock_cursor.fetchall.return_value = [
        {
            "id": "todo-1",
            "title": "Test Todo",
            "description": "Test description",
            "completed": False,
            "priority": None,
            "due_date": None,
            "created_at": "2026-01-01T00:00:00Z",
            "user_id": "1"
        }
    ]

    response = client.get(
        "/api/todos",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Test Todo"


def test_create_todo(client, auth_token, mock_db_connection):
    """Test creating a new todo."""
    # Mock the database responses
    mock_cursor = mock_db_connection.execute.return_value

    # Mock user lookup
    mock_cursor.fetchone.return_value = {
        "id": "1",
        "username": "admin",
        "password": "admin123"
    }

    todo_data = {
        "title": "Test Todo",
        "description": "This is a test todo",
    }

    response = client.post(
        "/api/todos",
        json=todo_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == todo_data["title"]
    assert data["description"] == todo_data["description"]
    assert "id" in data
    assert "created_at" in data


def test_update_todo(client, auth_token, mock_db_connection):
    """Test updating an existing todo."""
    # Mock the database responses
    mock_cursor = mock_db_connection.execute.return_value

    # Mock user lookup and todo fetch for each request
    mock_cursor.fetchone.side_effect = [
        {"id": "1", "username": "admin", "password": "admin123"},  # User for update
        {  # Existing todo
            "id": "todo-1",
            "title": "Original Title",
            "description": None,
            "completed": False,
            "priority": None,
            "due_date": None,
            "created_at": "2026-01-01T00:00:00Z",
            "user_id": "1"
        }
    ]

    update_data = {
        "title": "Updated Title",
        "description": "Updated description",
        "completed": True
    }

    response = client.put(
        "/api/todos/todo-1",
        json=update_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["completed"] == update_data["completed"]


def test_delete_todo(client, auth_token, mock_db_connection):
    """Test deleting a todo."""
    # Mock the database responses
    mock_cursor = mock_db_connection.execute.return_value

    # Mock user lookup and todo fetch
    mock_cursor.fetchone.side_effect = [
        {"id": "1", "username": "admin", "password": "admin123"},  # User
        {  # Existing todo
            "id": "todo-1",
            "title": "To be deleted",
            "description": None,
            "completed": False,
            "priority": None,
            "due_date": None,
            "created_at": "2026-01-01T00:00:00Z",
            "user_id": "1"
        }
    ]

    response = client.delete(
        "/api/todos/todo-1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_get_todos_with_filter_active(client, auth_token, mock_db_connection):
    """Test getting active todos only."""
    # Mock the database responses
    mock_cursor = mock_db_connection.execute.return_value

    mock_cursor.fetchone.return_value = {
        "id": "1",
        "username": "admin",
        "password": "admin123"
    }
    mock_cursor.fetchall.return_value = [
        {
            "id": "todo-1",
            "title": "Active Todo",
            "description": None,
            "completed": False,
            "priority": None,
            "due_date": None,
            "created_at": "2026-01-01T00:00:00Z",
            "user_id": "1"
        }
    ]

    response = client.get(
        "/api/todos?filter=active",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Verify all returned todos are not completed
    for todo in data:
        assert todo["completed"] == False


def test_get_todos_with_filter_completed(client, auth_token, mock_db_connection):
    """Test getting completed todos only."""
    # Mock the database responses
    mock_cursor = mock_db_connection.execute.return_value

    mock_cursor.fetchone.return_value = {
        "id": "1",
        "username": "admin",
        "password": "admin123"
    }
    mock_cursor.fetchall.return_value = [
        {
            "id": "todo-2",
            "title": "Completed Todo",
            "description": None,
            "completed": True,
            "priority": None,
            "due_date": None,
            "created_at": "2026-01-01T00:00:00Z",
            "user_id": "1"
        }
    ]

    response = client.get(
        "/api/todos?filter=completed",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Verify all returned todos are completed
    for todo in data:
        assert todo["completed"] == True
