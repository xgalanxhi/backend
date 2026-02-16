# Todo API Backend

Python FastAPI backend for the Todo Application.

## Features

- JWT-based authentication
- CRUD operations for todos
- Filter todos (all/active/completed)
- CORS enabled for frontend integration
- RESTful API design

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Testing

#### Option 1: Run tests with Docker Compose (Recommended)

This runs tests in an isolated environment with PostgreSQL:

```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

#### Option 2: Run tests locally

1. Ensure PostgreSQL is running (e.g., via `docker-compose up db`)

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Run tests:
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/todo_test
pytest
```

4. Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

#### CI/CD Testing

Tests are automatically run in the CloudBees Unify pipeline before building and deploying:
- `.cloudbees/workflows/test.yaml` - Standalone test workflow
- `.cloudbees/workflows/build-test-push.yaml` - Build workflow with integrated tests

### Docker

Build and run with Docker:

```bash
docker build -t todo-api .
docker run -p 8000:8000 todo-api
```

Or use docker-compose:

```bash
docker-compose up -d
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Default Credentials

- Username: `admin`
- Password: `admin123`

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout

### Todos
- `GET /api/todos` - Get all todos (supports ?filter=active|completed)
- `POST /api/todos` - Create a new todo
- `GET /api/todos/{id}` - Get a specific todo
- `PUT /api/todos/{id}` - Update a todo
- `DELETE /api/todos/{id}` - Delete a todo

## Environment Variables

- `SECRET_KEY` - JWT secret key (change in production)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `DATABASE_URL` - Postgres connection string, e.g. `postgresql://postgres:postgres@db:5432/todo`

## Notes

- Uses PostgreSQL for data persistence
- Database schema is initialized automatically on startup
- Database connections are created per-request (no connection pooling)
- Update SECRET_KEY in production
