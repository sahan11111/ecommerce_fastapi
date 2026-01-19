from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from .database import Base


# =========================
# User
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)

    # One-to-one relationship with Customer
    customer = relationship(
        "Customer",
        back_populates="user",
        uselist=False
    )


# =========================
# Customer
# =========================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(30), nullable=False)
    middle_name = Column(String(30), nullable=True)
    last_name = Column(String(30), nullable=False)

    shipping_address = Column(Text, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False
    )

    # Access related user
    user = relationship("User", back_populates="customer")

    # One customer can have multiple carts
    carts = relationship(
        "Cart",
        back_populates="customer",
        cascade="all, delete"
    )

    def __str__(self):
        full_name = self.first_name
        if self.middle_name:
            full_name += f" {self.middle_name}"
        full_name += f" {self.last_name}"
        return full_name


# =========================
# Category
# =========================
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # One category → many products
    products = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


# =========================
# Product
# =========================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    # Available stock
    stock_qty = Column(Integer, nullable=False)

    # Price stored as Decimal
    price = Column(Numeric(10, 2), nullable=False)

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False
    )

    # Access related category
    category = relationship("Category", back_populates="products")

    # Access cart items containing this product
    cart_items = relationship(
        "CartItem",
        back_populates="product",
        cascade="all, delete"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Price including 13% tax
    @property
    def price_with_tax(self):
        tax_rate = Decimal("0.13")
        return self.price + (self.price * tax_rate)

    def __str__(self):
        return self.name


# =========================
# Cart
# =========================
class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False
    )

    # Access related customer
    customer = relationship(
        "Customer",
        back_populates="carts"
    )

    # Items inside this cart
    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __str__(self):
        return str(self.id)

    # Total price without tax
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items)

    # Total price including tax
    @property
    def total_price_with_tax(self):
        return sum(item.total_price_with_tax for item in self.items)


# =========================
# CartItem
# =========================
class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    cart_id = Column(
        Integer,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False
    )

    # Quantity of product in cart
    qty = Column(Integer, nullable=False)

    # Access related product
    product = relationship(
        "Product",
        back_populates="cart_items"
    )

    # Access related cart
    cart = relationship(
        "Cart",
        back_populates="items"
    )

    # Total price for this item
    @property
    def total_price(self):
        return self.qty * self.product.price

    # Total price including tax
    @property
    def total_price_with_tax(self):
        return self.qty * self.product.price_with_tax

    def __str__(self):
        return f"{self.id} ({self.product.name})"
