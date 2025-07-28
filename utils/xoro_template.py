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
        
        if source_name.lower().replace(' ', '_') == 'unfi_east' or source_name.lower() == 'unfi east':
            # For UNFI East: use Pck Date (pickup date) for shipping dates
            shipping_date = pickup_date if pickup_date else self._calculate_shipping_date(order_date)
        elif pickup_date:
            # For other sources: use pickup_date if available
            shipping_date = pickup_date
        else:
            # Fallback: calculate from order_date
            shipping_date = self._calculate_shipping_date(order_date)
        
        # Split customer name into first/last if possible
        customer_name = str(order.get('customer_name', ''))
        first_name, last_name = self._split_customer_name(customer_name)
        
        # Handle store name mapping based on source
        if source_name.lower().replace(' ', '_') == 'unfi_west' or source_name.lower() == 'unfi west':
            # UNFI West: always use hardcoded store values
            sale_store_name = 'KL - Richmond'
            store_name = 'KL - Richmond'
            final_customer_name = customer_name if customer_name and customer_name != 'UNKNOWN' else 'UNKNOWN'
        elif source_name.lower().replace(' ', '_') == 'unfi_east' or source_name.lower() == 'unfi east':
            # UNFI East: map based on Order To number
            order_to_number = order.get('order_to_number')
            if order_to_number == '85948':
                sale_store_name = 'PSS - NJ'
                store_name = 'PSS - NJ'
            elif order_to_number == '85950':
                sale_store_name = 'IDI - Richmond'
                store_name = 'IDI - Richmond'
            else:
                # Default to mapped customer name for other order numbers
                sale_store_name = customer_name if customer_name and customer_name != 'UNKNOWN' else 'UNKNOWN'
                store_name = customer_name if customer_name and customer_name != 'UNKNOWN' else 'UNKNOWN'
            final_customer_name = customer_name if customer_name and customer_name != 'UNKNOWN' else 'UNKNOWN'
        else:
            # Other sources: use mapped customer name
            sale_store_name = customer_name if customer_name and customer_name != 'UNKNOWN' else 'UNKNOWN'
            store_name = customer_name if customer_name and customer_name != 'UNKNOWN' else 'UNKNOWN'
            final_customer_name = customer_name
        
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
            
            # Order dates - handle both datetime objects and strings
            'OrderDate': order_date.strftime('%Y-%m-%d') if hasattr(order_date, 'strftime') else (order_date if order_date else ''),
            'DateToBeShipped': shipping_date.strftime('%Y-%m-%d') if hasattr(shipping_date, 'strftime') else (shipping_date if shipping_date else ''),
            'LastDateToBeShipped': shipping_date.strftime('%Y-%m-%d') if hasattr(shipping_date, 'strftime') else (shipping_date if shipping_date else ''),
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
            'DiscountAmount': 0.0,
            'DiscountPercent': 0.0,
            'TaxAmount': 0.0,
            'TaxPercent': 0.0,
            
            # Custom fields
            'CustomFieldD1': '',
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
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is in valid format"""
        
        if not date_str:
            return True  # Empty dates are allowed
        
        try:
            datetime.strptime(str(date_str), '%Y-%m-%d')
            return True
        except ValueError:
            return False
