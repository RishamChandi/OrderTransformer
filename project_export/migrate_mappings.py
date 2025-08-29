#!/usr/bin/env python3
"""
Mapping Migration Script for Order Transformation Platform
Migrates all mapping files from one deployment to another
"""

import os
import pandas as pd
import shutil
from pathlib import Path
import argparse
import json
from datetime import datetime

def create_mapping_backup():
    """Create a backup of all current mapping files"""
    
    backup_dir = f"mapping_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    mapping_files = []
    
    # Find all mapping files
    for root, dirs, files in os.walk("mappings"):
        for file in files:
            if file.endswith(('.csv', '.xlsx')):
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, "mappings")
                mapping_files.append(src_path)
    
    # Copy to backup directory
    for src_path in mapping_files:
        rel_path = os.path.relpath(src_path, "mappings")
        dest_path = os.path.join(backup_dir, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        print(f"Backed up: {src_path} → {dest_path}")
    
    # Create backup manifest
    manifest = {
        "backup_date": datetime.now().isoformat(),
        "total_files": len(mapping_files),
        "files": mapping_files
    }
    
    with open(os.path.join(backup_dir, "backup_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Created backup directory: {backup_dir}")
    return backup_dir

def export_all_mappings():
    """Export all mappings to a portable format"""
    
    export_dir = f"mapping_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(export_dir, exist_ok=True)
    
    processors = ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
    mapping_types = ['customer_mapping', 'xoro_store_mapping', 'item_mapping']
    
    exported_files = []
    
    for processor in processors:
        processor_dir = os.path.join(export_dir, processor)
        os.makedirs(processor_dir, exist_ok=True)
        
        for mapping_type in mapping_types:
            # Check for existing files
            csv_file = f"mappings/{processor}/{mapping_type}.csv"
            xlsx_file = f"mappings/{processor}/{mapping_type}.xlsx"
            
            # Special case for KEHE item mapping
            if processor == 'kehe' and mapping_type == 'item_mapping':
                csv_file = "mappings/kehe_item_mapping.csv"
            
            source_file = None
            if os.path.exists(csv_file):
                source_file = csv_file
            elif os.path.exists(xlsx_file):
                source_file = xlsx_file
            
            if source_file:
                dest_file = os.path.join(processor_dir, f"{mapping_type}.csv")
                
                # Convert to CSV if needed
                if source_file.endswith('.xlsx'):
                    df = pd.read_excel(source_file, dtype=str)
                    df.to_csv(dest_file, index=False)
                else:
                    shutil.copy2(source_file, dest_file)
                
                exported_files.append(dest_file)
                print(f"Exported: {source_file} → {dest_file}")
    
    # Create export manifest
    manifest = {
        "export_date": datetime.now().isoformat(),
        "total_files": len(exported_files),
        "processors": processors,
        "mapping_types": mapping_types,
        "files": exported_files
    }
    
    with open(os.path.join(export_dir, "export_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Created export directory: {export_dir}")
    return export_dir

def import_mappings(import_dir):
    """Import mappings from export directory"""
    
    if not os.path.exists(import_dir):
        print(f"❌ Import directory not found: {import_dir}")
        return False
    
    manifest_file = os.path.join(import_dir, "export_manifest.json")
    if not os.path.exists(manifest_file):
        print(f"❌ Manifest file not found: {manifest_file}")
        return False
    
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    
    print(f"📦 Importing {manifest['total_files']} mapping files...")
    
    imported_count = 0
    
    for processor in manifest['processors']:
        processor_dir = os.path.join(import_dir, processor)
        
        if os.path.exists(processor_dir):
            # Ensure target directory exists
            target_processor_dir = f"mappings/{processor}"
            os.makedirs(target_processor_dir, exist_ok=True)
            
            for mapping_file in os.listdir(processor_dir):
                if mapping_file.endswith('.csv'):
                    src_path = os.path.join(processor_dir, mapping_file)
                    
                    # Special case for KEHE item mapping
                    if processor == 'kehe' and mapping_file == 'item_mapping.csv':
                        dest_path = "mappings/kehe_item_mapping.csv"
                    else:
                        dest_path = os.path.join(target_processor_dir, mapping_file)
                    
                    shutil.copy2(src_path, dest_path)
                    print(f"Imported: {src_path} → {dest_path}")
                    imported_count += 1
    
    print(f"✅ Successfully imported {imported_count} mapping files")
    return True

def validate_mappings():
    """Validate all mapping files"""
    
    processors = ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
    issues = []
    
    for processor in processors:
        print(f"\n🔍 Validating {processor} mappings...")
        
        # Check customer mapping
        customer_file = f"mappings/{processor}/customer_mapping.csv"
        if os.path.exists(customer_file):
            try:
                df = pd.read_csv(customer_file)
                print(f"  ✅ Customer mapping: {len(df)} entries")
            except Exception as e:
                issues.append(f"{customer_file}: {e}")
                print(f"  ❌ Customer mapping: {e}")
        else:
            print(f"  ⚠️ Customer mapping: file not found")
        
        # Check store mapping
        store_file = f"mappings/{processor}/xoro_store_mapping.csv"
        if os.path.exists(store_file):
            try:
                df = pd.read_csv(store_file)
                print(f"  ✅ Store mapping: {len(df)} entries")
            except Exception as e:
                issues.append(f"{store_file}: {e}")
                print(f"  ❌ Store mapping: {e}")
        else:
            print(f"  ⚠️ Store mapping: file not found")
        
        # Check item mapping
        if processor == 'kehe':
            item_file = "mappings/kehe_item_mapping.csv"
        else:
            item_file = f"mappings/{processor}/item_mapping.csv"
            
        if os.path.exists(item_file):
            try:
                df = pd.read_csv(item_file)
                print(f"  ✅ Item mapping: {len(df)} entries")
            except Exception as e:
                issues.append(f"{item_file}: {e}")
                print(f"  ❌ Item mapping: {e}")
        else:
            print(f"  ⚠️ Item mapping: file not found")
    
    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ All mappings validated successfully!")
    
    return len(issues) == 0

def main():
    parser = argparse.ArgumentParser(description="Order Transformation Platform Mapping Migration")
    parser.add_argument("action", choices=["backup", "export", "import", "validate"], 
                       help="Action to perform")
    parser.add_argument("--import-dir", help="Directory to import mappings from")
    
    args = parser.parse_args()
    
    if args.action == "backup":
        create_mapping_backup()
    elif args.action == "export":
        export_all_mappings()
    elif args.action == "import":
        if not args.import_dir:
            print("❌ --import-dir required for import action")
            return
        import_mappings(args.import_dir)
    elif args.action == "validate":
        validate_mappings()

if __name__ == "__main__":
    main()