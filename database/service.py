"""
Database service for order transformer operations
"""

from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import pandas as pd

def parse_boolean(value: Any) -> bool:
    """Safely parse boolean values, handling string 'False' correctly"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)
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
                    existing.mapped_name = mapped_name  # type: ignore
                    existing.updated_at = datetime.utcnow()  # type: ignore
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
                    existing.mapped_item = mapped_item  # type: ignore
                    existing.updated_at = datetime.utcnow()  # type: ignore
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
            
            return {str(mapping.raw_name): str(mapping.mapped_name) for mapping in mappings}
    
    def get_item_mappings(self, source: str) -> Dict[str, str]:
        """Get all item mappings for a source"""
        
        with get_session() as session:
            mappings = session.query(ItemMapping)\
                             .filter_by(source=source)\
                             .all()
            
            return {str(mapping.raw_item): str(mapping.mapped_item) for mapping in mappings}
    
    def delete_store_mapping(self, source: str, raw_name: str) -> bool:
        """Delete a store mapping"""
        
        try:
            with get_session() as session:
                mapping = session.query(StoreMapping)\
                               .filter_by(source=source, raw_name=raw_name)\
                               .first()
                
                if mapping:
                    session.delete(mapping)
                    return True
                return False
                
        except Exception:
            return False
    
    def delete_item_mapping(self, source: str, raw_item: str) -> bool:
        """Delete an item mapping"""
        
        try:
            with get_session() as session:
                mapping = session.query(ItemMapping)\
                               .filter_by(source=source, raw_item=raw_item)\
                               .first()
                
                if mapping:
                    session.delete(mapping)
                    return True
                return False
                
        except Exception:
            return False
    
    # Enhanced Item Mapping Methods for Template System
    
    def get_item_mappings_advanced(self, source: str = None, active_only: bool = True, 
                                 key_type: str = None, search_term: str = None) -> List[Dict[str, Any]]:
        """Get item mappings with advanced filtering options"""
        
        with get_session() as session:
            query = session.query(ItemMapping)
            
            # Apply filters
            if source:
                query = query.filter(ItemMapping.source == source)
            if active_only:
                query = query.filter(ItemMapping.active == True)  # type: ignore
            if key_type:
                query = query.filter(ItemMapping.key_type == key_type)
            if search_term:
                search_pattern = f"%{search_term}%"
                # Build search filters carefully with null checks
                search_filters = [
                    ItemMapping.raw_item.ilike(search_pattern),
                    ItemMapping.mapped_item.ilike(search_pattern)
                ]
                # Only add vendor/description filters if they're not null
                if search_term:  # Additional safety check
                    search_filters.extend([
                        ItemMapping.vendor.ilike(search_pattern),
                        ItemMapping.mapped_description.ilike(search_pattern)
                    ])
                query = query.filter(or_(*search_filters))
            
            # Order by priority, then by created date
            query = query.order_by(ItemMapping.priority.asc(), ItemMapping.created_at.desc())
            
            mappings = query.all()
            
            # Convert to dictionaries
            result = []
            for mapping in mappings:
                result.append({
                    'id': mapping.id,
                    'source': str(mapping.source),
                    'raw_item': str(mapping.raw_item),
                    'mapped_item': str(mapping.mapped_item),
                    'key_type': str(mapping.key_type),
                    'priority': mapping.priority,
                    'active': mapping.active,
                    'vendor': str(mapping.vendor) if mapping.vendor is not None else '',
                    'mapped_description': str(mapping.mapped_description) if mapping.mapped_description is not None else '',
                    'notes': str(mapping.notes) if mapping.notes is not None else '',
                    'created_at': mapping.created_at,
                    'updated_at': mapping.updated_at
                })
            
            return result
    
    def bulk_upsert_item_mappings(self, mappings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk insert or update item mappings with transaction safety and constraint validation"""
        
        session = get_session().__enter__()
        transaction = None
        
        try:
            # Start explicit transaction
            transaction = session.begin()
            stats = {'added': 0, 'updated': 0, 'errors': 0, 'error_details': []}
            
            # Phase 1: Validate all rows upfront
            validated_data = []
            for idx, mapping_data in enumerate(mappings_data):
                try:
                    source = mapping_data.get('source', '').strip()
                    raw_item = mapping_data.get('raw_item', '').strip()
                    key_type = mapping_data.get('key_type', 'vendor_item').strip()
                    mapped_item = mapping_data.get('mapped_item', '').strip()
                    
                    # Validate required fields
                    if not source or not raw_item:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {idx + 1}: Missing source or raw_item")
                        continue
                    
                    if not mapped_item:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {idx + 1}: Missing mapped_item")
                        continue
                    
                    # Parse boolean safely
                    active = parse_boolean(mapping_data.get('active', True))
                    
                    # Validate priority is integer
                    try:
                        priority = int(mapping_data.get('priority', 100))
                    except (ValueError, TypeError):
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {idx + 1}: Invalid priority value")
                        continue
                    
                    validated_data.append({
                        'row_index': idx + 1,
                        'source': source,
                        'raw_item': raw_item,
                        'key_type': key_type,
                        'mapped_item': mapped_item,
                        'priority': priority,
                        'active': active,
                        'vendor': mapping_data.get('vendor'),
                        'mapped_description': mapping_data.get('mapped_description'),
                        'notes': mapping_data.get('notes')
                    })
                    
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {idx + 1}: Validation error - {str(e)}")
            
            # Phase 2: Check constraints for active mappings
            if validated_data:
                active_mappings = [v for v in validated_data if v['active']]
                
                # Group by (source, key_type, raw_item) to detect duplicates
                constraint_groups = {}
                for data in active_mappings:
                    key = (data['source'], data['key_type'], data['raw_item'])
                    if key not in constraint_groups:
                        constraint_groups[key] = []
                    constraint_groups[key].append(data)
                
                # Check for multiple active mappings with same constraint key
                for constraint_key, mappings in constraint_groups.items():
                    if len(mappings) > 1:
                        # Mark all but the first as errors
                        for mapping in mappings[1:]:
                            stats['errors'] += 1
                            stats['error_details'].append(
                                f"Row {mapping['row_index']}: Duplicate active mapping for "
                                f"({constraint_key[0]}, {constraint_key[1]}, {constraint_key[2]})"
                            )
                            validated_data.remove(mapping)
                
                # Check existing database for constraint violations
                for data in [v for v in validated_data if v['active']]:
                    existing_active = session.query(ItemMapping).filter(
                        and_(
                            ItemMapping.source == data['source'],
                            ItemMapping.key_type == data['key_type'],
                            ItemMapping.raw_item == data['raw_item'],
                            ItemMapping.active == True  # type: ignore
                        )
                    ).first()
                    
                    if existing_active:
                        # Check if this would create a constraint violation
                        # (i.e., updating a different mapping to be active)
                        existing_for_this_row = session.query(ItemMapping).filter(
                            and_(
                                ItemMapping.source == data['source'],
                                ItemMapping.raw_item == data['raw_item'],
                                ItemMapping.key_type == data['key_type']
                            )
                        ).first()
                        
                        if not existing_for_this_row:  # New mapping would conflict
                            stats['errors'] += 1
                            stats['error_details'].append(
                                f"Row {data['row_index']}: Active mapping already exists for "
                                f"({data['source']}, {data['key_type']}, {data['raw_item']})"
                            )
                            validated_data.remove(data)
            
            # If validation errors, rollback and return early
            if stats['errors'] > 0:
                transaction.rollback()
                return stats
            
            # Phase 3: Apply all validated changes atomically
            for data in validated_data:
                try:
                    # Check if mapping exists
                    existing = session.query(ItemMapping).filter(
                        and_(
                            ItemMapping.source == data['source'],
                            ItemMapping.raw_item == data['raw_item'],
                            ItemMapping.key_type == data['key_type']
                        )
                    ).first()
                    
                    if existing:
                        # Update existing mapping
                        existing.mapped_item = data['mapped_item']  # type: ignore
                        existing.priority = data['priority']  # type: ignore
                        existing.active = data['active']  # type: ignore
                        existing.vendor = data['vendor']  # type: ignore
                        existing.mapped_description = data['mapped_description']  # type: ignore
                        existing.notes = data['notes']  # type: ignore
                        existing.updated_at = datetime.utcnow()  # type: ignore
                        stats['updated'] += 1
                    else:
                        # Create new mapping
                        new_mapping = ItemMapping(
                            source=data['source'],
                            raw_item=data['raw_item'],
                            mapped_item=data['mapped_item'],
                            key_type=data['key_type'],
                            priority=data['priority'],
                            active=data['active'],
                            vendor=data['vendor'],
                            mapped_description=data['mapped_description'],
                            notes=data['notes']
                        )
                        session.add(new_mapping)
                        stats['added'] += 1
                        
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {data['row_index']}: Database error - {str(e)}")
                    transaction.rollback()
                    return stats
            
            # Commit transaction
            transaction.commit()
            return stats
                
        except Exception as e:
            if transaction:
                transaction.rollback()
            return {'added': 0, 'updated': 0, 'errors': 1, 'error_details': [f"Database transaction error: {str(e)}"]}
        
        finally:
            session.close()
    
    def export_item_mappings_to_dataframe(self, source: str = None) -> pd.DataFrame:
        """Export item mappings to pandas DataFrame for CSV/Excel export"""
        
        mappings = self.get_item_mappings_advanced(source=source, active_only=False)
        
        # Convert to DataFrame with standard template columns
        df_data = []
        for mapping in mappings:
            df_data.append({
                'Source': mapping['source'],
                'RawKeyType': mapping['key_type'],
                'RawKeyValue': mapping['raw_item'],
                'MappedItemNumber': mapping['mapped_item'],
                'Vendor': mapping['vendor'],
                'MappedDescription': mapping['mapped_description'],
                'Priority': mapping['priority'],
                'Active': mapping['active'],
                'Notes': mapping['notes']
            })
        
        return pd.DataFrame(df_data)
    
    def deactivate_item_mappings(self, mapping_ids: List[int]) -> int:
        """Deactivate item mappings by IDs"""
        
        try:
            with get_session() as session:
                count = session.query(ItemMapping).filter(
                    ItemMapping.id.in_(mapping_ids)
                ).update(
                    {ItemMapping.active: False, ItemMapping.updated_at: datetime.utcnow()},
                    synchronize_session=False
                )
                session.commit()
                return count
        except Exception:
            return 0
    
    def delete_item_mappings(self, mapping_ids: List[int]) -> int:
        """Permanently delete item mappings by IDs"""
        
        try:
            with get_session() as session:
                count = session.query(ItemMapping).filter(
                    ItemMapping.id.in_(mapping_ids)
                ).delete(synchronize_session=False)
                session.commit()
                return count
        except Exception:
            return 0
    
    def resolve_item_number(self, lookup_attributes: Dict[str, str], source: str) -> Optional[str]:
        """
        Resolve item number using priority-based lookup across multiple key types.
        
        Args:
            lookup_attributes: Dict with potential keys like {'vendor_item': 'ABC123', 'upc': '123456789'}
            source: Source system (e.g., 'kehe', 'wholefoods')
            
        Returns:
            Mapped item number if found, None otherwise
        """
        
        with get_session() as session:
            # Define key type priority order
            key_priority = ['vendor_item', 'upc', 'ean', 'gtin', 'sku_alias']
            
            for key_type in key_priority:
                if key_type in lookup_attributes and lookup_attributes[key_type]:
                    raw_value = str(lookup_attributes[key_type]).strip()
                    
                    mapping = session.query(ItemMapping).filter(
                        and_(
                            ItemMapping.source == source,
                            ItemMapping.key_type == key_type,
                            ItemMapping.raw_item == raw_value,
                            ItemMapping.active == True  # type: ignore
                        )
                    ).order_by(ItemMapping.priority.asc()).first()
                    
                    if mapping:
                        return str(mapping.mapped_item)
            
            return None
    
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