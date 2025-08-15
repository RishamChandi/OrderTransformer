"""
KEHE - SPS Parser for KEHE CSV order files
Handles CSV format with PO data and line items
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import io
import os
from .base_parser import BaseParser
from utils.mapping_utils import MappingUtils


class KEHEParser(BaseParser):
    """Parser for KEHE - SPS CSV order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "KEHE - SPS"
        self.mapping_utils = MappingUtils()
        
        # Load KEHE customer mapping
        self.customer_mapping = self._load_customer_mapping()
        
    def _load_customer_mapping(self) -> Dict[str, str]:
        """Load KEHE customer mapping from CSV file"""
        try:
            mapping_file = os.path.join('mappings', 'kehe_customer_mapping.csv')
            if os.path.exists(mapping_file):
                df = pd.read_csv(mapping_file)
                # Create mapping from SPS Customer# to Store Mapping
                mapping = {}
                for _, row in df.iterrows():
                    sps_customer = str(row['SPS Customer#']).strip()
                    store_mapping = str(row['Store Mapping']).strip()
                    mapping[sps_customer] = store_mapping
                print(f"✅ Loaded {len(mapping)} KEHE customer mappings")
                return mapping
            else:
                print("⚠️ KEHE customer mapping file not found")
                return {}
        except Exception as e:
            print(f"❌ Error loading KEHE customer mapping: {e}")
            return {}
    
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
            
            # Get header information from the first 'H' record
            header_df = df[df['Record Type'] == 'H']
            if header_df.empty:
                return None
                
            header_info = header_df.iloc[0]
            
            # Filter for line item records (Record Type = 'D') and discount records (Record Type = 'I')
            line_items_df = df[df['Record Type'] == 'D'].copy()
            discount_records_df = df[df['Record Type'] == 'I'].copy()
            
            if line_items_df.empty:
                return None
            
            orders = []
            
            # Process each line item with potential discounts
            for idx, row in line_items_df.iterrows():
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
                    
                    # Extract Ship To Location for customer mapping
                    ship_to_location = str(header_info.get('Ship To Location', '')).strip()
                    
                    # Debug: Print all available header columns to see exact column names
                    print(f"DEBUG: Available header columns: {list(header_info.index)}")
                    print(f"DEBUG: Ship To Location value: '{ship_to_location}'")
                    print(f"DEBUG: Available mapping keys: {list(self.customer_mapping.keys())}")
                    
                    # Map Ship To Location to customer using the mapping file
                    customer_name = "IDI - Richmond"  # Default value
                    if ship_to_location and ship_to_location in self.customer_mapping:
                        customer_name = self.customer_mapping[ship_to_location]
                        print(f"DEBUG: Mapped Ship To Location '{ship_to_location}' to customer '{customer_name}'")
                    else:
                        print(f"DEBUG: No mapping found for Ship To Location '{ship_to_location}', using default '{customer_name}'")
                    
                    # Calculate total price before applying discounts
                    line_total = unit_price * quantity
                    
                    # Check for discount record that follows this line item
                    discount_amount = 0
                    discount_info = ""
                    
                    # Look for the next 'I' record that applies to this line
                    next_discount = self._find_next_discount_record(df, idx, discount_records_df)
                    if next_discount is not None:
                        discount_amount, discount_info = self._calculate_discount(next_discount, line_total, unit_price)
                    
                    # Apply discount to get final total
                    final_total = line_total - discount_amount
                    
                    # Build order data
                    order_data = {
                        'order_number': str(header_info.get('PO Number', '')),
                        'order_date': po_date,
                        'delivery_date': delivery_date,
                        'customer_name': customer_name,  # Use mapped customer from Ship To Location
                        'raw_customer_name': str(header_info.get('Ship To Name', 'KEHE DISTRIBUTORS')),
                        'ship_to_location': ship_to_location,  # Add ship to location for reference
                        'item_number': mapped_item,
                        'raw_item_number': kehe_number,
                        'item_description': description,
                        'quantity': int(quantity),
                        'unit_price': unit_price,
                        'total_price': final_total,
                        'original_total': line_total,
                        'discount_amount': discount_amount,
                        'discount_info': discount_info,
                        'source_file': filename
                    }
                    
                    orders.append(order_data)
                    
                except Exception as e:
                    print(f"Error processing line item: {e}")
                    continue
            
            return orders if orders else None
            
        except Exception as e:
            raise ValueError(f"Error parsing KEHE CSV: {str(e)}")
    
    def _find_next_discount_record(self, df: pd.DataFrame, current_idx: int, discount_records_df: pd.DataFrame) -> Optional[pd.Series]:
        """
        Find the discount record (type 'I') that applies to the current line item (type 'D')
        Discount records typically follow immediately after the line item they apply to
        """
        try:
            # Get all rows after current line item
            remaining_rows = df.loc[current_idx + 1:]
            
            # Find the first 'I' record after this line item
            for idx, row in remaining_rows.iterrows():
                if row.get('Record Type') == 'I':
                    return row
                elif row.get('Record Type') == 'D':
                    # Hit another line item, so no discount for current item
                    break
            
            return None
        except Exception:
            return None
    
    def _calculate_discount(self, discount_row: pd.Series, line_total: float, unit_price: float) -> tuple[float, str]:
        """
        Calculate discount amount based on discount record
        Returns: (discount_amount, discount_description)
        """
        try:
            discount_amount = 0
            discount_info = ""
            
            # Check for percentage discount (column BG - typically percentage value)
            percentage_discount = self.clean_numeric_value(str(discount_row.get('BG', '0')))
            if percentage_discount > 0:
                discount_amount = (line_total * percentage_discount) / 100
                discount_info = f"Percentage: {percentage_discount}%"
            
            # Check for flat/rate discount (column BH - typically flat amount)
            flat_discount = self.clean_numeric_value(str(discount_row.get('BH', '0')))
            if flat_discount > 0:
                discount_amount = flat_discount
                discount_info = f"Flat: ${flat_discount:.2f}"
            
            # If both are present, use the larger discount (benefit customer)
            if percentage_discount > 0 and flat_discount > 0:
                percentage_amount = (line_total * percentage_discount) / 100
                if flat_discount > percentage_amount:
                    discount_amount = flat_discount
                    discount_info = f"Flat: ${flat_discount:.2f} (better than {percentage_discount}%)"
                else:
                    discount_amount = percentage_amount
                    discount_info = f"Percentage: {percentage_discount}% (better than ${flat_discount:.2f})"
            
            # Get discount description if available
            discount_desc = str(discount_row.get('Product/Item Description', ''))
            if discount_desc and discount_desc.strip():
                discount_info += f" - {discount_desc.strip()}"
            
            return discount_amount, discount_info
            
        except Exception as e:
            print(f"Error calculating discount: {e}")
            return 0, ""
    
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