from .database import SessionLocal
from .models import Cart, CartItem, Product
from .store_schema import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    ProductOut
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

router = APIRouter(
    prefix="/carts",
)

# ---------- DB Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# ---------- CART ----------

@router.post("/{customer_id}", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(customer_id: int, db: Session = Depends(get_db)):
    cart = Cart(customer_id=customer_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart

@router.get("/{cart_id}", response_model=CartResponse)
def get_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        .filter(Cart.id == cart_id)
        .first()
    )

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return cart

# ---------- CART ITEM ----------

@router.post("/{cart_id}/items", response_model=CartResponse)
def add_item_to_cart(
    cart_id: int,
    data: CartItemCreate,
    db: Session = Depends(get_db)
):
    if data.qty <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    # 1️⃣ Validate cart exists
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # 2️⃣ Validate product exists
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 3️⃣ Check if item already in cart
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart_id, CartItem.product_id == data.product_id)
        .first()
    )

    # 4️⃣ Add or increment
    if cart_item:
        cart_item.qty += data.qty
    else:
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=data.product_id,
            qty=data.qty
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart)  # refresh cart with updated items

    return cart

@router.put("/items/{item_id}", response_model=CartResponse)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db)
):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart_item.qty = data.qty
    db.commit()
    db.refresh(cart_item.cart)

    return cart_item.cart

@router.delete("/items/{item_id}", response_model=CartResponse)
def remove_cart_item(item_id: int, db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart = cart_item.cart
    db.delete(cart_item)
    db.commit()
    db.refresh(cart)

    return cart



