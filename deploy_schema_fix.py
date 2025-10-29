#!/usr/bin/env python3
"""
Deploy schema fix for StoreMapping table
Run this on Render to fix the database schema
"""

import os
import sys
import subprocess

def run_schema_fix():
    """Run the schema fix on Render"""
    
    print("🔧 Running StoreMapping schema fix...")
    
    try:
        # Run the schema fix script
        result = subprocess.run([
            sys.executable, "render_fix_store_mapping.py"
        ], capture_output=True, text=True, timeout=60)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ Schema fix completed successfully!")
            return True
        else:
            print(f"❌ Schema fix failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Schema fix timed out")
        return False
    except Exception as e:
        print(f"❌ Error running schema fix: {e}")
        return False

if __name__ == "__main__":
    success = run_schema_fix()
    if not success:
        sys.exit(1)
