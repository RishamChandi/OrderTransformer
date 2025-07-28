"""
Parser for UNFI East order files (PDF format)
"""

from typing import List, Dict, Any, Optional
import re
import io
from PyPDF2 import PdfReader
from .base_parser import BaseParser

class UNFIEastParser(BaseParser):
    """Parser for UNFI East PDF order files"""
    
    def __init__(self, mapping_utils):
        super().__init__()
        self.source_name = "UNFI East"
        self.mapping_utils = mapping_utils
    
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse UNFI East PDF order file"""
        
        if file_extension.lower() != 'pdf':
            raise ValueError("UNFI East parser only supports PDF files")
        
        try:
            # Convert PDF content to text
            text_content = self._extract_text_from_pdf(file_content)
            
            orders = []
            
            # Extract order header information
            order_info = self._extract_order_header(text_content, filename)
            
            # Extract line items
            line_items = self._extract_line_items(text_content)
            
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
            raise ValueError(f"Error parsing UNFI East PDF: {str(e)}")
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file content using PyPDF2"""
        
        try:
            # Create a BytesIO object from the file content
            pdf_stream = io.BytesIO(file_content)
            
            # Use PyPDF2 to read the PDF
            pdf_reader = PdfReader(pdf_stream)
            
            # Extract text from all pages
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content
            
        except Exception as e:
            # Fallback: try to decode as text (for text-based files)
            try:
                return file_content.decode('utf-8', errors='ignore')
            except:
                raise ValueError(f"Could not extract text from PDF: {str(e)}")
    
    def _extract_order_header(self, text_content: str, filename: str) -> Dict[str, Any]:
        """Extract order header information from PDF text"""
        
        order_info = {
            'order_number': filename,
            'order_to_number': None,
            'order_date': None,
            'pickup_date': None,
            'eta_date': None,
            'customer_name': 'UNKNOWN',
            'raw_customer_name': '',
            'source_file': filename
        }
        
        # Extract Purchase Order Number
        po_match = re.search(r'Purchase Order Number:\s*(\d+)', text_content)
        if po_match:
            order_info['order_number'] = po_match.group(1)
        
        # Extract "Order To" number (like 85948, 85950) for store mapping
        order_to_match = re.search(r'Order To:\s*(\d+)', text_content)
        if order_to_match:
            order_info['order_to_number'] = order_to_match.group(1)
        
        # Extract order date (Ord Date) - for OrderDate in Xoro
        order_date_match = re.search(r'Ord Date.*?(\d{2}/\d{2}/\d{2})', text_content)
        if order_date_match:
            order_info['order_date'] = self.parse_date(order_date_match.group(1))
        
        # Extract pickup date (Pck Date) - for DateToBeShipped and LastDateToBeShipped in Xoro
        pickup_date_match = re.search(r'Pck Date.*?(\d{2}/\d{2}/\d{2})', text_content)
        if pickup_date_match:
            order_info['pickup_date'] = self.parse_date(pickup_date_match.group(1))
            
        # Extract ETA date - for reference only (not used in Xoro template)
        eta_date_match = re.search(r'ETA Date.*?(\d{2}/\d{2}/\d{2})', text_content)
        if eta_date_match:
            order_info['eta_date'] = self.parse_date(eta_date_match.group(1))
        
        # Extract warehouse/location information for customer mapping
        # First, try to extract the location code from the Int Ref# (like "mm-85950-G25" -> "MAN")
        int_ref_match = re.search(r'Int Ref#:\s*([a-zA-Z]+)-', text_content)
        if int_ref_match:
            location_prefix = int_ref_match.group(1).upper()
            print(f"DEBUG: Found Int Ref location prefix: {location_prefix}")
            
            # Map Int Ref prefixes to warehouse codes
            prefix_to_warehouse = {
                'MM': 'MAN',  # Manchester
                'JJ': 'HOW',  # Howell  
                'AA': 'ATL',  # Atlanta
                'SS': 'SAR',  # Sarasota
                'YY': 'YOR',  # York
                'RR': 'RCH'   # Richburg
            }
            
            location_code = prefix_to_warehouse.get(location_prefix, location_prefix)
            print(f"DEBUG: Mapped prefix {location_prefix} -> warehouse code {location_code}")
            
            # Try to map warehouse code to customer name using the mapping
            mapped_customer = self.mapping_utils.get_store_mapping(location_code, 'unfi_east')
            if mapped_customer and mapped_customer != location_code:
                order_info['customer_name'] = mapped_customer
                order_info['raw_customer_name'] = location_code
                print(f"DEBUG: Final mapping {location_code} -> {mapped_customer}")
        
        # Fallback 1: Look for warehouse info in "Ship To:" section like "Manchester", "Howell Warehouse", etc.
        if order_info['customer_name'] == 'UNKNOWN':
            ship_to_match = re.search(r'Ship To:\s*([A-Za-z\s]+?)(?:\s+Warehouse|\s*\n|\s+\d)', text_content)
            if ship_to_match:
                warehouse_location = ship_to_match.group(1).strip()
                order_info['warehouse_location'] = warehouse_location
                print(f"DEBUG: Found Ship To location: {warehouse_location}")
                
                # Convert full warehouse names to 3-letter codes for mapping
                warehouse_to_code = {
                    'Manchester': 'MAN',
                    'Howell': 'HOW', 
                    'Atlanta': 'ATL',
                    'Sarasota': 'SAR',
                    'York': 'YOR',
                    'Richburg': 'RCH'
                }
                
                location_code = warehouse_to_code.get(warehouse_location, warehouse_location.upper()[:3])
                mapped_customer = self.mapping_utils.get_store_mapping(location_code, 'unfi_east')
                if mapped_customer and mapped_customer != location_code:
                    order_info['customer_name'] = mapped_customer
                    order_info['raw_customer_name'] = warehouse_location
                    print(f"DEBUG: Mapped {warehouse_location} ({location_code}) -> {mapped_customer}")
        
        # Fallback 2: Apply store mapping based on Order To number
        if order_info['customer_name'] == 'UNKNOWN' and order_info['order_to_number']:
            mapped_customer = self.mapping_utils.get_store_mapping(order_info['order_to_number'], 'unfi_east')
            if mapped_customer and mapped_customer != order_info['order_to_number']:
                order_info['customer_name'] = mapped_customer
                order_info['raw_customer_name'] = order_info['order_to_number']
        
        return order_info
    
    def _extract_line_items(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract line items from UNFI East PDF text"""
        
        line_items = []
        
        # Debug: print the text content to see what we're working with
        print(f"DEBUG: PDF text content length: {len(text_content)}")
        
        # Print first few lines to debug
        first_lines = text_content.split('\n')[:20]
        for i, line in enumerate(first_lines):
            print(f"DEBUG Line {i}: {repr(line)}")
        
        # Look for the line items section and extract it
        lines = text_content.split('\n')
        item_section_started = False
        item_lines = []
        
        collecting_item = False
        current_item_text = ""
        
        for line in lines:
            # Check if we've reached the line items section
            if 'Prod# Seq' in line and 'Product Description' in line:
                item_section_started = True
                print(f"DEBUG: Found item section header")
                continue
            elif item_section_started:
                # Check if we've reached the end of items (skip the separator line)
                if '-------' in line and len(line) > 50 and not re.search(r'\d{6}', line):
                    print(f"DEBUG: Skipping separator line: {line[:50]}...")
                    continue
                elif 'Total Pieces' in line or ('Total' in line and 'Order Net' in line):
                    print(f"DEBUG: End of items section: {line[:50]}...")
                    # Add the last item if we were collecting one
                    if current_item_text.strip():
                        item_lines.append(current_item_text.strip())
                        print(f"DEBUG: Final item: {current_item_text.strip()[:80]}...")
                    break
                elif line.strip():
                    # Special handling for concatenated lines that contain multiple items
                    if re.search(r'\d{6}.*\d{6}.*\d{6}', line):
                        print(f"DEBUG: Found concatenated line with multiple items: {line[:100]}...")
                        # Split by product number pattern at the beginning of each item
                        parts = re.split(r'(?=\d{6}\s+\d+\s+\d+\s+\d+)', line)
                        for part in parts:
                            if part.strip() and re.match(r'\d{6}', part.strip()):
                                item_lines.append(part.strip())
                                print(f"DEBUG: Extracted item from concatenated line: {part.strip()[:80]}...")
                        continue
                    
                    # Check if this line starts with a product number (new item)
                    if re.match(r'\s*\d{6}\s+\d+', line):
                        # Save previous item if we have one
                        if current_item_text.strip():
                            item_lines.append(current_item_text.strip())
                            print(f"DEBUG: Completed item: {current_item_text.strip()[:80]}...")
                        # Start new item
                        current_item_text = line.strip()
                        collecting_item = True
                        print(f"DEBUG: Starting new item: {line.strip()[:80]}...")
                    elif collecting_item:
                        # This is a continuation line for the current item
                        current_item_text += " " + line.strip()
                        print(f"DEBUG: Adding to current item: {line.strip()[:50]}...")
                    else:
                        print(f"DEBUG: Skipping line: {line.strip()[:50]}...")
        
        # Add the last item if we ended while collecting
        if current_item_text.strip():
            item_lines.append(current_item_text.strip())
            print(f"DEBUG: Final collected item: {current_item_text.strip()[:80]}...")
        
        print(f"DEBUG: Extracted {len(item_lines)} item lines")
        
        # Process each item line individually
        for line in item_lines:
            # Pattern for UNFI East items - simpler pattern to match the concatenated format
            # Example: 315851   1    6    6 8-900-2      1   54 8 OZ    KTCHLV DSP,GRAIN POUCH,RTH,    102.60  102.60    615.60
            item_pattern = r'(\d{6})\s+\d+\s+\d+\s+(\d+)\s+([\d\-]+)\s+\d+\s+\d+\s+([\d\.]+)\s+OZ\s+([A-Z\s,&\.\-:]+?)\s+([\d\.]+)\s+[\d\.]+\s+([\d,]+\.?\d*)'
            
            match = re.search(item_pattern, line)
            if match:
                try:
                    prod_number = match.group(1)  # Prod# (like 315851)
                    qty = int(match.group(2))     # Qty
                    vend_id = match.group(3)      # Vend ID (like 8-900-2)
                    size = match.group(4)         # Size (like 54 or 3.5)
                    description = match.group(5).strip()  # Product Description
                    unit_cost = float(match.group(6))     # Unit Cost
                    extension = float(match.group(7).replace(',', ''))  # Extension
                    
                    # Apply item mapping using the original Prod#
                    mapped_item = self.mapping_utils.get_item_mapping(prod_number, 'unfi_east')
                    print(f"DEBUG: Item mapping lookup: {prod_number} -> {mapped_item}")
                    
                    item = {
                        'item_number': mapped_item,
                        'raw_item_number': prod_number,
                        'item_description': description,
                        'quantity': qty,
                        'unit_price': unit_cost,
                        'total_price': extension
                    }
                    
                    line_items.append(item)
                    print(f"DEBUG: Successfully parsed item: Prod#{prod_number} -> {mapped_item}, Qty: {qty}, Price: {unit_cost}")
                    
                except (ValueError, IndexError) as e:
                    print(f"DEBUG: Failed to parse line: {line} - Error: {e}")
                    continue
            else:
                print(f"DEBUG: No match for line: {line}")
        
        if not line_items:
            print("DEBUG: No items found with line-by-line method, trying regex on full text")
            # Fallback: try regex on the entire text content
            item_pattern = r'(\d{6})\s+\d+\s+\d+\s+(\d+)\s+([\d\-]+)\s+\d+\s+(\d+(?:\.\d+)?)\s+OZ\s+([A-Z][A-Z\s,&\.\-:]+?)\s+(\d+\.\d+)\s+[\d\.,]+\s+([\d,]+\.\d+)'
            matches = re.finditer(item_pattern, text_content)
            
            for match in matches:
                try:
                    prod_number = match.group(1)  # Prod# (like 315851)
                    qty = int(match.group(2))     # Qty
                    vend_id = match.group(3)      # Vend ID (like 8-900-2)
                    size = match.group(4)         # Size (like 54 or 3.5)
                    description = match.group(5).strip()  # Product Description
                    unit_cost = float(match.group(6))     # Unit Cost
                    extension = float(match.group(7).replace(',', ''))  # Extension
                    
                    # Apply item mapping using the original Prod#
                    mapped_item = self.mapping_utils.get_item_mapping(prod_number, 'unfi_east')
                    print(f"DEBUG: Item mapping lookup: {prod_number} -> {mapped_item}")
                    
                    item = {
                        'item_number': mapped_item,
                        'raw_item_number': prod_number,
                        'item_description': description,
                        'quantity': qty,
                        'unit_price': unit_cost,
                        'total_price': extension
                    }
                    
                    line_items.append(item)
                    print(f"DEBUG: Successfully parsed item: Prod#{prod_number} -> {mapped_item}, Qty: {qty}, Price: {unit_cost}")
                    
                except (ValueError, IndexError) as e:
                    print(f"DEBUG: Failed to parse match - Error: {e}")
                    continue
        
        print(f"=== DEBUG: Total line items extracted: {len(line_items)} ===")
        return line_items