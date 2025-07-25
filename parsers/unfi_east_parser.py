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
    
    def __init__(self):
        super().__init__()
        self.source_name = "UNFI East"
    
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
        
        # Extract order date (Ord Date)
        order_date_match = re.search(r'Ord Date.*?(\d{2}/\d{2}/\d{2})', text_content)
        if order_date_match:
            order_info['order_date'] = self.parse_date(order_date_match.group(1))
        
        # Extract pickup date (Pck Date)
        pickup_date_match = re.search(r'Pck Date.*?(\d{2}/\d{2}/\d{2})', text_content)
        if pickup_date_match:
            order_info['pickup_date'] = self.parse_date(pickup_date_match.group(1))
        
        # Extract warehouse/location information for store mapping
        # Look for warehouse names like "Sarasota Warehouse", "Atlanta Warehouse"
        warehouse_match = re.search(r'(Sarasota|Atlanta|[A-Z][a-z]+)\s+Warehouse', text_content)
        if warehouse_match:
            warehouse_name = warehouse_match.group(1)
            order_info['raw_customer_name'] = f"UNFI EAST - {warehouse_name.upper()}"
        else:
            # Look for location codes like "SAR", "ATL"
            location_match = re.search(r'\b([A-Z]{3})\s*$', text_content, re.MULTILINE)
            if location_match:
                location_code = location_match.group(1)
                order_info['raw_customer_name'] = f"UNFI EAST - {location_code}"
        
        # Apply store mapping
        if order_info['raw_customer_name']:
            order_info['customer_name'] = self.mapping_utils.get_store_mapping(
                order_info['raw_customer_name'], 
                'unfi_east'
            )
        
        return order_info
    
    def _extract_line_items(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract line items from UNFI East PDF text"""
        
        line_items = []
        
        # Split text into lines and look for lines starting with 6-digit product numbers
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or lines that don't start with a 6-digit number
            if not line or not re.match(r'^\d{6}', line):
                continue
            
            # Parse each line that starts with a product number
            # Format: 142630   1   96   96 17-041-1     1    6 7.9 OZ  CUCAMO BRUSCHETTA,ARTICHOKE     13.50   13.50  1,296.00
            item_pattern = r'^(\d{6})\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d\-]+)\s+.*?([A-Z][A-Z\s,&\.\-:]+?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+([\d,]+\.\d+)'
            
            match = re.search(item_pattern, line)
            if match:
                try:
                    prod_number = match.group(1)  # Prod# (like 142630)
                    seq = match.group(2)          # Seq (like 1)
                    ord_qty = int(match.group(3)) # Ord Qty (like 96)
                    qty = int(match.group(4))     # Qty (like 96)
                    vend_id = match.group(5)      # Vend ID (like 17-041-1)
                    description = match.group(6).strip()  # Product Description
                    unit_cost = float(match.group(7))     # Unit Cost
                    extension = float(match.group(9).replace(',', ''))  # Extension (remove commas)
                    
                    # Normalize Prod# by removing leading zeros 
                    normalized_prod = prod_number.lstrip('0') or '0'
                    
                    # Apply item mapping using normalized Prod# 
                    mapped_item = self.mapping_utils.get_item_mapping(normalized_prod, 'unfi_east')
                    
                    item = {
                        'item_number': mapped_item,
                        'raw_item_number': prod_number,  # Keep original Prod#
                        'item_description': description,
                        'quantity': qty,
                        'unit_price': unit_cost,
                        'total_price': extension
                    }
                    
                    line_items.append(item)
                    print(f"DEBUG: Successfully parsed item: Prod#{prod_number} -> {mapped_item}, Qty: {qty}, Price: {unit_cost}")
                    
                except (ValueError, IndexError) as e:
                    print(f"DEBUG: Failed to parse line: {line}")
                    continue
            else:
                print(f"DEBUG: Pattern didn't match line: {line}")
        
        print(f"=== DEBUG: Total line items extracted: {len(line_items)} ===")
        return line_items