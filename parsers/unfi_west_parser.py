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
        
        html_text = soup.get_text()
        
        # Look for purchase order number (specific to UNFI West format)
        po_match = re.search(r'P\.O\.B\.\s*(\d+[-]\d+)', html_text)
        if not po_match:
            po_match = re.search(r'PURCH ORDER\s*(\d+)', html_text)
        if not po_match:
            po_match = re.search(r'(\d{9,})', html_text)  # Long number sequences
        
        if po_match:
            order_info['order_number'] = po_match.group(1)
        
        # Look for UNFI location information (e.g., "UNFI - MORENO VALLEY, CA")
        # This appears in the header section of UNFI West HTML files
        unfi_location_match = re.search(r'UNFI\s*-\s*([^<\n\r]+)', html_text)
        if unfi_location_match:
            # Extract the full UNFI location string
            raw_customer = f"UNFI - {unfi_location_match.group(1).strip()}"
            order_info['raw_customer_name'] = raw_customer
        else:
            # Fallback: Look for ship to information
            ship_to_match = re.search(r'Ship To:\s*([^\n\r]+)', html_text)
            if ship_to_match:
                raw_customer = ship_to_match.group(1).strip()
                order_info['raw_customer_name'] = raw_customer
            else:
                # Look for buyer information
                buyer_match = re.search(r'Buyer[:\s]*([^\n\r]*?)\s*P\.O', html_text)
                if buyer_match:
                    raw_customer = buyer_match.group(1).strip()
                    order_info['raw_customer_name'] = raw_customer
        
        # Apply store mapping
        if order_info['raw_customer_name']:
            order_info['customer_name'] = self.mapping_utils.get_store_mapping(
                order_info['raw_customer_name'], 
                'unfi_west'
            )
        
        # Look for pickup date
        pickup_match = re.search(r'PICK UP\s*(\d{2}/\d{2}/\d{2})', html_text)
        if pickup_match:
            order_info['order_date'] = self.parse_date(pickup_match.group(1))
        else:
            # Look for other date patterns
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', html_text)
            if date_match:
                order_info['order_date'] = self.parse_date(date_match.group(1))
        
        return order_info
    
    def _extract_line_items(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract line items from UNFI West HTML format"""
        
        line_items = []
        html_text = soup.get_text()
        
        # Look for the main table with line items - it starts after "Line Qty Cases Plts Prod# Description"
        table_section = self._find_table_section(html_text)
        
        if table_section:
            items = self._parse_line_items_from_text(table_section)
            line_items.extend(items)
        
        return line_items
    
    def _find_table_section(self, html_text: str) -> Optional[str]:
        """Find the table section with line items"""
        
        # Look for the line items table header
        header_pattern = r'Line\s+Qty\s+Cases\s+Plts\s+Prod#\s+Description\s+Units\s+Vendor\s+P\.N\.\s+Cost\s+Extension'
        match = re.search(header_pattern, html_text, re.IGNORECASE)
        
        if match:
            # Extract everything from the header to SUBTOTAL
            start_pos = match.end()
            subtotal_match = re.search(r'SUBTOTAL', html_text[start_pos:], re.IGNORECASE)
            
            if subtotal_match:
                end_pos = start_pos + subtotal_match.start()
                return html_text[start_pos:end_pos].strip()
            else:
                # If no SUBTOTAL found, take a reasonable chunk
                return html_text[start_pos:start_pos + 5000].strip()
        
        return None
    
    def _parse_line_items_from_text(self, table_text: str) -> List[Dict[str, Any]]:
        """Parse line items from the extracted table text"""
        
        items = []
        lines = table_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Skip empty or very short lines
                continue
                
            # Parse line using regex pattern for UNFI West format
            # Pattern: Line# Qty Cases Plts Prod# Description Units Vendor_PN Cost Extension
            item = self._parse_unfi_west_line(line)
            if item:
                items.append(item)
        
        return items
    
    def _parse_unfi_west_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single UNFI West line item"""
        
        # Clean the line
        line = re.sub(r'\s+', ' ', line.strip())
        
        # Skip lines that don't start with a number (line number)
        if not re.match(r'^\d+\s', line):
            return None
        
        # Split the line into parts
        parts = line.split()
        
        if len(parts) < 8:  # Need at least 8 fields
            return None
        
        try:
            # Extract fields based on UNFI West format
            line_num = parts[0]
            qty = int(parts[1])
            
            # Find vendor P.N. by looking for patterns like "12-042", "17-006", etc.
            vendor_pn = None
            cost = 0.0
            description = ""
            
            # Look for vendor P.N. pattern (numbers with dashes/letters)
            for i, part in enumerate(parts):
                if re.match(r'^\d+[-]\d+[-]?\d*$', part) or re.match(r'^[A-Z][-]\d+[-]\d+$', part):
                    vendor_pn = part
                    # Cost should be one of the next parts
                    for j in range(i+1, min(i+4, len(parts))):
                        try:
                            cost = float(parts[j])
                            break
                        except ValueError:
                            continue
                    break
            
            # Extract description (between prod# and vendor P.N.)
            desc_parts = []
            capturing_desc = False
            for part in parts[4:]:  # Start after line, qty, cases, plts
                if re.match(r'^\d+[-]\d+', part):  # Found vendor P.N.
                    break
                if part and not part.replace('.', '').replace('-', '').isdigit():
                    desc_parts.append(part)
            
            description = ' '.join(desc_parts)
            
            if not vendor_pn:
                # Fallback: use last alphanumeric part as vendor P.N.
                for part in reversed(parts):
                    if re.match(r'^[A-Za-z0-9\-]+$', part) and not part.replace('.', '').isdigit():
                        vendor_pn = part
                        break
            
            # Apply item mapping
            mapped_item = self.mapping_utils.get_item_mapping(vendor_pn or "UNKNOWN", 'unfi_west')
            
            return {
                'item_number': mapped_item,
                'raw_item_number': vendor_pn or "UNKNOWN",
                'item_description': description.strip(),
                'quantity': qty,
                'unit_price': cost,
                'total_price': cost * qty
            }
            
        except (ValueError, IndexError):
            return None
    
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
