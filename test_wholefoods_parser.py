import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from parsers.wholefoods_parser import WholeFoodsParser
from utils.mapping_utils import MappingUtils

print('Testing Whole Foods parser...')

# Initialize parser
mapping_utils = MappingUtils()
parser = WholeFoodsParser()
parser.mapping_utils = mapping_utils  # Set the mapping utils

# Test with the 3-item order
pdf_path = 'order_samples/wholefoods/order_156338400.html'
if os.path.exists(pdf_path):
    print(f'Testing with: {pdf_path}')
    
    with open(pdf_path, 'rb') as f:
        file_content = f.read()
    
    try:
        # Parse the HTML
        orders = parser.parse(file_content, 'html', 'order_156338400.html')
        
        if orders:
            print(f'Successfully parsed {len(orders)} orders')
            
            # Show all orders
            for i, order in enumerate(orders):
                print(f'\nOrder {i+1}:')
                print(f'  Order Number: {order.get("order_number")}')
                print(f'  Customer Name: {order.get("customer_name")}')
                print(f'  Item Number: {order.get("item_number")}')
                print(f'  Raw Item Number: {order.get("raw_item_number")}')
                print(f'  Item Description: {order.get("item_description")}')
                print(f'  Quantity: {order.get("quantity")}')
                print(f'  Unit Price: {order.get("unit_price")}')
                print(f'  Total Price: {order.get("total_price")}')
        else:
            print('No orders parsed')
            
    except Exception as e:
        print(f'Error parsing HTML: {e}')
        import traceback
        traceback.print_exc()
else:
    print(f'Sample HTML not found: {pdf_path}')

print('\n' + '='*50)

# Test with the 2-item order
pdf_path2 = 'order_samples/wholefoods/order_156296288.html'
if os.path.exists(pdf_path2):
    print(f'Testing with: {pdf_path2}')
    
    with open(pdf_path2, 'rb') as f:
        file_content = f.read()
    
    try:
        # Parse the HTML
        orders = parser.parse(file_content, 'html', 'order_156296288.html')
        
        if orders:
            print(f'Successfully parsed {len(orders)} orders')
            
            # Show all orders
            for i, order in enumerate(orders):
                print(f'\nOrder {i+1}:')
                print(f'  Order Number: {order.get("order_number")}')
                print(f'  Customer Name: {order.get("customer_name")}')
                print(f'  Item Number: {order.get("item_number")}')
                print(f'  Raw Item Number: {order.get("raw_item_number")}')
                print(f'  Item Description: {order.get("item_description")}')
                print(f'  Quantity: {order.get("quantity")}')
                print(f'  Unit Price: {order.get("unit_price")}')
                print(f'  Total Price: {order.get("total_price")}')
        else:
            print('No orders parsed')
            
    except Exception as e:
        print(f'Error parsing HTML: {e}')
        import traceback
        traceback.print_exc()
else:
    print(f'Sample HTML not found: {pdf_path2}')
