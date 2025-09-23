#!/usr/bin/env python3
"""
Test the Whole Foods parser fix for item skipping issue
"""

import os
import sys

def test_wholefoods_parser():
    """Test the Whole Foods parser with sample files"""
    
    print("Testing Whole Foods parser fix...")
    
    try:
        # Set up environment
        os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
        
        # Import parser
        from parsers.wholefoods_parser import WholeFoodsParser
        from utils.mapping_utils import MappingUtils
        
        # Initialize parser
        mapping_utils = MappingUtils()
        parser = WholeFoodsParser()
        parser.mapping_utils = mapping_utils
        
        # Test with the 3-item order (should now capture all 3 items)
        print("\n=== Testing 3-item order (order_156338400.html) ===")
        
        with open('order_samples/wholefoods/order_156338400.html', 'rb') as f:
            file_content = f.read()
        
        orders = parser.parse(file_content, 'html', 'order_156338400.html')
        
        print(f"Expected: 3 items, Actual: {len(orders)} items")
        
        if len(orders) == 3:
            print("✅ SUCCESS: All 3 items captured!")
        else:
            print("❌ FAILED: Not all items captured")
        
        # Show details of captured items
        for i, order in enumerate(orders):
            print(f"  Item {i+1}: {order.get('raw_item_number')} - {order.get('item_description')}")
        
        # Test with the 2-item order (should capture both items)
        print("\n=== Testing 2-item order (order_156296288.html) ===")
        
        with open('order_samples/wholefoods/order_156296288.html', 'rb') as f:
            file_content = f.read()
        
        orders2 = parser.parse(file_content, 'html', 'order_156296288.html')
        
        print(f"Expected: 2 items, Actual: {len(orders2)} items")
        
        if len(orders2) == 2:
            print("✅ SUCCESS: All 2 items captured!")
        else:
            print("❌ FAILED: Not all items captured")
        
        # Show details of captured items
        for i, order in enumerate(orders2):
            print(f"  Item {i+1}: {order.get('raw_item_number')} - {order.get('item_description')}")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        print(f"3-item order: {len(orders)}/3 items captured")
        print(f"2-item order: {len(orders2)}/2 items captured")
        
        if len(orders) == 3 and len(orders2) == 2:
            print("🎉 ALL TESTS PASSED! Item skipping issue fixed!")
            return True
        else:
            print("❌ Some tests failed. Item skipping issue not fully resolved.")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wholefoods_parser()
    sys.exit(0 if success else 1)
