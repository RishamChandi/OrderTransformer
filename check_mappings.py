#!/usr/bin/env python3
import os

# Set environment
os.environ['ENVIRONMENT'] = 'local'
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'

from database.service import DatabaseService

db = DatabaseService()

print("Checking customer mappings for store 10447:")
customer_mappings = db.get_customer_mappings_advanced(source='wholefoods', active_only=True)
for m in customer_mappings:
    if '10447' in m['raw_customer_id']:
        print(f"  {m['raw_customer_id']} -> {m['mapped_customer_name']}")

print("\nChecking item mappings:")
item_mappings = db.get_item_mappings_advanced(source='wholefoods', active_only=True)
print(f"Total item mappings: {len(item_mappings)}")
for m in item_mappings[:5]:
    print(f"  {m['raw_item']} -> {m['mapped_item']}")

print("\nChecking if item 130357 exists in mappings:")
found = False
for m in item_mappings:
    if m['raw_item'] == '130357':
        print(f"  Found: {m['raw_item']} -> {m['mapped_item']}")
        found = True
        break
if not found:
    print("  Item 130357 not found in mappings")

print("\nChecking if item 130356 exists in mappings:")
found = False
for m in item_mappings:
    if m['raw_item'] == '130356':
        print(f"  Found: {m['raw_item']} -> {m['mapped_item']}")
        found = True
        break
if not found:
    print("  Item 130356 not found in mappings")
