"""
Parser for ROSS order files (PDF format)
Handles ROSS Dress for Less purchase orders
"""

from typing import List, Dict, Any, Optional
import re
import io
from PyPDF2 import PdfReader
from .base_parser import BaseParser
from utils.mapping_utils import MappingUtils


class ROSSParser(BaseParser):
    """Parser for ROSS PDF order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "ROSS"
        self.mapping_utils = MappingUtils(use_database=True)
    
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse ROSS PDF order file"""
        
        if file_extension.lower() != 'pdf':
            raise ValueError("ROSS parser only supports PDF files")
        
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
            raise ValueError(f"Error parsing ROSS PDF: {str(e)}")
    
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
            'order_date': None,
            'po_start_date': None,
            'po_cancel_date': None,
            'delivery_date': None,
            'customer_name': 'UNKNOWN',
            'raw_customer_name': '',
            'store_name': 'UNKNOWN',
            'pickup_location': '',
            'source_file': filename
        }
        
        # Extract Purchase Order Number
        po_match = re.search(r'PURCHASE\s+ORDER\s+NO[:\s]+(\d+)', text_content, re.IGNORECASE)
        if po_match:
            order_info['order_number'] = po_match.group(1)
        
        # Extract ORDER DATE
        order_date_match = re.search(r'ORDER\s+DATE[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})', text_content, re.IGNORECASE)
        if order_date_match:
            order_info['order_date'] = self.parse_date(order_date_match.group(1))
        
        # Extract PO START DATE
        po_start_match = re.search(r'PO\s+START\s+DATE[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})', text_content, re.IGNORECASE)
        if po_start_match:
            order_info['po_start_date'] = self.parse_date(po_start_match.group(1))
            # Use PO START DATE as delivery date if available
            order_info['delivery_date'] = order_info['po_start_date']
        
        # Extract PO CANCEL DATE
        po_cancel_match = re.search(r'PO\s+CANCEL\s+DATE[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})', text_content, re.IGNORECASE)
        if po_cancel_match:
            order_info['po_cancel_date'] = self.parse_date(po_cancel_match.group(1))
        
        # Extract Pickup Location - this is critical for customer mapping
        # Pattern: "PICKUP LOC: NJ - New Jersey" or "Domestic PICKUP LOC: NJ - New Je"
        pickup_patterns = [
            r'PICKUP\s+LOC[:\s]+([A-Z]{2})\s*[-–]\s*([^:\n]+)',
            r'Domestic\s+PICKUP\s+LOC[:\s]+([A-Z]{2})\s*[-–]\s*([^:\n]+)',
            r'PICKUP\s+LOC[:\s]+([A-Z]{2})',
        ]
        
        pickup_location = None
        for pattern in pickup_patterns:
            pickup_match = re.search(pattern, text_content, re.IGNORECASE)
            if pickup_match:
                state_code = pickup_match.group(1).strip()
                state_name = pickup_match.group(2).strip() if len(pickup_match.groups()) > 1 else state_code
                pickup_location = f"{state_code} - {state_name}"
                order_info['pickup_location'] = pickup_location
                print(f"DEBUG: Found pickup location: '{pickup_location}'")
                break
        
        # Map pickup location to customer using customer mapping
        # Special handling: "PICKUP LOC: NJ - New Jersey" -> "CUSTOMER PSS_NJ"
        if pickup_location:
            # Try to extract just the state code for mapping
            state_code_match = re.search(r'([A-Z]{2})', pickup_location)
            if state_code_match:
                state_code = state_code_match.group(1)
                # Try mapping with full pickup location first
                mapped_customer = self.mapping_utils.get_customer_mapping(pickup_location, 'ross')
                if mapped_customer and mapped_customer != 'UNKNOWN':
                    order_info['customer_name'] = mapped_customer
                    order_info['raw_customer_name'] = pickup_location
                    print(f"DEBUG: ROSS Customer Mapping: '{pickup_location}' -> '{mapped_customer}'")
                else:
                    # Try with just state code
                    mapped_customer = self.mapping_utils.get_customer_mapping(state_code, 'ross')
                    if mapped_customer and mapped_customer != 'UNKNOWN':
                        order_info['customer_name'] = mapped_customer
                        order_info['raw_customer_name'] = pickup_location
                        print(f"DEBUG: ROSS Customer Mapping (state code): '{state_code}' -> '{mapped_customer}'")
                    else:
                        # Default mapping for NJ
                        if state_code == 'NJ':
                            order_info['customer_name'] = 'CUSTOMER PSS_NJ'
                            order_info['raw_customer_name'] = pickup_location
                            print(f"DEBUG: Using default customer mapping for NJ: 'CUSTOMER PSS_NJ'")
                        else:
                            print(f"DEBUG: No customer mapping found for pickup location '{pickup_location}'")
        
        # Apply store mapping (separate from customer mapping)
        # For ROSS, store mapping might use pickup location or other identifiers
        if pickup_location:
            mapped_store = self.mapping_utils.get_store_mapping(pickup_location, 'ross')
            if mapped_store and mapped_store != 'UNKNOWN' and mapped_store != pickup_location:
                order_info['store_name'] = mapped_store
                print(f"DEBUG: ROSS Store Mapping: '{pickup_location}' -> '{mapped_store}'")
            else:
                # Default store name (same as customer for ROSS)
                order_info['store_name'] = order_info['customer_name']
        
        return order_info
    
    def _extract_line_items(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract line items from ROSS PDF text"""
        
        line_items = []
        
        # Split text into lines for easier processing
        lines = text_content.split('\n')
        
        # Look for the item table section
        # Items are typically in a table with columns:
        # VENDOR STYLE #, ITEM DESCRIPTION, UNIT COST, ROSS ITEM#, LABEL, PREPACK/INNER, etc.
        
        # Pattern to find item rows - look for vendor style numbers (e.g., "7-210-66")
        # Vendor style pattern: digits-digits-digits (e.g., "7-210-66", "7-210-71")
        vendor_style_pattern = r'(\d+-\d+-\d+)'
        
        # Also look for ROSS ITEM# (12-digit numbers like "400284764788")
        ross_item_pattern = r'(\d{12})'
        
        # Find all potential item lines
        item_section_started = False
        for i, line in enumerate(lines):
            # Check if we've reached the item section (look for table headers)
            if 'VENDOR STYLE' in line.upper() or 'ITEM DESCRIPTION' in line.upper():
                item_section_started = True
                continue
            
            # Check if we've reached the end of items
            if item_section_started and ('TOTAL' in line.upper() or 'SUMMARY' in line.upper()):
                break
            
            if item_section_started:
                # Try to extract item information from this line
                vendor_style_match = re.search(vendor_style_pattern, line)
                ross_item_match = re.search(ross_item_pattern, line)
                
                if vendor_style_match or ross_item_match:
                    try:
                        item = self._parse_item_line(line, lines, i)
                        if item:
                            line_items.append(item)
                    except Exception as e:
                        print(f"DEBUG: Error parsing item line: {e}")
                        continue
        
        # If no items found with line-by-line method, try regex on full text
        if not line_items:
            # Look for patterns in the full text
            # Pattern: Vendor Style, Description, Unit Cost, ROSS Item#, etc.
            item_pattern = r'(\d+-\d+-\d+)\s+([A-Z0-9\s:]+?)\s+(\d+\.\d{2})\s+(\d{12})'
            matches = re.finditer(item_pattern, text_content)
            
            for match in matches:
                try:
                    vendor_style = match.group(1)
                    description = match.group(2).strip()
                    unit_cost = float(match.group(3))
                    ross_item = match.group(4)
                    
                    # Try to find PREPACK/INNER (case qty) - look for number after the item
                    # Pattern: "PREPACK/INNER" followed by a number
                    context_start = match.end()
                    context = text_content[context_start:context_start + 200]
                    prepack_match = re.search(r'PREPACK/INNER[:\s]*(\d+)', context, re.IGNORECASE)
                    case_qty = int(prepack_match.group(1)) if prepack_match else None
                    
                    # Get quantity - look for quantity field (might be in a separate section)
                    # For now, we'll need to extract from the table structure
                    quantity = 1  # Default, will need to extract from PDF structure
                    
                    # Apply item mapping
                    mapped_item = self.mapping_utils.get_item_mapping(ross_item, 'ross')
                    if not mapped_item or mapped_item == ross_item:
                        # Try mapping with vendor style as fallback
                        mapped_item = self.mapping_utils.get_item_mapping(vendor_style, 'ross')
                        if not mapped_item or mapped_item == vendor_style:
                            mapped_item = ross_item
                    
                    # Get case_qty from item mapping for unit to case conversion
                    case_qty_from_mapping = self._get_case_qty_from_mapping(ross_item, vendor_style, 'ross')
                    if case_qty_from_mapping:
                        case_qty = case_qty_from_mapping
                    
                    # Convert units to cases if case_qty is available
                    quantity_in_cases = quantity
                    if case_qty and case_qty > 0:
                        quantity_in_cases = quantity / case_qty
                        print(f"DEBUG: Converted {quantity} units to {quantity_in_cases} cases (case_qty={case_qty})")
                    
                    item = {
                        'item_number': mapped_item,
                        'raw_item_number': ross_item,
                        'vendor_style': vendor_style,
                        'item_description': description,
                        'quantity': int(quantity_in_cases) if quantity_in_cases == int(quantity_in_cases) else quantity_in_cases,
                        'unit_price': unit_cost,
                        'total_price': unit_cost * quantity_in_cases,
                        'case_qty': case_qty,
                        'original_quantity_units': quantity
                    }
                    
                    line_items.append(item)
                    
                except Exception as e:
                    print(f"DEBUG: Error parsing item from regex: {e}")
                    continue
        
        print(f"DEBUG: Extracted {len(line_items)} line items from ROSS PDF")
        return line_items
    
    def _parse_item_line(self, line: str, all_lines: List[str], line_idx: int) -> Optional[Dict[str, Any]]:
        """Parse a single item line from the ROSS PDF"""
        
        try:
            # Extract vendor style number (e.g., "7-210-66")
            vendor_style_match = re.search(r'(\d+-\d+-\d+)', line)
            if not vendor_style_match:
                return None
            
            vendor_style = vendor_style_match.group(1)
            
            # Extract ROSS ITEM# (12-digit number)
            ross_item_match = re.search(r'(\d{12})', line)
            if not ross_item_match:
                return None
            
            ross_item = ross_item_match.group(1)
            
            # Extract UNIT COST (decimal number like "1.50")
            unit_cost_match = re.search(r'(\d+\.\d{2})', line)
            unit_cost = float(unit_cost_match.group(1)) if unit_cost_match else 0.0
            
            # Extract description - text between vendor style and unit cost
            # Description format: "16OZ ORG FUSILLI PASTA:NO COLOR:NO SIZES"
            desc_start = vendor_style_match.end()
            desc_end = unit_cost_match.start() if unit_cost_match else len(line)
            description = line[desc_start:desc_end].strip()
            
            # Clean up description (remove extra spaces, colons at end)
            description = re.sub(r'\s+', ' ', description).strip().rstrip(':')
            
            # Extract PREPACK/INNER (case qty) - look in current line and next few lines
            case_qty = None
            search_lines = [line] + all_lines[line_idx + 1:line_idx + 3]
            for search_line in search_lines:
                prepack_match = re.search(r'PREPACK/INNER[:\s]*(\d+)', search_line, re.IGNORECASE)
                if prepack_match:
                    case_qty = int(prepack_match.group(1))
                    break
            
            # Extract quantity - this might be in a separate column or section
            # For ROSS, quantity might be in "NESTED PK QTY" or another field
            # For now, we'll try to find it in the line or nearby lines
            quantity = 1  # Default
            qty_match = re.search(r'\b(\d+)\s*(?:CASE|UNIT|PK|PACK)', line, re.IGNORECASE)
            if qty_match:
                quantity = int(qty_match.group(1))
            
            # Apply item mapping
            mapped_item = self.mapping_utils.get_item_mapping(ross_item, 'ross')
            if not mapped_item or mapped_item == ross_item:
                # Try mapping with vendor style as fallback
                mapped_item = self.mapping_utils.get_item_mapping(vendor_style, 'ross')
                if not mapped_item or mapped_item == vendor_style:
                    mapped_item = ross_item
            
            # Get case_qty from item mapping for unit to case conversion
            case_qty_from_mapping = self._get_case_qty_from_mapping(ross_item, vendor_style, 'ross')
            if case_qty_from_mapping:
                case_qty = case_qty_from_mapping
            
            # If case_qty is available, convert units to cases
            quantity_in_cases = quantity
            if case_qty and case_qty > 0:
                quantity_in_cases = quantity / case_qty
                print(f"DEBUG: Converted {quantity} units to {quantity_in_cases} cases (case_qty={case_qty})")
            
            return {
                'item_number': mapped_item,
                'raw_item_number': ross_item,
                'vendor_style': vendor_style,
                'item_description': description,
                'quantity': int(quantity_in_cases) if quantity_in_cases == int(quantity_in_cases) else quantity_in_cases,
                'unit_price': unit_cost,
                'total_price': unit_cost * quantity_in_cases,
                'case_qty': case_qty,
                'original_quantity_units': quantity
            }
            
        except Exception as e:
            print(f"DEBUG: Error in _parse_item_line: {e}")
            return None
    
    def _get_case_qty_from_mapping(self, ross_item: str, vendor_style: str, source: str) -> Optional[float]:
        """Get case_qty from item mapping for unit to case conversion"""
        
        try:
            if self.mapping_utils.use_database and self.mapping_utils.db_service:
                # Try to get case_qty from database
                from database.service import DatabaseService
                db_service = DatabaseService()
                
                # Try with ROSS item number first
                mapping = db_service.get_item_mapping_with_case_qty(ross_item, source)
                if mapping and mapping.get('case_qty'):
                    return float(mapping['case_qty'])
                
                # Try with vendor style as fallback
                mapping = db_service.get_item_mapping_with_case_qty(vendor_style, source)
                if mapping and mapping.get('case_qty'):
                    return float(mapping['case_qty'])
            
        except Exception as e:
            print(f"DEBUG: Error getting case_qty from mapping: {e}")
        
        return None
