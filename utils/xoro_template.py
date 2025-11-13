"""
Xoro template conversion utilities
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

class XoroTemplate:
    """Handles conversion to Xoro CSV format"""
    
    def __init__(self):
        # Define required Xoro fields based on the template
        self.required_fields = [
            'ImportError', 'ThirdPartyRefNo', 'ThirdPartySource', 'ThirdPartyIconUrl',
            'ThirdPartyDisplayName', 'SaleStoreName', 'StoreName', 'CurrencyCode',
            'CustomerName', 'CustomerFirstName', 'CustomerLastName', 'CustomerMainPhone',
            'CustomerEmailMain', 'CustomerPO', 'CustomerId', 'CustomerAccountNumber',
            'OrderDate', 'DateToBeShipped', 'LastDateToBeShipped', 'DateToBeCancelled',
            'OrderClassCode', 'OrderClassName', 'OrderTypeCode', 'OrderTypeName',
            'ExchangeRate', 'Memo', 'PaymentTermsName', 'PaymentTermsType',
            'DepositRequiredTypeName', 'DepositRequiredAmount', 'ItemNumber',
            'ItemDescription', 'UnitPrice', 'Qty', 'LineTotal', 'DiscountAmount',
            'DiscountPercent', 'TaxAmount', 'TaxPercent', 'CustomFieldD1', 'CustomFieldD2'
        ]
    
    def convert_to_xoro(self, parsed_orders: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
        """
        Convert parsed order data to Xoro format
        
        Args:
            parsed_orders: List of parsed order dictionaries
            source_name: Name of the order source
            
        Returns:
            List of Xoro-formatted dictionaries
        """
        
        xoro_orders = []
        
        for order in parsed_orders:
            xoro_order = self._convert_single_order(order, source_name)
            xoro_orders.append(xoro_order)
        
        return xoro_orders
    
    def _convert_single_order(self, order: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """Convert a single order to Xoro format"""
        
        # For UNFI East, use ETA date for shipping dates, otherwise use pickup_date or calculate from order_date
        order_date = order.get('order_date')
        pickup_date = order.get('pickup_date')
        eta_date = order.get('eta_date')
        delivery_date = order.get('delivery_date')
        
        if source_name.lower().replace(' ', '_') == 'unfi_east' or source_name.lower() == 'unfi east':
            # For UNFI East: use Pck Date (pickup date) for shipping dates
            shipping_date = pickup_date if pickup_date else self._calculate_shipping_date(order_date)
            print(f"DEBUG: UNFI East detected - source_name: '{source_name}', pickup_date: {pickup_date}, shipping_date: {shipping_date}")
        elif source_name.lower().replace(' ', '_') == 'whole_foods' or source_name.lower() == 'whole foods':
            # For Whole Foods: use Expected Delivery Date from HTML
            shipping_date = delivery_date if delivery_date else self._calculate_shipping_date(order_date)
        elif pickup_date:
            # For other sources: use pickup_date if available
            shipping_date = pickup_date
        else:
            # Fallback: calculate from order_date
            shipping_date = self._calculate_shipping_date(order_date)
        
        # Split customer name into first/last if possible
        customer_name = str(order.get('customer_name', ''))
        first_name, last_name = self._split_customer_name(customer_name)
        
        # Use parser-provided mapped values from database, with source-specific overrides
        if source_name.lower().replace(' ', '_') in ['wholefoods', 'whole_foods', 'whole foods']:
            # For Whole Foods, always hardcode to IDI - Richmond as requested
            sale_store_name = 'IDI - Richmond'
            store_name = 'IDI - Richmond'
            final_customer_name = order.get('customer_name', 'UNKNOWN')
        elif source_name.lower().replace(' ', '_') == 'unfi_east' or source_name.lower() == 'unfi east':
            # For UNFI East: Store mapping and Customer mapping are SEPARATE
            # - Store mapping: "Order To" number (85948, 85950) -> Store name (PSS-NJ, IDI-Richmond) for SaleStoreName/StoreName
            # - Customer mapping: IOW code (RCH, HOW, etc.) -> Customer name (UNFI EAST - RICHBURG) for CustomerName
            sale_store_name = order.get('sale_store_name') or order.get('store_name') or 'PSS-NJ'
            store_name = order.get('store_name') or 'PSS-NJ'
            # Customer name comes from customer mapping (IOW code lookup)
            final_customer_name = order.get('customer_name', 'UNKNOWN')
            print(f"DEBUG: UNFI East - Store: '{sale_store_name}' (from store mapping), Customer: '{final_customer_name}' (from customer mapping)")
        elif source_name.lower().replace(' ', '_') == 'unfi_west' or source_name.lower() == 'unfi west':
            # For UNFI West: use store mapping from parser for store names, customer mapping for customer name
            sale_store_name = order.get('sale_store_name') or order.get('store_name') or 'KL - Richmond'
            store_name = order.get('store_name') or 'KL - Richmond'
            # Customer name comes from customer mapping (e.g., "UNFI MORENO VALLEY #2")
            final_customer_name = order.get('customer_name', 'UNKNOWN')
        else:
            sale_store_name = order.get('store_name')
            store_name = order.get('store_name')
            final_customer_name = order.get('customer_name', 'UNKNOWN')
        
        # Validate required fields - fail if no mapping found
        if not sale_store_name or sale_store_name == 'UNKNOWN':
            raise ValueError(f"No store mapping found for {source_name} order {order.get('order_number')}")
        if not final_customer_name or final_customer_name == 'UNKNOWN':
            # For UNFI East, provide more detailed error message with debugging info
            if source_name.lower().replace(' ', '_') in ['unfi_east', 'unfi east']:
                raw_customer = order.get('raw_customer_name', 'NOT EXTRACTED')
                raise ValueError(
                    f"No customer mapping found for {source_name} order {order.get('order_number')}. "
                    f"Raw customer ID extracted: '{raw_customer}'. "
                    f"Please verify the PDF contains a valid IOW code (RCH, HOW, CHE, YOR, IOW, GRW, MAN, ATL, SAR, SRQ, DAY, HVA, RAC, TWC) "
                    f"or add a customer mapping for '{raw_customer}' in the database."
                )
            else:
                raise ValueError(f"No customer mapping found for {source_name} order {order.get('order_number')}")
        
        # Create Xoro order
        xoro_order = {
            # Import metadata
            'ImportError': '',
            'ThirdPartyRefNo': str(order.get('order_number', '')),
            'ThirdPartySource': source_name,
            'ThirdPartyIconUrl': '',
            'ThirdPartyDisplayName': source_name,
            
            # Store information
            'SaleStoreName': sale_store_name,
            'StoreName': store_name,
            'CurrencyCode': 'USD',  # Default currency
            
            # Customer information
            'CustomerName': final_customer_name,
            'CustomerFirstName': '',  # Keep empty as requested
            'CustomerLastName': '',   # Keep empty as requested
            'CustomerMainPhone': '',
            'CustomerEmailMain': '',
            'CustomerPO': str(order.get('order_number', '')),
            'CustomerId': '',
            'CustomerAccountNumber': '',
            
            # Order dates - handle both datetime objects and strings with debugging
            'OrderDate': self._format_date_with_debug(order_date, 'OrderDate', source_name),
            'DateToBeShipped': self._format_date_with_debug(shipping_date, 'DateToBeShipped', source_name),
            'LastDateToBeShipped': self._format_date_with_debug(shipping_date, 'LastDateToBeShipped', source_name),
            'DateToBeCancelled': '',
            
            # Order classification - Keep empty as requested
            'OrderClassCode': '',
            'OrderClassName': '',
            'OrderTypeCode': '',
            'OrderTypeName': '',
            
            # Financial information
            'ExchangeRate': 1.0,
            'Memo': f"Imported from {source_name} - File: {order.get('source_file', '')}",
            'PaymentTermsName': '',
            'PaymentTermsType': '',
            'DepositRequiredTypeName': '',
            'DepositRequiredAmount': 0.0,
            
            # Line item information
            'ItemNumber': str(order.get('item_number', '')),
            'ItemDescription': str(order.get('item_description', '')),
            'UnitPrice': float(order.get('unit_price', 0.0)),
            'Qty': int(order.get('quantity', 1)),
            'LineTotal': float(order.get('total_price', 0.0)),
            # Extract discount information from order (for UNFI East, discounts are extracted from PDF)
            'DiscountAmount': float(order.get('discount_amount', 0.0)),
            'DiscountPercent': float(order.get('discount_percent', 0.0)),
            'TaxAmount': 0.0,
            'TaxPercent': 0.0,
            
            # Custom fields
            'CustomFieldD1': float(order.get('unit_price', 0.0)),
            'CustomFieldD2': ''
        }
        
        # Calculate line total if not provided
        if xoro_order['LineTotal'] == 0.0 and xoro_order['UnitPrice'] > 0:
            xoro_order['LineTotal'] = xoro_order['UnitPrice'] * xoro_order['Qty']
        
        return xoro_order
    
    def _calculate_shipping_date(self, order_date: str, days_to_add: int = 7) -> str:
        """Calculate shipping date based on order date"""
        
        if not order_date:
            # Use today + days_to_add if no order date
            shipping_date = datetime.now() + timedelta(days=days_to_add)
            return shipping_date.strftime('%Y-%m-%d')
        
        try:
            # Parse order date and add shipping days
            order_dt = datetime.strptime(order_date, '%Y-%m-%d')
            shipping_dt = order_dt + timedelta(days=days_to_add)
            return shipping_dt.strftime('%Y-%m-%d')
        except ValueError:
            # Fallback to current date + days if parsing fails
            shipping_date = datetime.now() + timedelta(days=days_to_add)
            return shipping_date.strftime('%Y-%m-%d')
    
    def _split_customer_name(self, full_name: str) -> tuple:
        """Split full customer name into first and last name"""
        
        if not full_name or full_name.strip() == '':
            return '', ''
        
        name_parts = full_name.strip().split()
        
        if len(name_parts) == 0:
            return '', ''
        elif len(name_parts) == 1:
            return name_parts[0], ''
        elif len(name_parts) == 2:
            return name_parts[0], name_parts[1]
        else:
            # More than 2 parts - first word is first name, rest is last name
            return name_parts[0], ' '.join(name_parts[1:])
    
    def validate_xoro_order(self, xoro_order: Dict[str, Any]) -> List[str]:
        """Validate Xoro order and return list of errors"""
        
        errors = []
        
        # Check required fields
        required_for_import = ['CustomerName', 'ItemNumber', 'Qty', 'UnitPrice']
        
        for field in required_for_import:
            if not xoro_order.get(field) or str(xoro_order[field]).strip() == '':
                errors.append(f"Missing required field: {field}")
        
        # Validate numeric fields
        numeric_fields = ['UnitPrice', 'Qty', 'LineTotal', 'ExchangeRate']
        
        for field in numeric_fields:
            try:
                float(xoro_order.get(field, 0))
            except (ValueError, TypeError):
                errors.append(f"Invalid numeric value for {field}: {xoro_order.get(field)}")
        
        # Validate dates
        date_fields = ['OrderDate', 'DateToBeShipped']
        
        for field in date_fields:
            date_value = xoro_order.get(field)
            if date_value and not self._is_valid_date(date_value):
                errors.append(f"Invalid date format for {field}: {date_value}")
        
        return errors
    
    def _format_date_with_debug(self, date_value: Any, field_name: str, source_name: str) -> str:
        """Format date value with debug logging"""
        
        print(f"DEBUG: {source_name} - Formatting {field_name}: {date_value} (type: {type(date_value)})")
        
        if not date_value:
            print(f"DEBUG: {source_name} - {field_name} is empty/None")
            return ''
        
        if hasattr(date_value, 'strftime'):
            result = date_value.strftime('%Y-%m-%d')
            print(f"DEBUG: {source_name} - {field_name} datetime formatted: {result}")
            return result
        elif isinstance(date_value, str) and date_value.strip():
            print(f"DEBUG: {source_name} - {field_name} string value: '{date_value}'")
            return date_value
        else:
            print(f"DEBUG: {source_name} - {field_name} fallback to empty string")
            return ''
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is in valid format"""
        
        if not date_str:
            return True  # Empty dates are allowed
        
        try:
            datetime.strptime(str(date_str), '%Y-%m-%d')
            return True
        except ValueError:
            return False
