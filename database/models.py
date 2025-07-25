"""
Database models for order transformer
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ProcessedOrder(Base):
    """Model for storing processed orders"""
    __tablename__ = 'processed_orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(100), nullable=False)
    source = Column(String(50), nullable=False)  # wholefoods, unfi_west, etc.
    customer_name = Column(String(200))
    raw_customer_name = Column(String(200))
    order_date = Column(DateTime)
    processed_at = Column(DateTime, default=datetime.utcnow)
    source_file = Column(String(500))
    
    # Relationships
    line_items = relationship("OrderLineItem", back_populates="order", cascade="all, delete-orphan")

class OrderLineItem(Base):
    """Model for storing order line items"""
    __tablename__ = 'order_line_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('processed_orders.id'), nullable=False)
    
    item_number = Column(String(100))
    raw_item_number = Column(String(100))
    item_description = Column(Text)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    
    # Relationship
    order = relationship("ProcessedOrder", back_populates="line_items")

class ConversionHistory(Base):
    """Model for tracking conversion history"""
    __tablename__ = 'conversion_history'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(500), nullable=False)
    source = Column(String(50), nullable=False)
    conversion_date = Column(DateTime, default=datetime.utcnow)
    orders_count = Column(Integer, default=0)
    line_items_count = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
class StoreMapping(Base):
    """Model for storing store/customer name mappings"""
    __tablename__ = 'store_mappings'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)
    raw_name = Column(String(200), nullable=False)
    mapped_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
class ItemMapping(Base):
    """Model for storing item number mappings"""
    __tablename__ = 'item_mappings'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)
    raw_item = Column(String(100), nullable=False)
    mapped_item = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)