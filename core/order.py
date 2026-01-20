from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .models import (
    Order,
    OrderItem,
    Cart,
    CartItem,
    User,
)
from.database import engine, SessionLocal, Base
from .dependencies import get_current_user


router = APIRouter(prefix="/orders")
# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)



# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================
# Pydantic Schemas (Django Serializers Equivalent)
# =====================================================

# ---------- OrderItemSerializer ----------
class OrderItemSchema(BaseModel):
    id: int
    product_id: int
    qty: int
    price: Decimal

    class Config:
        from_attributes = True


# ---------- OrderSerializer ----------
class OrderSchema(BaseModel):
    id: int
    status: str
    payment_mode: str
    is_paid: bool
    delivery_address: Optional[str]
    placed_at: datetime
    items: List[OrderItemSchema]

    class Config:
        from_attributes = True


# ---------- PlaceOrderSerializer ----------
class PlaceOrderSchema(BaseModel):
    delivery_address: str = Field(..., max_length=255)


# ---------- CancelOrderSerializer ----------
class CancelOrderSchema(BaseModel):
    pass


# =====================================================
# Service Logic (DRF create() equivalent)
# =====================================================

def place_order_service(
    data: PlaceOrderSchema,
    db: Session,
    user: User,
):
    # Get customer profile
    customer = user.customer
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer profile not found"
        )

    # Get active cart items
    cart_items = (
        db.query(CartItem)
        .join(Cart)
        .filter(Cart.customer_id == customer.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # Create order
    order = Order(
        customer_id=customer.id,
        delivery_address=data.delivery_address,
    )
    db.add(order)
    db.flush()  # get order.id without commit

    # Create order items (price snapshot)
    order_items = [
        OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            qty=item.qty,
            price=item.product.price,
        )
        for item in cart_items
    ]

    db.bulk_save_objects(order_items)

    # Clear cart
    for item in cart_items:
        db.delete(item)

    db.commit()
    db.refresh(order)

    return order


# =====================================================
# API Routes
# =====================================================

# ---------- Place Order ----------
@router.post(
    "",
    response_model=OrderSchema,
    status_code=status.HTTP_201_CREATED
)
def place_order(
    data: PlaceOrderSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return place_order_service(data, db, current_user)


# ---------- Get My Orders ----------
@router.get("", response_model=List[OrderSchema])
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = current_user.customer
    if not customer:
        raise HTTPException(400, "Customer profile not found")

    return (
        db.query(Order)
        .filter(Order.customer_id == customer.id)
        .order_by(Order.placed_at.desc())
        .all()
    )


# ---------- Cancel Order ----------
@router.patch("/{order_id}/cancel", response_model=OrderSchema)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = current_user.customer

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.customer_id == customer.id
        )
        .first()
    )

    if not order:
        raise HTTPException(404, "Order not found")

    if order.status != "P":
        raise HTTPException(400, "Only pending orders can be cancelled")

    order.status = "C"
    db.commit()
    db.refresh(order)

    return order
