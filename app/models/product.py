from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime

Base = declarative_base()


class Product(Base):
    """SQLAlchemy model for products"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    brand = Column(String(100), nullable=True)
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"


class ProductResponse(BaseModel):
    """Pydantic model for API responses"""
    id: int
    name: str
    category: str
    description: Optional[str] = None
    price: Decimal
    brand: Optional[str] = None
    in_stock: bool
    stock_quantity: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    """Pydantic model for creating products"""
    name: str
    category: str
    description: Optional[str] = None
    price: Decimal
    brand: Optional[str] = None
    in_stock: bool = True
    stock_quantity: int = 0


class ProductUpdate(BaseModel):
    """Pydantic model for updating products"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    brand: Optional[str] = None
    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None