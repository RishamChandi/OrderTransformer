"""
Parser for TJ Maxx PDF/CSV/Excel order files
Supports Distribution files (PDF) and PO files (PDF/CSV/Excel)
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import io
import re
from PyPDF2 import PdfReader
from .base_parser import BaseParser

class TKMaxxParser(BaseParser):
    """Parser for TJ Maxx PDF/CSV/Excel order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "TJ Maxx"
        # Cache PO and Distribution data to combine across uploads
        self._pending_po_data = {}
        self._pending_distribution_data = {}
        self.last_parse_status = None
    
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse TJ Maxx PDF/CSV/Excel order file"""
        
        if file_extension.lower() == 'pdf':
            return self._parse_pdf(file_content, filename)
        elif file_extension.lower() in ['csv', 'xlsx', 'xls']:
            return self._parse_csv_excel(file_content, file_extension, filename)
        else:
            raise ValueError("TJ Maxx parser only supports PDF, CSV and Excel files")
    
    def _parse_pdf(self, file_content: bytes, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse TJ Maxx PDF file (Distribution or PO)"""
        
        try:
            # Extract text from PDF
            text_content = self._extract_text_from_pdf(file_content)
            
            # Determine file type based on content
            if 'ROUTING AND DISTRIBUTION INSTRUCTIONS' in text_content.upper():
                # This is a Distribution file
                distribution_data = self._parse_distribution_data(text_content, filename)
                if not distribution_data:
                    return None
                
                po_number = distribution_data.get('po_number')
                if po_number and po_number in self._pending_po_data:
                    po_data = self._pending_po_data.pop(po_number)
                    self._pending_distribution_data.pop(po_number, None)
                    self.last_parse_status = "combined"
                    return self._combine_po_and_distribution(po_data, distribution_data)
                
                # Store distribution data and wait for matching PO file
                self._pending_distribution_data[po_number] = distribution_data
                self.last_parse_status = "pending"
                return []
            else:
                # This is likely a PO file (Vendor Copy)
                po_data = self._parse_po_data(text_content, filename)
                if not po_data:
                    return None
                
                po_number = po_data.get('po_number')
                if po_number and po_number in self._pending_distribution_data:
                    distribution_data = self._pending_distribution_data.pop(po_number)
                    self._pending_po_data.pop(po_number, None)
                    self.last_parse_status = "combined"
                    return self._combine_po_and_distribution(po_data, distribution_data)
                
                # Store PO data and wait for matching Distribution file
                self._pending_po_data[po_number] = po_data
                self.last_parse_status = "pending"
                return []
                
        except Exception as e:
            raise ValueError(f"Error parsing TJ Maxx PDF: {str(e)}")
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file content using PyPDF2"""
        
        try:
            pdf_stream = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_stream)
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content
            
        except Exception as e:
            raise ValueError(f"Could not extract text from PDF: {str(e)}")
    
    def _parse_distribution_data(self, text_content: str, filename: str) -> Optional[Dict[str, Any]]:
        """Parse Distribution file (ROUTING AND DISTRIBUTION INSTRUCTIONS)"""
        
        # Extract PO Number
        po_match = re.search(r'PO\s+Number[:\s]+(\d+)', text_content, re.IGNORECASE)
        po_number = po_match.group(1) if po_match else filename
        
        # Extract Order Date
        order_date_match = re.search(r'Order\s+Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})', text_content, re.IGNORECASE)
        order_date = None
        if order_date_match:
            order_date = self.parse_date(order_date_match.group(1))
        
        # Extract brand name from filename or content
        brand = self._extract_brand_name(filename, text_content)
        
        # Extract line items from the product table
        # Pattern matches the table with Vendor Style, TJX Style, Description, Units per DC
        line_items = self._extract_distribution_line_items(text_content)
        if not line_items:
            return None
        
        return {
            'po_number': po_number,
            'order_date': order_date,
            'brand': brand,
            'line_items': line_items,
            'source_file': filename
        }
    
    def _extract_brand_name(self, filename: str, text_content: str) -> str:
        """Extract brand name from filename or content"""
        
        # Check filename first
        filename_upper = filename.upper()
        if 'MARSHALLS' in filename_upper:
            return 'Marshalls'
        elif 'TJMAXX' in filename_upper or 'TJ MAXX' in filename_upper:
            return 'TJ Maxx'
        elif 'HOME GOODS' in filename_upper or 'HOMEGOODS' in filename_upper:
            return 'HomeGoods'
        elif 'HOMESENSE' in filename_upper:
            return 'Homesense'
        elif 'WINNERS' in filename_upper:
            return 'Winners'
        
        # Check content
        text_upper = text_content.upper()
        if 'MARSHALLS' in text_upper:
            return 'Marshalls'
        elif 'TJ MAXX' in text_upper or 'TJX' in text_upper:
            return 'TJ Maxx'
        elif 'HOME GOODS' in text_upper or 'HOMEGOODS' in text_upper:
            return 'HomeGoods'
        elif 'HOMESENSE' in text_upper:
            return 'Homesense'
        elif 'WINNERS' in text_upper:
            return 'Winners'
        
        return 'TJ Maxx'  # Default
    
    def _extract_distribution_line_items(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract line items from Distribution file table"""
        
        items = []
        
        # First, extract all DC numbers and their column positions from header
        # Pattern: "SAN DC# 881 Units" or "DC# 881"
        dc_header_pattern = r'(?:([A-Z]{3})\s+)?DC\s*#\s*(\d+)(?:\s+Units)?'
        dc_headers = re.finditer(dc_header_pattern, text_content, re.IGNORECASE)
        
        # Map DC codes to DC numbers (e.g., "SAN" -> "881")
        dc_code_to_number = {}
        dc_numbers_list = []
        
        for match in dc_headers:
            dc_code = match.group(1) if match.group(1) else ''
            dc_num = match.group(2)
            if dc_num:
                dc_numbers_list.append(dc_num)
                if dc_code:
                    dc_code_to_number[dc_code.upper()] = dc_num
        
        # Also extract DC codes from distribution center list if available
        dc_list_matches = re.findall(r'DC\s*#\s*(\d{2,5})', text_content, re.IGNORECASE)
        for dc_num in dc_list_matches:
            if dc_num not in dc_numbers_list:
                dc_numbers_list.append(dc_num)
        
        # Extract line items from table
        # Look for table rows with pattern: "1-1", "1-2", etc. (PG-LN format)
        lines = text_content.split('\n')
        
        # Find table start (after header with "Vendor Style", "TJX Style", etc.)
        table_start = -1
        for i, line in enumerate(lines):
            if 'Vendor Style' in line and ('TJX Style' in line or 'TJX' in line):
                table_start = i
                break
        
        if table_start == -1:
            # Try alternative header patterns
            for i, line in enumerate(lines):
                if 'PG-LN' in line or 'Vendor Style' in line:
                    table_start = i
                    break
        
        if table_start >= 0:
            # Parse table rows
            for i in range(table_start + 1, min(table_start + 100, len(lines))):
                line = lines[i].strip()
                
                # Skip empty lines or lines that don't look like data rows
                if not line or len(line) < 10:
                    continue
                
                # Pattern: "1-1" or "1/1" at start indicates a data row
                if not re.match(r'^\d+[-/]\d+', line):
                    continue
                
                # Split line into parts (handle variable spacing)
                # Try splitting by 2+ spaces first, then by single space if needed
                parts = re.split(r'\s{2,}', line)
                if len(parts) < 3:
                    parts = line.split()
                
                if len(parts) >= 3:
                    try:
                        pg_ln = parts[0].strip()
                        vendor_style = parts[1].strip() if len(parts) > 1 else ''
                        tjx_style = parts[2].strip() if len(parts) > 2 else ''
                        
                        # Description might be in parts[3] or combined
                        description = ''
                        desc_start = 3
                        # Description ends before numeric fields
                        for j in range(3, min(len(parts), 8)):
                            part = parts[j].strip()
                            # If it's a number, we've passed the description
                            if part.replace('.', '').isdigit():
                                desc_start = j
                                break
                            description += ' ' + part if description else part
                        
                        description = description.strip()
                        
                        # Extract total units (usually appears before DC-specific units)
                        total_units = 0
                        dc_units = {}
                        
                        # Look for "Total Units" column value
                        # It's usually one of the larger numbers in the row
                        numeric_parts = []
                        for part in parts[desc_start:]:
                            part_clean = part.strip().replace(',', '')
                            if part_clean.replace('.', '').isdigit():
                                try:
                                    num = int(float(part_clean))
                                    if 0 < num < 1000000:  # Reasonable range
                                        numeric_parts.append(num)
                                except:
                                    pass
                        
                        # The first large number is usually total units
                        # Subsequent numbers are DC-specific units
                        if numeric_parts:
                            total_units = numeric_parts[0]
                            
                            # Map remaining numbers to DCs based on position
                            # This is approximate - actual mapping depends on table structure
                            for idx, dc_num in enumerate(dc_numbers_list):
                                if idx + 1 < len(numeric_parts):
                                    dc_units[dc_num] = numeric_parts[idx + 1]
                        
                        # Alternative: Extract DC units by matching DC codes in header
                        # Look for patterns like "SAN DC# 881 Units: 348" in the text near this row
                        for dc_code, dc_num in dc_code_to_number.items():
                            # Search for DC code followed by units in nearby text
                            pattern = rf'{dc_code}[^\d]*(\d+)'
                            matches = re.findall(pattern, line, re.IGNORECASE)
                            if matches:
                                try:
                                    units = int(matches[-1])  # Take last match (most likely the units)
                                    if 0 < units < 100000:
                                        dc_units[dc_num] = units
                                except:
                                    pass
                        
                        if vendor_style or tjx_style:
                            items.append({
                                'vendor_style': vendor_style,
                                'tjx_style': tjx_style,
                                'description': description,
                                'total_units': total_units,
                                'dc_units': dc_units,
                                'unit_cost': 0.0  # Will be in PO file
                            })
                    except Exception as e:
                        print(f"DEBUG: Error parsing line item at line {i}: {e}")
                        continue
        
        return items

    def _parse_po_data(self, text_content: str, filename: str) -> Optional[Dict[str, Any]]:
        """Parse PO file (VENDOR COPY) for prices and store state"""
        
        # Extract PO Number
        po_number = None
        po_patterns = [
            r'PO\s+Number[:\s]+(\d+)',
            r'DOMESTIC\s+PO\s*#\s*(\d+)',
            r'PO\s*#\s*(\d+)'
        ]
        for pattern in po_patterns:
            po_match = re.search(pattern, text_content, re.IGNORECASE)
            if po_match:
                po_number = po_match.group(1)
                break
        if not po_number:
            po_number = filename
        
        # Extract Order Date
        order_date = None
        order_date_match = re.search(r'ORDER\s+DATE[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})', text_content, re.IGNORECASE)
        if order_date_match:
            order_date = self.parse_date(order_date_match.group(1))
        
        # Extract state for store mapping
        state = None
        state_match = re.search(r'STATE[:\s]+([A-Z]{2})', text_content, re.IGNORECASE)
        if state_match:
            state = state_match.group(1).upper()
        
        # Extract line items with pricing
        line_items = self._extract_po_line_items(text_content)
        if not line_items:
            return None
        
        return {
            'po_number': po_number,
            'order_date': order_date,
            'state': state,
            'line_items': line_items,
            'source_file': filename
        }

    def _extract_po_line_items(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract line items (vendor/tjx style + unit cost) from PO file"""
        
        items = []
        lines = text_content.split('\n')
        in_table = False
        
        for line in lines:
            line_upper = line.upper()
            if 'VENDOR STYLE' in line_upper and 'UNIT COST' in line_upper:
                in_table = True
                continue
            
            if not in_table:
                continue
            
            if not line.strip():
                continue
            
            # Skip repeated headers
            if 'VENDOR STYLE' in line_upper and 'UNIT COST' in line_upper:
                continue
            
            tokens = re.split(r'\s{2,}|\s+', line.strip())
            if not tokens:
                continue
            
            # Unit cost token (e.g., 2.25 or $2.25)
            unit_cost = None
            unit_token = None
            for token in tokens:
                token_clean = token.replace('$', '')
                if re.match(r'^\d+\.\d{2}$', token_clean):
                    unit_cost = float(token_clean)
                    unit_token = token
                    break
            
            if unit_cost is None:
                continue
            
            # Style numbers are typically 5-8 digits
            numeric_tokens = [t for t in tokens if re.match(r'^\d{5,8}$', t)]
            if not numeric_tokens:
                continue
            
            vendor_style = numeric_tokens[0]
            tjx_style = numeric_tokens[1] if len(numeric_tokens) > 1 else ''
            
            items.append({
                'vendor_style': vendor_style,
                'tjx_style': tjx_style,
                'unit_cost': unit_cost,
                'description': ''
            })
        
        return items

    def _combine_po_and_distribution(self, po_data: Dict[str, Any], distribution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Combine PO pricing with Distribution quantities"""
        
        orders = []
        po_number = distribution_data.get('po_number') or po_data.get('po_number')
        order_date = po_data.get('order_date') or distribution_data.get('order_date')
        brand = distribution_data.get('brand') or 'TJ Maxx'
        state = po_data.get('state')
        
        # Build price lookup maps
        price_by_tjx = {}
        price_by_vendor = {}
        for item in po_data.get('line_items', []):
            tjx_style = item.get('tjx_style')
            vendor_style = item.get('vendor_style')
            if tjx_style:
                price_by_tjx[tjx_style] = item
            if vendor_style:
                price_by_vendor[vendor_style] = item
        
        # Map store based on state (PO file)
        raw_state = state or ''
        mapped_store = self.mapping_utils.get_store_mapping(raw_state, 'tkmaxx') if raw_state else None
        if not mapped_store or mapped_store == raw_state:
            mapped_store = raw_state or 'UNKNOWN'
        
        for dist_item in distribution_data.get('line_items', []):
            vendor_style = dist_item.get('vendor_style', '')
            tjx_style = dist_item.get('tjx_style', '')
            description = dist_item.get('description', '')
            
            # Match price from PO file
            po_item = None
            if tjx_style and tjx_style in price_by_tjx:
                po_item = price_by_tjx[tjx_style]
            elif vendor_style and vendor_style in price_by_vendor:
                po_item = price_by_vendor[vendor_style]
            
            unit_cost = po_item.get('unit_cost', 0.0) if po_item else 0.0
            if po_item and po_item.get('description'):
                description = po_item['description']
            
            # Extract units per DC from distribution file
            dc_units = dist_item.get('dc_units', {})
            for dc_num, units_for_dc in dc_units.items():
                if not units_for_dc or int(units_for_dc) <= 0:
                    continue
                
                raw_dc = str(dc_num)
                mapped_customer = self.mapping_utils.get_customer_mapping(raw_dc, 'tkmaxx')
                if not mapped_customer or mapped_customer == 'UNKNOWN':
                    mapped_customer = f"TJ Maxx DC {dc_num}"
                
                order_item = {
                    'order_number': po_number,
                    'order_date': order_date,
                    'customer_name': mapped_customer,
                    'raw_customer_name': raw_dc,
                    'sale_store_name': mapped_store,
                    'store_name': mapped_store,
                    'item_number': tjx_style or vendor_style,
                    'raw_item_number': vendor_style,
                    'item_description': description,
                    'quantity': int(units_for_dc),
                    'unit_price': unit_cost,
                    'total_price': unit_cost * int(units_for_dc),
                    'source_file': distribution_data.get('source_file') or po_data.get('source_file'),
                    'brand': brand,
                    'dc_number': dc_num,
                    'ship_state': raw_state
                }
                
                orders.append(order_item)
        
        return orders
    
    def _parse_csv_excel(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse TJ Maxx CSV/Excel order file (legacy support)"""
        
        try:
            # Read file into DataFrame
            if file_extension.lower() == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            
            if df.empty:
                return None
            
            # Process the DataFrame
            orders = self._process_dataframe(df, filename)
            
            return orders if orders else None
            
        except Exception as e:
            raise ValueError(f"Error parsing TJ Maxx file: {str(e)}")
    
    def _process_dataframe(self, df: pd.DataFrame, filename: str) -> List[Dict[str, Any]]:
        """Process DataFrame and extract order information"""
        
        orders = []
        
        # Create column mapping for common TJ Maxx fields
        column_map = self._create_column_mapping(df.columns.tolist())
        
        # Extract common order information
        order_number = self._extract_order_number(df, filename)
        order_date = self._extract_order_date(df)
        
        for index, row in df.iterrows():
            try:
                # Extract item information
                item_data = self._extract_item_from_row(row, column_map)
                
                if item_data and item_data.get('item_number'):
                    
                    # Extract customer information for this row
                    customer_info = self._extract_customer_info(row, column_map)
                    
                    # Apply store mapping
                    raw_customer = customer_info.get('raw_customer_name', '')
                    mapped_customer = self.mapping_utils.get_store_mapping(
                        raw_customer or filename, 
                        'tkmaxx'
                    )
                    
                    order_item = {
                        'order_number': order_number,
                        'order_date': order_date,
                        'customer_name': mapped_customer,
                        'raw_customer_name': raw_customer,
                        'item_number': item_data['item_number'],
                        'item_description': item_data.get('description', ''),
                        'quantity': item_data.get('quantity', 1),
                        'unit_price': item_data.get('unit_price', 0.0),
                        'total_price': item_data.get('total_price', 0.0),
                        'source_file': filename
                    }
                    
                    orders.append(order_item)
                    
            except Exception as e:
                # Skip problematic rows but continue processing
                continue
        
        return orders
    
    def _create_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """Create mapping of standard fields to actual column names"""
        
        mapping = {}
        
        for col in columns:
            col_lower = col.lower().strip()
            
            # Order number mapping
            if any(term in col_lower for term in ['order', 'po', 'purchase', 'ref']):
                if any(term in col_lower for term in ['number', 'no', 'id', 'ref']):
                    mapping['order_number'] = col
            
            # Date mapping
            elif any(term in col_lower for term in ['date', 'created', 'ordered', 'delivery']):
                mapping['order_date'] = col
            
            # Customer mapping
            elif any(term in col_lower for term in ['customer', 'store', 'location', 'branch']):
                if 'name' in col_lower or 'location' in col_lower:
                    mapping['customer_name'] = col
            
            # Item number mapping
            elif any(term in col_lower for term in ['item', 'product', 'sku', 'style']):
                if any(term in col_lower for term in ['number', 'code', 'id']):
                    mapping['item_number'] = col
            
            # Description mapping
            elif any(term in col_lower for term in ['description', 'name', 'title', 'product']):
                if 'description' in col_lower or ('product' in col_lower and 'name' in col_lower):
                    mapping['description'] = col
            
            # Quantity mapping
            elif any(term in col_lower for term in ['qty', 'quantity', 'units', 'pieces']):
                mapping['quantity'] = col
            
            # Unit price mapping
            elif any(term in col_lower for term in ['unit', 'price', 'cost', 'retail']):
                if ('unit' in col_lower and 'price' in col_lower) or 'retail' in col_lower:
                    mapping['unit_price'] = col
            
            # Total price mapping
            elif any(term in col_lower for term in ['total', 'amount', 'value', 'extended']):
                if any(term in col_lower for term in ['price', 'amount', 'value']):
                    mapping['total_price'] = col
        
        return mapping
    
    def _extract_order_number(self, df: pd.DataFrame, filename: str) -> str:
        """Extract order number from DataFrame"""
        
        # Look for order number in various columns
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['order', 'po', 'purchase', 'ref']):
                values = df[col].dropna().unique()
                if len(values) > 0:
                    return str(values[0])
        
        # Use filename as fallback
        return filename
    
    def _extract_order_date(self, df: pd.DataFrame) -> Optional[str]:
        """Extract order date from DataFrame"""
        
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['date', 'created', 'ordered', 'delivery']):
                values = df[col].dropna()
                if len(values) > 0:
                    return self.parse_date(str(values.iloc[0]))
        
        return None
    
    def _extract_customer_info(self, row: pd.Series, column_map: Dict[str, str]) -> Dict[str, str]:
        """Extract customer information from row"""
        
        customer_info = {
            'raw_customer_name': ''
        }
        
        # Use column mapping if available
        if 'customer_name' in column_map:
            customer_info['raw_customer_name'] = str(row.get(column_map['customer_name'], ''))
        else:
            # Look for customer info in any column with relevant names
            for col in row.index:
                col_lower = col.lower()
                if any(term in col_lower for term in ['customer', 'store', 'location', 'branch']):
                    if any(term in col_lower for term in ['name', 'location']):
                        customer_info['raw_customer_name'] = str(row[col])
                        break
        
        return customer_info
    
    def _extract_item_from_row(self, row: pd.Series, column_map: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract item information from DataFrame row"""
        
        item = {
            'item_number': '',
            'description': '',
            'quantity': 1,
            'unit_price': 0.0,
            'total_price': 0.0
        }
        
        # Use column mapping to extract data
        for field, col_name in column_map.items():
            if col_name in row.index and pd.notna(row[col_name]):
                value = row[col_name]
                
                if field == 'item_number':
                    item['item_number'] = str(value).strip()
                elif field == 'description':
                    item['description'] = str(value).strip()
                elif field == 'quantity':
                    try:
                        item['quantity'] = int(float(str(value))) or 1
                    except:
                        item['quantity'] = 1
                elif field == 'unit_price':
                    item['unit_price'] = self.clean_numeric_value(str(value))
                elif field == 'total_price':
                    item['total_price'] = self.clean_numeric_value(str(value))
        
        # If no mapping worked, try to find data by position or name matching
        if not item['item_number']:
            for col in row.index:
                col_lower = col.lower()
                
                # Look for item number
                if any(term in col_lower for term in ['item', 'sku', 'product', 'style']):
                    if any(term in col_lower for term in ['number', 'code', 'id']):
                        if pd.notna(row[col]):
                            item['item_number'] = str(row[col]).strip()
                            break
        
        # Calculate missing values
        if item['total_price'] == 0.0 and item['unit_price'] > 0:
            item['total_price'] = item['unit_price'] * item['quantity']
        
        return item if item['item_number'] else None
