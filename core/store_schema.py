from decimal import Decimal
from pydantic import BaseModel
from datetime import datetime


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

