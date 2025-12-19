"""Test VMC parser with sample file"""
import os
from parsers.vmc_parser import VMCParser

# Test the parser
parser = VMCParser()
file_path = 'order_samples/vmc/VMC Grocery_Order93659_735994.csv'

print(f"Testing VMC parser with file: {file_path}")
print("-" * 60)

try:
    with open(file_path, 'rb') as f:
        content = f.read()
    
    result = parser.parse(content, 'csv', os.path.basename(file_path))
    
    if result:
        print(f"SUCCESS! Parsed {len(result)} line items")
        print(f"\nFirst item details:")
        first_item = result[0]
        print(f"  Order Number: {first_item.get('order_number')}")
        print(f"  Item Number: {first_item.get('item_number')} (raw: {first_item.get('raw_item_number')})")
        print(f"  Quantity: {first_item.get('quantity')}")
        print(f"  Unit Price: ${first_item.get('unit_price')}")
        print(f"  Total Price: ${first_item.get('total_price')}")
        print(f"  Customer: {first_item.get('customer_name')}")
        print(f"  Store: {first_item.get('store_name')}")
        print(f"  Description: {first_item.get('item_description')}")
    else:
        print("FAILED: Parser returned None (no orders found)")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

