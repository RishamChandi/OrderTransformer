"""
KEHE - SPS Parser for KEHE CSV order files
Handles CSV format with PO data and line items
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import io
from .base_parser import BaseParser
from utils.mapping_utils import MappingUtils


class KEHEParser(BaseParser):
    """Parser for KEHE - SPS CSV order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "KEHE - SPS"
        self.mapping_utils = MappingUtils()
    
    def parse(self, file_content, file_format: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse KEHE CSV file and return structured order data
        
        Args:
            file_content: Raw file content (bytes or string)
            file_format: File format ('csv' expected)
            filename: Name of the source file
            
        Returns:
            List of order dictionaries with parsed data
        """
        try:
            # Handle different content types
            if isinstance(file_content, bytes):
                content_str = file_content.decode('utf-8-sig')
            else:
                content_str = file_content
            
            # Read CSV using pandas with error handling for inconsistent columns
            try:
                df = pd.read_csv(io.StringIO(content_str))
            except pd.errors.ParserError:
                # Handle files with inconsistent columns - use on_bad_lines parameter for newer pandas
                try:
                    df = pd.read_csv(io.StringIO(content_str), on_bad_lines='skip')
                except TypeError:
                    # Fallback for older pandas versions
                    df = pd.read_csv(io.StringIO(content_str), error_bad_lines=False, warn_bad_lines=False)
            
            # Filter for line item records only (Record Type = 'D')
            line_items_df = df[df['Record Type'] == 'D'].copy()
            
            if line_items_df.empty:
                return None
            
            # Get header information from the first 'H' record
            header_df = df[df['Record Type'] == 'H']
            if header_df.empty:
                return None
                
            header_info = header_df.iloc[0]
            
            orders = []
            
            # Process each line item
            for _, row in line_items_df.iterrows():
                try:
                    # Extract line item data - handle different column name variations
                    kehe_number = str(row.get('Buyers Catalog or Stock Keeping #', '')).strip()
                    if not kehe_number:
                        kehe_number = str(row.get("Buyer's Catalog or Stock Keeping #", '')).strip()
                    
                    # Clean KEHE number - remove .0 if present
                    if kehe_number.endswith('.0'):
                        kehe_number = kehe_number[:-2]
                    
                    quantity = self.clean_numeric_value(str(row.get('Qty Ordered', '0')))
                    unit_price = self.clean_numeric_value(str(row.get('Unit Price', '0')))
                    description = str(row.get('Product/Item Description', '')).strip()
                    
                    # Skip invalid entries
                    if not kehe_number or quantity <= 0:
                        continue
                    
                    # Map KEHE number to Xoro item number
                    mapped_item = self.mapping_utils.get_item_mapping(kehe_number, 'kehe')
                    if not mapped_item or mapped_item == kehe_number:
                        # If no mapping found, use the raw number as fallback
                        mapped_item = kehe_number
                    
                    # Extract dates
                    po_date = self.parse_date(str(header_info.get('PO Date', '')))
                    requested_delivery_date = self.parse_date(str(header_info.get('Requested Delivery Date', '')))
                    ship_date = self.parse_date(str(header_info.get('Ship Dates', '')))
                    
                    # Use the most appropriate date for shipping
                    delivery_date = requested_delivery_date or ship_date or po_date
                    
                    # Build order data
                    order_data = {
                        'order_number': str(header_info.get('PO Number', '')),
                        'order_date': po_date,
                        'delivery_date': delivery_date,
                        'customer_name': 'IDI - Richmond',  # Hardcoded as per other parsers
                        'raw_customer_name': str(header_info.get('Ship To Name', 'KEHE DISTRIBUTORS')),
                        'item_number': mapped_item,
                        'raw_item_number': kehe_number,
                        'item_description': description,
                        'quantity': int(quantity),
                        'unit_price': unit_price,
                        'total_price': unit_price * quantity,
                        'source_file': filename
                    }
                    
                    orders.append(order_data)
                    
                except Exception as e:
                    print(f"Error processing line item: {e}")
                    continue
            
            return orders if orders else None
            
        except Exception as e:
            raise ValueError(f"Error parsing KEHE CSV: {str(e)}")
    
    def _extract_line_items_from_csv(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract line items from KEHE CSV DataFrame"""
        line_items = []
        
        # Filter for line item records (Record Type = 'D')
        item_rows = df[df['Record Type'] == 'D']
        
        for _, row in item_rows.iterrows():
            try:
                # Extract item data
                kehe_number = str(row.get('Buyers Catalog or Stock Keeping #', '')).strip()
                if not kehe_number:
                    kehe_number = str(row.get("Buyer's Catalog or Stock Keeping #", '')).strip()
                
                if not kehe_number:
                    continue
                
                quantity = self.clean_numeric_value(str(row.get('Qty Ordered', '0')))
                unit_price = self.clean_numeric_value(str(row.get('Unit Price', '0')))
                description = str(row.get('Product/Item Description', '')).strip()
                
                line_items.append({
                    'kehe_number': kehe_number,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'description': description,
                    'vendor_style': str(row.get('Vendor Style', '')).strip()
                })
                
            except Exception as e:
                print(f"Error extracting line item: {e}")
                continue
        
        return line_items