from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import uuid

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
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# In-memory storage (use database in production)
users_db = {
    "admin": {"username": "admin", "password": "admin123", "id": "1"}
}
todos_db = {}

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
    if user.username not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    db_user = users_db[user.username]
    if db_user["password"] != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/logout")
def logout(username: str = Depends(verify_token)):
    return {"message": "Successfully logged out"}

@app.get("/api/todos", response_model=List[Todo])
def get_todos(
    filter: Optional[str] = None,
    username: str = Depends(verify_token)
):
    user_id = users_db[username]["id"]
    user_todos = [todo for todo in todos_db.values() if todo["user_id"] == user_id]
    
    if filter == "active":
        user_todos = [todo for todo in user_todos if not todo["completed"]]
    elif filter == "completed":
        user_todos = [todo for todo in user_todos if todo["completed"]]
    
    return user_todos

@app.post("/api/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    username: str = Depends(verify_token)
):
    user_id = users_db[username]["id"]
    todo_id = str(uuid.uuid4())
    
    new_todo = {
        "id": todo_id,
        "title": todo.title,
        "description": todo.description,
        "completed": False,
        "created_at": datetime.utcnow().isoformat(),
        "user_id": user_id
    }
    
    todos_db[todo_id] = new_todo
    return new_todo

@app.get("/api/todos/{todo_id}", response_model=Todo)
def get_todo(
    todo_id: str,
    username: str = Depends(verify_token)
):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_db[todo_id]
    user_id = users_db[username]["id"]
    
    if todo["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    return todo

@app.put("/api/todos/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    username: str = Depends(verify_token)
):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_db[todo_id]
    user_id = users_db[username]["id"]
    
    if todo["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    if todo_update.title is not None:
        todo["title"] = todo_update.title
    if todo_update.description is not None:
        todo["description"] = todo_update.description
    if todo_update.completed is not None:
        todo["completed"] = todo_update.completed
    
    return todo

@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: str,
    username: str = Depends(verify_token)
):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_db[todo_id]
    user_id = users_db[username]["id"]
    
    if todo["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    del todos_db[todo_id]
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
