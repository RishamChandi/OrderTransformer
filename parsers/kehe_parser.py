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
        
        # Load legacy KEHE mappings for backward compatibility
        # NEW: These now serve as fallbacks to the database-first system
        self.customer_mapping = self._load_customer_mapping()
        self.item_mapping = self._load_item_mapping()
        
    def _load_customer_mapping(self) -> Dict[str, str]:
        """Load KEHE customer mapping from CSV file"""
        try:
            mapping_file = os.path.join('mappings', 'kehe_customer_mapping.csv')
            if os.path.exists(mapping_file):
                # Force SPS Customer# to be read as string to preserve leading zeros
                self.mapping_df = pd.read_csv(mapping_file, dtype={'SPS Customer#': 'str'})
                # Create mapping from SPS Customer# to CompanyName (for CustomerName field)
                mapping = {}
                for _, row in self.mapping_df.iterrows():
                    sps_customer = str(row['SPS Customer#']).strip()
                    company_name = str(row['CompanyName']).strip()
                    mapping[sps_customer] = company_name
                print(f"✅ Loaded {len(mapping)} KEHE customer mappings")
                print(f"DEBUG: Sample mapping keys: {list(mapping.keys())[:3]}")  # Show first 3 keys for verification
                return mapping
            else:
                print("⚠️ KEHE customer mapping file not found")
                return {}
        except Exception as e:
            print(f"❌ Error loading KEHE customer mapping: {e}")
            return {}
    
    def _get_store_mapping(self, ship_to_location: str) -> str:
        """Get store mapping for the given Ship To Location"""
        try:
            if hasattr(self, 'mapping_df') and self.mapping_df is not None:
                # Find the row with matching Ship To Location
                matching_row = self.mapping_df[self.mapping_df['SPS Customer#'] == ship_to_location]
                if not matching_row.empty:
                    store_mapping = str(matching_row.iloc[0]['Store Mapping']).strip()
                    print(f"DEBUG: KEHE Store Mapping: '{ship_to_location}' → '{store_mapping}'")
                    return store_mapping
            return "KL - Richmond"  # Default fallback
        except Exception as e:
            print(f"DEBUG: Error getting store mapping: {e}")
            return "KL - Richmond"  # Default fallback
    
    def parse(self, file_content, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
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
                    # Fallback for older pandas versions - just read normally
                    df = pd.read_csv(io.StringIO(content_str))
            
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
                    
                    # Clean KEHE number - remove .0 if present and ensure leading zeros
                    if kehe_number.endswith('.0'):
                        kehe_number = kehe_number[:-2]
                    
                    # Ensure KEHE number has proper leading zeros (should be 8 digits)
                    if kehe_number.isdigit() and len(kehe_number) < 8:
                        kehe_number = kehe_number.zfill(8)
                        print(f"DEBUG: Padded KEHE number with leading zeros: '{str(row.get('Buyers Catalog or Stock Keeping #', '')).strip()}' → '{kehe_number}'")
                    
                    quantity = self.clean_numeric_value(str(row.get('Qty Ordered', '0')))
                    unit_price = self.clean_numeric_value(str(row.get('Unit Price', '0')))
                    description = str(row.get('Product/Item Description', '')).strip()
                    
                    # Skip invalid entries
                    if not kehe_number or quantity <= 0:
                        continue
                    
                    # NEW: Use priority-based multi-key resolution system
                    # Extract multiple key types from KEHE data
                    item_attributes = {
                        'vendor_item': kehe_number  # Primary KEHE number
                    }
                    
                    # Add vendor style if available (could be UPC or other identifier)
                    vendor_style = str(row.get('Vendor Style', '')).strip()
                    if vendor_style and vendor_style != 'nan' and vendor_style != '':
                        # Try to determine if vendor style is UPC (typically 12 digits)
                        if vendor_style.isdigit() and len(vendor_style) == 12:
                            item_attributes['upc'] = vendor_style
                        else:
                            item_attributes['sku_alias'] = vendor_style
                    
                    # Use enhanced mapping resolution with priority system
                    mapped_item = self.mapping_utils.resolve_item_number(item_attributes, 'kehe')
                    
                    if mapped_item:
                        print(f"DEBUG: KEHE Priority Mapping: {item_attributes} → '{mapped_item}'")
                    else:
                        # Fallback to legacy CSV mapping for backward compatibility
                        if kehe_number in self.item_mapping:
                            mapped_item = self.item_mapping[kehe_number]
                            print(f"DEBUG: KEHE Legacy Mapping: '{kehe_number}' → '{mapped_item}'")
                        else:
                            mapped_item = kehe_number  # Final fallback to original number
                            print(f"DEBUG: No KEHE mapping found for '{kehe_number}', using raw number")
                    
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
                    
                    # Ensure it starts with 0 if it's a numeric value (KEHE Ship To Location should be 13 digits)
                    if ship_to_location.isdigit() and len(ship_to_location) == 12:
                        ship_to_location = '0' + ship_to_location
                        print(f"DEBUG: Added leading zero to Ship To Location: '{ship_to_location_raw}' → '{ship_to_location}'")
                    
                    # NEW: Use database-first store mapping resolution
                    customer_name = "IDI - Richmond"  # Default value
                    if ship_to_location:
                        # Try database-first store mapping
                        db_mapped_customer = self.mapping_utils.get_store_mapping(ship_to_location, 'kehe')
                        if db_mapped_customer and db_mapped_customer != ship_to_location:
                            customer_name = db_mapped_customer
                            print(f"DEBUG: KEHE DB Store Mapping: '{ship_to_location}' → '{customer_name}'")
                        # Fallback to legacy CSV mapping
                        elif ship_to_location in self.customer_mapping:
                            customer_name = self.customer_mapping[ship_to_location]
                            print(f"DEBUG: KEHE Legacy Customer Mapping: '{ship_to_location}' → '{customer_name}'")
                        else:
                            print(f"DEBUG: No KEHE customer mapping found for '{ship_to_location}' (raw: '{ship_to_location_raw}'), using default: '{customer_name}'")
                    
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
                    # For KEHE, use the Store Mapping from customer mapping file, not the company name
                    store_name = "KL - Richmond"  # Default for KEHE SPS orders
                    if ship_to_location and ship_to_location in self.customer_mapping:
                        # Get store mapping from the CSV file - need to reload to get Store Mapping column
                        store_name = self._get_store_mapping(ship_to_location)
                    
                    # Build order data
                    order_data = {
                        'order_number': str(header_info.get('PO Number', '')),
                        'order_date': po_date,
                        'delivery_date': delivery_date,
                        'customer_name': customer_name,  # Use mapped company name from Ship To Location
                        'store_name': store_name,  # Use store mapping, not customer mapping
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
    
    def _load_item_mapping(self) -> Dict[str, str]:
        """Load KEHE item mapping from CSV file"""
        try:
            mapping_file = os.path.join('mappings', 'kehe_item_mapping.csv')
            if os.path.exists(mapping_file):
                # Force KeHE Number to be read as string to preserve leading zeros
                df = pd.read_csv(mapping_file, dtype={'KeHE Number': 'str'})
                # Create mapping from KeHE Number to ItemNumber (Xoro item number)
                mapping = {}
                for _, row in df.iterrows():
                    kehe_number = str(row['KeHE Number']).strip()
                    item_number = str(row['ItemNumber']).strip()
                    mapping[kehe_number] = item_number
                print(f"✅ Loaded {len(mapping)} KEHE item mappings")
                print(f"DEBUG: Sample item mapping keys: {list(mapping.keys())[:3]}")  # Show first 3 keys
                return mapping
            else:
                print("⚠️ KEHE item mapping file not found")
                return {}
        except Exception as e:
            print(f"❌ Error loading KEHE item mapping: {e}")
            return {}
    
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