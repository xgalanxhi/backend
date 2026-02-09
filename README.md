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

- Currently uses in-memory storage
- For production, integrate with a database (PostgreSQL, MongoDB, etc.)
- Update SECRET_KEY in production
