import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from parsers.unfi_east_parser import UNFIEastParser
from utils.mapping_utils import MappingUtils

print('Testing UNFI East parser...')

# Initialize parser
mapping_utils = MappingUtils()
parser = UNFIEastParser(mapping_utils)

# Read sample PDF file
pdf_path = 'order_samples/unfi_east/UNFI East PO4480501 (1).pdf'
if os.path.exists(pdf_path):
    print(f'Found sample PDF: {pdf_path}')
    
    with open(pdf_path, 'rb') as f:
        file_content = f.read()
    
    try:
        # Parse the PDF
        orders = parser.parse(file_content, 'pdf', 'UNFI East PO4480501 (1).pdf')
        
        if orders:
            print(f'Successfully parsed {len(orders)} orders')
            
            # Show first order details
            first_order = orders[0]
            print(f'Order Number: {first_order.get("order_number")}')
            print(f'Customer Name: {first_order.get("customer_name")}')
            print(f'Raw Customer Name: {first_order.get("raw_customer_name")}')
            print(f'Order Date: {first_order.get("order_date")}')
            print(f'Pickup Date: {first_order.get("pickup_date")}')
            print(f'Vendor Number: {first_order.get("vendor_number")}')
            print(f'Store Name: {first_order.get("store_name")}')
            print(f'Item Number: {first_order.get("item_number")}')
            print(f'Raw Item Number: {first_order.get("raw_item_number")}')
            print(f'Item Description: {first_order.get("item_description")}')
            print(f'Quantity: {first_order.get("quantity")}')
            print(f'Unit Price: {first_order.get("unit_price")}')
            print(f'Total Price: {first_order.get("total_price")}')
        else:
            print('No orders parsed')
            
    except Exception as e:
        print(f'Error parsing PDF: {e}')
        import traceback
        traceback.print_exc()
else:
    print(f'Sample PDF not found: {pdf_path}')
