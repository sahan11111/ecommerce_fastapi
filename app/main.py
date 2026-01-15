import fastapi
from sqlalchemy.orm import Session
from .models import User
from .schemas import UserCreate,UserOut
from .security import hash_password
from fastapi import FastAPI,status,HTTPException,Depends
from typing import List
from sqlalchemy.orm import Session
from.database import engine, SessionLocal, Base
# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)
app = FastAPI()
# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Root endpoint for basic check
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI CRUD API!"}


@app.post(
    "/users/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

