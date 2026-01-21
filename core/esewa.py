# esewa.py
import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal
from typing import List

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .dependencies import get_db, get_current_user
from .models import Order, OrderStatusEnum, OrderItem, PaymentModeEnum

router = APIRouter(prefix="/payments/esewa", tags=["eSewa Payments"])

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

def build_signed_string_from_fields(fields: List[str], data: dict) -> str:
    return ",".join(f"{field}={data[field]}" for field in fields)

def generate_esewa_signature(secret_key: str, message: str) -> str:
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

# ---------------------------
# Backend verification
# ---------------------------
def verify_esewa_payment(order: Order) -> bool:
    """
    Verify eSewa payment in backend using their verification API.
    No secret key is needed here.
    """
    ESEWA_VERIFY_URL = "https://rc-epay.esewa.com.np/api/epay/verify"  # UAT URL
    merchant_code = "EPAYTEST"

    total_amount = sum(item.price * item.qty for item in order.items)

    payload = {
        "amt": str(total_amount),
        "scd": merchant_code,
        "pid": order.transaction_uuid,
        "txAmt": "0",
        "tAmt": str(total_amount),
        "pdc": "0",
        "psc": "0"
    }

    response = requests.post(ESEWA_VERIFY_URL, data=payload)
    # eSewa responds with XML containing "Success" on success
    return response.status_code == 200 and "Success" in response.text

def pay_order_backend(order: Order, db: Session) -> Order:
    """
    Marks order as paid in backend after verifying eSewa payment
    """
    success = verify_esewa_payment(order)
    if not success:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    order.is_paid = True
    order.status = OrderStatusEnum.CONFIRM
    db.commit()
    db.refresh(order)
    return order

# ---------------------------
# Endpoints
# ---------------------------
@router.post("/initiate")
def initiate_esewa_payment(
    payload: EsewaPaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate eSewa payment. Returns frontend payload including signature.
    """
    # Fetch order
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="Only pending orders can be paid")

    # Calculate total amount from items
    total_amount = sum(item.price * item.qty for item in order.items)
    total_amount += payload.tax_amount + payload.product_service_charge + payload.product_delivery_charge

    # Merchant credentials
    merchant_code = "EPAYTEST"
    secret_key = "8gBm/:&EnhH.1/q"  # only for signature
    callback_url = "http://localhost:5173/payment/result/"  # frontend callback

    # Generate transaction UUID
    transaction_uuid = generate_transaction_uuid()
    order.transaction_uuid = transaction_uuid
    db.commit()
    db.refresh(order)

    # Build signature
    signed_field_names = ["total_amount", "transaction_uuid", "product_code"]
    data_to_sign = {
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
        "product_code": merchant_code
    }
    signed_string = build_signed_string_from_fields(signed_field_names, data_to_sign)
    signature = generate_esewa_signature(secret_key, signed_string)

    # Payload for frontend
    payment_payload = {
        "amount": total_amount,
        "tax_amount": payload.tax_amount,
        "product_service_charge": payload.product_service_charge,
        "product_delivery_charge": payload.product_delivery_charge,
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
        "product_code": merchant_code,
        "success_url": callback_url,
        "failure_url": callback_url,
        "signed_field_names": ",".join(signed_field_names),
        "signature": signature
    }

    return {
        "order": {
            "id": order.id,
            "status": order.status,
            "payment_mode": order.payment_mode,
            "is_paid": order.is_paid,
            "delivery_address": order.delivery_address,
            "placed_at": order.placed_at,
            "items": [
                {"id": item.id, "product_id": item.product_id, "qty": item.qty, "price": str(item.price)}
                for item in order.items
            ]
        },
        "payment_payload": payment_payload
    }

@router.post("/pay-backend/{order_id}")
def pay_order_backend_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Verify eSewa payment from backend and mark order as paid.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.is_paid:
        return {"message": "Order already paid"}

    paid_order = pay_order_backend(order, db)

    return {
        "message": "Order marked as paid via backend",
        "order": {
            "id": paid_order.id,
            "status": paid_order.status,
            "is_paid": paid_order.is_paid,
            "customer": f"{current_user.customer.first_name} {current_user.customer.last_name}"
        }
    }
