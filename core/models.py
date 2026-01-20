"""
Database models for Ecommerce system
------------------------------------
Tech stack:
- FastAPI
- SQLAlchemy ORM
- PostgreSQL / MySQL compatible
- Alembic-ready

This file contains:
- User & Customer models
- Product & Category models
- Cart & CartItem models
- Order & OrderItem models
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from enum import Enum 

from .database import Base



# User

class User(Base):
    """
    Represents application users.
    Used for authentication & authorization.
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    #Login Credential
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    #email / otp verification
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)

    # One-to-one relationship with Customer
    customer = relationship(
        "Customer",
        back_populates="user",
        uselist=False
    )



# Customer

class Customer(Base):
    """
    Customer profile linked to a User.
    Stores personal and shipping information.
    """
    
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(30), nullable=False)
    middle_name = Column(String(30), nullable=True)
    last_name = Column(String(30), nullable=False)

    # Default shipping address
    shipping_address = Column(Text, nullable=False)

    # One-to-one link with User
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False
    )

    # Access related user
    user = relationship("User", back_populates="customer")

    # A customer can have multiple carts (history / sessions)
    carts = relationship(
        "Cart",
        back_populates="customer",
        cascade="all, delete"
    )

    # A customer can have multiple orders
    orders = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete"
    )

    def __str__(self):
        return f"{self.first_name} {self.middle_name or ''} {self.last_name}".strip()



# Category

class Category(Base):
    """
    Product categories (e.g. Electronics, Clothing).
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # One category → many products
    products = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete"
    )

    # Timestamp fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )



# Product

class Product(Base):
    """
    Represents a sellable product.
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    # Available stock quantity
    stock_qty = Column(Integer, nullable=False)

    # Product price stored as Decimal for accuracy
    price = Column(Numeric(10, 2), nullable=False)

    # Category relationship
    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False
    )

    category = relationship("Category", back_populates="products")

    # Cart items referencing this product
    cart_items = relationship(
        "CartItem",
        back_populates="product",
        cascade="all, delete"
    )

    # Timestamp fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Computed property: price including 13% VAT
    @property
    def price_with_tax(self):
        tax_rate = Decimal("0.13")
        return self.price + (self.price * tax_rate)

    def __str__(self):
        return self.name



# Cart

class Cart(Base):
    """
    Shopping cart belonging to a customer.
    """
    
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

    def __str__(self):
        return str(self.id)

# CartItem

class CartItem(Base):
    """
    Individual product entry inside a cart.
    """
    
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


class PaymentModeEnum(str, Enum):
    PENDING = "P"
    CASH = "C"
    ESEWA = "E"
    
class OrderStatusEnum(str, Enum):
    PENDING = "P"
    CONFIRM = "CF"
    REJECTED = "R"
    CANCELLED = "C"
    
class Order(Base):
    """
    Represents a finalized order.
    Created after checkout from cart.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    # Order status (pending, confirmed, rejected, cancelled)
    status = Column(
        SQLEnum(OrderStatusEnum),
        default=OrderStatusEnum.PENDING,
        nullable=False
    )

    # Optional link to customer
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Shipping address snapshot
    delivery_address = Column(String(255), nullable=True)

    # Order placement timestamp
    placed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Payment method
    payment_mode = Column(
        SQLEnum(PaymentModeEnum),
        default=PaymentModeEnum.PENDING,
        nullable=False
    )

    # Payment status flag
    is_paid = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="orders")

    # Items purchased in this order
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    def __str__(self):
        return f"Order No {self.id}"
        return f"Order No {self.id}"

class OrderItem(Base):
    """
    Individual product entry inside an order.
    Stores snapshot price for order history.
    """

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )

    # Quantity ordered
    qty = Column(Integer, nullable=False)

    # Snapshot price at time of order
    price = Column(Numeric(10, 2), nullable=False)

    product = relationship("Product")
    order = relationship("Order", back_populates="items")

    def __str__(self):
        return f"OrderItem {self.id}"
