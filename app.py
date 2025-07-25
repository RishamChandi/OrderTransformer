import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
from parsers.wholefoods_parser import WholeFoodsParser
from parsers.unfi_west_parser import UNFIWestParser
from parsers.unfi_east_parser import UNFIEastParser
from parsers.unfi_parser import UNFIParser
from parsers.tkmaxx_parser import TKMaxxParser
from utils.xoro_template import XoroTemplate
from database.service import DatabaseService

def main():
    st.title("Order Transformer - Multiple Sources to Xoro CSV")
    st.write("Convert sales orders from different sources into standardized Xoro import CSV format")
    
    # Initialize database service
    db_service = DatabaseService()
    
    # Sidebar for configuration and navigation
    st.sidebar.header("Navigation")
    
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
    
    # Order source selection
    order_sources = {
        "Whole Foods": WholeFoodsParser(),
        "UNFI West": UNFIWestParser(),
        "UNFI East": UNFIEastParser(),
        "UNFI": UNFIParser(),
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
    """Manage store and item mappings"""
    
    st.header("Manage Mappings")
    
    tab1, tab2 = st.tabs(["Store Mappings", "Item Mappings"])
    
    with tab1:
        st.subheader("Store/Customer Name Mappings")
        
        # Add new mapping
        with st.expander("Add New Store Mapping"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_source = st.selectbox("Source", ["wholefoods", "unfi_west", "unfi", "tkmaxx"], key="store_source")
            with col2:
                new_raw_name = st.text_input("Raw Name", key="store_raw")
            with col3:
                new_mapped_name = st.text_input("Mapped Name", key="store_mapped")
            
            if st.button("Add Store Mapping"):
                if new_raw_name and new_mapped_name:
                    success = db_service.save_store_mapping(new_source, new_raw_name, new_mapped_name)
                    if success:
                        st.success("Store mapping added successfully!")
                        st.rerun()
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
