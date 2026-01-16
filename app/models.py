from sqlalchemy import Column, Integer, String, Float,Boolean,DateTime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)

    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)