"""
Parser for TK Maxx CSV/Excel order files
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import io
from .base_parser import BaseParser

class TKMaxxParser(BaseParser):
    """Parser for TK Maxx CSV/Excel order files"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "TK Maxx"
    
    def parse(self, file_content: bytes, file_extension: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Parse TK Maxx CSV/Excel order file"""
        
        if file_extension.lower() not in ['csv', 'xlsx', 'xls']:
            raise ValueError("TK Maxx parser only supports CSV and Excel files")
        
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
            raise ValueError(f"Error parsing TK Maxx file: {str(e)}")
    
    def _process_dataframe(self, df: pd.DataFrame, filename: str) -> List[Dict[str, Any]]:
        """Process DataFrame and extract order information"""
        
        orders = []
        
        # Create column mapping for common TK Maxx fields
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
