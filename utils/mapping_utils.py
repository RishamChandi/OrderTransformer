"""
Utilities for handling customer and store name mappings
"""

import pandas as pd
import os
from typing import Optional, Dict, Any

class MappingUtils:
    """Utilities for mapping customer/store names"""
    
    def __init__(self, use_database: bool = True):
        self.mapping_cache = {}
        self.use_database = use_database
        
        if use_database:
            try:
                from database.service import DatabaseService
                self.db_service = DatabaseService()
            except ImportError:
                self.use_database = False
                self.db_service = None
        else:
            self.db_service = None
    
    def get_store_mapping(self, raw_name: str, source: str) -> str:
        """
        Get mapped store name for a given raw name and source
        
        Args:
            raw_name: Original customer/store name from order file
            source: Order source (wholefoods, unfi_west, unfi, tkmaxx)
            
        Returns:
            Mapped store name or original name if no mapping found
        """
        
        if not raw_name or not raw_name.strip():
            return "UNKNOWN"
        
        raw_name_clean = raw_name.strip()
        
        # Try database first if available
        if self.use_database and self.db_service:
            try:
                mapping_dict = self.db_service.get_store_mappings(source)
                
                # Try exact match first
                if raw_name_clean in mapping_dict:
                    return mapping_dict[raw_name_clean]
                
                # Try case-insensitive match
                raw_name_lower = raw_name_clean.lower()
                for key, value in mapping_dict.items():
                    if key.lower() == raw_name_lower:
                        return value
                
                # Try partial match
                for key, value in mapping_dict.items():
                    if key.lower() in raw_name_lower or raw_name_lower in key.lower():
                        return value
                        
            except Exception:
                pass  # Fall back to file-based mapping
        
        # Fallback to file-based mapping
        mapping_key = f"{source}_mapping"
        if mapping_key not in self.mapping_cache:
            self._load_mapping(source)
        
        # Get mapping
        mapping_dict = self.mapping_cache.get(mapping_key, {})
        
        # Try exact match first
        if raw_name_clean in mapping_dict:
            return mapping_dict[raw_name_clean]
        
        # Try case-insensitive match
        raw_name_lower = raw_name_clean.lower()
        for key, value in mapping_dict.items():
            if key.lower() == raw_name_lower:
                return value
        
        # Try partial match
        for key, value in mapping_dict.items():
            if key.lower() in raw_name_lower or raw_name_lower in key.lower():
                return value
        
        # Return default for Whole Foods if no mapping found
        if source.lower().replace(' ', '_') in ['wholefoods', 'whole_foods', 'whole foods']:
            return 'IDI - Richmond'
        # Otherwise return original
        return raw_name_clean
    
    def get_customer_mapping(self, raw_customer_id: str, source: str) -> str:
        """
        Get mapped customer name for a given raw customer ID and source
        
        Args:
            raw_customer_id: Original customer ID from order file (e.g., store number, IOW code)
            source: Order source (wholefoods, unfi_west, unfi_east, tkmaxx)
            
        Returns:
            Mapped customer name or 'UNKNOWN' if no mapping found
        """
        
        if not raw_customer_id or not str(raw_customer_id).strip():
            return "UNKNOWN"
        
        raw_customer_id_clean = str(raw_customer_id).strip()
        raw_customer_id_lower = raw_customer_id_clean.lower()
        
        # Try database first if available
        if self.use_database and self.db_service:
            try:
                mapping_dict = self.db_service.get_customer_mappings(source)
                
                # Debug output for UNFI East
                if source.lower() in ['unfi_east', 'unfi east']:
                    print(f"DEBUG: Looking up customer mapping for '{raw_customer_id_clean}' (source: {source})")
                    print(f"DEBUG: Found {len(mapping_dict)} customer mappings")
                    if len(mapping_dict) > 0:
                        sample_keys = list(mapping_dict.keys())[:5]
                        print(f"DEBUG: Sample mapping keys: {sample_keys}")
                
                # Try exact match first
                if raw_customer_id_clean in mapping_dict:
                    print(f"DEBUG: Found exact match for '{raw_customer_id_clean}'")
                    return mapping_dict[raw_customer_id_clean]
                
                # Try case-insensitive exact match
                for key, value in mapping_dict.items():
                    if str(key).lower() == raw_customer_id_lower:
                        return value
                
                # For UNFI East: Try matching the code at the end of the key (e.g., "128 RCH" matches "RCH")
                # This handles cases where database has "128 RCH" but parser extracts just "RCH"
                if source.lower() in ['unfi_east', 'unfi east']:
                    # Try matching code as suffix/end of key (most common case)
                    for key, value in mapping_dict.items():
                        key_str = str(key).strip()
                        key_lower = key_str.lower()
                        # Check if raw_customer_id matches the end of the key after a space
                        # Examples: "RCH" matches "128 RCH", "HOW" matches "129 HOW"
                        if key_lower.endswith(' ' + raw_customer_id_lower) or key_lower.endswith(raw_customer_id_lower):
                            # Verify it's a complete match (not partial) - check if preceded by space or is exact match
                            if key_lower == raw_customer_id_lower or \
                               (len(key_lower) > len(raw_customer_id_lower) and 
                                key_lower[-len(raw_customer_id_lower)-1] == ' '):
                                return value
                        # Also check if key ends with just the code (no prefix) - exact match
                        elif key_lower == raw_customer_id_lower:
                            return value
                        # Check if key starts with code followed by space
                        elif key_lower.startswith(raw_customer_id_lower + ' '):
                            return value
                        # Extract code from key if it follows pattern "NUMBER CODE" (e.g., "128 RCH" -> "RCH")
                        elif ' ' in key_lower:
                            parts = key_lower.split()
                            if len(parts) >= 2 and parts[-1] == raw_customer_id_lower:
                                print(f"DEBUG: Matched '{raw_customer_id_clean}' to key '{key_str}' (extracted code from end)")
                                return value
                
                # Try partial match (key contains raw_customer_id or vice versa)
                for key, value in mapping_dict.items():
                    key_lower = str(key).lower()
                    if raw_customer_id_lower in key_lower or key_lower in raw_customer_id_lower:
                        return value
                        
            except Exception as e:
                # Log error for debugging but don't raise
                print(f"DEBUG: Error in get_customer_mapping for {source}: {e}")
                pass
        
        # Fallback: return UNKNOWN if no mapping found
        return "UNKNOWN"
    
    def _load_mapping(self, source: str) -> None:
        """Load mapping file for the given source"""
        
        mapping_file = f"mappings/{source}/store_mapping.xlsx"
        mapping_key = f"{source}_mapping"
        
        try:
            if os.path.exists(mapping_file):
                df = pd.read_excel(mapping_file)
                
                # Expected columns: raw_name, mapped_name
                if len(df.columns) >= 2:
                    raw_col = df.columns[0]
                    mapped_col = df.columns[1]
                    
                    mapping_dict = {}
                    for _, row in df.iterrows():
                        if pd.notna(row[raw_col]) and pd.notna(row[mapped_col]):
                            mapping_dict[str(row[raw_col]).strip()] = str(row[mapped_col]).strip()
                    
                    self.mapping_cache[mapping_key] = mapping_dict
                else:
                    self.mapping_cache[mapping_key] = {}
            else:
                # Create default mapping structure
                self.mapping_cache[mapping_key] = {}
                self._create_default_mapping_file(source)
                
        except Exception as e:
            # Use empty mapping on error
            self.mapping_cache[mapping_key] = {}
    
    def _create_default_mapping_file(self, source: str) -> None:
        """Create a default mapping file with sample entries"""
        
        mapping_dir = f"mappings/{source}"
        os.makedirs(mapping_dir, exist_ok=True)
        
        mapping_file = os.path.join(mapping_dir, "store_mapping.xlsx")
        
        # Create sample mapping data
        sample_data = {
            'Raw Name': [
                'Sample Store 1',
                'Sample Customer A',
                'Example Location',
                'Default Entry'
            ],
            'Mapped Name': [
                'Mapped Store 1',
                'Mapped Customer A', 
                'Mapped Location',
                'Default Mapped'
            ]
        }
        
        try:
            df = pd.DataFrame(sample_data)
            df.to_excel(mapping_file, index=False)
        except Exception:
            # Ignore file creation errors
            pass
    
    def add_mapping(self, raw_name: str, mapped_name: str, source: str) -> bool:
        """
        Add a new mapping entry
        
        Args:
            raw_name: Original name from order file
            mapped_name: Standardized name to map to
            source: Order source
            
        Returns:
            True if mapping was added successfully
        """
        
        try:
            mapping_key = f"{source}_mapping"
            
            # Load existing mapping if not cached
            if mapping_key not in self.mapping_cache:
                self._load_mapping(source)
            
            # Add to cache
            self.mapping_cache[mapping_key][raw_name.strip()] = mapped_name.strip()
            
            # Update file
            mapping_file = f"mappings/{source}/store_mapping.xlsx"
            
            # Read existing data
            if os.path.exists(mapping_file):
                df = pd.read_excel(mapping_file)
            else:
                df = pd.DataFrame(columns=['Raw Name', 'Mapped Name'])
            
            # Add new row
            new_row = pd.DataFrame({
                'Raw Name': [raw_name.strip()],
                'Mapped Name': [mapped_name.strip()]
            })
            
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['Raw Name'], keep='last')
            
            # Save file
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            df.to_excel(mapping_file, index=False)
            
            return True
            
        except Exception:
            return False
    
    def get_all_mappings(self, source: str) -> Dict[str, str]:
        """Get all mappings for a source"""
        
        mapping_key = f"{source}_mapping"
        if mapping_key not in self.mapping_cache:
            self._load_mapping(source)
        
        return self.mapping_cache.get(mapping_key, {})
    
    def get_item_mapping(self, raw_item: str, source: str) -> str:
        """
        Get mapped item number for a given raw item and source
        
        Args:
            raw_item: Original item number/vendor P.N from order file
            source: Order source (wholefoods, unfi_west, unfi, tkmaxx)
            
        Returns:
            Mapped item number or original item if no mapping found
        """
        
        if not raw_item or not raw_item.strip():
            return "UNKNOWN"
        
        raw_item_clean = raw_item.strip()
        
        # Try database first if available
        if self.use_database and self.db_service:
            try:
                item_mapping_dict = self.db_service.get_item_mappings(source)
                
                # Try exact match first
                if raw_item_clean in item_mapping_dict:
                    return item_mapping_dict[raw_item_clean]
                
                # Try case-insensitive match
                raw_item_lower = raw_item_clean.lower()
                for key, value in item_mapping_dict.items():
                    if key.lower() == raw_item_lower:
                        return value
                        
            except Exception:
                pass  # Fall back to file-based mapping
        
        # Fallback to file-based mapping
        item_mapping_key = f"{source}_item_mapping"
        if item_mapping_key not in self.mapping_cache:
            self._load_item_mapping(source)
        
        # Get mapping
        item_mapping_dict = self.mapping_cache.get(item_mapping_key, {})
        
        # Try exact match first
        if raw_item_clean in item_mapping_dict:
            return item_mapping_dict[raw_item_clean]
        
        # Try case-insensitive match
        raw_item_lower = raw_item_clean.lower()
        for key, value in item_mapping_dict.items():
            if key.lower() == raw_item_lower:
                return value
        
        # Return original item if no mapping found
        return raw_item_clean
    
    def _load_item_mapping(self, source: str) -> None:
        """Load item mapping file for the given source"""
        
        item_mapping_file = f"mappings/{source}/item_mapping.xlsx"
        item_mapping_key = f"{source}_item_mapping"
        
        try:
            if os.path.exists(item_mapping_file):
                df = pd.read_excel(item_mapping_file)
                
                # Handle different column structures for each source
                item_mapping_dict = {}
                
                if source == 'unfi_east':
                    # For UNFI East: columns are ['UPC', 'UNFI East ', 'Description', 'Xoro Item#', 'Xoro Description']
                    # We want to map 'UNFI East ' (column 1) -> 'Xoro Item#' (column 3)
                    if len(df.columns) >= 4:
                        raw_col = df.columns[1]  # 'UNFI East ' column
                        mapped_col = df.columns[3]  # 'Xoro Item#' column
                        
                        for _, row in df.iterrows():
                            if pd.notna(row[raw_col]) and pd.notna(row[mapped_col]):
                                raw_item = str(row[raw_col]).strip()
                                mapped_item = str(row[mapped_col]).strip()
                                item_mapping_dict[raw_item] = mapped_item
                                print(f"DEBUG: Loaded item mapping: {raw_item} -> {mapped_item}")
                else:
                    # For other sources: use first two columns
                    if len(df.columns) >= 2:
                        raw_col = df.columns[0]  # First column: raw item number
                        mapped_col = df.columns[1]  # Second column: mapped item number
                        
                        for _, row in df.iterrows():
                            if pd.notna(row[raw_col]) and pd.notna(row[mapped_col]):
                                item_mapping_dict[str(row[raw_col]).strip()] = str(row[mapped_col]).strip()
                
                self.mapping_cache[item_mapping_key] = item_mapping_dict
            else:
                # Use empty mapping if file doesn't exist
                self.mapping_cache[item_mapping_key] = {}
                
        except Exception as e:
            # Use empty mapping on error
            self.mapping_cache[item_mapping_key] = {}
    
    def resolve_item_number(self, item_attributes: Dict[str, Any], source: str) -> Optional[str]:
        """
        Resolve item number using priority-based lookup across multiple key types.
        
        This is the NEW enhanced method that uses the database-backed priority system
        to resolve items using multiple attribute types in priority order.
        
        Args:
            item_attributes: Dictionary with potential keys like:
                           {'vendor_item': 'ABC123', 'upc': '123456789', 'ean': '0123456789012'}
            source: Source system (e.g., 'kehe', 'wholefoods', 'unfi_east', 'unfi_west')
            
        Returns:
            Mapped item number if found using priority resolution, None if not found
        """
        
        if not item_attributes or not source:
            return None
        
        # Clean and prepare lookup attributes
        lookup_attributes = {}
        for key, value in item_attributes.items():
            if value and str(value).strip():
                # Normalize key names to standard types
                normalized_key = self._normalize_key_type(key)
                if normalized_key:
                    lookup_attributes[normalized_key] = str(value).strip()
        
        if not lookup_attributes:
            return None
        
        # Use database service for priority-based resolution
        if self.use_database and self.db_service:
            try:
                resolved_item = self.db_service.resolve_item_number(lookup_attributes, source)
                if resolved_item:
                    return resolved_item
            except Exception:
                pass  # Fall back to legacy method
        
        # Fallback to legacy single-key resolution for backward compatibility
        # Try vendor_item first, then other common keys
        fallback_order = ['vendor_item', 'upc', 'ean', 'gtin', 'sku_alias']
        
        for key_type in fallback_order:
            if key_type in lookup_attributes:
                legacy_result = self.get_item_mapping(lookup_attributes[key_type], source)
                # Only return if we actually found a mapping (not just the original value)
                if legacy_result != lookup_attributes[key_type]:
                    return legacy_result
        
        return None
    
    def _normalize_key_type(self, key: str) -> Optional[str]:
        """
        Normalize various key type names to standard format.
        
        Args:
            key: Raw key name from parser (e.g., 'Vendor Item#', 'UPC Code', 'Item Number')
            
        Returns:
            Standardized key type or None if not recognized
        """
        
        if not key:
            return None
        
        key_lower = key.lower().strip()
        
        # Vendor item variations
        if any(term in key_lower for term in ['vendor', 'item', 'product', 'part', 'model']):
            if 'upc' not in key_lower and 'ean' not in key_lower:
                return 'vendor_item'
        
        # UPC variations  
        if 'upc' in key_lower:
            return 'upc'
        
        # EAN variations
        if 'ean' in key_lower:
            return 'ean'
        
        # GTIN variations
        if 'gtin' in key_lower:
            return 'gtin'
        
        # SKU variations
        if 'sku' in key_lower:
            return 'sku_alias'
        
        # Direct key type matches
        standard_keys = ['vendor_item', 'upc', 'ean', 'gtin', 'sku_alias']
        if key_lower in standard_keys:
            return key_lower
        
        return 'vendor_item'  # Default fallback
