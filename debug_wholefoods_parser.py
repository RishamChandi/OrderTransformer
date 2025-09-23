#!/usr/bin/env python3
"""
Debug script to test Whole Foods parser with the actual order file
"""

import os
import sys
from parsers.wholefoods_parser import WholeFoodsParser

def debug_wholefoods_parsing():
    """Debug the Whole Foods parser with the actual order file"""
    
    print("🔍 Debugging Whole Foods Parser...")
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'local'
    os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
    
    # Initialize parser
    parser = WholeFoodsParser()
    
    # Read the actual order file
    order_file_path = "order_samples/wholefoods/order_156338400.html"
    
    if not os.path.exists(order_file_path):
        print(f"❌ Order file not found: {order_file_path}")
        return
    
    print(f"📁 Reading order file: {order_file_path}")
    
    with open(order_file_path, 'rb') as f:
        file_content = f.read()
    
    print(f"📊 File size: {len(file_content)} bytes")
    
    # Parse the file
    try:
        orders = parser.parse(file_content, 'html', 'order_156338400.html')
        
        if orders:
            print(f"✅ Successfully parsed {len(orders)} order items")
            
            for i, order in enumerate(orders, 1):
                print(f"\n📦 Order Item {i}:")
                print(f"   Order Number: {order.get('order_number', 'N/A')}")
                print(f"   Customer: {order.get('customer_name', 'N/A')}")
                print(f"   Item Number: {order.get('item_number', 'N/A')}")
                print(f"   Raw Item Number: {order.get('raw_item_number', 'N/A')}")
                print(f"   Description: {order.get('item_description', 'N/A')}")
                print(f"   Quantity: {order.get('quantity', 'N/A')}")
                print(f"   Unit Price: {order.get('unit_price', 'N/A')}")
                print(f"   Total Price: {order.get('total_price', 'N/A')}")
        else:
            print("❌ No orders parsed")
            
    except Exception as e:
        print(f"❌ Error parsing file: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_wholefoods_parsing()
