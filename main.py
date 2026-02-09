from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import os
import time
import jwt
import uuid
import psycopg
from psycopg.rows import dict_row

app = FastAPI(title="Todo API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required (e.g. postgresql://user:pass@host:5432/db)")

security = HTTPBearer()


@app.exception_handler(psycopg.OperationalError)
def psycopg_operational_error_handler(
    request: Request, exc: psycopg.OperationalError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database unavailable; please retry"},
    )


def get_db_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def wait_for_db(max_seconds: int = 60) -> None:
    start = time.monotonic()
    delay = 1.0
    last_err: Exception | None = None

    while time.monotonic() - start < max_seconds:
        try:
            conn = get_db_connection()
            conn.close()
            return
        except psycopg.OperationalError as err:
            last_err = err
            print(f"DB not ready yet ({err}); retrying in {delay:.1f}s")
            time.sleep(delay)
            delay = min(5.0, delay * 1.5)

    raise RuntimeError(f"Database not reachable after {max_seconds}s") from last_err


def init_db() -> None:
    wait_for_db(max_seconds=int(os.getenv("DB_CONNECT_MAX_SECONDS", "60")))

    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              username TEXT NOT NULL UNIQUE,
              password TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              description TEXT,
              completed BOOLEAN NOT NULL,
              created_at TEXT NOT NULL,
              user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # Seed default user if missing
        existing = conn.execute(
            "SELECT id FROM users WHERE username = %s",
            ("admin",),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO users (id, username, password) VALUES (%s, %s, %s)",
                ("1", "admin", "admin123"),
            )
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def on_startup():
    init_db()


def get_user_row(conn: psycopg.Connection, username: str) -> dict:
    row = conn.execute(
        "SELECT id, username, password FROM users WHERE username = %s",
        (username,),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return row

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: str
    user_id: str

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# API endpoints
@app.get("/")
def read_root():
    return {"message": "Todo API is running"}

@app.post("/api/auth/login", response_model=Token)
def login(user: User):
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT username, password FROM users WHERE username = %s",
            (user.username,),
        ).fetchone()
        if row is None or row["password"] != user.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        conn.close()

@app.post("/api/auth/logout")
def logout(username: str = Depends(verify_token)):
    return {"message": "Successfully logged out"}

@app.get("/api/todos", response_model=List[Todo])
def get_todos(
    filter: Optional[str] = None,
    username: str = Depends(verify_token)
):
    conn = get_db_connection()
    try:
        user_row = get_user_row(conn, username)
        user_id = user_row["id"]

        where = "WHERE user_id = %s"
        params: list = [user_id]
        if filter == "active":
            where += " AND completed = false"
        elif filter == "completed":
            where += " AND completed = true"

        rows = conn.execute(
            f"SELECT id, title, description, completed, created_at, user_id FROM todos {where} ORDER BY created_at DESC",
            tuple(params),
        ).fetchall()

        return [
            {
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "completed": bool(r["completed"]),
                "created_at": r["created_at"],
                "user_id": r["user_id"],
            }
            for r in rows
        ]
    finally:
        conn.close()

@app.post("/api/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    username: str = Depends(verify_token)
):
    conn = get_db_connection()
    try:
        user_row = get_user_row(conn, username)
        user_id = user_row["id"]
        todo_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        conn.execute(
            """
            INSERT INTO todos (id, title, description, completed, created_at, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (todo_id, todo.title, todo.description, False, created_at, user_id),
        )
        conn.commit()

        return {
            "id": todo_id,
            "title": todo.title,
            "description": todo.description,
            "completed": False,
            "created_at": created_at,
            "user_id": user_id,
        }
    finally:
        conn.close()

@app.get("/api/todos/{todo_id}", response_model=Todo)
def get_todo(
    todo_id: str,
    username: str = Depends(verify_token)
):
    conn = get_db_connection()
    try:
        user_row = get_user_row(conn, username)
        user_id = user_row["id"]

        row = conn.execute(
            "SELECT id, title, description, completed, created_at, user_id FROM todos WHERE id = %s",
            (todo_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access forbidden")

        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "user_id": row["user_id"],
        }
    finally:
        conn.close()

@app.put("/api/todos/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    username: str = Depends(verify_token)
):
    conn = get_db_connection()
    try:
        user_row = get_user_row(conn, username)
        user_id = user_row["id"]

        existing = conn.execute(
            "SELECT id, user_id FROM todos WHERE id = %s",
            (todo_id,),
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        if existing["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access forbidden")

        fields = []
        params: list = []
        if todo_update.title is not None:
            fields.append("title = %s")
            params.append(todo_update.title)
        if todo_update.description is not None:
            fields.append("description = %s")
            params.append(todo_update.description)
        if todo_update.completed is not None:
            fields.append("completed = %s")
            params.append(bool(todo_update.completed))

        if fields:
            params.append(todo_id)
            conn.execute(
                f"UPDATE todos SET {', '.join(fields)} WHERE id = %s",
                tuple(params),
            )
            conn.commit()

        row = conn.execute(
            "SELECT id, title, description, completed, created_at, user_id FROM todos WHERE id = %s",
            (todo_id,),
        ).fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "user_id": row["user_id"],
        }
    finally:
        conn.close()

@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: str,
    username: str = Depends(verify_token)
):
    conn = get_db_connection()
    try:
        user_row = get_user_row(conn, username)
        user_id = user_row["id"]

        row = conn.execute(
            "SELECT id, user_id FROM todos WHERE id = %s",
            (todo_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access forbidden")

        conn.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
        conn.commit()
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
