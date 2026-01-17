from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# SQLite database URL. The `check_same_thread=False` is crucial for SQLite
# when used with FastAPI's asynchronous nature to prevent concurrency issues.
SQLALCHEMY_DATABASE_URL = "sqlite:///./ecommerce.db"
# Create a SQLAlchemy engine
# echo=True will log all SQL statements, useful for debugging
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=True
)
# Configure a sessionmaker to create new session objects
# autocommit=False: Changes won't be automatically committed
# autoflush=False: Changes won't be automatically flushed before a query
# expire_on_commit=False: Prevents objects from expiring after commit, useful for re-using objects
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
# Declare a base class for SQLAlchemy models
Base = declarative_base()