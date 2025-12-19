"""
VMC Parser for VMC CSV order files
Handles CSV format with PO data and line items (similar to KEHE - SPS)
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import io
from .base_parser import BaseParser
from utils.mapping_utils import MappingUtils


class VMCParser(BaseParser):
    """Parser for VMC CSV order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "VMC"
        self.mapping_utils = MappingUtils()
        # Initialize customer_mapping as empty dict for backward compatibility
        self.customer_mapping = {}
        
    
    def parse(self, file_content, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse VMC CSV file and return structured order data
        
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
            
            # Read CSV using pandas - handle inconsistent field counts
            # Some rows have extra trailing commas/fields, so we need to handle this gracefully
            try:
                # First, read the CSV with a more lenient approach
                # Use Python's csv module to normalize field counts, then convert to DataFrame
                import csv
                csv_reader = csv.reader(io.StringIO(content_str))
                rows = list(csv_reader)
                
                if not rows:
                    raise ValueError("CSV file is empty")
                
                # Get header (first row)
                header = rows[0]
                header_len = len(header)
                
                # Normalize all rows to have the same number of fields as header
                # If row has more fields, truncate; if fewer, pad with empty strings
                normalized_rows = []
                for row in rows:
                    if len(row) > header_len:
                        # Truncate extra fields
                        normalized_rows.append(row[:header_len])
                    elif len(row) < header_len:
                        # Pad with empty strings
                        normalized_rows.append(row + [''] * (header_len - len(row)))
                    else:
                        normalized_rows.append(row)
                
                # Create DataFrame from normalized rows
                df = pd.DataFrame(normalized_rows[1:], columns=header)
                df = df.astype(str)  # Convert all to string
                df = df.replace('nan', '')  # Replace 'nan' strings with empty
                
            except Exception as e:
                print(f"ERROR: Failed to read CSV file: {e}")
                raise ValueError(f"Failed to parse CSV file: {str(e)}")
            except Exception as e:
                print(f"ERROR: Failed to read CSV file: {e}")
                raise ValueError(f"Failed to parse CSV file: {str(e)}")
            
            # Check if required columns exist
            if 'Record Type' not in df.columns:
                available_cols = ', '.join(df.columns[:10].tolist())  # Show first 10 columns
                raise ValueError(
                    f"CSV file missing required 'Record Type' column. "
                    f"Available columns: {available_cols}{'...' if len(df.columns) > 10 else ''}. "
                    f"Expected format: CSV with Record Type column containing 'H' (header), 'D' (detail), and 'I' (invoice/discount) records."
                )
            
            # Strip whitespace from Record Type column to handle any formatting issues
            # Use str.strip() on the Series to handle any whitespace
            df['Record Type'] = df['Record Type'].str.strip()
            
            # Debug: Print Record Type values for troubleshooting
            unique_record_types = df['Record Type'].unique().tolist()
            print(f"DEBUG: Found Record Types after stripping: {unique_record_types}")
            
            # Get header information from the first 'H' record (case-insensitive)
            header_df = df[df['Record Type'].str.strip().str.upper() == 'H']
            if header_df.empty:
                record_types = sorted(df['Record Type'].unique().tolist())
                # Filter out nan/empty values for cleaner error message
                record_types = [rt for rt in record_types if rt and str(rt).strip() and str(rt).lower() != 'nan']
                raise ValueError(
                    f"No header record (Record Type='H') found in CSV file. "
                    f"Found Record Types: {record_types}. "
                    f"Expected at least one 'H' record for header information."
                )
                
            header_info = header_df.iloc[0]
            
            # Filter for line item records (Record Type = 'D') and discount records (Record Type = 'I')
            line_items_df = df[df['Record Type'] == 'D'].copy()
            discount_records_df = df[df['Record Type'] == 'I'].copy()
            
            if line_items_df.empty:
                record_types = sorted(df['Record Type'].unique().tolist())
                # Filter out nan/empty values for cleaner error message
                record_types = [rt for rt in record_types if rt and str(rt).strip() and str(rt).lower() != 'nan']
                raise ValueError(
                    f"No line item records (Record Type='D') found in CSV file. "
                    f"Found Record Types: {record_types}. "
                    f"Expected at least one 'D' record for line items."
                )
            
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
                    # Extract multiple key types from VMC data
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
                    mapped_item = self.mapping_utils.resolve_item_number(item_attributes, 'vmc')
                    
                    if mapped_item:
                        print(f"DEBUG: VMC Priority Mapping: {item_attributes} -> '{mapped_item}'")
                    else:
                        mapped_item = item_number  # Fallback to original number
                        print(f"DEBUG: No VMC mapping found for '{item_number}', using raw number")
                    
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
                        db_mapped_customer = self.mapping_utils.get_customer_mapping(ship_to_location, 'vmc')
                        if db_mapped_customer and db_mapped_customer != 'UNKNOWN':
                            customer_name = db_mapped_customer
                            print(f"DEBUG: VMC DB Customer Mapping: '{ship_to_location}' -> '{customer_name}'")
                        # Fallback to legacy CSV mapping
                        elif ship_to_location in self.customer_mapping:
                            customer_name = self.customer_mapping[ship_to_location]
                            print(f"DEBUG: VMC Legacy Customer Mapping: '{ship_to_location}' -> '{customer_name}'")
                        else:
                            print(f"DEBUG: No VMC customer mapping found for '{ship_to_location}' (raw: '{ship_to_location_raw}'), using default: '{customer_name}'")
                    
                    # Calculate total price before applying discounts
                    line_total = unit_price * quantity
                    
                    # Check for discount record that follows this line item
                    discount_amount = 0
                    discount_info = ""
                    
                    # Look for the next 'I' record that applies to this line
                    next_discount = self._find_next_discount_record(df, int(idx), discount_records_df)
                    if next_discount is not None:
                        discount_amount, discount_info = self._calculate_discount(next_discount, line_total, unit_price, quantity)
                    
                    # Apply discount to get final total
                    final_total = line_total - discount_amount
                    
                    # Get store mapping for SaleStoreName and StoreName fields
                    # For VMC, use store mapping (separate from customer mapping)
                    store_name = "PSS - NJ"  # Default for VMC orders
                    if ship_to_location:
                        # Try database store mapping first
                        db_mapped_store = self.mapping_utils.get_store_mapping(ship_to_location, 'vmc')
                        if db_mapped_store and db_mapped_store != 'UNKNOWN' and db_mapped_store != ship_to_location:
                            store_name = db_mapped_store
                            print(f"DEBUG: VMC DB Store Mapping: '{ship_to_location}' -> '{store_name}'")
                        else:
                            print(f"DEBUG: No VMC store mapping found for '{ship_to_location}', using default: '{store_name}'")
                    
                    # Build order data
                    order_data = {
                        'order_number': str(header_info.get('PO Number', '')),
                        'order_date': po_date,
                        'delivery_date': delivery_date,
                        'customer_name': customer_name,  # Use mapped company name from Ship To Location
                        'store_name': store_name,  # Use store mapping, not customer mapping
                        'raw_customer_name': str(header_info.get('Ship To Name', 'VMC')),
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
            raise ValueError(f"Error parsing VMC CSV: {str(e)}")
    
    def _find_next_discount_record(self, df: pd.DataFrame, current_idx: int, discount_records_df: pd.DataFrame) -> Optional[pd.Series]:
        """
        Find the discount record (type 'I') that applies to the current line item (type 'D')
        Discount records typically follow immediately after the line item they apply to
        """
        try:
            # Get all rows after current line item
            remaining_rows = df.loc[current_idx + 1:]
            
            # Find the first 'I' record after this line item
            # Ensure Record Type is string and stripped for comparison
            for idx, row in remaining_rows.iterrows():
                record_type = str(row.get('Record Type', '')).strip()
                if record_type == 'I':
                    return row
                elif record_type == 'D':
                    # Hit another line item, so no discount for current item
                    break
            
            return None
        except Exception:
            return None
    
    def _calculate_discount(self, discount_row: pd.Series, line_total: float, unit_price: float, quantity: float = 0) -> tuple[float, str]:
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
            
            # Check for flat amount discount
            flat_discount = self.clean_numeric_value(str(discount_row.get('Allow/Charge amt', '0')))
            if flat_discount > 0:
                discount_amount = flat_discount
                discount_info = f"Flat: ${flat_discount:.2f}"
            
            # Check for rate-based discount (per-unit rate)
            rate_discount = self.clean_numeric_value(str(discount_row.get('Allow/Charge Rate', '0')))
            rate_qty = self.clean_numeric_value(str(discount_row.get('Allow/Charge Qty', '0')))
            if rate_discount > 0:
                # If Qty is specified in discount record, use it; otherwise use the line item quantity
                if rate_qty > 0:
                    rate_amount = rate_discount * rate_qty
                else:
                    # Use the actual quantity from the line item
                    rate_amount = rate_discount * quantity if quantity > 0 else 0
                
                # Only use rate if it's better than existing discount
                if rate_amount > discount_amount:
                    discount_amount = rate_amount
                    discount_info = f"Rate: ${rate_discount:.2f} per unit (total: ${rate_amount:.2f})"
            
            # If multiple discount types are present, use the largest (benefit customer)
            discount_options = []
            if percentage_discount > 0:
                percentage_amount = (line_total * percentage_discount) / 100
                discount_options.append(('percentage', percentage_amount, f"Percentage: {percentage_discount}%"))
            if flat_discount > 0:
                discount_options.append(('flat', flat_discount, f"Flat: ${flat_discount:.2f}"))
            if rate_discount > 0:
                if rate_qty > 0:
                    rate_amount = rate_discount * rate_qty
                else:
                    rate_amount = rate_discount * quantity if quantity > 0 else 0
                discount_options.append(('rate', rate_amount, f"Rate: ${rate_discount:.2f} per unit"))
            
            if len(discount_options) > 1:
                # Use the largest discount
                best_option = max(discount_options, key=lambda x: x[1])
                discount_amount = best_option[1]
                discount_info = best_option[2]
                if len(discount_options) > 1:
                    other_options = [opt[2] for opt in discount_options if opt != best_option]
                    discount_info += f" (better than {', '.join(other_options)})"
            
            # Get discount description if available
            discount_desc = str(discount_row.get('Allow/Charge Desc', ''))
            if discount_desc and discount_desc.strip():
                discount_info += f" - {discount_desc.strip()}"
            
            return discount_amount, discount_info
            
        except Exception as e:
            print(f"Error calculating discount: {e}")
            return 0, ""

