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
from .models import ProcessedOrder, OrderLineItem, ConversionHistory, StoreMapping, ItemMapping, CustomerMapping
from .connection import get_session

class DatabaseService:
    """Service class for database operations"""
    
    @staticmethod
    def normalize_source_name(source: str) -> str:
        """Normalize processor/source names to canonical database value."""
        if not source:
            return ""
        normalized = source.lower().strip().replace(' ', '_').replace('-', '_')
        if normalized in ('kehe', 'kehe_sps', 'kehe___sps'):
            return 'kehe'
        if normalized in ('whole_foods', 'wholefoods'):
            return 'wholefoods'
        if normalized in ('unfi_east',):
            return 'unfi_east'
        if normalized in ('unfi_west',):
            return 'unfi_west'
        return normalized
    
    def migrate_legacy_customer_mappings(self, source: Optional[str] = None) -> Dict[str, int]:
        """
        Move any legacy customer mappings that were accidentally stored in the
        StoreMapping table (store_type == 'customer') into the dedicated
        CustomerMapping table.
        """
        stats = {'migrated': 0, 'updated': 0, 'deleted': 0}
        normalized_source = self.normalize_source_name(source) if source else None
        candidate_sources: set[str] = set()
        if normalized_source:
            candidate_sources.update({normalized_source})
            if normalized_source == 'kehe':
                candidate_sources.update({'kehe_sps', 'kehe___sps', 'kehe - sps', 'KEHE - SPS', 'KEHE_SPS', 'KEHE___SPS'})
            elif normalized_source == 'wholefoods':
                candidate_sources.update({'whole_foods', 'whole foods', 'Whole Foods'})
            elif normalized_source == 'unfi_east':
                candidate_sources.update({'unfi east', 'unfi-east', 'UNFI EAST'})
            elif normalized_source == 'unfi_west':
                candidate_sources.update({'unfi west', 'unfi-west', 'UNFI WEST'})
            if source:
                candidate_sources.update({str(source).strip(), str(source).strip().lower()})
        candidate_sources.discard('')
        
        try:
            with get_session() as session:
                query = session.query(StoreMapping).filter(StoreMapping.store_type == 'customer')
                if candidate_sources:
                    query = query.filter(StoreMapping.source.in_(candidate_sources))
                legacy_mappings = query.all()
                
                for legacy in legacy_mappings:
                    target_source = legacy.source
                    normalized_target_source = self.normalize_source_name(target_source)
                    if not normalized_target_source:
                        normalized_target_source = target_source
                    raw_id = str(legacy.raw_store_id)
                    existing = session.query(CustomerMapping).filter_by(
                        source=normalized_target_source,
                        raw_customer_id=raw_id
                    ).first()
                    
                    if existing:
                        # Update existing customer mapping with latest values
                        existing.source = normalized_target_source  # type: ignore
                        existing.mapped_customer_name = legacy.mapped_store_name  # type: ignore
                        existing.customer_type = getattr(legacy, 'store_type', 'customer')  # type: ignore
                        existing.priority = legacy.priority  # type: ignore
                        existing.active = legacy.active  # type: ignore
                        existing.notes = legacy.notes  # type: ignore
                        existing.updated_at = datetime.utcnow()  # type: ignore
                        stats['updated'] += 1
                    else:
                        new_mapping = CustomerMapping(
                            source=normalized_target_source,
                            raw_customer_id=raw_id,
                            mapped_customer_name=str(legacy.mapped_store_name),
                            customer_type=getattr(legacy, 'store_type', 'customer'),
                            priority=legacy.priority,
                            active=legacy.active,
                            notes=legacy.notes
                        )
                        session.add(new_mapping)
                        stats['migrated'] += 1
                    
                    session.delete(legacy)
                    stats['deleted'] += 1
                
                if legacy_mappings:
                    session.commit()
        except Exception:
            # If migration fails we don't want to block the UI; just return stats so caller can log if needed.
            pass
        
        return stats
    
    def get_session(self):
        """Get database session"""
        return get_session()
    
    # Model references for direct access
    StoreMapping = StoreMapping
    ItemMapping = ItemMapping
    CustomerMapping = CustomerMapping
    
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
                                .filter_by(source=source, raw_store_id=raw_name)\
                                .first()
                
                if existing:
                    existing.mapped_store_name = mapped_name  # type: ignore
                    existing.updated_at = datetime.utcnow()  # type: ignore
                else:
                    mapping = StoreMapping(
                        source=source,
                        raw_store_id=raw_name,
                        mapped_store_name=mapped_name
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
        """Get all store mappings for a source (excludes customer mappings)"""
        
        with get_session() as session:
            mappings = session.query(StoreMapping)\
                             .filter_by(source=source)\
                             .filter(StoreMapping.store_type != 'customer')\
                             .all()
            
            return {str(mapping.raw_store_id): str(mapping.mapped_store_name) for mapping in mappings}
    
    def get_customer_mappings(self, source: str) -> Dict[str, str]:
        """Get all customer mappings for a source"""
        
        def _normalize_key(key: str) -> str:
            """Normalize key by removing .0 suffix from numeric strings"""
            key_str = str(key).strip()
            # Remove .0 suffix if the key is numeric (e.g., "569813000000.0" -> "569813000000")
            if key_str.endswith('.0') and key_str[:-2].replace('.', '').isdigit():
                return key_str[:-2]
            return key_str
        
        try:
            # Normalize source name (e.g., "Whole Foods" -> "wholefoods", "UNFI East" -> "unfi_east")
            source_lower = source.lower().strip()
            # Handle special cases first
            if source_lower in ['whole foods', 'whole_foods']:
                normalized_source = 'wholefoods'
            elif source_lower in ['unfi east', 'unfi_east']:
                normalized_source = 'unfi_east'
            elif source_lower in ['unfi west', 'unfi_west']:
                normalized_source = 'unfi_west'
            elif source_lower in ['kehe', 'kehe - sps', 'kehe_sps', 'kehe___sps']:
                normalized_source = 'kehe'
            else:
                # General normalization: replace spaces and hyphens with underscores
                normalized_source = source_lower.replace(' ', '_').replace('-', '_')
            
            mapping_dict = {}
            
            with get_session() as session:
                # Try CustomerMapping table first
                try:
                    mappings = session.query(CustomerMapping)\
                                     .filter_by(source=normalized_source, active=True)\
                                     .order_by(CustomerMapping.priority.asc())\
                                     .all()
                    
                    # Normalize keys to remove .0 suffixes
                    for mapping in mappings:
                        normalized_key = _normalize_key(mapping.raw_customer_id)
                        mapping_dict[normalized_key] = str(mapping.mapped_customer_name)
                except Exception as e:
                    print(f"DEBUG: CustomerMapping table query failed for {source}: {e}")
                    mapping_dict = {}
                
                # Fallback to StoreMapping table with store_type='customer' if CustomerMapping is empty or doesn't exist
                if not mapping_dict:
                    try:
                        store_mappings = session.query(StoreMapping)\
                                               .filter_by(source=normalized_source)\
                                               .filter(StoreMapping.store_type == 'customer')\
                                               .all()
                        
                        # Build mapping dict from StoreMapping (using raw_store_id as key)
                        for mapping in store_mappings:
                            raw_id = _normalize_key(mapping.raw_store_id)
                            mapped_name = str(mapping.mapped_store_name).strip()
                            if raw_id and mapped_name:
                                mapping_dict[raw_id] = mapped_name
                        
                        if store_mappings:
                            print(f"DEBUG: Found {len(store_mappings)} customer mappings in StoreMapping table for {source}")
                    except Exception as e:
                        print(f"DEBUG: StoreMapping fallback query failed for {source}: {e}")
                
                return mapping_dict
        except Exception as e:
            # Return empty dict if query fails (e.g., table doesn't exist yet)
            print(f"DEBUG: Error in get_customer_mappings for {source}: {e}")
            return {}
    
    def get_item_mappings(self, source: str) -> Dict[str, str]:
        """Get all item mappings for a source"""
        
        def _normalize_item_key(key: str) -> str:
            """Normalize item key by removing .0 suffix from numeric strings"""
            key_str = str(key).strip()
            # Remove .0 suffix if the key is numeric (e.g., "256821.0" -> "256821")
            if key_str.endswith('.0') and key_str[:-2].replace('.', '').isdigit():
                return key_str[:-2]
            return key_str
        
        # Normalize source name
        source_lower = source.lower().strip()
        if source_lower in ['kehe', 'kehe - sps', 'kehe_sps', 'kehe___sps']:
            normalized_source = 'kehe'
        else:
            normalized_source = source_lower.replace(' ', '_').replace('-', '_')
        
        with get_session() as session:
            mappings = session.query(ItemMapping)\
                             .filter_by(source=normalized_source)\
                             .all()
            
            # Normalize keys to remove .0 suffixes
            result = {}
            for mapping in mappings:
                normalized_key = _normalize_item_key(mapping.raw_item)
                result[normalized_key] = str(mapping.mapped_item)
            
            return result
    
    def get_item_mappings_dict(self, source: str) -> Dict[str, Dict[str, str]]:
        """
        Bulk-fetch all item mappings with descriptions for a source in one query
        
        Args:
            source: Order source (wholefoods, unfi_west, etc.)
            
        Returns:
            Dictionary mapping raw_item to {'mapped_item': str, 'mapped_description': str}
            Example: {'71094': {'mapped_item': '13-025-23', 'mapped_description': 'Bonne Maman Cranberry...'}}
        """
        def _normalize_item_key(key: str) -> str:
            """Normalize item key by removing .0 suffix from numeric strings, preserving spaces"""
            key_str = str(key).strip()
            # Remove .0 suffix if the key is numeric (e.g., "256821.0" -> "256821")
            # But preserve spaces in item numbers like "13 025 24"
            if key_str.endswith('.0') and key_str[:-2].replace('.', '').replace(' ', '').isdigit():
                return key_str[:-2]
            return key_str
        
        try:
            # Normalize source name
            source_lower = source.lower().strip()
            if source_lower in ['kehe', 'kehe - sps', 'kehe_sps', 'kehe___sps']:
                normalized_source = 'kehe'
            elif source_lower in ['whole foods', 'whole_foods']:
                normalized_source = 'wholefoods'
            elif source_lower in ['unfi east', 'unfi_east']:
                normalized_source = 'unfi_east'
            elif source_lower in ['unfi west', 'unfi_west']:
                normalized_source = 'unfi_west'
            else:
                normalized_source = source_lower.replace(' ', '_').replace('-', '_')
            
            with get_session() as session:
                mappings = session.query(ItemMapping)\
                                 .filter_by(source=normalized_source)\
                                 .all()
                
                result = {}
                for mapping in mappings:
                    # Normalize key to remove .0 suffixes but preserve spaces
                    normalized_key = _normalize_item_key(mapping.raw_item)
                    result[normalized_key] = {
                        'mapped_item': str(mapping.mapped_item),
                        'mapped_description': str(mapping.mapped_description) if mapping.mapped_description else ''
                    }
                
                return result
                
        except Exception:
            return {}
    
    def get_item_mapping_with_description(self, raw_item: str, source: str) -> Optional[Dict[str, str]]:
        """
        Get item mapping with description for a specific raw item and source
        
        Args:
            raw_item: Original item number from order file
            source: Order source (wholefoods, unfi_west, etc.)
            
        Returns:
            Dictionary with 'mapped_item' and 'mapped_description' if found, None otherwise
        """
        if not raw_item or not raw_item.strip():
            return None
        
        try:
            with get_session() as session:
                mapping = session.query(ItemMapping)\
                               .filter_by(source=source, raw_item=str(raw_item).strip())\
                               .first()
                
                if mapping:
                    return {
                        'mapped_item': str(mapping.mapped_item),
                        'mapped_description': str(mapping.mapped_description) if mapping.mapped_description else ''
                    }
                
                return None
                
        except Exception:
            return None
    
    def delete_store_mapping(self, source: str, raw_name: str) -> bool:
        """Delete a store mapping"""
        
        try:
            with get_session() as session:
                mapping = session.query(StoreMapping)\
                               .filter_by(source=source, raw_store_id=raw_name)\
                               .first()
                
                if mapping:
                    session.delete(mapping)
                    session.commit()
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
                    session.commit()
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
    
    def bulk_upsert_store_mappings(self, mappings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk insert or update store mappings with transaction safety"""
        
        session = get_session().__enter__()
        transaction = None
        
        try:
            transaction = session.begin()
            stats = {'added': 0, 'updated': 0, 'errors': 0, 'error_details': []}
            
            validated_data = []
            for idx, mapping_data in enumerate(mappings_data):
                try:
                    source = str(mapping_data.get('source', mapping_data.get('Source', '')) or '').strip()
                    raw_store_id = str(mapping_data.get('raw_store_id', mapping_data.get('RawStoreID', '')) or '').strip()
                    mapped_store_name = str(mapping_data.get('mapped_store_name', mapping_data.get('MappedStoreName', '')) or '').strip()
                    
                    if not source:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {idx + 1}: Missing source")
                        continue
                    
                    if not raw_store_id:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {idx + 1}: Missing raw_store_id")
                        continue
                    
                    if not mapped_store_name:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {idx + 1}: Missing mapped_store_name")
                        continue
                    
                    active = parse_boolean(mapping_data.get('active', mapping_data.get('Active', True)))
                    
                    try:
                        priority = int(mapping_data.get('priority', mapping_data.get('Priority', 100)))
                    except (ValueError, TypeError):
                        priority = 100
                    
                    store_type = mapping_data.get('store_type', mapping_data.get('StoreType', 'distributor'))
                    # Ensure store_type is never 'customer' for store mappings
                    if store_type == 'customer':
                        store_type = 'distributor'  # Default to distributor if customer is specified
                    
                    validated_data.append({
                        'row_index': idx + 1,
                        'source': source,
                        'raw_store_id': raw_store_id,
                        'mapped_store_name': mapped_store_name,
                        'store_type': store_type,
                        'priority': priority,
                        'active': active,
                        'notes': mapping_data.get('notes', mapping_data.get('Notes', ''))
                    })
                    
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {idx + 1}: Validation error - {str(e)}")
            
            for data in validated_data:
                try:
                    # Filter by store_type != 'customer' to avoid overwriting customer mappings
                    # This ensures store mappings and customer mappings remain separate
                    existing = session.query(StoreMapping).filter(
                        and_(
                            StoreMapping.source == data['source'],
                            StoreMapping.raw_store_id == data['raw_store_id'],
                            StoreMapping.store_type != 'customer'  # Exclude customer mappings
                        )
                    ).first()
                    
                    if existing:
                        existing.mapped_store_name = data['mapped_store_name']  # type: ignore
                        existing.store_type = data['store_type']  # type: ignore
                        existing.priority = data['priority']  # type: ignore
                        existing.active = data['active']  # type: ignore
                        existing.notes = data['notes']  # type: ignore
                        existing.updated_at = datetime.utcnow()  # type: ignore
                        stats['updated'] += 1
                    else:
                        new_mapping = StoreMapping(
                            source=data['source'],
                            raw_store_id=data['raw_store_id'],
                            mapped_store_name=data['mapped_store_name'],
                            store_type=data['store_type'],
                            priority=data['priority'],
                            active=data['active'],
                            notes=data['notes']
                        )
                        session.add(new_mapping)
                        stats['added'] += 1
                        
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {data['row_index']}: Database error - {str(e)}")
                    transaction.rollback()
                    return stats
            
            transaction.commit()
            return stats
                
        except Exception as e:
            if transaction:
                transaction.rollback()
            return {'added': 0, 'updated': 0, 'errors': 1, 'error_details': [f"Database transaction error: {str(e)}"]}
        
        finally:
            session.close()
    
    def bulk_upsert_customer_mappings(self, mappings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk insert or update customer mappings with transaction safety"""
        
        session = get_session().__enter__()
        transaction = None
        
        try:
            transaction = session.begin()
            stats = {'added': 0, 'updated': 0, 'errors': 0, 'error_details': []}
            
            validated_data = []
            for idx, mapping_data in enumerate(mappings_data):
                try:
                    source = mapping_data.get('source', '').strip()
                    raw_customer_id = mapping_data.get('raw_customer_id', '').strip()
                    mapped_customer_name = mapping_data.get('mapped_customer_name', '').strip()
                    
                    if not source or not raw_customer_id or not mapped_customer_name:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {idx + 1}: Missing required fields")
                        continue
                    
                    active = parse_boolean(mapping_data.get('active', True))
                    
                    try:
                        priority = int(mapping_data.get('priority', 100))
                    except (ValueError, TypeError):
                        priority = 100
                    
                    validated_data.append({
                        'source': source,
                        'raw_customer_id': raw_customer_id,
                        'mapped_customer_name': mapped_customer_name,
                        'customer_type': mapping_data.get('customer_type', 'store'),
                        'priority': priority,
                        'active': active,
                        'notes': mapping_data.get('notes', ''),
                        'row_index': idx
                    })
                    
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {idx + 1}: Validation error - {str(e)}")
                    continue
            
            # Process validated data
            for data in validated_data:
                try:
                    existing = session.query(CustomerMapping).filter_by(
                        source=data['source'],
                        raw_customer_id=data['raw_customer_id']
                    ).first()
                    
                    if existing:
                        existing.mapped_customer_name = data['mapped_customer_name']
                        existing.customer_type = data['customer_type']
                        existing.priority = data['priority']
                        existing.active = data['active']
                        existing.notes = data['notes']
                        existing.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        new_mapping = CustomerMapping(
                            source=data['source'],
                            raw_customer_id=data['raw_customer_id'],
                            mapped_customer_name=data['mapped_customer_name'],
                            customer_type=data['customer_type'],
                            priority=data['priority'],
                            active=data['active'],
                            notes=data['notes']
                        )
                        session.add(new_mapping)
                        stats['added'] += 1
                        
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {data['row_index']}: Database error - {str(e)}")
                    transaction.rollback()
                    return stats
            
            transaction.commit()
            return stats
                
        except Exception as e:
            if transaction:
                transaction.rollback()
            return {'added': 0, 'updated': 0, 'errors': 1, 'error_details': [f"Database transaction error: {str(e)}"]}
        
        finally:
            session.close()
    
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