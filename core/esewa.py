# core/esewa.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import requests
import logging

from .models import Order, OrderStatusEnum, PaymentModeEnum
from .dependencies import get_db
import os

router = APIRouter(prefix="/payments/esewa", tags=["eSewa Payments"])
logger = logging.getLogger(__name__)

# ---------------------------
# eSewa UAT Credentials
# ---------------------------
ESEWA_MERCHANT_CODE = os.getenv("ESEWA_MERCHANT_CODE")
ESEWA_SECRET_KEY = os.getenv("ESEWA_SECRET_KEY")
ESEWA_CALLBACK_URL = os.getenv("ESEWA_PAYMENT_CALLBACK_URL")
ESEWA_UAT_VERIFY_URL = os.getenv("ESEWA_UAT_BASE_URL")

# ---------------------------
# Pydantic Schema
# ---------------------------
class EsewaPaymentRequest(BaseModel):
    order_id: int
    tax_amount: Decimal = 0
    product_service_charge: Decimal = 0
    product_delivery_charge: Decimal = 0

# ---------------------------
# Utility
# ---------------------------
def generate_transaction_uuid() -> str:
    return str(uuid.uuid4())

# ---------------------------
# Verify payment with eSewa UAT
# ---------------------------
def verify_esewa_payment(order: Order) -> bool:
    """
    Call eSewa UAT verification API to confirm payment.
    """
    if not order.transaction_uuid:
        raise HTTPException(status_code=400, detail="Order has no transaction UUID")

    total_amount = sum(item.price * item.qty for item in order.items)

    payload = {
        "amt": str(total_amount),
        "scd": ESEWA_MERCHANT_CODE,
        "pid": order.transaction_uuid,
        "txAmt": "0",
        "tAmt": str(total_amount),
        "psc": "0",
        "pdc": "0"
    }

    logger.info(f"Calling eSewa UAT verify API with payload: {payload}")
    response = requests.post(ESEWA_UAT_VERIFY_URL, data=payload)
    logger.info(f"eSewa UAT response: {response.text}")

    return response.status_code == 200 and "Success" in response.text

# ---------------------------
# Endpoint: Initiate payment
# ---------------------------
@router.post("/initiate")
def initiate_esewa_payment(payload: EsewaPaymentRequest, db: Session = Depends(get_db)):
    """
    Create transaction UUID for the order (required for eSewa payment)
    """
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="Only pending orders can be paid")

    total_amount = sum([item.price * item.qty for item in order.items])
    total_amount += payload.tax_amount + payload.product_service_charge + payload.product_delivery_charge

    # Generate and store transaction UUID
    order.transaction_uuid = generate_transaction_uuid()
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "transaction_uuid": order.transaction_uuid,
        "total_amount": total_amount,
        "tax_amount": payload.tax_amount,
        "product_service_charge": payload.product_service_charge,
        "product_delivery_charge": payload.product_delivery_charge,
        "success_url": ESEWA_CALLBACK_URL,
        "failure_url": ESEWA_CALLBACK_URL,
        "message": "Transaction UUID generated. Ready for backend payment verification."
    }

# ---------------------------
# Endpoint: Pay backend via real UAT
# ---------------------------
@router.post("/pay-backend/{order_id}")
def pay_order_backend(order_id: int, db: Session = Depends(get_db)):
    """
    Verify and pay an order using real eSewa UAT.
    Requires that a payment was actually made in eSewa UAT.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.is_paid:
        return {"message": "Order already paid", "order_id": order.id}
    if not getattr(order, "transaction_uuid", None):
        raise HTTPException(status_code=400, detail="Transaction UUID missing. Initiate payment first.")

    # Verify with eSewa UAT
    success = verify_esewa_payment(order)
    if not success:
        raise HTTPException(status_code=400, detail="Payment verification failed at eSewa UAT")

    # Mark order paid
    order.is_paid = True
    order.status = OrderStatusEnum.CONFIRM
    order.payment_mode = PaymentModeEnum.ESEWA
    db.commit()
    db.refresh(order)

    return {
        "message": "Order successfully paid via eSewa UAT",
        "order_id": order.id,
        "status": order.status,
        "is_paid": order.is_paid,
        "transaction_uuid": order.transaction_uuid
    }

# ---------------------------
# Endpoint: Simulated backend payment (for testing)
# ---------------------------
@router.post("/pay-esewa/{order_id}")
def pay_order_simulated(order_id: int, db: Session = Depends(get_db)):
    """
    Simulate full backend payment without calling eSewa.
    Useful for testing and backend-only workflow.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.is_paid:
        return {"message": "Order already paid", "order_id": order.id}

    # Generate transaction UUID
    order.transaction_uuid = generate_transaction_uuid()

    # Mark order paid
    order.is_paid = True
    order.status = OrderStatusEnum.CONFIRM
    order.payment_mode = PaymentModeEnum.ESEWA
    db.commit()
    db.refresh(order)

    total_amount = sum([item.price * item.qty for item in order.items])

    return {
        "message": "Order successfully paid via backend (simulation)",
        "order_id": order.id,
        "status": order.status,
        "is_paid": order.is_paid,
        "transaction_uuid": order.transaction_uuid,
        "total_amount": total_amount
    }