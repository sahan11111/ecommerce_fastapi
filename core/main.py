from datetime import datetime
import fastapi
import jwt
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from .models import Customer, User
from .schemas import CustomerCreate, ForgotPasswordRequest, OTPVerify, ResetPasswordOTP, UserCreate, UserLogin,UserOut
from .security import hash_password,verify_password
from fastapi import APIRouter,status,HTTPException,Depends, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from.database import engine, SessionLocal, Base
from datetime import datetime, timedelta
from .email_utils import send_otp_email
from .otp_utils import generate_otp, otp_expiry


from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


security=HTTPBearer()
app = APIRouter()
SECRET_KEY=os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)
ALGORITHM = os.getenv("ALGORITHM")


# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)



# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/users/register", status_code=201)
def register_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # check existing user
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    otp = generate_otp()

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        otp_code=otp,
        otp_expires_at=otp_expiry(),
        is_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    background_tasks.add_task(send_otp_email, user.email, user.username, otp)

    return {"message": "OTP sent to your email"}

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

    # ❌ User not found or password incorrect
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # ❌ User exists but NOT verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please verify OTP first."
        )

    # ✅ User verified → allow login
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
    



@app.put("/users/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Account already verified"}

    if user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None

    db.commit()
    db.refresh(user)

    return {"message": "Account verified successfully 🎉"}


@app.post("/users/forgot-password", status_code=200)
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()

    user.otp_code = otp
    user.otp_expires_at = otp_expiry()
    db.commit()

    background_tasks.add_task(
        send_otp_email,
        user.email,
        user.username,
        otp
    )

    return {"message": "OTP sent to your email for password reset"}
   

@app.post("/users/reset-password", status_code=200)
def reset_password(
    data: ResetPasswordOTP,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.otp_code or not user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP not requested")

    if user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    # ✅ Hash new password (same as registration)
    user.hashed_password = hash_password(data.new_password)

    # Clear OTP
    user.otp_code = None
    user.otp_expires_at = None

    db.commit()

    return {"message": "Password reset successfully 🎉"}


@app.post("/")
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),  # 👈 JWT user
):
    # Prevent duplicate customer profile
    if current_user.customer:
        raise HTTPException(
            status_code=400,
            detail="Customer profile already exists"
        )

    customer = Customer(
        first_name=customer_in.first_name,
        middle_name=customer_in.middle_name,
        last_name=customer_in.last_name,
        shipping_address=customer_in.shipping_address,
        user_id=current_user.id,  # 🔥 AUTO-ASSIGNED HERE
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer
