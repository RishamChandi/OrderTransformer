#!/usr/bin/env python3
"""
Test UNFI East PDF extraction to debug IOW code extraction
"""

import os
from pathlib import Path
from parsers.unfi_east_parser import UNFIEastParser
from utils.mapping_utils import MappingUtils

def test_pdf_extraction(pdf_path):
    """Test PDF extraction and see what's being extracted"""
    
    print("=" * 70)
    print(f"Testing PDF: {pdf_path}")
    print("=" * 70)
    print()
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    try:
        # Initialize parser
        mapping_utils = MappingUtils(use_database=True)
        parser = UNFIEastParser(mapping_utils)
        
        # Read PDF file
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        print(f"✅ PDF file size: {len(file_content)} bytes")
        print()
        
        # Extract text from PDF
        print("=" * 70)
        print("Extracting text from PDF...")
        print("=" * 70)
        print()
        
        text_content = parser._extract_text_from_pdf(file_content)
        print(f"✅ Extracted {len(text_content)} characters of text")
        print()
        
        # Show first 1000 characters
        print("=" * 70)
        print("First 1000 characters of extracted text:")
        print("=" * 70)
        print(repr(text_content[:1000]))
        print()
        
        # Show all text (might be long)
        print("=" * 70)
        print("Full extracted text:")
        print("=" * 70)
        print(text_content)
        print()
        
        # Look for key patterns
        print("=" * 70)
        print("Searching for key patterns...")
        print("=" * 70)
        print()
        
        import re
        
        # Search for "Ship To"
        ship_to_matches = list(re.finditer(r'Ship\s+To[:\s]+', text_content, re.IGNORECASE))
        print(f"Found {len(ship_to_matches)} 'Ship To' matches:")
        for i, match in enumerate(ship_to_matches[:5]):  # Show first 5
            start = max(0, match.start() - 20)
            end = min(len(text_content), match.end() + 100)
            context = text_content[start:end]
            print(f"  Match {i+1}: {repr(context)}")
        print()
        
        # Search for "Int Ref"
        int_ref_matches = list(re.finditer(r'Int(?:ernal)?\s+Ref(?:\s+Number)?[:#]', text_content, re.IGNORECASE))
        print(f"Found {len(int_ref_matches)} 'Int Ref' matches:")
        for i, match in enumerate(int_ref_matches[:5]):  # Show first 5
            start = max(0, match.start() - 20)
            end = min(len(text_content), match.end() + 100)
            context = text_content[start:end]
            print(f"  Match {i+1}: {repr(context)}")
        print()
        
        # Search for IOW codes
        iow_codes = ['RCH', 'HOW', 'CHE', 'YOR', 'IOW', 'GRW', 'MAN', 'ATL', 'SAR', 'SRQ', 'DAY', 'HVA', 'RAC', 'TWC']
        print(f"Searching for IOW codes:")
        for code in iow_codes:
            pattern = rf'\b{code}\b'
            matches = list(re.finditer(pattern, text_content, re.IGNORECASE))
            if matches:
                print(f"  ✅ Found '{code}': {len(matches)} matches")
                for i, match in enumerate(matches[:2]):  # Show first 2
                    start = max(0, match.start() - 30)
                    end = min(len(text_content), match.end() + 30)
                    context = text_content[start:end]
                    print(f"    Context {i+1}: {repr(context)}")
            else:
                print(f"  ❌ Not found: '{code}'")
        print()
        
        # Try to parse the order
        print("=" * 70)
        print("Attempting to parse order...")
        print("=" * 70)
        print()
        
        filename = os.path.basename(pdf_path)
        orders = parser.parse(file_content, 'pdf', filename)
        
        if orders:
            print(f"✅ Parsed {len(orders)} order(s)")
            print()
            for i, order in enumerate(orders):
                print(f"Order {i+1}:")
                print(f"  Order Number: {order.get('order_number')}")
                print(f"  Customer Name: {order.get('customer_name')}")
                print(f"  Raw Customer Name: {order.get('raw_customer_name')}")
                print(f"  Warehouse Location: {order.get('warehouse_location', 'N/A')}")
                print()
        else:
            print("❌ No orders parsed")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test with the problematic PDFs
    test_files = [
        'order_samples/unfi_east/UNFI East PO4531546.pdf',
        'order_samples/unfi_east/UNFI East PO4531367.pdf',
        'order_samples/unfi_east/UNFI East PO4531365.pdf',
        'order_samples/unfi_east/UNFI East PO4480501 (1).pdf',
    ]
    
    # Find available PDFs
    available_files = []
    for test_file in test_files:
        if os.path.exists(test_file):
            available_files.append(test_file)
    
    # Also check for any PDFs in the directory
    unfi_east_dir = Path('order_samples/unfi_east')
    if unfi_east_dir.exists():
        for pdf_file in unfi_east_dir.glob('*.pdf'):
            if str(pdf_file) not in available_files:
                available_files.append(str(pdf_file))
    
    if not available_files:
        print("❌ No PDF files found in order_samples/unfi_east")
        print("Please add some UNFI East PDF files to test")
    else:
        print(f"Found {len(available_files)} PDF file(s) to test")
        print()
        
        # Test first PDF
        if available_files:
            test_pdf_extraction(available_files[0])
            
            if len(available_files) > 1:
                print()
                print("=" * 70)
                print(f"Would you like to test more PDFs? Found {len(available_files)} total")
                print("=" * 70)

