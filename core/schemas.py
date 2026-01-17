# app/schemas/user.py
from pydantic import BaseModel, EmailStr, field_validator,Field


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if v != info.data.get("password"):
            raise ValueError("Passwords do not match")
        return v
    
    
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True
        
class UserLogin(BaseModel):
    username: str
    password: str
    
    
class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
    
class ResetPasswordOTP(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=6)
    new_password: str = Field(min_length=8)