#!/usr/bin/env python3
"""
Script to create mapping Excel files for all order sources
"""

import pandas as pd
import os

def create_mapping_files():
    """Create mapping Excel files for all order sources"""
    
    # Whole Foods mapping
    wholefoods_data = {
        'Raw Name': [
            'Whole Foods Market - Downtown',
            'Whole Foods Market - Uptown', 
            'Whole Foods Market - West Side',
            'WFM Central',
            'Whole Foods - Main Street',
            'Sample Store Name'
        ],
        'Mapped Name': [
            'Whole Foods Downtown',
            'Whole Foods Uptown',
            'Whole Foods West Side', 
            'Whole Foods Central',
            'Whole Foods Main Street',
            'Mapped Store Name'
        ]
    }
    
    # UNFI West mapping
    unfi_west_data = {
        'Raw Name': [
            'UNFI WEST Distribution Center',
            'UNFI West - Portland',
            'UNFI West - Seattle',
            'UNFI West Regional',
            'Sample UNFI West Store',
            'Default Store Name'
        ],
        'Mapped Name': [
            'UNFI West Distribution',
            'UNFI West Portland',
            'UNFI West Seattle',
            'UNFI West Regional',
            'Mapped UNFI West Store',
            'Default Mapped Store'
        ]
    }
    
    # UNFI mapping
    unfi_data = {
        'Raw Name': [
            'UNFI Distribution Center',
            'UNFI - East Coast',
            'UNFI - West Coast',
            'UNFI Regional Hub',
            'Sample UNFI Store',
            'Generic Store Name'
        ],
        'Mapped Name': [
            'UNFI Distribution',
            'UNFI East Coast',
            'UNFI West Coast',
            'UNFI Regional',
            'Mapped UNFI Store',
            'Generic Mapped Store'
        ]
    }
    
    # TK Maxx mapping
    tkmaxx_data = {
        'Raw Name': [
            'TK Maxx - London',
            'TK Maxx - Manchester',
            'TK Maxx - Birmingham',
            'TK Maxx Regional',
            'Sample TK Maxx Store',
            'Example Store'
        ],
        'Mapped Name': [
            'TK Maxx London',
            'TK Maxx Manchester',
            'TK Maxx Birmingham',
            'TK Maxx Regional',
            'Mapped TK Maxx Store',
            'Example Mapped Store'
        ]
    }
    
    # Create mapping files
    mappings = [
        ('wholefoods', wholefoods_data),
        ('unfi_west', unfi_west_data),
        ('unfi', unfi_data),
        ('tkmaxx', tkmaxx_data)
    ]
    
    for source, data in mappings:
        # Create directory
        mapping_dir = f'mappings/{source}'
        os.makedirs(mapping_dir, exist_ok=True)
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(data)
        mapping_file = os.path.join(mapping_dir, 'store_mapping.xlsx')
        df.to_excel(mapping_file, index=False)
        print(f"Created {mapping_file}")

if __name__ == "__main__":
    create_mapping_files()