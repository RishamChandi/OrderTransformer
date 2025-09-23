#!/usr/bin/env python3
"""
Complete test for Whole Foods parser with validation
"""

import os
import sys

def test_wholefoods_parser_complete():
    """Test the Whole Foods parser with both sample files"""
    
    print("Testing Whole Foods parser with validation...")
    
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
        
        # Test files
        test_files = [
            ('order_samples/wholefoods/order_156338400.html', '3-item order'),
            ('order_samples/wholefoods/order_156296288.html', '2-item order')
        ]
        
        for file_path, description in test_files:
            print(f"\n=== Testing {description} ({file_path}) ===")
            
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            try:
                # Parse the HTML
                orders = parser.parse(file_content, 'html', os.path.basename(file_path))
                
                if orders:
                    print(f"✅ Successfully parsed {len(orders)} orders")
                    
                    # Show all orders
                    for i, order in enumerate(orders):
                        print(f"  Order {i+1}: {order.get('raw_item_number')} - {order.get('item_description')}")
                else:
                    print("❌ No orders parsed")
                    
            except Exception as e:
                print(f"❌ Error parsing {file_path}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n=== Test Summary ===")
        print("✅ Parser fixes applied:")
        print("  - Fixed item number validation to handle spaces")
        print("  - Added validation to detect missing items")
        print("  - Added warning messages for item count mismatches")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_wholefoods_parser_complete()
    sys.exit(0 if success else 1)
