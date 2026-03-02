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
            text_content = self._extract_text_from_pdf(file_content)
            
            order_info = self._extract_order_header(text_content, filename)
            line_items = self._extract_line_items(text_content)
            
            orders = []
            if line_items:
                for item in line_items:
                    order_item = {**order_info, **item}
                    orders.append(order_item)
            else:
                orders.append(order_info)
            
            if not orders:
                raise ValueError("No orders extracted from ROSS PDF. Please verify the PDF format is correct.")
            
            return orders
            
        except ValueError:
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"DEBUG: ROSS Parser Error: {error_details}")
            raise ValueError(f"Error parsing ROSS PDF: {str(e)}")
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file content using PyPDF2"""
        
        try:
            pdf_stream = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_stream)
            
            if len(pdf_reader.pages) == 0:
                raise ValueError("PDF file appears to be empty or corrupted (no pages found)")
            
            text_content = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                except Exception as page_error:
                    print(f"DEBUG: Warning - Could not extract text from page {page_num + 1}: {page_error}")
                    continue
            
            if not text_content or len(text_content.strip()) < 50:
                raise ValueError("PDF text extraction returned very little or no text. The PDF may be image-based or corrupted.")
            
            return text_content
            
        except ValueError:
            raise
        except Exception as e:
            try:
                decoded = file_content.decode('utf-8', errors='ignore')
                if len(decoded) > 100:
                    return decoded
            except:
                pass
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
        
        # --- Date extraction ---
        # The PDF layout has dates in a table that gets extracted as:
        #   "10/13/23 YPO CANCEL DATE"    (preticket date + Y flag + label)
        #   "10/12/23 12/05/23"            (ORDER DATE value + PO CANCEL DATE value)
        #   ...
        #   "PO START DATE"
        #   "12/01/23"
        
        # Strategy: find the line containing "PO CANCEL DATE", then the NEXT line
        # has ORDER DATE (first date) and PO CANCEL DATE (second date)
        lines = text_content.split('\n')
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})'
        
        for i, line in enumerate(lines):
            if 'PO CANCEL DATE' in line.upper():
                # Look at the next few lines for dates
                for j in range(i + 1, min(i + 3, len(lines))):
                    dates_on_line = re.findall(date_pattern, lines[j])
                    if len(dates_on_line) >= 2:
                        # First date = ORDER DATE, Second date = PO CANCEL DATE
                        order_info['order_date'] = self.parse_date(dates_on_line[0])
                        order_info['po_cancel_date'] = self.parse_date(dates_on_line[1])
                        print(f"DEBUG: Extracted ORDER DATE: {order_info['order_date']}, PO CANCEL DATE: {order_info['po_cancel_date']}")
                        break
                    elif len(dates_on_line) == 1:
                        # Single date after PO CANCEL DATE label = cancel date
                        order_info['po_cancel_date'] = self.parse_date(dates_on_line[0])
                        break
                break
        
        # Extract PO START DATE (ship date)
        po_start_match = re.search(r'PO\s+START\s+DATE\s*[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})', text_content, re.IGNORECASE)
        if po_start_match:
            order_info['po_start_date'] = self.parse_date(po_start_match.group(1))
            order_info['delivery_date'] = order_info['po_start_date']
            print(f"DEBUG: Extracted PO START DATE: {order_info['po_start_date']}")
        
        # If ORDER DATE still not found, try a direct regex
        if not order_info['order_date']:
            # Try: "ORDER DATE" possibly followed by other text, then a date on a nearby line
            order_date_match = re.search(r'ORDER\s+DATE[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})', text_content, re.IGNORECASE)
            if order_date_match:
                order_info['order_date'] = self.parse_date(order_date_match.group(1))
        
        # Extract Pickup Location
        # Pattern: "PICKUP LOC: CA - California" (stop before "THIS ORDER")
        pickup_match = re.search(
            r'PICKUP\s+LOC[:\s]+([A-Z]{2})\s*[-–]\s*([A-Za-z\s]+?)(?=THIS|$)',
            text_content, re.IGNORECASE
        )
        if pickup_match:
            state_code = pickup_match.group(1).strip()
            state_name = pickup_match.group(2).strip()
            order_info['pickup_location'] = f"{state_code} - {state_name}"
            print(f"DEBUG: Found pickup location: '{order_info['pickup_location']}'")
        else:
            # Simpler fallback: just get the state code
            pickup_simple = re.search(r'PICKUP\s+LOC[:\s]+([A-Z]{2})', text_content, re.IGNORECASE)
            if pickup_simple:
                order_info['pickup_location'] = pickup_simple.group(1)
        
        # Map customer - ROSS has one customer, use the first/only customer mapping
        customer_mappings = self.mapping_utils.db_service.get_customer_mappings('ross')
        if customer_mappings:
            mapped_customer_name = list(customer_mappings.values())[0]
            order_info['customer_name'] = mapped_customer_name
            order_info['raw_customer_name'] = 'ROSS'
            print(f"DEBUG: ROSS Customer Mapping: '{mapped_customer_name}'")
        else:
            print(f"DEBUG: No customer mapping found for ROSS, using default")
            order_info['customer_name'] = 'UNKNOWN'
            order_info['raw_customer_name'] = 'ROSS'
        
        # Apply store mapping using PICKUP LOC from PDF
        # Both SaleStoreName and StoreName in Xoro should come from this mapping
        pickup_location = order_info.get('pickup_location', '')
        if pickup_location:
            mapped_store = self.mapping_utils.get_store_mapping(pickup_location, 'ross')
            if mapped_store and mapped_store != 'UNKNOWN' and mapped_store != pickup_location:
                order_info['store_name'] = mapped_store
                order_info['sale_store_name'] = mapped_store
                print(f"DEBUG: ROSS Store Mapping: PICKUP LOC '{pickup_location}' -> '{mapped_store}'")
            else:
                print(f"DEBUG: ROSS - No store mapping found for PICKUP LOC '{pickup_location}'")
                order_info['store_name'] = 'UNKNOWN'
                order_info['sale_store_name'] = 'UNKNOWN'
        else:
            print("DEBUG: ROSS - No PICKUP LOC found in PDF")
            order_info['store_name'] = 'UNKNOWN'
            order_info['sale_store_name'] = 'UNKNOWN'
        
        return order_info
    
    def _extract_line_items(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract line items from ROSS PDF text.
        
        ROSS PDFs have items in a table. For multi-item POs the PDF
        extraction stacks per-column values, so we detect the number
        of items from header duplication and parse accordingly.
        """
        
        text_lines = text_content.split('\n')
        
        # Collect text between the last "NESTED PK QTY" header and "ALL CARTONS"
        item_text = ""
        in_items = False
        for line in text_lines:
            upper = line.upper()
            if 'NESTED PK QTY' in upper:
                idx = upper.rfind('NESTED PK QTY')
                after_header = line[idx + len('NESTED PK QTY'):]
                if after_header.strip():
                    item_text += after_header + "\n"
                in_items = True
                continue
            if in_items:
                if 'ALL CARTONS MUST BE MARKED' in upper:
                    # Keep text BEFORE the marker (e.g. "NO SIZES 8ALL CARTONS...")
                    marker_idx = upper.find('ALL CARTONS MUST BE MARKED')
                    before_marker = line[:marker_idx].strip()
                    if before_marker:
                        item_text += before_marker + "\n"
                    break
                item_text += line + "\n"
        
        if not item_text.strip():
            print("DEBUG: No item text found")
            return []
        
        print(f"DEBUG: Item section text:\n{item_text[:600]}")
        
        # --- Step 1: Extract vendor styles from line beginnings ---
        # In ROSS PDFs vendor styles appear at the start of lines.
        # Pattern: 1-2 digits, hyphen, 1-3 digits, optional hyphen + 1-2 digits
        # e.g. "8-100-9", "8-100-10", "17-001-5", "17-601"
        vendor_styles = []
        remaining_text_parts = []
        
        for line in item_text.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            # Try to extract a vendor style from the start of the line
            m = re.match(r'(\d{1,2}-\d{1,3}(?:-\d{1,2})?)(.*)', stripped)
            if m:
                style = m.group(1)
                rest = m.group(2).strip()
                if style not in vendor_styles:
                    vendor_styles.append(style)
                if rest:
                    remaining_text_parts.append(rest)
            else:
                remaining_text_parts.append(stripped)
        
        if not vendor_styles:
            print("DEBUG: No vendor style numbers found in item text")
            return []
        
        remaining_text = '\n'.join(remaining_text_parts)
        num_items = len(vendor_styles)
        print(f"DEBUG: Found {num_items} vendor styles: {vendor_styles}")
        
        # --- Step 2: Extract descriptions ---
        # Descriptions contain product info (e.g. "7.9OZ VEGAN BASIL PESTO")
        # They may be preceded by a date (e.g. "5/1/24") which we strip
        desc_lines = []
        skip_words = {'NO COLOR', 'NO SIZES', 'CUCINA AMORE', 'CUCINA', 'ALL CARTONS'}
        for part in remaining_text_parts:
            # Strip leading date if present (e.g. "5/1/24 ")
            cleaned = re.sub(r'^\d{1,2}/\d{1,2}/\d{2,4}\s*', '', part).strip()
            # Stop at first price on the line
            cleaned = re.split(r'\s+\d+\.\d{2}', cleaned)[0].strip()
            # Remove trailing :NO COLOR:NO SIZES
            cleaned = re.sub(r':NO COLOR.*$', '', cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r':NO SIZES.*$', '', cleaned, flags=re.IGNORECASE).strip()
            # Must contain letters, be > 2 chars, not be a known non-description
            if (cleaned and len(cleaned) > 2
                    and re.search(r'[A-Z]', cleaned, re.IGNORECASE)
                    and cleaned.upper() not in skip_words
                    and not re.match(r'^(NO COLOR|NO SIZES|CUCINA|ALL CARTONS)', cleaned, re.IGNORECASE)):
                desc_lines.append(cleaned)
        
        # --- Step 3: Extract prices (unit cost) ---
        # Prices are decimal numbers like "1.50", "5.00"
        # Filter out remaining_text to remove vendor styles before scanning
        all_prices = re.findall(r'(\d+\.\d{2})', remaining_text)
        # First N prices are unit costs, next N are comp retail
        unit_costs = []
        for p in all_prices:
            unit_costs.append(float(p))
            if len(unit_costs) >= num_items:
                break
        
        # --- Step 4: Extract ORDER QTY ---
        # Look for comma-separated thousands (e.g. "6,000", "1,200") or plain large numbers
        all_qty_strs = re.findall(r'(?<!\d)(\d{1,3}(?:,\d{3})+)(?!\d)', remaining_text)
        all_qtys = [int(q.replace(',', '')) for q in all_qty_strs]
        if len(all_qtys) < num_items:
            # Fallback: find plain numbers >= 3 digits.
            # Exclude numbers preceded by comma (fragments of comma-separated numbers like "600" from "1,600")
            # and numbers that are part of prices (preceded/followed by ".")
            plain_nums = re.findall(r'(?<!\d)(?<!\.)(?<!,)(\d{3,})(?!\d)(?!\.)', remaining_text)
            for n in plain_nums:
                val = int(n)
                if val > 10 and val not in all_qtys:
                    all_qtys.append(val)
        
        # --- Step 5: Extract NESTED PK QTY ---
        # Small numbers (typically 6 or 8) appearing near the end of the item section.
        # Exclude digits that are part of prices or dates.
        nested_pks = []
        for part in reversed(remaining_text_parts):
            # Remove dates (e.g. "5/1/24") and prices (e.g. "12.99") to avoid false matches
            cleaned_part = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '', part)
            cleaned_part = re.sub(r'\d+\.\d+', '', cleaned_part)
            nums = re.findall(r'(?<!\d)(?<!\.)(\d{1,2})(?!\d)(?!\.)', cleaned_part)
            for n in reversed(nums):
                val = int(n)
                if 2 <= val <= 48:
                    nested_pks.insert(0, val)
                    if len(nested_pks) >= num_items:
                        break
            if len(nested_pks) >= num_items:
                break
        
        # If fewer nested_pks found than items, repeat values to fill
        if nested_pks and len(nested_pks) < num_items:
            while len(nested_pks) < num_items:
                nested_pks.insert(0, nested_pks[0])
        
        # --- Step 6: Build item records ---
        line_items = []
        for i, style in enumerate(vendor_styles):
            try:
                unit_cost = unit_costs[i] if i < len(unit_costs) else 0.0
                order_qty = all_qtys[i] if i < len(all_qtys) else 1
                description = desc_lines[i] if i < len(desc_lines) else ''
                nested_pk = nested_pks[i] if i < len(nested_pks) else None
                
                # Apply item mapping
                mapped_item = self.mapping_utils.get_item_mapping(style, 'ross')
                if not mapped_item or mapped_item == style:
                    mapped_item = style
                
                # Get case_qty from item mapping (takes priority over PDF nested_pk)
                case_qty_from_mapping = self._get_case_qty_from_mapping(style, style, 'ross')
                case_qty = case_qty_from_mapping if case_qty_from_mapping else nested_pk
                
                # Convert units to cases: Xoro qty = ORDER QTY / case_qty
                quantity_in_cases = order_qty
                if case_qty and case_qty > 0:
                    try:
                        quantity_in_cases = order_qty / case_qty
                        print(f"DEBUG: Item {style}: {order_qty} units / {case_qty} case_qty = {quantity_in_cases} cases")
                    except ZeroDivisionError:
                        quantity_in_cases = order_qty
                
                final_qty = max(1, int(round(quantity_in_cases)))
                
                print(f"DEBUG: Parsed item: style={style}, desc='{description}', "
                      f"cost={unit_cost}, order_qty={order_qty}, "
                      f"case_qty={case_qty}, final_qty={final_qty}")
                
                line_items.append({
                    'item_number': mapped_item,
                    'raw_item_number': style,
                    'vendor_style': style,
                    'item_description': description,
                    'quantity': final_qty,
                    'unit_price': unit_cost,
                    'total_price': unit_cost * final_qty,
                    'case_qty': case_qty,
                    'original_quantity_units': order_qty
                })
                
            except Exception as e:
                print(f"DEBUG: Error parsing item {style}: {e}")
                continue
        
        print(f"DEBUG: Extracted {len(line_items)} line items from ROSS PDF")
        return line_items
    
    def _get_case_qty_from_mapping(self, ross_item: str, vendor_style: str, source: str) -> Optional[float]:
        """Get case_qty from item mapping for unit to case conversion"""
        
        try:
            if self.mapping_utils.use_database and self.mapping_utils.db_service:
                db_service = self.mapping_utils.db_service
                
                mapping = db_service.get_item_mapping_with_case_qty(ross_item, source)
                if mapping and mapping.get('case_qty'):
                    return float(mapping['case_qty'])
                
                if vendor_style != ross_item:
                    mapping = db_service.get_item_mapping_with_case_qty(vendor_style, source)
                    if mapping and mapping.get('case_qty'):
                        return float(mapping['case_qty'])
            
        except Exception as e:
            print(f"DEBUG: Error getting case_qty from mapping: {e}")
        
        return None
