import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from parsers.wholefoods_parser import WholeFoodsParser
from utils.mapping_utils import MappingUtils
from bs4 import BeautifulSoup

print('Debugging 2-item Whole Foods order...')

# Initialize parser
mapping_utils = MappingUtils()
parser = WholeFoodsParser()
parser.mapping_utils = mapping_utils

# Test with the 2-item order
with open('order_samples/wholefoods/order_156296288.html', 'rb') as f:
    file_content = f.read()

# Parse HTML manually to see what's in the table
soup = BeautifulSoup(file_content, 'html.parser')

print('Looking for tables with line items...')
tables = soup.find_all('table')
print(f'Found {len(tables)} tables')

for i, table in enumerate(tables):
    print(f'\nTable {i+1}:')
    rows = table.find_all('tr')
    print(f'  Rows: {len(rows)}')
    
    # Check if this looks like a line items table
    if rows:
        header_row = rows[0]
        header_text = header_row.get_text().lower()
        print(f'  Header: {header_text}')
        
        if 'item no' in header_text and 'description' in header_text:
            print('  *** This looks like a line items table ***')
            for j, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 6:
                    item_number = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    description = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    print(f'    Row {j+1}: {item_number} - {description}')

print('\n' + '='*50)
print('Now testing the parser...')

orders = parser.parse(file_content, 'html', 'order_156296288.html')
print(f'Parser result: {len(orders)} orders')

for i, order in enumerate(orders):
    print(f'Order {i+1}: {order.get("raw_item_number")} - {order.get("item_description")}')
