from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import firebase_admin
from firebase_admin import credentials, auth
from database import SessionLocal, Base, engine, get_db
from models import User, Task

# Initialize Firebase (pakai google-services.json atau env)
try:
    firebase_admin.initialize_app()
except:
    pass

app = FastAPI(title="Wellbeing Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class TaskCreate(BaseModel):
    text: str

class TaskResponse(BaseModel):
    id: int
    text: str
    completed: bool
    
    class Config:
        from_attributes = True

# Verify Firebase token
def verify_token(token: str) -> str:
    try:
        decoded = auth.verify_id_token(token)
        return decoded['uid']
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
def read_root():
    return {"message": "Wellbeing Backend API"}

@app.post("/login")
def login(token: str, db: Session = Depends(get_db)):
    """Verify Firebase token dan create user jika belum ada"""
    try:
        decoded = auth.verify_id_token(token)
        firebase_uid = decoded['uid']
        email = decoded.get('email', '')
        
        # Check if user exists
        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not user:
            user = User(firebase_uid=firebase_uid, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return {"user_id": user.id, "firebase_uid": firebase_uid, "email": email}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/tasks")
def get_tasks(token: str, db: Session = Depends(get_db)):
    """Get all tasks untuk user"""
    firebase_uid = verify_token(token)
    tasks = db.query(Task).filter(Task.firebase_uid == firebase_uid).all()
    return {"tasks": tasks}

@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, token: str, db: Session = Depends(get_db)):
    """Create task baru"""
    firebase_uid = verify_token(token)
    db_task = Task(text=task.text, firebase_uid=firebase_uid)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, token: str, db: Session = Depends(get_db)):
    """Delete task"""
    firebase_uid = verify_token(token)
    task = db.query(Task).filter(Task.id == task_id, Task.firebase_uid == firebase_uid).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskCreate, token: str, db: Session = Depends(get_db)):
    """Update task"""
    firebase_uid = verify_token(token)
    db_task = db.query(Task).filter(Task.id == task_id, Task.firebase_uid == firebase_uid).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.text = task.text
    db.commit()
    db.refresh(db_task)
    return db_task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
