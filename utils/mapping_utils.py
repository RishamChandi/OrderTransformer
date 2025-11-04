"""
Utilities for handling customer and store name mappings
"""

import pandas as pd
import os
import re
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
            source: Order source (wholefoods, unfi_west, unfi_east, tkmaxx, kehe)
            
        Returns:
            Mapped customer name or 'UNKNOWN' if no mapping found
        """
        
        if not raw_customer_id or not str(raw_customer_id).strip():
            return "UNKNOWN"
        
        # Normalize the raw customer ID - remove .0 suffix if present
        raw_customer_id_clean = str(raw_customer_id).strip()
        if raw_customer_id_clean.endswith('.0') and raw_customer_id_clean[:-2].replace('.', '').isdigit():
            raw_customer_id_clean = raw_customer_id_clean[:-2]
        
        raw_customer_id_lower = raw_customer_id_clean.lower()
        
        # Try database first if available
        if self.use_database and self.db_service:
            try:
                mapping_dict = self.db_service.get_customer_mappings(source)
                
                # Debug output for KeHE and UNFI East
                if source.lower() in ['kehe', 'kehe_sps', 'kehe - sps', 'unfi_east', 'unfi east']:
                    print(f"DEBUG: Looking up customer mapping for '{raw_customer_id_clean}' (source: {source})")
                    print(f"DEBUG: Found {len(mapping_dict)} customer mappings")
                    if len(mapping_dict) > 0:
                        sample_keys = list(mapping_dict.keys())[:10]
                        print(f"DEBUG: Sample mapping keys (first 10): {sample_keys}")
                        # Also show all keys if there aren't too many
                        if len(mapping_dict) <= 20:
                            print(f"DEBUG: All mapping keys: {list(mapping_dict.keys())}")
                    else:
                        print(f"DEBUG: WARNING - No customer mappings found in database for source '{source}'")
                
                # Try exact match first
                if raw_customer_id_clean in mapping_dict:
                    print(f"DEBUG: Found exact match for '{raw_customer_id_clean}'")
                    return mapping_dict[raw_customer_id_clean]
                
                # Try with .0 suffix if the clean version doesn't match (for backward compatibility)
                if raw_customer_id_clean + '.0' in mapping_dict:
                    print(f"DEBUG: Found match with .0 suffix for '{raw_customer_id_clean}'")
                    return mapping_dict[raw_customer_id_clean + '.0']
                
                # Try case-insensitive exact match
                for key, value in mapping_dict.items():
                    if str(key).lower() == raw_customer_id_lower:
                        return value
                
                # For UNFI East: Try matching the code at the end of the key (e.g., "128 RCH" matches "RCH")
                # This handles cases where database has "128 RCH" but parser extracts just "RCH"
                if source.lower() in ['unfi_east', 'unfi east']:
                    # First, try exact match (case-insensitive)
                    for key, value in mapping_dict.items():
                        key_str = str(key).strip()
                        key_lower = key_str.lower()
                        if key_lower == raw_customer_id_lower:
                            print(f"DEBUG: Found exact case-insensitive match: '{raw_customer_id_clean}' = '{key_str}'")
                            return value
                    
                    # Try matching code as suffix/end of key (most common case)
                    # Examples: "RCH" matches "128 RCH", "HOW" matches "129 HOW", "RCH" matches "RCH"
                    for key, value in mapping_dict.items():
                        key_str = str(key).strip()
                        key_lower = key_str.lower()
                        
                        # Check if key ends with the code (with or without space prefix)
                        if key_lower.endswith(' ' + raw_customer_id_lower):
                            # Matches "128 RCH" -> "RCH"
                            print(f"DEBUG: Matched '{raw_customer_id_clean}' to key '{key_str}' (suffix match with space)")
                            return value
                        elif key_lower.endswith(raw_customer_id_lower):
                            # Check if it's a complete word match (not partial like "RCH" matching "RICH")
                            # Verify it's either an exact match or preceded by space/non-letter
                            if key_lower == raw_customer_id_lower:
                                # Already handled above, but keep for safety
                                continue
                            elif len(key_lower) > len(raw_customer_id_lower):
                                # Check if the character before the match is a space or non-letter
                                char_before = key_lower[-len(raw_customer_id_lower)-1] if len(key_lower) > len(raw_customer_id_lower) else ''
                                if char_before == ' ' or not char_before.isalnum():
                                    print(f"DEBUG: Matched '{raw_customer_id_clean}' to key '{key_str}' (suffix match)")
                                    return value
                        
                        # Check if key starts with code followed by space
                        if key_lower.startswith(raw_customer_id_lower + ' '):
                            print(f"DEBUG: Matched '{raw_customer_id_clean}' to key '{key_str}' (prefix match)")
                            return value
                        
                        # Extract code from key if it follows pattern "NUMBER CODE" or "CODE NUMBER" (e.g., "128 RCH" -> "RCH")
                        if ' ' in key_lower:
                            parts = key_lower.split()
                            # Check if last part matches
                            if len(parts) >= 1 and parts[-1] == raw_customer_id_lower:
                                print(f"DEBUG: Matched '{raw_customer_id_clean}' to key '{key_str}' (extracted code from end)")
                                return value
                            # Check if first part matches (for patterns like "RCH 128")
                            if len(parts) >= 1 and parts[0] == raw_customer_id_lower:
                                print(f"DEBUG: Matched '{raw_customer_id_clean}' to key '{key_str}' (extracted code from start)")
                                return value
                
                # Try partial match (key contains raw_customer_id or vice versa) - but only for UNFI East
                # This is a last resort and should be more careful to avoid false matches
                if source.lower() in ['unfi_east', 'unfi east']:
                    for key, value in mapping_dict.items():
                        key_lower = str(key).lower()
                        # Only match if the raw_customer_id is a complete word in the key
                        # This prevents "RCH" from matching "RICH" incorrectly
                        if raw_customer_id_lower in key_lower:
                            # Check if it's a word boundary match
                            pattern = r'\b' + re.escape(raw_customer_id_lower) + r'\b'
                            if re.search(pattern, key_lower):
                                print(f"DEBUG: Matched '{raw_customer_id_clean}' to key '{key}' (partial word match)")
                                return value
                        
            except Exception as e:
                # Log error for debugging but don't raise
                print(f"DEBUG: Error in get_customer_mapping for {source}: {e}")
                import traceback
                traceback.print_exc()
                pass
        
        # Fallback: return UNKNOWN if no mapping found
        if source.lower() in ['unfi_east', 'unfi east']:
            print(f"DEBUG: FAILED to find customer mapping for '{raw_customer_id_clean}' (source: {source})")
            if self.use_database and self.db_service:
                try:
                    mapping_dict = self.db_service.get_customer_mappings(source)
                    if mapping_dict:
                        print(f"DEBUG: Available keys in database: {sorted(mapping_dict.keys())}")
                    else:
                        print(f"DEBUG: No mappings returned from database for source '{source}'")
                except:
                    pass
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
            source: Order source (wholefoods, unfi_west, unfi_east, tkmaxx, kehe)
            
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
                
                # For Whole Foods: Try variations with spaces/dashes removed
                # This handles cases where item is "13 025 24" but mapping is "1302524"
                if source.lower() in ['wholefoods', 'whole foods', 'whole_foods']:
                    # Try without spaces
                    item_no_spaces = raw_item_clean.replace(' ', '')
                    if item_no_spaces in item_mapping_dict:
                        print(f"DEBUG: Found mapping for '{raw_item_clean}' by removing spaces -> '{item_no_spaces}'")
                        return item_mapping_dict[item_no_spaces]
                    
                    # Try without dashes
                    item_no_dashes = raw_item_clean.replace('-', '')
                    if item_no_dashes in item_mapping_dict:
                        print(f"DEBUG: Found mapping for '{raw_item_clean}' by removing dashes -> '{item_no_dashes}'")
                        return item_mapping_dict[item_no_dashes]
                    
                    # Try without both spaces and dashes
                    item_normalized = raw_item_clean.replace(' ', '').replace('-', '')
                    if item_normalized in item_mapping_dict:
                        print(f"DEBUG: Found mapping for '{raw_item_clean}' by removing spaces and dashes -> '{item_normalized}'")
                        return item_mapping_dict[item_normalized]
                    
                    # Try reverse lookup: check if any key matches when normalized
                    for key, value in item_mapping_dict.items():
                        key_normalized = str(key).replace(' ', '').replace('-', '')
                        if key_normalized == item_normalized:
                            print(f"DEBUG: Found mapping for '{raw_item_clean}' via normalized match: '{key}' -> '{value}'")
                            return value
                        
            except Exception as e:
                print(f"DEBUG: Error in get_item_mapping database lookup: {e}")
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
        
        # For Whole Foods: Try variations with spaces/dashes removed in file-based mapping too
        if source.lower() in ['wholefoods', 'whole foods', 'whole_foods']:
            item_no_spaces = raw_item_clean.replace(' ', '')
            if item_no_spaces in item_mapping_dict:
                return item_mapping_dict[item_no_spaces]
            
            item_no_dashes = raw_item_clean.replace('-', '')
            if item_no_dashes in item_mapping_dict:
                return item_mapping_dict[item_no_dashes]
            
            item_normalized = raw_item_clean.replace(' ', '').replace('-', '')
            if item_normalized in item_mapping_dict:
                return item_mapping_dict[item_normalized]
            
            # Try reverse lookup
            for key, value in item_mapping_dict.items():
                key_normalized = str(key).replace(' ', '').replace('-', '')
                if key_normalized == item_normalized:
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
