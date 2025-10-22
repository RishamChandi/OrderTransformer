import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from parsers.unfi_east_parser import UNFIEastParser
from utils.mapping_utils import MappingUtils

print('Testing UNFI East parser with sample PDF...')

mapping_utils = MappingUtils()
parser = UNFIEastParser(mapping_utils)

with open('order_samples/unfi_east/UNFI East PO4480501 (1).pdf', 'rb') as f:
    content = f.read()

orders = parser.parse(content, 'pdf', 'UNFI East PO4480501 (1).pdf')
print(f'✅ Successfully parsed {len(orders)} orders from sample PDF')

print('Sample order details:')
for i, order in enumerate(orders[:2], 1):
    print(f'  {i}. Order: {order.get("order_number", "N/A")}')
    print(f'     Customer: {order.get("customer_name", "N/A")}')
    print(f'     Item: {order.get("item_number", "N/A")} - {order.get("item_description", "N/A")}')
