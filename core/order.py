from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    Customer,
    Order,
    OrderItem,
    Cart,
    CartItem,
    OrderStatusEnum,
    PaymentModeEnum,
    User,
)
from.database import SessionLocal
from .dependencies import get_current_user


router = APIRouter(prefix="/orders")


# =====================================================
# Database Dependency
# =====================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================
# Pydantic Schemas
# =====================================================

class OrderItemSchema(BaseModel):
    id: int
    product_id: int
    qty: int
    price: Decimal

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    id: int
    status: str
    payment_mode: Optional[str]
    is_paid: bool
    delivery_address: Optional[str]
    placed_at: datetime
    items: List[OrderItemSchema]

    class Config:
        from_attributes = True


class PlaceOrderSchema(BaseModel):
    delivery_address: str = Field(..., max_length=255)


class PaymentRequestSchema(BaseModel):
    payment_mode: PaymentModeEnum


# =====================================================
# Service Logic
# =====================================================

def place_order_service(
    data: PlaceOrderSchema,
    db: Session,
    user: User,
):
    customer = user.customer
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )

    cart_items = (
        db.query(CartItem)
        .join(Cart)
        .filter(
            Cart.customer_id == customer.id,
            Cart.is_active == True
        )
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    try:
        order = Order(
            customer_id=customer.id,
            delivery_address=data.delivery_address,
            status="P",
            is_paid=False,
        )
        db.add(order)
        db.flush()  # get order.id

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

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order placement failed"
        )


# =====================================================
# API Routes
# =====================================================

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


@router.get("", response_model=List[OrderSchema])
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auto-create customer if missing
    customer = current_user.customer
    if not customer:
        customer = Customer(
            user_id=current_user.id,
            first_name=current_user.username,
            last_name="",
            shipping_address="Not set"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    orders = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == customer.id)
        .order_by(Order.placed_at.desc())
        .all()
    )

    return orders


@router.patch("/{order_id}/cancel", response_model=OrderSchema)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = current_user.customer
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )

    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(
            Order.id == order_id,
            Order.customer_id == customer.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status != "P":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be cancelled"
        )

    order.status = "C"
    db.commit()
    db.refresh(order)

    return order

@router.patch("/{order_id}/pay", response_model=OrderSchema)
def pay_order(
    order_id: int,
    data: PaymentRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = current_user.customer
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.customer_id == customer.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be paid"
        )

    if order.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already paid"
        )

    # ---- PAYMENT LOGIC ----
    order.payment_mode = data.payment_mode

    if data.payment_mode == PaymentModeEnum.CASH:
        # COD → not paid yet, but confirmed
        order.is_paid = False
        order.status = OrderStatusEnum.CONFIRM

    elif data.payment_mode == PaymentModeEnum.ESEWA:
        # Online payment → assume success
        order.is_paid = True
        order.status = OrderStatusEnum.CONFIRM

    db.commit()
    db.refresh(order)

    return order

@router.patch("/{order_id}/mark-paid", response_model=OrderSchema)
def mark_order_paid(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ⚠️ Ideally admin-only check here

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already marked as paid"
        )

    if order.payment_mode != PaymentModeEnum.CASH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only cash orders can be manually marked paid"
        )

    order.is_paid = True
    order.status = OrderStatusEnum.CONFIRM

    db.commit()
    db.refresh(order)

    return order
