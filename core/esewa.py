# payments/esewa.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import base64
import hmac
import hashlib
import os
import logging
import requests

from .models import Order, OrderItem, OrderStatusEnum, PaymentModeEnum
from .dependencies import get_db

router = APIRouter(prefix="/payments/esewa", tags=["eSewa Payments"])
logger = logging.getLogger(__name__)

# ---------------------------
# Environment variables
# ---------------------------
ESEWA_SECRET_KEY = os.getenv("ESEWA_SECRET_KEY", "your_test_secret")
ESEWA_MERCHANT_CODE = os.getenv("ESEWA_MERCHANT_CODE", "EPAYTEST")
ESEWA_PAYMENT_CALLBACK_URL = os.getenv("ESEWA_PAYMENT_CALLBACK_URL", "http://localhost:8000/payments/esewa/callback")
ESEWA_VERIFY_URL = "https://rc-epay.esewa.com.np/api/epay/verify"  # UAT test URL

# ---------------------------
# Pydantic Schemas
# ---------------------------
class EsewaPaymentRequest(BaseModel):
    order_id: int
    tax_amount: Decimal = 0
    product_service_charge: Decimal = 0
    product_delivery_charge: Decimal = 0

# ---------------------------
# Utility functions
# ---------------------------
def generate_transaction_uuid() -> str:
    return str(uuid.uuid4())

def build_signed_string_from_fields(fields: list, data: dict) -> str:
    return ",".join(f"{field}={data[field]}" for field in fields)

def generate_esewa_signature(secret_key: str, message: str) -> str:
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

# ---------------------------
# Backend verification function
# ---------------------------
def verify_esewa_payment(order: Order) -> bool:
    """
    Verify payment with eSewa backend API.
    """
    total_amount = sum([item.price * item.qty for item in order.items])
    payload = {
        "amt": str(total_amount),
        "scd": ESEWA_MERCHANT_CODE,
        "pid": order.transaction_uuid,
        "txAmt": "0",
        "tAmt": str(total_amount),
        "psc": "0",
        "pdc": "0"
    }

    response = requests.post(ESEWA_VERIFY_URL, data=payload)
    logger.info(f"eSewa verify response: {response.text}")
    return response.status_code == 200 and "Success" in response.text

# ---------------------------
# Endpoint: Initiate Payment (backend-only)
# ---------------------------
@router.post("/initiate")
def initiate_esewa_payment(payload: EsewaPaymentRequest, db: Session = Depends(get_db)):
    # Fetch order
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="Only pending orders can be paid")

    # Calculate total amount
    total_amount = sum([item.price * item.qty for item in order.items])
    total_amount += payload.tax_amount + payload.product_service_charge + payload.product_delivery_charge

    # ---------------------------
    # Generate and store transaction UUID
    # ---------------------------
    transaction_uuid = generate_transaction_uuid()
    order.transaction_uuid = transaction_uuid
    db.commit()
    db.refresh(order)

    # Build signed string and signature
    signed_field_names = ["total_amount", "transaction_uuid", "product_code"]
    data_to_sign = {
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
        "product_code": ESEWA_MERCHANT_CODE
    }
    signed_string = build_signed_string_from_fields(signed_field_names, data_to_sign)
    signature = generate_esewa_signature(ESEWA_SECRET_KEY, signed_string)

    # Payload to send (frontend or backend processing)
    payment_payload = {
        "amount": total_amount,
        "tax_amount": payload.tax_amount,
        "product_service_charge": payload.product_service_charge,
        "product_delivery_charge": payload.product_delivery_charge,
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
        "product_code": ESEWA_MERCHANT_CODE,
        "success_url": ESEWA_PAYMENT_CALLBACK_URL,
        "failure_url": ESEWA_PAYMENT_CALLBACK_URL,
        "signed_field_names": ",".join(signed_field_names),
        "signature": signature
    }

    return payment_payload

# ---------------------------
# Endpoint: Pay & verify backend
# ---------------------------
@router.post("/pay-backend/{order_id}")
def pay_order_backend(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.is_paid:
        return {"message": "Order already paid"}

    # Verify with eSewa API (simulate success in UAT)
    success = verify_esewa_payment(order)
    if not success:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Mark order paid
    order.is_paid = True
    order.status = OrderStatusEnum.CONFIRM
    order.payment_mode = PaymentModeEnum.ESEWA
    db.commit()
    db.refresh(order)

    return {
        "message": "Order successfully paid via eSewa",
        "order_id": order.id,
        "status": order.status,
        "is_paid": order.is_paid
    }
