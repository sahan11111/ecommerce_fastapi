from decimal import Decimal
from pydantic import BaseModel, Field,conint
from datetime import datetime
from typing import List

# ---------- CATEGORY ----------

class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- PRODUCT ----------

class ProductBase(BaseModel):
    name: str
    stock_qty: int
    price: Decimal
    category_id: int



class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    stock_qty: int | None = None
    price: Decimal | None = None
    category_id: int | None = None



class ProductOut(ProductBase):
    id: int
    price_with_tax: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
        
# =========================
# CartItem Schemas
# =========================

class CartItemCreate(BaseModel):
    product_id: int
    qty: int = Field(..., gt=0)  # quantity must be > 0


class CartItemUpdate(BaseModel):
    qty: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    qty: int
    total_price: Decimal
    total_price_with_tax: Decimal

    class Config:
        from_attributes = True


# =========================
# Cart Schemas
# =========================

class CartResponse(BaseModel):
    id: int
    customer_id: int
    total_price: Decimal
    total_price_with_tax: Decimal
    created_at: datetime
    updated_at: datetime
    items: List[CartItemResponse]

