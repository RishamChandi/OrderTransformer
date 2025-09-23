import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from parsers.wholefoods_parser import WholeFoodsParser
from utils.mapping_utils import MappingUtils

print('Testing parser...')
mapping_utils = MappingUtils()
parser = WholeFoodsParser()
parser.mapping_utils = mapping_utils
print('Parser initialized')

with open('order_samples/wholefoods/order_156296288.html', 'rb') as f:
    content = f.read()

orders = parser.parse(content, 'html', 'test.html')
print(f'Parsed {len(orders)} orders')

for i, order in enumerate(orders):
    print(f'Order {i+1}: {order.get("raw_item_number")} - {order.get("item_description")}')
