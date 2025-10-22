#!/usr/bin/env python3
"""
Test UNFI West parser with cost and description mapping fixes
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set database URL
os.environ['DATABASE_URL'] = 'sqlite:///orderparser_dev.db'

from parsers.unfi_west_parser import UNFIWestParser
from utils.mapping_utils import MappingUtils

def test_unfi_west_parser():
    print("Testing UNFI West Parser with Cost and Description Fixes")
    print("=" * 60)
    
    try:
        # Initialize parser
        mapping_utils = MappingUtils()
        mapping_utils.use_database = True
        parser = UNFIWestParser()
        parser.mapping_utils = mapping_utils
        
        # Test with a sample HTML file if available
        html_path = "order_samples/unfi_west/UNFI West PO044820201.html"
        if not os.path.exists(html_path):
            print(f"HTML file not found: {html_path}")
            print("Testing with sample data instead...")
            
            # Create sample HTML content that mimics the actual UNFI West format
            sample_html = """
            <html>
            <body>
            <p>PICK UP 09/16/25</p>
            <p>Buyer: BLONG VANG</p>
            <p>P.O. #: 044820201-002</p>
            <p>Vendor #: L-085948</p>
            <p>UNFI - MORENO VALLEY, CA</p>
            <p>Dated: 09/15/25</p>
            <pre>
Line Qty Cases Plts Prod# Description Units Vendor P.N. Cost Extension
1    6   1     0    23041 CAM SNDRD TOM BRSHTA 6/7.9 OZ 17-041-7 12.1500p 72.90
12   8   1     0    12345 K LOVE MLKCHC ALM STFDTE 8/3.5 OZ 12-600-1 20.0000 160.00
13   10  1     0    67890 K LOVE SW NEST CSHW DATE 8/3.5 OZ 12-600-2 22.0000 220.00
            </pre>
            <p>SUBTOTAL $ 26554.47</p>
            </body>
            </html>
            """
            
            # Parse the sample HTML
            orders = parser.parse(sample_html.encode('utf-8'), 'html', 'test_order.html')
        else:
            # Read the actual HTML file
            with open(html_path, 'rb') as f:
                file_content = f.read()
            
            # Parse the file
            orders = parser.parse(file_content, 'html', 'UNFI West PO044820201.html')
        
        print(f"Total orders parsed: {len(orders) if orders else 0}")
        
        if orders:
            print("\nOrder details:")
            for key, value in orders[0].items():
                if key not in ['item_number', 'raw_item_number', 'item_description', 'quantity', 'unit_price', 'total_price']:
                    print(f"  {key}: {value}")
            
            print(f"\nTotal line items: {len(orders)}")
            for i, order in enumerate(orders[:5]):  # Show first 5 items
                item_num = order.get('item_number', 'N/A')
                desc = order.get('item_description', 'N/A')
                qty = order.get('quantity', 'N/A')
                price = order.get('unit_price', 'N/A')
                raw_num = order.get('raw_item_number', 'N/A')
                print(f"Item {i+1}: {raw_num} -> {item_num}")
                print(f"  Description: {desc}")
                print(f"  Qty: {qty}, Price: {price}")
                print()
            
            # Check for items with costs that should have been captured
            items_with_cost = [o for o in orders if o.get('unit_price', 0) > 0]
            items_without_cost = [o for o in orders if o.get('unit_price', 0) == 0]
            
            print(f"Items with cost captured: {len(items_with_cost)}")
            print(f"Items without cost: {len(items_without_cost)}")
            
            if items_without_cost:
                print("\nItems missing cost:")
                for item in items_without_cost:
                    print(f"  {item.get('raw_item_number', 'N/A')} - {item.get('item_description', 'N/A')}")
            
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
    success = test_unfi_west_parser()
    sys.exit(0 if success else 1)
