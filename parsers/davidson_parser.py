"""
Davidson Parser for Davidson CSV order files
Handles CSV format with PO data and line items (similar to KEHE - SPS)
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import io
from .base_parser import BaseParser
from utils.mapping_utils import MappingUtils


class DavidsonParser(BaseParser):
    """Parser for Davidson CSV order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "Davidson"
        self.mapping_utils = MappingUtils()
        # Initialize customer_mapping as empty dict for backward compatibility
        self.customer_mapping = {}
        
    
    def parse(self, file_content, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse Davidson CSV file and return structured order data
        
        Args:
            file_content: Raw file content (bytes or string)
            file_extension: File format ('csv' expected)
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
            except pd.errors.ParserError as e:
                # Handle files with inconsistent columns - use on_bad_lines parameter for newer pandas
                try:
                    df = pd.read_csv(io.StringIO(content_str), on_bad_lines='skip')
                except TypeError:
                    # Fallback for older pandas versions - just read normally
                    df = pd.read_csv(io.StringIO(content_str))
            except Exception as e:
                print(f"ERROR: Failed to read CSV file: {e}")
                raise ValueError(f"Failed to parse CSV file: {str(e)}")
            
            # Check if required columns exist
            if 'Record Type' not in df.columns:
                raise ValueError("CSV file missing required 'Record Type' column")
            
            # Get header information from the first 'H' record
            header_df = df[df['Record Type'] == 'H']
            if header_df.empty:
                raise ValueError("No header record (Record Type='H') found in CSV file")
                
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
                    item_number = str(row.get("Buyer's Catalog or Stock Keeping #", '')).strip()
                    if not item_number:
                        item_number = str(row.get('Buyers Catalog or Stock Keeping #', '')).strip()
                    
                    # Clean item number - remove .0 if present and ensure leading zeros
                    if item_number.endswith('.0'):
                        item_number = item_number[:-2]
                    
                    quantity = self.clean_numeric_value(str(row.get('Qty Ordered', '0')))
                    unit_price = self.clean_numeric_value(str(row.get('Unit Price', '0')))
                    description = str(row.get('Product/Item Description', '')).strip()
                    
                    # Skip invalid entries
                    if not item_number or quantity <= 0:
                        continue
                    
                    # Use priority-based multi-key resolution system
                    # Extract multiple key types from Davidson data
                    item_attributes = {
                        'vendor_item': item_number  # Primary item number
                    }
                    
                    # Add vendor style if available (could be UPC or other identifier)
                    vendor_style = str(row.get('Vendor Style', '')).strip()
                    if vendor_style and vendor_style != 'nan' and vendor_style != '':
                        # Try to determine if vendor style is UPC (typically 12 digits)
                        if vendor_style.isdigit() and len(vendor_style) == 12:
                            item_attributes['upc'] = vendor_style
                        else:
                            item_attributes['sku_alias'] = vendor_style
                    
                    # Add UPC if available
                    upc = str(row.get('UPC/EAN', '')).strip()
                    if upc and upc != 'nan' and upc != '':
                        item_attributes['upc'] = upc
                    
                    # Use enhanced mapping resolution with priority system
                    mapped_item = self.mapping_utils.resolve_item_number(item_attributes, 'davidson')
                    
                    if mapped_item:
                        print(f"DEBUG: Davidson Priority Mapping: {item_attributes} → '{mapped_item}'")
                    else:
                        mapped_item = item_number  # Fallback to original number
                        print(f"DEBUG: No Davidson mapping found for '{item_number}', using raw number")
                    
                    # Extract dates
                    po_date = self.parse_date(str(header_info.get('PO Date', '')))
                    requested_delivery_date = self.parse_date(str(header_info.get('Requested Delivery Date', '')))
                    ship_date = self.parse_date(str(header_info.get('Ship Dates', '')))
                    
                    # Use the most appropriate date for shipping
                    delivery_date = requested_delivery_date or ship_date or po_date
                    
                    # Extract Ship To Location for customer mapping
                    ship_to_location_raw = str(header_info.get('Ship To Location', '')).strip()
                    
                    # Clean Ship To Location value - remove .0 suffix and ensure proper format
                    ship_to_location = ship_to_location_raw
                    if ship_to_location.endswith('.0'):
                        ship_to_location = ship_to_location[:-2]
                    
                    # Use customer mapping for customer names (separate from store mappings)
                    customer_name = "IDI - Richmond"  # Default value
                    if ship_to_location:
                        # Try database customer mapping first
                        db_mapped_customer = self.mapping_utils.get_customer_mapping(ship_to_location, 'davidson')
                        if db_mapped_customer and db_mapped_customer != 'UNKNOWN':
                            customer_name = db_mapped_customer
                            print(f"DEBUG: Davidson DB Customer Mapping: '{ship_to_location}' → '{customer_name}'")
                        # Fallback to legacy CSV mapping
                        elif ship_to_location in self.customer_mapping:
                            customer_name = self.customer_mapping[ship_to_location]
                            print(f"DEBUG: Davidson Legacy Customer Mapping: '{ship_to_location}' → '{customer_name}'")
                        else:
                            print(f"DEBUG: No Davidson customer mapping found for '{ship_to_location}' (raw: '{ship_to_location_raw}'), using default: '{customer_name}'")
                    
                    # Calculate total price before applying discounts
                    line_total = unit_price * quantity
                    
                    # Check for discount record that follows this line item
                    discount_amount = 0
                    discount_info = ""
                    
                    # Look for the next 'I' record that applies to this line
                    next_discount = self._find_next_discount_record(df, int(idx), discount_records_df)
                    if next_discount is not None:
                        discount_amount, discount_info = self._calculate_discount(next_discount, line_total, unit_price)
                    
                    # Apply discount to get final total
                    final_total = line_total - discount_amount
                    
                    # Get store mapping for SaleStoreName and StoreName fields
                    # For Davidson, use store mapping (separate from customer mapping)
                    store_name = "KL - Richmond"  # Default for Davidson orders
                    if ship_to_location:
                        # Try database store mapping first
                        db_mapped_store = self.mapping_utils.get_store_mapping(ship_to_location, 'davidson')
                        if db_mapped_store and db_mapped_store != 'UNKNOWN' and db_mapped_store != ship_to_location:
                            store_name = db_mapped_store
                            print(f"DEBUG: Davidson DB Store Mapping: '{ship_to_location}' → '{store_name}'")
                        else:
                            print(f"DEBUG: No Davidson store mapping found for '{ship_to_location}', using default: '{store_name}'")
                    
                    # Build order data
                    order_data = {
                        'order_number': str(header_info.get('PO Number', '')),
                        'order_date': po_date,
                        'delivery_date': delivery_date,
                        'customer_name': customer_name,  # Use mapped company name from Ship To Location
                        'store_name': store_name,  # Use store mapping, not customer mapping
                        'raw_customer_name': str(header_info.get('Ship To Name', 'Davidson')),
                        'ship_to_location': ship_to_location,  # Add ship to location for reference
                        'item_number': mapped_item,
                        'raw_item_number': item_number,
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
            raise ValueError(f"Error parsing Davidson CSV: {str(e)}")
    
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
            
            # Check for percentage discount
            percentage_discount = self.clean_numeric_value(str(discount_row.get('Allow/Charge %', '0')))
            if percentage_discount > 0:
                discount_amount = (line_total * percentage_discount) / 100
                discount_info = f"Percentage: {percentage_discount}%"
            
            # Check for flat/rate discount
            flat_discount = self.clean_numeric_value(str(discount_row.get('Allow/Charge amt', '0')))
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
            discount_desc = str(discount_row.get('Allow/Charge Desc', ''))
            if discount_desc and discount_desc.strip():
                discount_info += f" - {discount_desc.strip()}"
            
            return discount_amount, discount_info
            
        except Exception as e:
            print(f"Error calculating discount: {e}")
            return 0, ""

