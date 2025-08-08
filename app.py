import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
from parsers.wholefoods_parser import WholeFoodsParser
from parsers.unfi_west_parser import UNFIWestParser
from parsers.unfi_east_parser import UNFIEastParser
from parsers.kehe_parser import KEHEParser
from parsers.tkmaxx_parser import TKMaxxParser
from utils.xoro_template import XoroTemplate
from utils.mapping_utils import MappingUtils
from database.service import DatabaseService

# Import for database initialization
from database.models import Base
from database.connection import get_database_engine
from sqlalchemy import inspect

def initialize_database_if_needed():
    """Initialize database tables if they don't exist"""
    try:
        from database.connection import get_current_environment
        env = get_current_environment()
        
        engine = get_database_engine()
        inspector = inspect(engine)
        
        # Check if tables exist
        tables_exist = inspector.get_table_names()
        if not tables_exist:
            st.info(f"Initializing {env} database for first run...")
            Base.metadata.create_all(bind=engine)
            st.success(f"Database initialized successfully in {env} environment!")
        else:
            st.success(f"Connected to {env} database ({len(tables_exist)} tables found)")
            
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.info("💡 **Environment Detection Help:**")
        st.info("- **Replit Development**: Uses local PostgreSQL without SSL")
        st.info("- **Streamlit Cloud**: Uses production database with SSL")
        st.info("- **Issue**: Check if you have production database credentials in development environment")

def main():
    # Initialize database if needed
    initialize_database_if_needed()
    st.title("Order Transformer - Multiple Sources to Xoro CSV")
    st.write("Convert sales orders from different sources into standardized Xoro import CSV format")
    
    # Initialize database service
    db_service = DatabaseService()
    
    # Sidebar for configuration and navigation
    st.sidebar.header("Navigation")
    
    # One-time database initialization for cloud deployment
    if st.sidebar.button("🔧 Initialize Database (First-time setup)"):
        try:
            from init_database import main as init_db
            init_db()
            st.sidebar.success("Database initialized!")
        except Exception as e:
            st.sidebar.error(f"Database init failed: {e}")
    
    # Add navigation options
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Process Orders", "Conversion History", "View Processed Orders", "Manage Mappings"]
    )
    
    if page == "Process Orders":
        process_orders_page(db_service)
    elif page == "Conversion History":
        conversion_history_page(db_service)
    elif page == "View Processed Orders":
        processed_orders_page(db_service)
    elif page == "Manage Mappings":
        manage_mappings_page(db_service)

def process_orders_page(db_service: DatabaseService):
    """Main order processing page"""
    
    st.header("Process Orders")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Initialize mapping utils
    mapping_utils = MappingUtils()
    
    # Order source selection
    order_sources = {
        "Whole Foods": WholeFoodsParser(),
        "UNFI West": UNFIWestParser(),
        "UNFI East": UNFIEastParser(mapping_utils),
        "KEHE - SPS": KEHEParser(),
        "TK Maxx": TKMaxxParser()
    }
    
    selected_source = st.sidebar.selectbox(
        "Select Order Source",
        list(order_sources.keys())
    )
    
    st.subheader(f"Processing {selected_source} Orders")
    
    # Determine accepted file types based on selected source
    if selected_source == "Whole Foods":
        accepted_types = ['html']
        help_text = "Upload HTML files exported from Whole Foods orders"
    elif selected_source == "UNFI West":
        accepted_types = ['html']
        help_text = "Upload HTML files from UNFI West purchase orders"
    elif selected_source == "UNFI East":
        accepted_types = ['pdf']
        help_text = "Upload PDF files from UNFI East purchase orders"
    elif selected_source == "UNFI":
        accepted_types = ['csv', 'xlsx']
        help_text = "Upload CSV or Excel files from UNFI orders"
    elif selected_source == "TK Maxx":
        accepted_types = ['csv', 'xlsx']
        help_text = "Upload CSV or Excel files from TK Maxx orders"
    else:
        accepted_types = ['html', 'csv', 'xlsx', 'pdf']
        help_text = f"Upload {selected_source} order files for conversion"
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload order files",
        type=accepted_types,
        accept_multiple_files=True,
        help=help_text
    )
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} file(s)")
        
        # Process files button
        if st.button("Process Orders", type="primary"):
            process_orders(uploaded_files, order_sources[selected_source], selected_source, db_service)

