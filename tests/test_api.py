import pytest


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_login_success(client):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_get_todos_unauthorized(client):
    """Test getting todos without authentication."""
    response = client.get("/api/todos")
    assert response.status_code == 403


def test_get_todos_authorized(client, auth_token):
    """Test getting todos with valid authentication."""
    response = client.get(
        "/api/todos",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_todo(client, auth_token):
    """Test creating a new todo."""
    todo_data = {
        "title": "Test Todo",
        "description": "This is a test todo",
        "completed": False
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
    assert data["completed"] == todo_data["completed"]
    assert "id" in data


def test_update_todo(client, auth_token):
    """Test updating an existing todo."""
    # First create a todo
    create_response = client.post(
        "/api/todos",
        json={"title": "Original Title", "completed": False},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    todo_id = create_response.json()["id"]

    # Update the todo
    update_data = {
        "title": "Updated Title",
        "description": "Updated description",
        "completed": True
    }
    response = client.put(
        f"/api/todos/{todo_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["completed"] == update_data["completed"]


def test_delete_todo(client, auth_token):
    """Test deleting a todo."""
    # First create a todo
    create_response = client.post(
        "/api/todos",
        json={"title": "To be deleted", "completed": False},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    todo_id = create_response.json()["id"]

    # Delete the todo
    response = client.delete(
        f"/api/todos/{todo_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

    # Verify it's deleted
    get_response = client.get(
        f"/api/todos/{todo_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.status_code == 404
