#!/usr/bin/env python3
"""
Test UNFI East parser with PO4480501
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set database URL
os.environ['DATABASE_URL'] = 'sqlite:///orderparser_dev.db'

from parsers.unfi_east_parser import UNFIEastParser
from utils.mapping_utils import MappingUtils

def test_unfi_east_parser():
    print("Testing UNFI East Parser with PO4480501")
    print("=" * 50)
    
    try:
        # Initialize parser
        mapping_utils = MappingUtils()
        mapping_utils.use_database = True
        parser = UNFIEastParser(mapping_utils)
        
        # Read the PDF file
        pdf_path = "order_samples/unfi_east/UNFI East PO4480501 (1).pdf"
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
        
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        print(f"PDF file size: {len(file_content)} bytes")
        
        # Parse the file
        orders = parser.parse(file_content, 'pdf', 'UNFI East PO4480501 (1).pdf')
        print(f"Total orders parsed: {len(orders) if orders else 0}")
        
        if orders:
            print("\nFirst order details:")
            for key, value in orders[0].items():
                print(f"  {key}: {value}")
            
            print(f"\nTotal line items: {len(orders)}")
            for i, order in enumerate(orders[:5]):  # Show first 5 items
                item_num = order.get('item_number', 'N/A')
                desc = order.get('item_description', 'N/A')
                qty = order.get('quantity', 'N/A')
                price = order.get('unit_price', 'N/A')
                print(f"Item {i+1}: {item_num} - {desc} - Qty: {qty} - Price: {price}")
            
            # Check customer mapping
            customer_name = orders[0].get('customer_name', 'UNKNOWN')
            raw_customer = orders[0].get('raw_customer_name', '')
            print(f"\nCustomer Mapping:")
            print(f"  Raw: {raw_customer}")
            print(f"  Mapped: {customer_name}")
            
        else:
            print("No orders parsed")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_unfi_east_parser()
    sys.exit(0 if success else 1)