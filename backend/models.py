from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="owner")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    completed = Column(Boolean, default=False)
    firebase_uid = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="tasks")
