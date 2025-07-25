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
        
        # Debug: Print extracted text to understand structure
        print("=== DEBUG: Extracted PDF Text ===")
        print(text_content[:1000])  # Print first 1000 chars
        print("=== END DEBUG ===")
        
        # Find the line items section
        # Look for the table with Prod#, Seq, Ord Qty, etc.
        lines = text_content.split('\n')
        in_items_section = False
        
        print(f"=== DEBUG: Total lines in PDF: {len(lines)} ===")
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Start of items section - look for header
            if 'Prod#' in line and ('Seq' in line or 'Ord' in line or 'Product Description' in line):
                in_items_section = True
                print(f"DEBUG: Found items section header at line {i}: {line}")
                continue
            
            # End of items section
            if in_items_section and ('Total Pieces' in line or 'Total Vendor Cases' in line or line.startswith('---')):
                print(f"DEBUG: End of items section at line {i}: {line}")
                break
            
            # Parse line items
            if in_items_section and line and len(line) > 10:  # Skip very short lines
                print(f"DEBUG: Trying to parse line {i}: {line}")
                item = self._parse_unfi_east_line(line)
                if item:
                    print(f"DEBUG: Successfully parsed item: {item}")
                    line_items.append(item)
                else:
                    print(f"DEBUG: Failed to parse line: {line}")
        
        print(f"=== DEBUG: Total line items extracted: {len(line_items)} ===")
        return line_items
    
    def _parse_unfi_east_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single UNFI East line item"""
        
        # Skip lines that are comments or special instructions
        if line.startswith('?') or line.startswith('MIN ') or line.startswith('-'):
            return None
        
        # Pattern for UNFI East line items:
        # Prod# Seq Ord Qty Vend ID MC Pack U/M Brand Product Description Unit Cst Vend CS Extension
        # Example: 268066   1   40   40 8-907        1    6 8 OZ    KTCHLV RICE,CAULIFLOWER,RTH     10.20   10.20    408.00
        
        # Try to parse the line by splitting and extracting fields
        parts = line.split()
        if len(parts) < 8:  # Need at least 8 parts for a valid line
            return None
        
        try:
            # Extract basic fields
            prod_number = parts[0]  # Prod# (like 268066)
            seq = parts[1]          # Seq (like 1)
            ord_qty = int(parts[2]) # Ord Qty (like 40)
            qty = int(parts[3])     # Qty (like 40)
            vend_id = parts[4]      # Vend ID (like 8-907)
            
            # Find unit cost - look for decimal numbers in the line
            unit_costs = re.findall(r'\b(\d+\.\d+)\b', line)
            if len(unit_costs) >= 2:
                unit_cost = float(unit_costs[0])  # First decimal is usually unit cost
            else:
                unit_cost = 0.0
            
            # Extract description - find text between vend_id and first decimal number
            # Look for the brand and product description pattern
            desc_pattern = r'[A-Z]+\s+([A-Z][A-Z\s,&\.\-]+?)\s+\d+\.\d+'
            desc_match = re.search(desc_pattern, line)
            if desc_match:
                description = desc_match.group(1).strip()
            else:
                # Fallback: extract text after brand code
                brand_pattern = r'[A-Z]{2,}\s+([A-Z][A-Z\s,&\.\-]+)'
                brand_match = re.search(brand_pattern, line)
                description = brand_match.group(1).strip() if brand_match else ""
            
            # Normalize Prod# by removing leading zeros (like UNFI West)
            normalized_prod = prod_number.lstrip('0') or '0'
            
            # Apply item mapping using normalized Prod# 
            mapped_item = self.mapping_utils.get_item_mapping(normalized_prod, 'unfi_east')
            
            return {
                'item_number': mapped_item,
                'raw_item_number': prod_number,  # Keep original Prod#
                'item_description': description,
                'quantity': qty,
                'unit_price': unit_cost,
                'total_price': unit_cost * qty
            }
            
        except (ValueError, IndexError) as e:
            # If parsing fails, return None
            return None