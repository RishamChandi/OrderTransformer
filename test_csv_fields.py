"""Check CSV field counts"""
import csv

file_path = 'order_samples/vmc/VMC Grocery_Order93659_735994.csv'

print("Checking field counts per line...")
with open(file_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"Header has {len(header)} fields")
    print(f"Header: {header}")
    
    for i, row in enumerate(reader, start=2):
        if i <= 10:  # First 10 data rows
            print(f"Line {i}: {len(row)} fields, Record Type (col 27): '{row[26] if len(row) > 26 else 'N/A'}'")
            if len(row) != len(header):
                print(f"  WARNING: Field count mismatch! Header={len(header)}, Row={len(row)}")
                if len(row) > len(header):
                    print(f"  Extra fields: {row[len(header):]}")

