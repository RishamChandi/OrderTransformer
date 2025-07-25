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
            'DiscountPercent', 'TaxAmount', 'TaxPercent'
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
        
        # Calculate shipping date (default to 7 days from order date)
        order_date = order.get('order_date')
        shipping_date = self._calculate_shipping_date(order_date)
        
        # Split customer name into first/last if possible
        customer_name = str(order.get('customer_name', ''))
        first_name, last_name = self._split_customer_name(customer_name)
        
        # Create Xoro order
        xoro_order = {
            # Import metadata
            'ImportError': '',
            'ThirdPartyRefNo': str(order.get('order_number', '')),
            'ThirdPartySource': source_name,
            'ThirdPartyIconUrl': '',
            'ThirdPartyDisplayName': source_name,
            
            # Store information
            'SaleStoreName': 'KL - Richmond' if source_name.lower() == 'unfi_west' else customer_name,
            'StoreName': 'KL - Richmond' if source_name.lower() == 'unfi_west' else customer_name,
            'CurrencyCode': 'USD',  # Default currency
            
            # Customer information
            'CustomerName': customer_name,
            'CustomerFirstName': first_name,
            'CustomerLastName': last_name,
            'CustomerMainPhone': '',
            'CustomerEmailMain': '',
            'CustomerPO': str(order.get('order_number', '')),
            'CustomerId': '',
            'CustomerAccountNumber': '',
            
            # Order dates
            'OrderDate': order_date or '',
            'DateToBeShipped': shipping_date,
            'LastDateToBeShipped': shipping_date,
            'DateToBeCancelled': '',
            
            # Order classification
            'OrderClassCode': 'STANDARD',
            'OrderClassName': 'Standard Order',
            'OrderTypeCode': 'SALE',
            'OrderTypeName': 'Sales Order',
            
            # Financial information
            'ExchangeRate': 1.0,
            'Memo': f"Imported from {source_name} - File: {order.get('source_file', '')}",
            'PaymentTermsName': 'Net 30',
            'PaymentTermsType': 'Net',
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
            'TaxPercent': 0.0
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
