"""
Utilities for handling customer and store name mappings
"""

import pandas as pd
import os
from typing import Optional, Dict

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
        
        # Return original name if no mapping found
        return raw_name_clean
    
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
