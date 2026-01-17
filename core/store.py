import fastapi
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import SessionLocal
from .models import Category, Product
from .store_schema import CategoryCreate, CategoryOut
from fastapi import APIRouter,status,HTTPException,Depends, BackgroundTasks
from typing import List





router = APIRouter()


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
        
# ✅ Public
@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.post("/categories", status_code=status.HTTP_201_CREATED, response_model=CategoryOut)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
        
