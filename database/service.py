"""
Database service for order transformer operations
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from .models import ProcessedOrder, OrderLineItem, ConversionHistory, StoreMapping, ItemMapping
from .connection import get_session

class DatabaseService:
    """Service class for database operations"""
    
    def get_session(self):
        """Get database session"""
        return get_session()
    
    # Model references for direct access
    StoreMapping = StoreMapping
    ItemMapping = ItemMapping
    
    def save_processed_orders(self, orders_data: List[Dict[str, Any]], source: str, filename: str) -> bool:
        """Save processed orders to database"""
        
        try:
            with get_session() as session:
                # Group orders by order number first to get accurate counts
                orders_by_number = {}
                for order_data in orders_data:
                    order_num = order_data.get('order_number', filename)
                    if order_num not in orders_by_number:
                        orders_by_number[order_num] = {
                            'order_info': order_data,
                            'line_items': []
                        }
                    orders_by_number[order_num]['line_items'].append(order_data)
                
                conversion_record = ConversionHistory(
                    filename=filename,
                    source=source,
                    orders_count=len(orders_by_number),  # Count unique orders
                    line_items_count=len(orders_data),   # Total line items
                    success=True
                )
                session.add(conversion_record)
                
                # Save orders and line items
                for order_num, order_group in orders_by_number.items():
                    order_info = order_group['order_info']
                    
                    # Create order record
                    order = ProcessedOrder(
                        order_number=order_num,
                        source=source,
                        customer_name=order_info.get('customer_name', 'UNKNOWN'),
                        raw_customer_name=order_info.get('raw_customer_name', ''),
                        order_date=self._parse_date(order_info.get('order_date')),
                        source_file=filename
                    )
                    session.add(order)
                    session.flush()  # Get the order ID
                    
                    # Create line items
                    for item_data in order_group['line_items']:
                        line_item = OrderLineItem(
                            order_id=order.id,
                            item_number=item_data.get('item_number', 'UNKNOWN'),
                            raw_item_number=item_data.get('raw_item_number', ''),
                            item_description=item_data.get('item_description', ''),
                            quantity=int(item_data.get('quantity', 1)),
                            unit_price=float(item_data.get('unit_price', 0.0)),
                            total_price=float(item_data.get('total_price', 0.0))
                        )
                        session.add(line_item)
                
                return True
                
        except Exception as e:
            # Log conversion error
            try:
                with get_session() as session:
                    error_record = ConversionHistory(
                        filename=filename,
                        source=source,
                        success=False,
                        error_message=str(e)
                    )
                    session.add(error_record)
            except:
                pass
            
            # Print error for debugging
            print(f"Database save error for {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return False
    
    def get_conversion_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversion history"""
        
        with get_session() as session:
            records = session.query(ConversionHistory)\
                           .order_by(ConversionHistory.conversion_date.desc())\
                           .limit(limit)\
                           .all()
            
            return [{
                'id': record.id,
                'filename': record.filename,
                'source': record.source,
                'conversion_date': record.conversion_date,
                'orders_count': record.orders_count,
                'line_items_count': record.line_items_count,
                'success': record.success,
                'error_message': record.error_message
            } for record in records]
    
    def get_processed_orders(self, source: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get processed orders with line items"""
        
        with get_session() as session:
            query = session.query(ProcessedOrder)
            
            if source:
                query = query.filter(ProcessedOrder.source == source)
            
            orders = query.order_by(ProcessedOrder.processed_at.desc()).limit(limit).all()
            
            result = []
            for order in orders:
                order_dict = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'source': order.source,
                    'customer_name': order.customer_name,
                    'raw_customer_name': order.raw_customer_name,
                    'order_date': order.order_date,
                    'processed_at': order.processed_at,
                    'source_file': order.source_file,
                    'line_items': [{
                        'id': item.id,
                        'item_number': item.item_number,
                        'raw_item_number': item.raw_item_number,
                        'item_description': item.item_description,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'total_price': item.total_price
                    } for item in order.line_items]
                }
                result.append(order_dict)
            
            return result
    
    def save_store_mapping(self, source: str, raw_name: str, mapped_name: str) -> bool:
        """Save or update store mapping"""
        
        try:
            with get_session() as session:
                # Check if mapping already exists
                existing = session.query(StoreMapping)\
                                .filter_by(source=source, raw_name=raw_name)\
                                .first()
                
                if existing:
                    existing.mapped_name = mapped_name
                    existing.updated_at = datetime.utcnow()
                else:
                    mapping = StoreMapping(
                        source=source,
                        raw_name=raw_name,
                        mapped_name=mapped_name
                    )
                    session.add(mapping)
                
                return True
                
        except Exception:
            return False
    
    def save_item_mapping(self, source: str, raw_item: str, mapped_item: str) -> bool:
        """Save or update item mapping"""
        
        try:
            with get_session() as session:
                # Check if mapping already exists
                existing = session.query(ItemMapping)\
                                .filter_by(source=source, raw_item=raw_item)\
                                .first()
                
                if existing:
                    existing.mapped_item = mapped_item
                    existing.updated_at = datetime.utcnow()
                else:
                    mapping = ItemMapping(
                        source=source,
                        raw_item=raw_item,
                        mapped_item=mapped_item
                    )
                    session.add(mapping)
                
                return True
                
        except Exception:
            return False
    
    def get_store_mappings(self, source: str) -> Dict[str, str]:
        """Get all store mappings for a source"""
        
        with get_session() as session:
            mappings = session.query(StoreMapping)\
                             .filter_by(source=source)\
                             .all()
            
            return {mapping.raw_name: mapping.mapped_name for mapping in mappings}
    
    def get_item_mappings(self, source: str) -> Dict[str, str]:
        """Get all item mappings for a source"""
        
        with get_session() as session:
            mappings = session.query(ItemMapping)\
                             .filter_by(source=source)\
                             .all()
            
            return {mapping.raw_item: mapping.mapped_item for mapping in mappings}
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        
        if not date_str:
            return None
        
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        return None