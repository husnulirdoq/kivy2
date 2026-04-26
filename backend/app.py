from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, Base, engine, get_db
from models import User, Task

app = FastAPI(title="Wellbeing Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

class TaskCreate(BaseModel):
    text: str

class TaskResponse(BaseModel):
    id: int
    text: str
    completed: bool
    
    class Config:
        from_attributes = True

@app.get("/")
def read_root():
    return {"message": "Wellbeing Backend API"}

@app.post("/login")
def login(token: str, db: Session = Depends(get_db)):
    """Temporary: bypass Firebase verification for testing"""
    firebase_uid = token[:20]  # Use token prefix as user ID for now
    email = "test@test.com"
    
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        user = User(firebase_uid=firebase_uid, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return {"user_id": user.id, "firebase_uid": firebase_uid, "email": email}

@app.get("/tasks")
def get_tasks(token: str, db: Session = Depends(get_db)):
    """Get tasks"""
    firebase_uid = token[:20]
    tasks = db.query(Task).filter(Task.firebase_uid == firebase_uid).all()
    return {"tasks": tasks}

@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, token: str, db: Session = Depends(get_db)):
    """Create task"""
    firebase_uid = token[:20]
    db_task = Task(text=task.text, firebase_uid=firebase_uid)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, token: str, db: Session = Depends(get_db)):
    """Delete task"""
    firebase_uid = token[:20]
    task = db.query(Task).filter(Task.id == task_id, Task.firebase_uid == firebase_uid).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskCreate, token: str, db: Session = Depends(get_db)):
    """Update task"""
    firebase_uid = token[:20]
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
