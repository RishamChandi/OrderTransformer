"""
Parser for Whole Foods order files
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import pandas as pd
from .base_parser import BaseParser

class WholeFoodsParser(BaseParser):
    """Parser for Whole Foods HTML order files"""
    
    def __init__(self, db_service=None):
        super().__init__()
        self.source_name = "Whole Foods"
        self.db_service = db_service
    
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse Whole Foods HTML order file following the reference code pattern"""
        
        if file_extension.lower() != 'html':
            raise ValueError("Whole Foods parser only supports HTML files")
        
        try:
            # Decode file content
            html_content = self._decode_file_content(file_content)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract order metadata from entire document
            all_text = soup.get_text()
            import re
            
            order_data = {'metadata': {}}
            
            # Extract order number (robustly like reference code)
            order_match = re.search(r'Purchase Order #\s*(\d+)', all_text)
            if order_match:
                order_data['metadata']['order_number'] = order_match.group(1)
            elif filename:
                match = re.search(r'order_(\d+)', filename) 
                if match:
                    order_data['metadata']['order_number'] = match.group(1)
            
            # Extract order date
            date_match = re.search(r'Order Date:\s*(\d{4}-\d{2}-\d{2})', all_text)
            if date_match:
                order_data['metadata']['order_date'] = date_match.group(1)
            
            # Extract expected delivery date
            delivery_patterns = [
                r'Expected Delivery Date[:\s\n]*(\d{4}-\d{2}-\d{2})',
                r'Expected\s+Delivery\s+Date[:\s]*(\d{4}-\d{2}-\d{2})',
                r'(?i)expected.*delivery.*date[:\s\n]*(\d{4}-\d{2}-\d{2})'
            ]
            
            for pattern in delivery_patterns:
                delivery_match = re.search(pattern, all_text, re.MULTILINE | re.IGNORECASE)
                if delivery_match:
                    order_data['metadata']['delivery_date'] = delivery_match.group(1)
                    break
            
            # Extract store number (robustly like reference code)
            store_match = re.search(r'Store No:\s*(\d+)', all_text)
            if store_match:
                order_data['metadata']['store_number'] = store_match.group(1)
            
            # Bulk-fetch all item mappings once (database-first optimization)
            item_mappings_dict = {}
            if self.db_service:
                try:
                    item_mappings_dict = self.db_service.get_item_mappings_dict('wholefoods')
                except Exception:
                    pass  # Fall back to CSV mappings if database fails
            
            # Find and parse the line items table
            line_items = []
            for table in soup.find_all('table'):
                header_row = table.find('tr')
                if header_row:
                    header_text = header_row.get_text().lower()
                    if 'item no' in header_text and 'description' in header_text and 'cost' in header_text:
                        # Found the line items table
                        rows = table.find_all('tr')
                        
                        for row in rows[1:]:  # Skip header row
                            cells = row.find_all('td')
                            if len(cells) >= 6:  # Expect: Line, Item No, Qty, Description, Size, Cost, UPC
                                
                                # Extract data from specific columns
                                item_number = cells[1].get_text(strip=True)
                                qty_text = cells[2].get_text(strip=True)
                                description = cells[3].get_text(strip=True)
                                cost_text = cells[5].get_text(strip=True)
                                
                                # Skip totals row and empty rows
                                # Allow item numbers with spaces (e.g., "13 025 24"), but require at least some digits
                                if not item_number or item_number.lower() == 'totals:' or not any(c.isdigit() for c in item_number):
                                    continue
                                
                                # Parse cost
                                unit_price = 0.0
                                if cost_text:
                                    cost_value = self.clean_numeric_value(cost_text)
                                    if cost_value > 0:
                                        unit_price = cost_value
                                
                                line_items.append({
                                    'item_no': item_number,
                                    'description': description,
                                    'qty': qty_text,
                                    'cost': str(unit_price)
                                })
                        
                        break  # Found and processed the line items table, exit loop
            
            # Build orders using the reference code pattern
            orders = []
            if line_items:
                # Process each line item with bulk-fetched mappings
                for line_item in line_items:
                    xoro_row = self._build_xoro_row(order_data, line_item, item_mappings_dict)
                    orders.append(xoro_row)
            else:
                # No line items found - create single fallback entry
                fallback_item = {
                    'item_no': 'UNKNOWN',
                    'description': 'Order item details not found',
                    'qty': '1',
                    'cost': '0.0'
                }
                xoro_row = self._build_xoro_row(order_data, fallback_item, item_mappings_dict)
                orders.append(xoro_row)
            
            return orders if orders else None
            
        except Exception as e:
            raise ValueError(f"Error parsing Whole Foods HTML: {str(e)}")
    
    def _decode_file_content(self, file_content: bytes) -> str:
        """Try multiple encodings to decode file content"""
        
        # List of encodings to try
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, use utf-8 with error handling
        return file_content.decode('utf-8', errors='replace')
    
    def _build_xoro_row(self, order_data: Dict[str, Any], line_item: Dict[str, str], 
                        item_mappings_dict: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
        """Build a row for Xoro Sales Order Import Template following reference code pattern
        
        Args:
            order_data: Order metadata dictionary
            line_item: Individual line item data
            item_mappings_dict: Pre-fetched item mappings dictionary (optimization to avoid per-row DB queries)
        """
        
        # Use customer mapping with store number (which is the Raw Customer ID)
        store_number = order_data['metadata'].get('store_number')
        if store_number:
            mapped_customer = self.mapping_utils.get_customer_mapping(store_number, 'wholefoods')
            if not mapped_customer or mapped_customer == 'UNKNOWN':
                mapped_customer = 'IDI - Richmond'
        else:
            mapped_customer = 'IDI - Richmond'
        
        # Map item number and description using bulk-fetched dictionary first, then CSV fallback
        mapped_item = None
        item_description = line_item.get('description', '')
        raw_item_no = line_item['item_no']
        mapping_warning = None
        
        # Try bulk-fetched mappings dictionary first (optimized - no per-row DB calls)
        if item_mappings_dict:
            # Try exact match first
            if raw_item_no in item_mappings_dict:
                db_mapping = item_mappings_dict[raw_item_no]
                mapped_item = db_mapping.get('mapped_item')
                db_description = db_mapping.get('mapped_description', '').strip()
                if db_description:
                    item_description = db_description
            else:
                # Try variations: without spaces, without dashes, normalized
                variations = [
                    raw_item_no.replace(' ', ''),  # Remove spaces: "13 025 24" -> "1302524"
                    raw_item_no.replace('-', ''),   # Remove dashes: "13-025-25" -> "1302525"
                    raw_item_no.replace(' ', '').replace('-', '')  # Remove both
                ]
                
                for variant in variations:
                    if variant in item_mappings_dict:
                        db_mapping = item_mappings_dict[variant]
                        mapped_item = db_mapping.get('mapped_item')
                        db_description = db_mapping.get('mapped_description', '').strip()
                        if db_description:
                            item_description = db_description
                        print(f"DEBUG: Found mapping for '{raw_item_no}' via variant '{variant}'")
                        break
                
                # Also try reverse lookup: normalize both keys and raw item
                if not mapped_item:
                    raw_normalized = raw_item_no.replace(' ', '').replace('-', '')
                    for key, db_mapping in item_mappings_dict.items():
                        key_normalized = str(key).replace(' ', '').replace('-', '')
                        if key_normalized == raw_normalized:
                            mapped_item = db_mapping.get('mapped_item')
                            db_description = db_mapping.get('mapped_description', '').strip()
                            if db_description:
                                item_description = db_description
                            print(f"DEBUG: Found mapping for '{raw_item_no}' via normalized match with key '{key}'")
                            break
        
        # If no database mapping found, try mapping_utils (which handles CSV and variations)
        if not mapped_item:
            mapped_item = self.mapping_utils.get_item_mapping(raw_item_no, 'wholefoods')
            # If mapping_utils returns the original item, it means no mapping was found
            if mapped_item == raw_item_no:
                # Check if item has spaces or dashes - suggest mapping without them
                if ' ' in raw_item_no or '-' in raw_item_no:
                    normalized_item = raw_item_no.replace(' ', '').replace('-', '')
                    mapping_warning = f"Item mapping missing for '{raw_item_no}'. Try mapping as '{normalized_item}' (spaces/dashes removed)."
                    print(f"WARNING: {mapping_warning}")
                    # Still process the item, but use "Invalid Item" as mapped_item
                    mapped_item = "Invalid Item"
                else:
                    # No mapping found, use "Invalid Item"
                    mapped_item = "Invalid Item"
                    print(f"WARNING: Item mapping missing for '{raw_item_no}'")
        
        # Always include the item, even if mapping is missing (critical requirement)
        # Store warning in item description if mapping is missing (for visibility)
        if mapping_warning and mapped_item == "Invalid Item":
            # Append warning to description so user can see it
            item_description = f"{item_description} [WARNING: {mapping_warning}]" if item_description else f"[WARNING: {mapping_warning}]"
        
        # Parse quantity from qty field
        import re
        qty_raw = line_item.get('qty', '1')
        qty_match = re.match(r"(\d+)", qty_raw)
        quantity = int(qty_match.group(1)) if qty_match else 1
        
        # Parse unit price
        unit_price = float(line_item.get('cost', '0.0'))
        
        # Build the order item - ALWAYS include, never skip
        return {
            'order_number': order_data['metadata'].get('order_number', ''),
            'order_date': self.parse_date(order_data['metadata'].get('order_date')) if order_data['metadata'].get('order_date') else None,
            'delivery_date': self.parse_date(order_data['metadata'].get('delivery_date')) if order_data['metadata'].get('delivery_date') else None,
            'customer_name': mapped_customer,
            'raw_customer_name': f"WHOLE FOODS #{order_data['metadata'].get('store_number')}" if order_data['metadata'].get('store_number') else 'UNKNOWN',
            'item_number': mapped_item,
            'raw_item_number': line_item['item_no'],
            'item_description': item_description,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': unit_price * quantity,
            'source_file': order_data['metadata'].get('order_number', '') + '.html',
            'mapping_warning': mapping_warning  # Include warning in order data
        }
    
    def _extract_order_from_table(self, table_element, filename: str) -> List[Dict[str, Any]]:
        """Extract order data from HTML document"""
        
        orders = []
        
        try:
            # Extract basic order information from entire document
            all_text = table_element.get_text()
            import re
            
            # Extract order number
            order_number = None
            order_match = re.search(r'Purchase Order #\s*(\d+)', all_text)
            if order_match:
                order_number = order_match.group(1)
            elif filename:
                match = re.search(r'order_(\d+)', filename)
                if match:
                    order_number = match.group(1)
            
            # Extract order date
            order_date = None
            date_match = re.search(r'Order Date:\s*(\d{4}-\d{2}-\d{2})', all_text)
            if date_match:
                order_date = date_match.group(1)
            
            # Extract expected delivery date with more flexible pattern
            delivery_date = None
            # Try multiple patterns to ensure we catch the delivery date
            delivery_patterns = [
                r'Expected Delivery Date[:\s\n]*(\d{4}-\d{2}-\d{2})',
                r'Expected\s+Delivery\s+Date[:\s]*(\d{4}-\d{2}-\d{2})',
                r'(?i)expected.*delivery.*date[:\s\n]*(\d{4}-\d{2}-\d{2})'
            ]
            
            for pattern in delivery_patterns:
                delivery_match = re.search(pattern, all_text, re.MULTILINE | re.IGNORECASE)
                if delivery_match:
                    delivery_date = delivery_match.group(1)
                    break
            
            # Extract store number and map to customer
            store_number = None
            customer_name = None
            store_match = re.search(r'Store No:\s*(\d+)', all_text)
            if store_match:
                store_number = store_match.group(1)
                customer_name = f"WHOLE FOODS #{store_number}"
                # Map store number (Raw Customer ID) to customer name using customer mapping
                mapped_customer = self.mapping_utils.get_customer_mapping(store_number, 'wholefoods')
                if not mapped_customer or mapped_customer == 'UNKNOWN':
                    mapped_customer = "IDI - Richmond"  # Default fallback
            else:
                mapped_customer = "IDI - Richmond"  # Default fallback
            
            # Find and parse the line items table
            line_items_found = False
            for table in table_element.find_all('table'):
                header_row = table.find('tr')
                if header_row:
                    header_text = header_row.get_text().lower()
                    if 'item no' in header_text and 'description' in header_text and 'cost' in header_text:
                        # Found the line items table
                        line_items_found = True
                        rows = table.find_all('tr')
                        
                        for row in rows[1:]:  # Skip header row
                            cells = row.find_all('td')
                            if len(cells) >= 6:  # Expect: Line, Item No, Qty, Description, Size, Cost, UPC
                                
                                # Extract data from specific columns
                                line_num = cells[0].get_text(strip=True)
                                item_number = cells[1].get_text(strip=True)
                                qty_text = cells[2].get_text(strip=True)
                                description = cells[3].get_text(strip=True)
                                size = cells[4].get_text(strip=True)
                                cost_text = cells[5].get_text(strip=True)
                                upc = cells[6].get_text(strip=True) if len(cells) > 6 else ""
                                
                                # Skip totals row and empty rows
                                # Allow item numbers with spaces (e.g., "13 025 24"), but require at least some digits
                                if not item_number or item_number.lower() == 'totals:' or not any(c.isdigit() for c in item_number):
                                    continue
                                
                                # Parse quantity (e.g., "1  CA" -> 1)
                                quantity = 1
                                if qty_text:
                                    qty_match = re.search(r'^(\d+)', qty_text)
                                    if qty_match:
                                        quantity = int(qty_match.group(1))
                                
                                # Parse cost (e.g., "  14.94" -> 14.94)
                                unit_price = 0.0
                                if cost_text:
                                    cost_value = self.clean_numeric_value(cost_text)
                                    if cost_value > 0:
                                        unit_price = cost_value
                                
                                # Apply item mapping with support for spaces/dashes
                                mapped_item = self.mapping_utils.get_item_mapping(item_number, 'wholefoods')
                                mapping_warning = None
                                
                                # If mapping_utils returns the original item, it means no mapping was found
                                if mapped_item == item_number:
                                    # Check if item has spaces or dashes - suggest mapping without them
                                    if ' ' in item_number or '-' in item_number:
                                        normalized_item = item_number.replace(' ', '').replace('-', '')
                                        mapping_warning = f"Item mapping missing for '{item_number}'. Try mapping as '{normalized_item}' (spaces/dashes removed)."
                                        print(f"WARNING: {mapping_warning}")
                                    else:
                                        mapping_warning = f"Item mapping missing for '{item_number}'"
                                        print(f"WARNING: {mapping_warning}")
                                    # Use "Invalid Item" if no mapping found, but still process the item
                                    mapped_item = "Invalid Item"
                                
                                # Always include the item, even if mapping is missing (critical requirement)
                                # Append warning to description if mapping is missing
                                final_description = description
                                if mapping_warning and mapped_item == "Invalid Item":
                                    final_description = f"{description} [WARNING: {mapping_warning}]" if description else f"[WARNING: {mapping_warning}]"
                                
                                order_item = {
                                    'order_number': order_number or filename,
                                    'order_date': self.parse_date(order_date) if order_date else None,
                                    'delivery_date': self.parse_date(delivery_date) if delivery_date else None,
                                    'customer_name': mapped_customer,
                                    'raw_customer_name': customer_name,
                                    'item_number': mapped_item,
                                    'raw_item_number': item_number,
                                    'item_description': final_description,
                                    'quantity': quantity,
                                    'unit_price': unit_price,
                                    'total_price': unit_price * quantity,
                                    'source_file': filename,
                                    'mapping_warning': mapping_warning  # Include warning in order data
                                }
                                
                                orders.append(order_item)
                        
                        break  # Found and processed the line items table, exit loop
            
            # If no line items found, create a single order entry (only if we haven't found any items)
            if not orders and not line_items_found:
                orders.append({
                    'order_number': order_number or filename,
                    'order_date': self.parse_date(order_date) if order_date else None,
                    'delivery_date': self.parse_date(delivery_date) if delivery_date else None,
                    'customer_name': mapped_customer,
                    'raw_customer_name': customer_name or 'UNKNOWN',
                    'item_number': 'UNKNOWN',
                    'item_description': 'Order item details not found',
                    'quantity': 1,
                    'unit_price': 0.0,
                    'total_price': 0.0,
                    'source_file': filename
                })
                
        except Exception as e:
            # Return basic order if extraction fails
            if not orders:  # Only add error if no orders were processed
                orders.append({
                    'order_number': filename,
                    'order_date': None,
                    'delivery_date': None,
                    'customer_name': 'UNKNOWN',
                    'raw_customer_name': '',
                    'item_number': 'ERROR',
                    'item_description': f'Parsing error: {str(e)}',
                    'quantity': 1,
                    'unit_price': 0.0,
                    'total_price': 0.0,
                    'source_file': filename
                })
        
        return orders
    
    def _extract_text_by_label(self, element, labels: List[str]) -> Optional[str]:
        """Extract text by searching for labels"""
        
        for label in labels:
            # Search for elements containing the label
            found_elements = element.find_all(text=lambda text: text and label.lower() in text.lower())
            
            for found_text in found_elements:
                parent = found_text.parent
                if parent:
                    # Look for value in next sibling or same row
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        text = next_sibling.get_text(strip=True)
                        if text and text.lower() != label.lower():
                            return text
                    
                    # Look in same element after the label
                    full_text = parent.get_text(strip=True)
                    if ':' in full_text:
                        parts = full_text.split(':', 1)
                        if len(parts) > 1:
                            return parts[1].strip()
                    
                    # Special case for Whole Foods order number (look for # pattern)
                    if 'order' in label.lower():
                        import re
                        order_match = re.search(r'#\s*(\d+)', full_text)
                        if order_match:
                            return order_match.group(1)
        
        return None
    
    def _extract_item_from_row(self, cells) -> Optional[Dict[str, Any]]:
        """Extract item information from table row cells"""
        
        if len(cells) < 2:
            return None
        
        # Get text from all cells
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        
        # Skip header rows
        if any(header in ' '.join(cell_texts).lower() for header in ['item', 'product', 'description', 'qty', 'price', 'order number', 'purchase order']):
            return None
        
        # Skip empty rows
        if all(not text for text in cell_texts):
            return None
            
        # Skip rows with order header information
        combined_text = ' '.join(cell_texts).lower()
        if any(keyword in combined_text for keyword in ['purchase order', 'order number', 'order date', 'delivery date', 'store no', 'account no', 'buyer']):
            return None
        
        # Skip very long text that looks like headers (over 50 chars for first cell)
        if cell_texts[0] and len(cell_texts[0]) > 50:
            return None
        
        # Try to identify item number (usually first non-empty cell that looks like an item code)
        item_number = None
        description = None
        quantity = 1
        unit_price = 0.0
        total_price = 0.0
        
        # Parse Whole Foods table structure: Item No, Qty, Description, Size, Cost, UPC
        for i, text in enumerate(cell_texts):
            if text and not item_number and text.isdigit() and len(text) <= 10:
                # First numeric cell is likely item number
                item_number = text
            elif text and not description and text != item_number and len(text) <= 200:
                # Non-numeric text is likely description
                if not text.isdigit() and not any(word in text.lower() for word in ['ounce', 'lb', 'oz', 'ca']):
                    description = text
            elif text and any(char.isdigit() for char in text):
                # Parse numeric values
                numeric_value = self.clean_numeric_value(text)
                if numeric_value > 0:
                    if '.' in text and numeric_value < 1000 and unit_price == 0.0:
                        # Decimal value likely price
                        unit_price = numeric_value
                    elif numeric_value < 100 and quantity == 1:
                        # Small integer likely quantity
                        quantity = int(numeric_value)
                    elif numeric_value > unit_price and total_price == 0.0:
                        # Larger value likely total
                        total_price = numeric_value
        
        if not item_number or len(item_number) > 50:
            return None
        
        # Calculate total if not provided
        if total_price == 0.0 and unit_price > 0:
            total_price = unit_price * quantity
        
        return {
            'item_number': item_number,
            'description': description or '',
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price
        }
