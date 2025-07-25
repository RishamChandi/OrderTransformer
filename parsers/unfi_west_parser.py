"""
Parser for UNFI West order files
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from .base_parser import BaseParser

class UNFIWestParser(BaseParser):
    """Parser for UNFI West HTML order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "UNFI West"
    
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse UNFI West HTML order file"""
        
        if file_extension.lower() != 'html':
            raise ValueError("UNFI West parser only supports HTML files")
        
        try:
            # Try multiple encodings to handle different file formats
            html_content = self._decode_file_content(file_content)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            orders = []
            
            # Extract order header information
            order_info = self._extract_order_header(soup, filename)
            
            # Extract line items
            line_items = self._extract_line_items(soup)
            
            # Combine header and line items
            if line_items:
                for item in line_items:
                    order_item = {**order_info, **item}
                    orders.append(order_item)
            else:
                # Create single order if no line items found
                orders.append(order_info)
            
            return orders if orders else None
            
        except Exception as e:
            raise ValueError(f"Error parsing UNFI West HTML: {str(e)}")
    
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
    
    def _extract_order_header(self, soup: BeautifulSoup, filename: str) -> Dict[str, Any]:
        """Extract order header information from HTML"""
        
        order_info = {
            'order_number': filename,
            'order_date': None,
            'customer_name': 'UNKNOWN',
            'raw_customer_name': '',
            'source_file': filename
        }
        
        # Look for order number patterns
        order_patterns = [
            r'Purchase Order[:\s#]*(\d+)',
            r'PO[:\s#]*(\d+)',
            r'Order[:\s#]*(\d+)',
            r'(\d{8,})'  # Long number sequences
        ]
        
        html_text = soup.get_text()
        for pattern in order_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                order_info['order_number'] = match.group(1)
                break
        
        # Look for customer/store name
        customer_patterns = [
            r'Ship To[:\s]*([^\n\r]+)',
            r'Customer[:\s]*([^\n\r]+)',
            r'Store[:\s]*([^\n\r]+)',
            r'Bill To[:\s]*([^\n\r]+)'
        ]
        
        for pattern in customer_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                raw_customer = match.group(1).strip()
                order_info['raw_customer_name'] = raw_customer
                # Apply mapping
                order_info['customer_name'] = self.mapping_utils.get_store_mapping(
                    raw_customer, 
                    'unfi_west'
                )
                break
        
        # Look for order date patterns
        date_patterns = [
            r'Date[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, html_text)
            if matches:
                order_info['order_date'] = self.parse_date(matches[0])
                break
        
        return order_info
    
    def _extract_line_items(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract line items from HTML tables"""
        
        line_items = []
        
        # Find all tables that might contain line items
        tables = soup.find_all('table')
        
        for table in tables:
            items = self._process_item_table(table)
            line_items.extend(items)
        
        # If no tables found, try to extract from structured divs
        if not line_items:
            divs = soup.find_all('div', class_=re.compile(r'item|product|line'))
            for div in divs:
                item = self._extract_item_from_div(div)
                if item:
                    line_items.append(item)
        
        return line_items
    
    def _process_item_table(self, table) -> List[Dict[str, Any]]:
        """Process a table to extract line items"""
        
        items = []
        rows = table.find_all('tr')
        
        if len(rows) < 2:  # Need at least header and one data row
            return items
        
        # Try to identify header row and column mappings
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        # Map common column names
        column_map = self._create_column_mapping(headers)
        
        # Process data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= len(headers):
                item = self._extract_item_from_cells(cells, column_map)
                if item and item.get('item_number'):
                    items.append(item)
        
        return items
    
    def _create_column_mapping(self, headers: List[str]) -> Dict[str, int]:
        """Create mapping of field names to column indices"""
        
        mapping = {}
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            
            # Item number mapping
            if any(term in header_lower for term in ['item', 'product', 'sku', 'code']):
                mapping['item_number'] = i
            
            # Description mapping
            elif any(term in header_lower for term in ['description', 'name', 'title']):
                mapping['description'] = i
            
            # Quantity mapping
            elif any(term in header_lower for term in ['qty', 'quantity', 'count']):
                mapping['quantity'] = i
            
            # Unit price mapping
            elif any(term in header_lower for term in ['unit', 'price', 'cost']) and 'total' not in header_lower:
                mapping['unit_price'] = i
            
            # Total price mapping
            elif any(term in header_lower for term in ['total', 'amount', 'extended']):
                mapping['total_price'] = i
        
        return mapping
    
    def _extract_item_from_cells(self, cells, column_map: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Extract item data from table cells using column mapping"""
        
        if not cells:
            return None
        
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        
        # Skip empty rows
        if all(not text for text in cell_texts):
            return None
        
        item = {
            'item_number': '',
            'item_description': '',
            'quantity': 1,
            'unit_price': 0.0,
            'total_price': 0.0
        }
        
        # Extract using column mapping
        for field, col_index in column_map.items():
            if col_index < len(cell_texts):
                value = cell_texts[col_index]
                
                if field == 'item_number':
                    item['item_number'] = value
                elif field == 'description':
                    item['item_description'] = value
                elif field == 'quantity':
                    try:
                        item['quantity'] = int(float(self.clean_numeric_value(value))) or 1
                    except:
                        item['quantity'] = 1
                elif field == 'unit_price':
                    item['unit_price'] = self.clean_numeric_value(value)
                elif field == 'total_price':
                    item['total_price'] = self.clean_numeric_value(value)
        
        # If no column mapping worked, try positional extraction
        if not item['item_number'] and len(cell_texts) > 0:
            item['item_number'] = cell_texts[0]
            
            if len(cell_texts) > 1:
                item['item_description'] = cell_texts[1]
            
            # Look for numeric values in remaining cells
            for text in cell_texts[2:]:
                numeric_value = self.clean_numeric_value(text)
                if numeric_value > 0:
                    if item['quantity'] == 1 and numeric_value < 1000:
                        item['quantity'] = int(numeric_value)
                    elif item['unit_price'] == 0.0:
                        item['unit_price'] = numeric_value
                    elif item['total_price'] == 0.0:
                        item['total_price'] = numeric_value
        
        # Calculate total if missing
        if item['total_price'] == 0.0 and item['unit_price'] > 0:
            item['total_price'] = item['unit_price'] * item['quantity']
        
        return item if item['item_number'] else None
    
    def _extract_item_from_div(self, div) -> Optional[Dict[str, Any]]:
        """Extract item information from div element"""
        
        text = div.get_text(strip=True)
        if not text:
            return None
        
        # Try to extract structured information from text
        lines = text.split('\n')
        
        item = {
            'item_number': '',
            'item_description': '',
            'quantity': 1,
            'unit_price': 0.0,
            'total_price': 0.0
        }
        
        # Look for patterns in the text
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for item number (usually starts with letters/numbers)
            if not item['item_number'] and re.match(r'^[A-Z0-9]+', line):
                item['item_number'] = line.split()[0]
                # Rest might be description
                remaining = ' '.join(line.split()[1:])
                if remaining:
                    item['item_description'] = remaining
            
            # Look for quantity patterns
            qty_match = re.search(r'qty[:\s]*(\d+)', line, re.IGNORECASE)
            if qty_match:
                item['quantity'] = int(qty_match.group(1))
            
            # Look for price patterns
            price_matches = re.findall(r'\$?[\d,]+\.?\d*', line)
            for price_text in price_matches:
                price_value = self.clean_numeric_value(price_text)
                if price_value > 0:
                    if item['unit_price'] == 0.0:
                        item['unit_price'] = price_value
                    else:
                        item['total_price'] = price_value
        
        return item if item['item_number'] else None
