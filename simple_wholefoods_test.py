import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from parsers.wholefoods_parser import WholeFoodsParser
from utils.mapping_utils import MappingUtils

print('Testing Whole Foods parser...')

# Initialize parser
mapping_utils = MappingUtils()
parser = WholeFoodsParser()
parser.mapping_utils = mapping_utils

# Test with the 3-item order
with open('order_samples/wholefoods/order_156338400.html', 'rb') as f:
    file_content = f.read()

orders = parser.parse(file_content, 'html', 'order_156338400.html')
print(f'Parsed {len(orders)} orders from 3-item file')

for i, order in enumerate(orders):
    print(f'Order {i+1}: {order.get("raw_item_number")} - {order.get("item_description")}')
