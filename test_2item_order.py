import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from parsers.wholefoods_parser import WholeFoodsParser
from utils.mapping_utils import MappingUtils

print('Testing 2-item Whole Foods order...')

# Initialize parser
mapping_utils = MappingUtils()
parser = WholeFoodsParser()
parser.mapping_utils = mapping_utils

# Test with the 2-item order
with open('order_samples/wholefoods/order_156296288.html', 'rb') as f:
    file_content = f.read()

orders = parser.parse(file_content, 'html', 'order_156296288.html')
print(f'Parsed {len(orders)} orders from 2-item file')

for i, order in enumerate(orders):
    print(f'Order {i+1}: {order.get("raw_item_number")} - {order.get("item_description")}')

# Expected items:
print('\nExpected items:')
print('1. 170411 - BRUSCHETTA ARTICHOKE')
print('2. 170512 - ARTICHOKES GRILLED MARINATED')
