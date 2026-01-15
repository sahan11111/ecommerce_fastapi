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

@app.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[UserOut])
def list_users(skip: int = 0, limit: int = 100,db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users
