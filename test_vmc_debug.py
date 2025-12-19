"""Debug VMC CSV parsing"""
import pandas as pd
import io

file_path = 'order_samples/vmc/VMC Grocery_Order93659_735994.csv'

print("Reading CSV file...")
with open(file_path, 'r', encoding='utf-8-sig') as f:
    content_str = f.read()

print("Creating DataFrame with dtype=str, keep_default_na=False...")
df = pd.read_csv(io.StringIO(content_str), dtype=str, keep_default_na=False)

print(f"\nDataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

if 'Record Type' in df.columns:
    print(f"\nRecord Type column found!")
    print(f"Record Type values (first 30):")
    print(df['Record Type'].head(30).tolist())
    print(f"\nUnique Record Types: {sorted(df['Record Type'].unique().tolist())}")
    
    print(f"\nAfter stripping:")
    df['Record Type'] = df['Record Type'].str.strip()
    print(f"Unique Record Types: {sorted(df['Record Type'].unique().tolist())}")
    
    print(f"\nRows with Record Type = 'D':")
    d_rows = df[df['Record Type'] == 'D']
    print(f"Found {len(d_rows)} rows with 'D'")
    if len(d_rows) > 0:
        print("First 'D' row:")
        print(d_rows.iloc[0][['Record Type', 'Qty Ordered', 'Buyer\'s Catalog or Stock Keeping #', 'Product/Item Description']])
    
    print(f"\nRows with Record Type containing 'D':")
    d_contains = df[df['Record Type'].str.contains('D', na=False)]
    print(f"Found {len(d_contains)} rows containing 'D'")
    
    # Check for hidden characters
    print(f"\nChecking for hidden characters in Record Type='D' rows...")
    for idx, row in df.iterrows():
        rt = row['Record Type']
        if 'D' in str(rt) or 'd' in str(rt).lower():
            print(f"Row {idx}: Record Type = '{rt}' (repr: {repr(rt)}, len: {len(str(rt))})")
            if idx >= 5:  # Only show first few
                break
else:
    print("ERROR: 'Record Type' column not found in DataFrame!")

