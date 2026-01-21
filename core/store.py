from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload
from typing import List

from core.dependencies import get_current_user,superuser_required

from .database import SessionLocal
from .models import Cart, CartItem, Category, Product, User
from .store_schema import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    CategoryCreate,
    CategoryOut,
    ProductCreate,
    ProductUpdate,
    ProductOut
)

router = APIRouter()


# ---------- DB Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- CATEGORY ----------
@router.get("/categories", response_model=List[CategoryOut])
def read_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryOut
)
def create_category(category: CategoryCreate, db: Session = Depends(get_db),current_user: User = Depends(superuser_required)):
    db_category = Category(**category.model_dump())
    db.add(db_category,current_user)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/categories/{category_id}", response_model=CategoryOut)
def read_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category



@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
):
    category=db.query(Category).filter(Category.id==category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category_id=db.query(Category).filter(Category.id==category_id).first()
    if not category_id:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category_id)
    db.commit()


# ---------- PRODUCT ----------
@router.get("/products", response_model=List[ProductOut])
def read_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.post(
    "/products",
    status_code=status.HTTP_201_CREATED,
    response_model=ProductOut
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    db_product = Product(
        name=product.name,
        stock_qty=product.stock_qty,   
        price=product.price,
        category_id=product.category_id,
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product



@router.get("/products/{product_id}", response_model=ProductOut)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product



@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

