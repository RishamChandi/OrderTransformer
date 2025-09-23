import os
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'
from database.service import DatabaseService
import pandas as pd

print('Testing UNFI East migration...')

# Test customer mapping
df = pd.read_csv('mappings/unfi_east/customer_mapping.csv')
print(f'Found {len(df)} customer mappings')

db_service = DatabaseService()
mappings_data = []
for _, row in df.iterrows():
    mapping_data = {
        'source': 'unfi_east',
        'raw_customer_id': str(row.get('StoreNumber', '')).strip(),
        'mapped_customer_name': str(row.get('CompanyName', '')).strip(),
        'customer_type': 'store',
        'priority': 100,
        'active': True,
        'notes': f'Account: {row.get("AccountNumber", "")}, ShipTo: {row.get("ShipToCompanyName", "")}'
    }
    mappings_data.append(mapping_data)

stats = db_service.bulk_upsert_customer_mappings(mappings_data)
print(f'Customer mapping import: {stats}')
