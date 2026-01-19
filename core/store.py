from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload
from typing import List

from .database import SessionLocal
from .models import Cart, CartItem, Category, Product
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
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(**category.model_dump())
    db.add(db_category)
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



