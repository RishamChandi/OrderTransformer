#!/usr/bin/env python3
"""
Final test for Whole Foods parser to verify all items are captured
"""

import os
import sys

def test_wholefoods_parser_final():
    """Test the Whole Foods parser with both sample files"""
    
    print("Testing Whole Foods parser - Final Test")
    print("=" * 50)
    
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
        
        # Test files with expected results
        test_cases = [
            {
                'file': 'order_samples/wholefoods/order_156338400.html',
                'description': '3-item order',
                'expected_items': 3,
                'expected_item_numbers': ['130252', '13 025 126', '130255']
            },
            {
                'file': 'order_samples/wholefoods/order_156296288.html', 
                'description': '2-item order',
                'expected_items': 2,
                'expected_item_numbers': ['170411', '170512']
            }
        ]
        
        all_tests_passed = True
        
        for test_case in test_cases:
            print(f"\n=== Testing {test_case['description']} ===")
            print(f"File: {test_case['file']}")
            print(f"Expected: {test_case['expected_items']} items")
            
            if not os.path.exists(test_case['file']):
                print(f"❌ File not found: {test_case['file']}")
                all_tests_passed = False
                continue
            
            with open(test_case['file'], 'rb') as f:
                file_content = f.read()
            
            try:
                # Parse the HTML
                orders = parser.parse(file_content, 'html', os.path.basename(test_case['file']))
                
                print(f"Parsed: {len(orders)} orders")
                
                if len(orders) == test_case['expected_items']:
                    print("✅ Correct number of items parsed")
                    
                    # Check if all expected item numbers are present
                    parsed_item_numbers = [order.get('raw_item_number') for order in orders]
                    missing_items = []
                    
                    for expected_item in test_case['expected_item_numbers']:
                        if expected_item not in parsed_item_numbers:
                            missing_items.append(expected_item)
                    
                    if not missing_items:
                        print("✅ All expected items found")
                        for i, order in enumerate(orders):
                            print(f"  {i+1}. {order.get('raw_item_number')} - {order.get('item_description')}")
                    else:
                        print(f"❌ Missing items: {missing_items}")
                        all_tests_passed = False
                else:
                    print(f"❌ Expected {test_case['expected_items']} items, got {len(orders)}")
                    all_tests_passed = False
                    
                    # Show what was parsed
                    for i, order in enumerate(orders):
                        print(f"  {i+1}. {order.get('raw_item_number')} - {order.get('item_description')}")
                    
            except Exception as e:
                print(f"❌ Error parsing {test_case['file']}: {e}")
                all_tests_passed = False
        
        print("\n" + "=" * 50)
        if all_tests_passed:
            print("🎉 All tests passed! Whole Foods parser is working correctly.")
        else:
            print("❌ Some tests failed. Please review the issues above.")
        
        return all_tests_passed
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wholefoods_parser_final()
    sys.exit(0 if success else 1)
