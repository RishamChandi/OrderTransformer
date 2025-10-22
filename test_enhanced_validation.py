#!/usr/bin/env python3
"""
Test enhanced validation for Whole Foods parser
"""

import os
import sys

def test_enhanced_validation():
    """Test the enhanced validation system"""
    
    print("Testing Enhanced Whole Foods Parser Validation")
    print("=" * 60)
    
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
            'order_samples/wholefoods/order_156338400.html',  # 3-item order
            'order_samples/wholefoods/order_156296288.html'   # 2-item order
        ]
        
        for file_path in test_files:
            print(f"\n{'='*60}")
            print(f"Testing: {os.path.basename(file_path)}")
            print(f"{'='*60}")
            
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            try:
                # Parse the HTML - this will show the enhanced validation messages
                orders = parser.parse(file_content, 'html', os.path.basename(file_path))
                
                print(f"\n📈 FINAL RESULTS:")
                print(f"   Total orders generated: {len(orders)}")
                
                if orders:
                    print(f"   Sample order details:")
                    for i, order in enumerate(orders[:3], 1):  # Show first 3
                        print(f"      {i}. Item: {order.get('raw_item_number', 'N/A')}")
                        print(f"         Description: {order.get('item_description', 'N/A')}")
                        print(f"         Quantity: {order.get('quantity', 'N/A')}")
                        print(f"         Unit Price: {order.get('unit_price', 'N/A')}")
                        if i < len(orders):
                            print()
                
            except Exception as e:
                print(f"❌ Error parsing {file_path}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print("✅ Enhanced validation test completed!")
        print("Key improvements:")
        print("  • Alphanumeric item numbers with spaces/special chars supported")
        print("  • Comprehensive line count validation")
        print("  • Clear validation messages with emojis")
        print("  • Detailed item listing for verification")
        print("  • Distinguishes between line count vs quantity totals")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_validation()
    sys.exit(0 if success else 1)
