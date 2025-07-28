"""
Parser for Whole Foods order files
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import pandas as pd
from .base_parser import BaseParser

class WholeFoodsParser(BaseParser):
    """Parser for Whole Foods HTML order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "Whole Foods"
    
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse Whole Foods HTML order file"""
        
        if file_extension.lower() != 'html':
            raise ValueError("Whole Foods parser only supports HTML files")
        
        try:
            # Try multiple encodings to handle different file formats
            html_content = self._decode_file_content(file_content)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract order information
            orders = []
            
            # Look for order tables or containers
            order_tables = soup.find_all('table') or soup.find_all('div', class_=['order', 'order-item'])
            
            if not order_tables:
                # Try to find any structured data
                order_tables = [soup]
            
            for table in order_tables:
                order_data = self._extract_order_from_table(table, filename)
                if order_data:
                    orders.extend(order_data)
            
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
    
    def _extract_order_from_table(self, table_element, filename: str) -> List[Dict[str, Any]]:
        """Extract order data from HTML table element"""
        
        orders = []
        
        try:
            # Extract basic order information - Whole Foods specific patterns
            order_number = None
            order_date = None
            customer_name = None
            
            # Look for "Whole Foods Market Purchase Order # XXXXXXX" pattern
            all_text = table_element.get_text()
            import re
            order_match = re.search(r'Purchase Order #\s*(\d+)', all_text)
            if order_match:
                order_number = order_match.group(1)
            
            # Extract order number from filename if not found (e.g., order_154533670.html -> 154533670)
            if not order_number:
                match = re.search(r'order_(\d+)', filename)
                if match:
                    order_number = match.group(1)
            
            # Extract order date
            date_match = re.search(r'Order Date:\s*(\d{4}-\d{2}-\d{2})', all_text)
            if date_match:
                order_date = date_match.group(1)
            
            # Extract store number
            store_match = re.search(r'Store No:\s*(\d+)', all_text)
            if store_match:
                customer_name = f"WHOLE FOODS #{store_match.group(1)}"
            
            # Extract line items
            rows = table_element.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Minimum columns for item data
                    
                    # Try to extract item information
                    item_data = self._extract_item_from_row(cells)
                    
                    if item_data and item_data.get('item_number'):
                        
                        # Apply store mapping - always use "IDI - Richmond" for Whole Foods
                        mapped_customer = "IDI - Richmond"
                        
                        # Apply item mapping
                        mapped_item = self.mapping_utils.get_item_mapping(
                            item_data['item_number'], 
                            'wholefoods'
                        )
                        
                        order_item = {
                            'order_number': order_number or filename,
                            'order_date': self.parse_date(order_date) if order_date else None,
                            'customer_name': mapped_customer,
                            'raw_customer_name': customer_name,
                            'item_number': mapped_item,
                            'raw_item_number': item_data['item_number'],
                            'item_description': item_data.get('description', ''),
                            'quantity': item_data.get('quantity', 1),
                            'unit_price': item_data.get('unit_price', 0.0),
                            'total_price': item_data.get('total_price', 0.0),
                            'source_file': filename
                        }
                        
                        orders.append(order_item)
            
            # If no line items found, create a single order entry
            if not orders and (order_number or customer_name):
                mapped_customer = "IDI - Richmond"
                
                orders.append({
                    'order_number': order_number or filename,
                    'order_date': self.parse_date(order_date) if order_date else None,
                    'customer_name': mapped_customer,
                    'raw_customer_name': customer_name,
                    'item_number': 'UNKNOWN',
                    'item_description': 'Order item details not found',
                    'quantity': 1,
                    'unit_price': 0.0,
                    'total_price': 0.0,
                    'source_file': filename
                })
                
        except Exception as e:
            # Return basic order if extraction fails
            orders.append({
                'order_number': filename,
                'order_date': None,
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
