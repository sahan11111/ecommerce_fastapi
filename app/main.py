import fastapi
import jwt
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .models import User
from .schemas import UserCreate, UserLogin,UserOut
from .security import hash_password,verify_password
from fastapi import FastAPI,status,HTTPException,Depends
from typing import List
from sqlalchemy.orm import Session
from.database import engine, SessionLocal, Base
from datetime import datetime, timedelta

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)


security=HTTPBearer()
app = FastAPI()
SECRET_KEY="LMO123"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"





# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



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


@app.post("/user/login/", status_code=status.HTTP_200_OK)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == user_in.username).first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id
        }
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }
    
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return token


@app.post("/user/logout/", status_code=status.HTTP_200_OK)
def logout_user():
    return {"message": "Logout successful"}
    

    

