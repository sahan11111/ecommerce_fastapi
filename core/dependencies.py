from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from .models import User
from.database import engine, SessionLocal, Base


from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

security=HTTPBearer()
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

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts user from JWT token.
    Acts like Django's request.user
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id: int | None = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


