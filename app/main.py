from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app import models
from app.cache import get_from_cache, set_in_cache, delete_from_cache

# Create FastAPI app
app = FastAPI(title="FastAPI Demo", description="A simple FastAPI application with PostgreSQL and Redis")

# Create database tables
@app.on_event("startup")
async def startup():
    engine = models.create_engine("postgresql://postgres:postgres@db:5432/fastapi_db")
    models.Base.metadata.create_all(bind=engine)

# User schemas
class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

# API endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Demo!"}

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(models.get_db)):
    # Check if user exists in cache
    cache_key = f"user:{user.username}"
    cached_user = get_from_cache(cache_key)
    if cached_user:
        return cached_user

    # Create new user
    db_user = models.User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Cache the new user
    user_response = {"id": db_user.id, "username": db_user.username, "email": db_user.email}
    set_in_cache(cache_key, user_response)
    
    return user_response

@app.get("/users/{username}", response_model=UserResponse)
async def get_user(username: str, db: Session = Depends(models.get_db)):
    # Try to get from cache first
    cache_key = f"user:{username}"
    cached_user = get_from_cache(cache_key)
    if cached_user:
        return cached_user

    # Get from database
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cache the user
    user_response = {"id": user.id, "username": user.username, "email": user.email}
    set_in_cache(cache_key, user_response)
    
    return user_response

@app.get("/users/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(models.get_db)):
    # Get all users from database
    users = db.query(models.User).all()
    return [{"id": user.id, "username": user.username, "email": user.email} for user in users] 