def process_orders(uploaded_files, parser, source_name, db_service: DatabaseService):
    """Process uploaded files and convert to Xoro format"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_converted_data = []
    all_parsed_data = []  # Keep original parsed data for database storage
    errors = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Read file content
            file_content = uploaded_file.read()
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            # Parse the file
            parsed_data = parser.parse(file_content, file_extension, uploaded_file.name)
            
            if parsed_data:
                # Store parsed data for database
                all_parsed_data.extend(parsed_data)
                
                # Convert to Xoro format
                xoro_template = XoroTemplate()
                converted_data = xoro_template.convert_to_xoro(parsed_data, source_name)
                all_converted_data.extend(converted_data)
                
                # Save to database
                db_saved = db_service.save_processed_orders(parsed_data, source_name, uploaded_file.name)
                
                if db_saved:
                    st.success(f"✅ Successfully processed and saved {uploaded_file.name}")
                else:
                    st.warning(f"⚠️ Processed {uploaded_file.name} but database save failed")
            else:
                errors.append(f"Failed to parse {uploaded_file.name}")
                st.error(f"❌ Failed to process {uploaded_file.name}")
                
        except Exception as e:
            error_msg = f"Error processing {uploaded_file.name}: {str(e)}"
            errors.append(error_msg)
            st.error(f"❌ {error_msg}")
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    status_text.text("Processing complete!")
    
    # Display results
    if all_converted_data:
        st.subheader("Conversion Results")
        
        # Create DataFrame for preview
        df_converted = pd.DataFrame(all_converted_data)
        
        # Display summary
        unique_orders = df_converted['ThirdPartyRefNo'].nunique()
        st.write(f"**Total Orders Processed:** {unique_orders}")
        st.write(f"**Unique Customers:** {df_converted['CustomerName'].nunique()}")
        st.write(f"**Total Line Items:** {len(df_converted)}")
        
        # Preview data
        st.subheader("Data Preview")
        st.dataframe(df_converted.head(10))
        
        # Download button
        csv_data = df_converted.to_csv(index=False)
        st.download_button(
            label="📥 Download Xoro CSV",
            data=csv_data,
            file_name=f"xoro_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )
        
        # Show detailed data in expander
        with st.expander("View Full Converted Data"):
            st.dataframe(df_converted)
    
    # Display errors if any
    if errors:
        st.subheader("Errors")
        for error in errors:
            st.error(error)

def conversion_history_page(db_service: DatabaseService):
    """Display conversion history from database"""
    
    st.header("Conversion History")
    
    try:
        history = db_service.get_conversion_history(limit=100)
        
        if history:
            df_history = pd.DataFrame(history)
            
            # Display summary stats
            total_conversions = len(df_history)
            successful_conversions = len(df_history[df_history['success'] == True])
            failed_conversions = total_conversions - successful_conversions
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Conversions", total_conversions)
            with col2:
                st.metric("Successful", successful_conversions)
            with col3:
                st.metric("Failed", failed_conversions)
            
            # Display history table
            st.subheader("Recent Conversions")
            st.dataframe(df_history[['filename', 'source', 'conversion_date', 'orders_count', 'success']])
            
            # Show errors in expander
            failed_records = df_history[df_history['success'] == False]
            if not failed_records.empty:
                with st.expander("View Failed Conversions"):
                    for _, record in failed_records.iterrows():
                        st.error(f"**{record['filename']}**: {record['error_message']}")
        else:
            st.info("No conversion history found.")
            
    except Exception as e:
        st.error(f"Error loading conversion history: {str(e)}")

def processed_orders_page(db_service: DatabaseService):
    """Display processed orders from database"""
    
    st.header("Processed Orders")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        source_filter = st.selectbox(
            "Filter by Source",
            ["All", "Whole Foods", "UNFI West", "UNFI", "TK Maxx"]
        )
    
    with col2:
        limit = st.number_input("Number of orders to display", min_value=10, max_value=1000, value=50)
    
    try:
        source = None if source_filter == "All" else source_filter.lower().replace(" ", "_")
        orders = db_service.get_processed_orders(source=source, limit=int(limit))
        
        if orders:
            st.write(f"Found {len(orders)} orders")
            
            # Display orders summary
            for order in orders:
                with st.expander(f"Order {order['order_number']} - {order['customer_name']} ({len(order['line_items'])} items)"):
                    
                    # Order details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Source:** {order['source']}")
                        st.write(f"**Customer:** {order['customer_name']}")
                    with col2:
                        st.write(f"**Order Date:** {order['order_date']}")
                        st.write(f"**Processed:** {order['processed_at']}")
                    with col3:
                        st.write(f"**Source File:** {order['source_file']}")
                    
                    # Line items
                    if order['line_items']:
                        st.write("**Line Items:**")
                        df_items = pd.DataFrame(order['line_items'])
                        st.dataframe(df_items[['item_number', 'item_description', 'quantity', 'unit_price', 'total_price']])
        else:
            st.info("No processed orders found.")
            
    except Exception as e:
        st.error(f"Error loading processed orders: {str(e)}")

def manage_mappings_page(db_service: DatabaseService):
    """Manage store and item mappings with editable interface"""
    
    st.header("📋 Manage Mappings")
    
    # Create tabs for different mapping types
    tab1, tab2, tab3 = st.tabs(["🏪 Store Mapping", "👥 Customer Mapping", "📦 Item Mapping"])
    
    mapping_utils = MappingUtils()
    sources = ['wholefoods', 'unfi_west', 'unfi_east', 'unfi', 'kehe', 'tkmaxx']
    
    with tab1:
        st.subheader("Store Mappings")
        show_editable_store_mappings(mapping_utils, sources, db_service)
    
    with tab2:
        st.subheader("Customer Mappings")
        show_editable_customer_mappings(mapping_utils, sources, db_service)
    
    with tab3:
        st.subheader("Item Mappings")
        show_editable_item_mappings(mapping_utils, sources, db_service)

def show_editable_store_mappings(mapping_utils, sources, db_service):
    """Show editable store mappings interface"""
    
    # Source selector
    selected_source = st.selectbox("Select Source", sources, key="store_source")
    
    try:
        # Get store mappings for selected source
        store_mappings = {}
        
        # Try to get mappings from database first
        try:
            with db_service.get_session() as session:
                mappings = session.query(db_service.StoreMapping).filter_by(source=selected_source).all()
                for mapping in mappings:
                    store_mappings[mapping.raw_name] = mapping.mapped_name
        except Exception:
            pass
        
        # If no database mappings, try Excel files
        if not store_mappings:
            store_mappings = mapping_utils._load_store_mappings_from_excel(selected_source)
        
        if store_mappings:
            st.write(f"**{selected_source.replace('_', ' ').title()} Store Mappings:**")
            
            # Add option to add new mapping
            with st.expander("➕ Add New Store Mapping"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    new_raw = st.text_input("Raw Store Name", key=f"new_store_raw_{selected_source}")
                with col2:
                    new_mapped = st.text_input("Mapped Store Name", key=f"new_store_mapped_{selected_source}")
                with col3:
                    if st.button("Add", key=f"add_store_{selected_source}"):
                        if new_raw and new_mapped:
                            success = db_service.save_store_mapping(selected_source, new_raw, new_mapped)
                            if success:
                                st.success("Store mapping added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add mapping")
            
            # Display editable table with delete options
            for idx, (raw, mapped) in enumerate(store_mappings.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text_input("Raw Store", value=raw, disabled=True, key=f"store_raw_{idx}_{selected_source}")
                with col2:
                    new_mapped_value = st.text_input("Mapped Store", value=mapped, key=f"store_mapped_{idx}_{selected_source}")
                with col3:
                    if st.button("🗑️", key=f"delete_store_{idx}_{selected_source}", help="Delete mapping"):
                        try:
                            with db_service.get_session() as session:
                                mapping_to_delete = session.query(db_service.StoreMapping).filter_by(
                                    source=selected_source, raw_name=raw
                                ).first()
                                if mapping_to_delete:
                                    session.delete(mapping_to_delete)
                                    session.commit()
                                st.success("Store mapping deleted!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete mapping: {e}")
                
                # Update mapping if changed
                if new_mapped_value != mapped:
                    success = db_service.save_store_mapping(selected_source, raw, new_mapped_value)
                    if success:
                        st.success(f"Updated mapping: {raw} → {new_mapped_value}")
                        st.rerun()
                    else:
                        st.error("Failed to update mapping")
        else:
            st.info(f"No store mappings found for {selected_source}")
            
    except Exception as e:
        st.error(f"Error loading store mappings: {e}")

def show_editable_customer_mappings(mapping_utils, sources, db_service):
    """Show editable customer mappings interface (same as store mappings for now)"""
    st.info("Customer mappings are currently the same as store mappings. Use the Store Mapping tab to manage customer mappings.")
    
def show_editable_item_mappings(mapping_utils, sources, db_service):
    """Show editable item mappings interface"""
    
    # Source selector
    selected_source = st.selectbox("Select Source", sources, key="item_source")
    
    try:
        # Get item mappings for selected source
        item_mappings = {}
        
        # Try to get mappings from database first
        try:
            with db_service.get_session() as session:
                mappings = session.query(db_service.ItemMapping).filter_by(source=selected_source).all()
                for mapping in mappings:
                    item_mappings[mapping.raw_item] = mapping.mapped_item
        except Exception:
            pass
        
        # If no database mappings, try Excel files
        if not item_mappings:
            item_mappings = mapping_utils._load_item_mappings_from_excel(selected_source)
        
        if item_mappings:
            st.write(f"**{selected_source.replace('_', ' ').title()} Item Mappings:**")
            
            # Add option to add new mapping
            with st.expander("➕ Add New Item Mapping"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    new_raw_item = st.text_input("Raw Item Number", key=f"new_item_raw_{selected_source}")
                with col2:
                    new_mapped_item = st.text_input("Mapped Item Number", key=f"new_item_mapped_{selected_source}")
                with col3:
                    if st.button("Add", key=f"add_item_{selected_source}"):
                        if new_raw_item and new_mapped_item:
                            success = db_service.save_item_mapping(selected_source, new_raw_item, new_mapped_item)
                            if success:
                                st.success("Item mapping added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add mapping")
            
            # Search functionality
            search_term = st.text_input("🔍 Search mappings", key=f"search_{selected_source}")
            
            # Filter mappings based on search
            filtered_mappings = item_mappings
            if search_term:
                filtered_mappings = {k: v for k, v in item_mappings.items() 
                                   if search_term.lower() in k.lower() or search_term.lower() in v.lower()}
            
            st.write(f"Showing {len(filtered_mappings)} of {len(item_mappings)} mappings")
            
            # Display editable table with pagination
            items_per_page = 20
            total_pages = (len(filtered_mappings) + items_per_page - 1) // items_per_page
            
            if total_pages > 1:
                page = st.selectbox("Page", range(1, total_pages + 1), key=f"page_{selected_source}") - 1
            else:
                page = 0
            
            start_idx = page * items_per_page
            end_idx = start_idx + items_per_page
            
            page_mappings = dict(list(filtered_mappings.items())[start_idx:end_idx])
            
            # Display editable mappings
            for idx, (raw_item, mapped_item) in enumerate(page_mappings.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text_input("Raw Item", value=raw_item, disabled=True, key=f"item_raw_{idx}_{page}_{selected_source}")
                with col2:
                    new_mapped_value = st.text_input("Mapped Item", value=mapped_item, key=f"item_mapped_{idx}_{page}_{selected_source}")
                with col3:
                    if st.button("🗑️", key=f"delete_item_{idx}_{page}_{selected_source}", help="Delete mapping"):
                        try:
                            with db_service.get_session() as session:
                                mapping_to_delete = session.query(db_service.ItemMapping).filter_by(
                                    source=selected_source, raw_item=raw_item
                                ).first()
                                if mapping_to_delete:
                                    session.delete(mapping_to_delete)
                                    session.commit()
                                st.success("Item mapping deleted!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete mapping: {e}")
                
                # Update mapping if changed
                if new_mapped_value != mapped_item:
                    success = db_service.save_item_mapping(selected_source, raw_item, new_mapped_value)
                    if success:
                        st.success(f"Updated mapping: {raw_item} → {new_mapped_value}")
                        st.rerun()
                    else:
                        st.error("Failed to update mapping")
        else:
            st.info(f"No item mappings found for {selected_source}")
            
    except Exception as e:
        st.error(f"Error loading item mappings: {e}")
                    else:
                        st.error("Failed to add store mapping")
                else:
                    st.error("Please fill in all fields")
        
        # Display existing mappings
        for source in ["wholefoods", "unfi_west", "unfi", "tkmaxx"]:
            mappings = db_service.get_store_mappings(source)
            if mappings:
                st.write(f"**{source.replace('_', ' ').title()} Mappings:**")
                df_mappings = pd.DataFrame(list(mappings.items()), columns=['Raw Name', 'Mapped Name'])
                st.dataframe(df_mappings)
    
    with tab2:
        st.subheader("Item Number Mappings")
        
        # Add new mapping
        with st.expander("Add New Item Mapping"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_source = st.selectbox("Source", ["wholefoods", "unfi_west", "unfi", "tkmaxx"], key="item_source")
            with col2:
                new_raw_item = st.text_input("Raw Item Number", key="item_raw")
            with col3:
                new_mapped_item = st.text_input("Mapped Item Number", key="item_mapped")
            
            if st.button("Add Item Mapping"):
                if new_raw_item and new_mapped_item:
                    success = db_service.save_item_mapping(new_source, new_raw_item, new_mapped_item)
                    if success:
                        st.success("Item mapping added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add item mapping")
                else:
                    st.error("Please fill in all fields")
        
        # Display existing mappings
        for source in ["wholefoods", "unfi_west", "unfi", "tkmaxx"]:
            mappings = db_service.get_item_mappings(source)
            if mappings:
                st.write(f"**{source.replace('_', ' ').title()} Item Mappings:**")
                df_mappings = pd.DataFrame(list(mappings.items()), columns=['Raw Item', 'Mapped Item'])
                st.dataframe(df_mappings)

if __name__ == "__main__":
    main()
