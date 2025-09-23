#!/usr/bin/env python3
import os
import sys

# Set environment
os.environ['ENVIRONMENT'] = 'local'
os.environ['DATABASE_URL'] = 'sqlite:///./orderparser_dev.db'

print("Testing Whole Foods processor with new mappings...")

try:
    from parsers.wholefoods_parser import WholeFoodsParser
    from database.service import DatabaseService
    
    # Initialize parser and database service
    parser = WholeFoodsParser()
    db_service = DatabaseService()
    
    print("✓ Parser and database service initialized")
    
    # Test with a sample Whole Foods file
    sample_file = "attached_assets/wholefoods order_154533670_1753747046214.html"
    
    if os.path.exists(sample_file):
        print(f"\nTesting with file: {sample_file}")
        
        # Read the file
        with open(sample_file, 'rb') as f:
            file_content = f.read()
        
        # Parse the file
        orders = parser.parse(file_content, 'html', os.path.basename(sample_file))
        
        if orders:
            print(f"✓ Successfully parsed {len(orders)} order items")
            
            # Show sample results
            for i, order in enumerate(orders[:3]):  # Show first 3 items
                print(f"\nOrder Item {i+1}:")
                print(f"  Order Number: {order.get('order_number', 'N/A')}")
                print(f"  Customer: {order.get('customer_name', 'N/A')}")
                print(f"  Raw Customer: {order.get('raw_customer_name', 'N/A')}")
                print(f"  Item Number: {order.get('item_number', 'N/A')}")
                print(f"  Raw Item: {order.get('raw_item_number', 'N/A')}")
                print(f"  Description: {order.get('item_description', 'N/A')}")
                print(f"  Quantity: {order.get('quantity', 'N/A')}")
                print(f"  Unit Price: ${order.get('unit_price', 0):.2f}")
                print(f"  Total Price: ${order.get('total_price', 0):.2f}")
            
            # Test saving to database
            print(f"\nSaving {len(orders)} order items to database...")
            success = db_service.save_processed_orders(orders, 'wholefoods', os.path.basename(sample_file))
            
            if success:
                print("✓ Orders saved to database successfully")
                
                # Verify the mappings are working
                print("\nVerifying mappings are working:")
                
                # Check if customer mappings are being applied
                customer_mappings = db_service.get_customer_mappings_advanced(source='wholefoods', active_only=True)
                print(f"  Customer mappings available: {len(customer_mappings)}")
                
                # Check if item mappings are being applied
                item_mappings = db_service.get_item_mappings_advanced(source='wholefoods', active_only=True)
                print(f"  Item mappings available: {len(item_mappings)}")
                
                # Check if store mappings are being applied
                store_mappings = db_service.get_store_mappings_advanced(source='wholefoods', active_only=True)
                print(f"  Store mappings available: {len(store_mappings)}")
                
                # Show some sample mappings in action
                sample_orders = db_service.get_processed_orders(source='wholefoods', limit=5)
                if sample_orders:
                    print(f"\nSample processed orders from database:")
                    for order in sample_orders[:2]:
                        print(f"  Order: {order['order_number']} - Customer: {order['customer_name']}")
                        if order['line_items']:
                            for item in order['line_items'][:2]:
                                print(f"    Item: {item['raw_item_number']} -> {item['item_number']}")
                
            else:
                print("❌ Failed to save orders to database")
        else:
            print("❌ No orders parsed from file")
    else:
        print(f"❌ Sample file not found: {sample_file}")
        
        # List available Whole Foods files
        print("\nAvailable Whole Foods files:")
        import glob
        wholefoods_files = glob.glob("attached_assets/wholefoods*.html")
        for file in wholefoods_files:
            print(f"  {file}")
    
    print("\n✓ Whole Foods processor test completed")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
