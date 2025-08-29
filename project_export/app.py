import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
import sys
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

# Health check for deployment
def health_check():
    """Health check endpoint for deployment readiness"""
    try:
        # Check database connectivity
        from sqlalchemy import text
        engine = get_database_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

# Add health check route handling
if st.query_params.get('health') == 'check':
    if health_check():
        st.json({"status": "healthy", "timestamp": datetime.now().isoformat()})
    else:
        st.json({"status": "unhealthy", "timestamp": datetime.now().isoformat()})
        st.stop()

def initialize_database_if_needed():
    """Initialize database tables if they don't exist with improved error handling"""
    try:
        from database.connection import get_current_environment
        from database.env_config import get_environment
        from cloud_config import get_deployment_environment
        
        env = get_current_environment()
        deployment_env = get_deployment_environment()
        
        # Enhanced logging for deployment troubleshooting
        print(f"🔍 Environment Detection: {env}")
        print(f"🔍 Deployment Platform: {deployment_env}")
        
        engine = get_database_engine()
        inspector = inspect(engine)
        
        # Check if tables exist
        tables_exist = inspector.get_table_names()
        if not tables_exist:
            print(f"📊 Initializing {env} database for first run...")
            Base.metadata.create_all(bind=engine)
            print(f"✅ Database initialized successfully in {env} environment!")
            # Only show Streamlit messages in non-deployment contexts
            if not os.getenv('REPLIT_DEPLOYMENT'):
                st.success(f"Database initialized successfully in {env} environment!")
        else:
            print(f"✅ Connected to {env} database ({len(tables_exist)} tables found)")
            # Only show Streamlit messages in non-deployment contexts
            if not os.getenv('REPLIT_DEPLOYMENT'):
                st.success(f"Connected to {env} database ({len(tables_exist)} tables found)")
            
    except Exception as e:
        error_msg = f"Database connection failed: {e}"
        print(f"❌ {error_msg}")
        
        # Enhanced error information for troubleshooting
        try:
            from database.connection import get_current_environment
            from database.env_config import get_database_url
            from cloud_config import get_deployment_environment
            
            env = get_current_environment()
            deployment_env = get_deployment_environment()
            db_url = get_database_url()
            
            print(f"🔧 Database Connection Troubleshooting:")
            print(f"   Environment: {env}")
            print(f"   Deployment: {deployment_env}")
            print(f"   URL Pattern: {db_url[:50] if db_url else 'Not found'}...")
            
            # For deployment environments, don't show Streamlit error UI
            if os.getenv('REPLIT_DEPLOYMENT'):
                # Log to console only for deployment
                print(f"❌ Deployment health check failed: {error_msg}")
                sys.exit(1)  # Exit with error code for deployment failure
            else:
                # Show detailed error UI for development
                st.error(f"Database connection failed: {e}")
                st.error("🔧 **Database Connection Troubleshooting:**")
                st.info(f"**Environment**: {env}")
                st.info(f"**Deployment Platform**: {deployment_env}")
                st.info(f"**Database URL Pattern**: {db_url[:50] if db_url else 'Not found'}...")
                
                if 'SSL connection has been closed' in str(e):
                    st.warning("**SSL Issue Detected**")
                    st.info("**Solutions**:")
                    st.info("1. Check DATABASE_URL environment variable")
                    st.info("2. Verify SSL configuration for your deployment platform")
                    
        except Exception as debug_error:
            print(f"❌ Error during troubleshooting: {debug_error}")
            if not os.getenv('REPLIT_DEPLOYMENT'):
                st.error("Database configuration error. Check environment variables.")



def main():
    # Initialize database if needed
    try:
        initialize_database_if_needed()
    except Exception as e:
        # Critical error during initialization
        if os.getenv('REPLIT_DEPLOYMENT'):
            print(f"❌ Critical initialization error in deployment: {e}")
            sys.exit(1)
        else:
            st.error(f"Critical initialization error: {e}")
            st.stop()
    
    # Modern header with better styling
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; text-align: center;">🔄 Order Transformer</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">Convert sales orders into standardized Xoro CSV format</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database service
    db_service = DatabaseService()
    
    # Two-dropdown navigation system
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Select Client/Source")
        sources = {
            "🌐 All Sources": "all",
            "🛒 Whole Foods": "wholefoods", 
            "📦 UNFI West": "unfi_west",
            "🏭 UNFI East": "unfi_east", 
            "📋 KEHE - SPS": "kehe",
            "🏬 TK Maxx": "tkmaxx"
        }
        
        selected_source_name = st.selectbox(
            "Choose your client:",
            list(sources.keys()),
            index=0,
            label_visibility="collapsed"
        )
        selected_source = sources[selected_source_name]
        source_display_name = selected_source_name.replace("🌐 ", "").replace("🛒 ", "").replace("📦 ", "").replace("🏭 ", "").replace("📋 ", "").replace("🏬 ", "")
    
    with col2:
        st.markdown("### ⚡ Select Action")
        actions = {
            "📝 Process Orders": "process",
            "📊 Order History": "history",
            "👁️ View Orders": "view",
            "⚙️ Manage Mappings": "mappings"
        }
        
        selected_action_name = st.selectbox(
            "Choose your action:",
            list(actions.keys()),
            index=0,
            label_visibility="collapsed"
        )
        action = actions[selected_action_name]
    
    # Show source-specific information card when a specific source is selected for processing
    if selected_source != "all" and action == "process":
        st.markdown("---")
        source_info = {
            "wholefoods": {
                "description": "HTML order files from Whole Foods stores",
                "formats": "HTML files from order pages", 
                "features": "Store mapping (51 locations), Item mapping (31 products), Expected delivery dates",
                "color": "#FF6B6B"
            },
            "unfi_west": {
                "description": "HTML purchase orders from UNFI West", 
                "formats": "HTML files with product tables",
                "features": "Cost-based pricing, Prod# mapping (71 items), Hardcoded KL-Richmond store",
                "color": "#4ECDC4"
            },
            "unfi_east": {
                "description": "PDF purchase orders from UNFI East",
                "formats": "PDF files with order details", 
                "features": "IOW customer mapping (15 codes), Vendor-to-store mapping",
                "color": "#45B7D1"
            },
            "kehe": {
                "description": "CSV files from KEHE - SPS system",
                "formats": "CSV with header (H) and line (D) records",
                "features": "Item mapping (88 products), Discount support, IDI-Richmond store",
                "color": "#96CEB4"
            },
            "tkmaxx": {
                "description": "CSV/Excel files from TK Maxx orders", 
                "formats": "CSV and Excel files",
                "features": "Basic order processing and item mapping",
                "color": "#FFEAA7"
            }
        }
        
        if selected_source in source_info:
            info = source_info[selected_source]
            st.markdown(f"""
            <div style="background-color: {info['color']}20; border-left: 4px solid {info['color']}; padding: 1rem; border-radius: 5px; margin: 1rem 0;">
                <h4 style="color: {info['color']}; margin: 0 0 0.5rem 0;">📋 {source_display_name} Information</h4>
                <p style="margin: 0.2rem 0;"><strong>📄 Description:</strong> {info['description']}</p>
                <p style="margin: 0.2rem 0;"><strong>📁 Formats:</strong> {info['formats']}</p>
                <p style="margin: 0.2rem 0;"><strong>⚡ Features:</strong> {info['features']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Database initialization in sidebar
    with st.sidebar:
        st.markdown("### ⚙️ System")
        if st.button("🔧 Initialize Database", help="First-time setup for cloud deployment"):
            try:
                # Re-initialize database tables
                engine = get_database_engine()
                Base.metadata.create_all(bind=engine)
                st.success("✅ Database initialized!")
            except Exception as e:
                st.error(f"❌ Database init failed: {e}")
    
    # Route to appropriate page based on action
    if action == "process":
        process_orders_page(db_service, selected_source, source_display_name)
    elif action == "history":
        conversion_history_page(db_service, selected_source)
    elif action == "view":
        processed_orders_page(db_service, selected_source)
    elif action == "mappings":
        manage_mappings_page(db_service, selected_source)

def process_orders_page(db_service: DatabaseService, selected_source: str = "all", selected_source_name: str = "All Sources"):
    """Main order processing page"""
    
    if selected_source != "all":
        # Source-specific processing page
        source_names = {
            "wholefoods": "Whole Foods",
            "unfi_west": "UNFI West", 
            "unfi_east": "UNFI East",
            "kehe": "KEHE - SPS",
            "tkmaxx": "TK Maxx"
        }
        clean_selected_name = selected_source_name.replace("🛒 ", "").replace("📦 ", "").replace("🏭 ", "").replace("📋 ", "").replace("🏬 ", "").replace("🌐 ", "")
        
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #667eea;">
            <h2 style="margin: 0; color: #667eea;">📝 Process {clean_selected_name} Orders</h2>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Ready to process {clean_selected_name} files</p>
        </div>
        """, unsafe_allow_html=True)
        
        selected_order_source = source_names[selected_source]
    else:
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #667eea;">
            <h2 style="margin: 0; color: #667eea;">📝 Process Orders</h2>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Choose your order source and upload files</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize mapping utils
        mapping_utils = MappingUtils()
        
        # Order source selection with modern styling
        order_sources = {
            "Whole Foods": WholeFoodsParser(),
            "UNFI West": UNFIWestParser(),
            "UNFI East": UNFIEastParser(mapping_utils),
            "KEHE - SPS": KEHEParser(),
            "TK Maxx": TKMaxxParser()
        }
        
        # Source already selected, use it directly
        selected_order_source = selected_source_name
    
    # Initialize mapping utils
    mapping_utils = MappingUtils()
    
    # Order source selection for parsers
    order_sources = {
        "Whole Foods": WholeFoodsParser(),
        "UNFI West": UNFIWestParser(),
        "UNFI East": UNFIEastParser(mapping_utils),
        "KEHE - SPS": KEHEParser(),
        "TK Maxx": TKMaxxParser()
    }
    
    # Determine accepted file types based on selected source
    clean_source_name = selected_order_source.replace("🌐 ", "").replace("🛒 ", "").replace("📦 ", "").replace("🏭 ", "").replace("📋 ", "").replace("🏬 ", "")
    
    if clean_source_name == "Whole Foods":
        accepted_types = ['html']
        help_text = "📄 Upload HTML files exported from Whole Foods orders"
        file_icon = "🌐"
    elif clean_source_name == "UNFI West":
        accepted_types = ['html']
        help_text = "📄 Upload HTML files from UNFI West purchase orders"
        file_icon = "🌐"
    elif clean_source_name == "UNFI East":
        accepted_types = ['pdf']
        help_text = "📋 Upload PDF files from UNFI East purchase orders"
        file_icon = "📄"
    elif clean_source_name == "KEHE - SPS":
        accepted_types = ['csv']
        help_text = "📊 Upload CSV files from KEHE - SPS system"
        file_icon = "📊"
    elif clean_source_name == "TK Maxx":
        accepted_types = ['csv', 'xlsx']
        help_text = "📊 Upload CSV or Excel files from TK Maxx orders"
        file_icon = "📊"
    else:
        accepted_types = ['html', 'csv', 'xlsx', 'pdf']
        help_text = f"📁 Upload order files for conversion"
        file_icon = "📁"
    
    st.markdown("---")
    
    # Enhanced file upload section
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; border: 2px dashed #667eea; text-align: center;">
        <h3 style="color: #667eea; margin: 0;">{file_icon} Upload Your Files</h3>
        <p style="color: #666; margin: 0.5rem 0;">{help_text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=accepted_types,
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        # Show uploaded files with better styling
        st.markdown("#### ✅ Files Ready for Processing")
        
        for i, file in enumerate(uploaded_files):
            file_size = len(file.getvalue()) / 1024  # KB
            st.markdown(f"""
            <div style="background-color: #e8f5e8; padding: 0.5rem 1rem; border-radius: 5px; margin: 0.2rem 0; border-left: 3px solid #28a745;">
                📁 <strong>{file.name}</strong> ({file_size:.1f} KB)
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Process files button with better styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Process Orders", type="primary", use_container_width=True):
                if clean_source_name == "All Sources":
                    st.error("⚠️ Please select a specific source before processing files. Auto-detection is not yet supported.")
                elif clean_source_name in order_sources:
                    process_orders(uploaded_files, order_sources[clean_source_name], clean_source_name, db_service)
                else:
                    st.error(f"⚠️ Unknown source: {clean_source_name}. Please select a valid source.")

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

def conversion_history_page(db_service: DatabaseService, selected_source: str = "all"):
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

def processed_orders_page(db_service: DatabaseService, selected_source: str = "all"):
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

def manage_mappings_page(db_service: DatabaseService, selected_source: str = "all"):
    """Enhanced mapping management page with file upload/download"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; text-align: center;">⚙️ Mapping Management Center</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">Complete mapping management by order processor</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Order processor selector
    processors = ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
    
    if selected_source != "all" and selected_source in processors:
        selected_processor = selected_source
        st.info(f"Managing mappings for: **{selected_processor.replace('_', ' ').title()}**")
    else:
        selected_processor = st.selectbox(
            "Select Order Processor:",
            processors,
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    if selected_processor:
        show_processor_mapping_management(selected_processor, db_service)

def show_processor_mapping_management(processor: str, db_service: DatabaseService):
    """Complete mapping management for a specific processor"""
    
    processor_display = processor.replace('_', ' ').title()
    
    # Processor overview card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;
                border-left: 5px solid #4f46e5;">
        <h2 style="color: white; margin: 0;">{processor_display} Mapping Management</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Manage Customer, Store (Xoro), and Item mappings for {processor_display} orders
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for the three mapping types
    tab1, tab2, tab3 = st.tabs([
        "👥 Customer Mapping", 
        "🏪 Store (Xoro) Mapping", 
        "📦 Item Mapping"
    ])
    
    with tab1:
        show_customer_mapping_manager(processor, db_service)
    
    with tab2:
        show_store_mapping_manager(processor, db_service)
        
    with tab3:
        show_item_mapping_manager(processor, db_service)

def show_customer_mapping_manager(processor: str, db_service: DatabaseService):
    """Customer mapping management with CSV support"""
    
    st.subheader("👥 Customer Mapping")
    st.write("Maps raw customer identifiers to Xoro customer names")
    
    mapping_file = f"mappings/{processor}/customer_mapping.csv"
    
    # Upload section
    with st.expander("📤 Upload Customer Mapping File"):
        uploaded_file = st.file_uploader(
            "Upload CSV file", 
            type=['csv'], 
            key=f"customer_upload_{processor}"
        )
        if uploaded_file and st.button("Save Customer Mapping", key=f"save_customer_{processor}"):
            save_uploaded_mapping(uploaded_file, mapping_file)
    
    # Display and edit current mappings
    display_csv_mapping(mapping_file, "Customer", ["Raw Customer ID", "Mapped Customer Name"], processor)

def show_store_mapping_manager(processor: str, db_service: DatabaseService):
    """Store (Xoro) mapping management with CSV support"""
    
    st.subheader("🏪 Store (Xoro) Mapping")
    st.write("Maps raw store identifiers to Xoro store names")
    
    mapping_file = f"mappings/{processor}/xoro_store_mapping.csv"
    
    # Upload section
    with st.expander("📤 Upload Store Mapping File"):
        uploaded_file = st.file_uploader(
            "Upload CSV file", 
            type=['csv'], 
            key=f"store_upload_{processor}"
        )
        if uploaded_file and st.button("Save Store Mapping", key=f"save_store_{processor}"):
            save_uploaded_mapping(uploaded_file, mapping_file)
    
    # Display and edit current mappings
    display_csv_mapping(mapping_file, "Store", ["Raw Store ID", "Xoro Store Name"], processor)

def show_item_mapping_manager(processor: str, db_service: DatabaseService):
    """Item mapping management with CSV support"""
    
    st.subheader("📦 Item Mapping")
    st.write("Maps raw item numbers to Xoro item numbers")
    
    mapping_file = f"mappings/{processor}/item_mapping.csv"
    
    # Upload section  
    with st.expander("📤 Upload Item Mapping File"):
        uploaded_file = st.file_uploader(
            "Upload CSV file", 
            type=['csv'], 
            key=f"item_upload_{processor}"
        )
        if uploaded_file and st.button("Save Item Mapping", key=f"save_item_{processor}"):
            save_uploaded_mapping(uploaded_file, mapping_file)
    
    # Display and edit current mappings
    if processor == 'kehe':
        # Special handling for KEHE - use the existing kehe_item_mapping.csv
        kehe_file = "mappings/kehe_item_mapping.csv"
        display_csv_mapping(kehe_file, "Item", ["KeHE Number", "Xoro Item Number", "Description"], processor)
    else:
        display_csv_mapping(mapping_file, "Item", ["Raw Item Number", "Mapped Item Number"], processor)

def display_csv_mapping(file_path: str, mapping_type: str, columns: list, processor: str):
    """Display and edit CSV mapping with download option"""
    
    import pandas as pd
    import os
    
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, dtype=str)
            
            st.success(f"✅ Loaded {len(df)} {mapping_type.lower()} mappings")
            
            # Download button
            csv_data = df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {mapping_type} Mappings",
                data=csv_data,
                file_name=f"{processor}_{mapping_type.lower()}_mapping.csv",
                mime="text/csv",
                key=f"download_{mapping_type}_{processor}"
            )
            
            # Search functionality
            search_term = st.text_input(
                f"🔍 Search {mapping_type.lower()} mappings", 
                key=f"search_{mapping_type}_{processor}"
            )
            
            # Filter mappings based on search
            if search_term:
                mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                filtered_df = df[mask]
            else:
                filtered_df = df
            
            st.write(f"Showing {len(filtered_df)} of {len(df)} mappings")
            
            # Pagination
            items_per_page = 20
            total_items = len(filtered_df)
            total_pages = (total_items + items_per_page - 1) // items_per_page
            
            if total_pages > 1:
                page = st.selectbox(
                    "Page", 
                    range(1, total_pages + 1), 
                    key=f"page_{mapping_type}_{processor}"
                ) - 1
            else:
                page = 0
            
            start_idx = page * items_per_page
            end_idx = min(start_idx + items_per_page, total_items)
            page_df = filtered_df.iloc[start_idx:end_idx]
            
            # Display mappings
            if len(page_df) > 0:
                st.dataframe(page_df, use_container_width=True)
                
                # Add new mapping
                with st.expander(f"➕ Add New {mapping_type} Mapping"):
                    add_new_mapping_form(file_path, columns, mapping_type, processor)
            else:
                st.info(f"No {mapping_type.lower()} mappings found")
                
        else:
            st.warning(f"⚠️ {mapping_type} mapping file not found: {file_path}")
            st.write("Create a new mapping file:")
            
            # Create new file
            if st.button(f"Create {mapping_type} Mapping File", key=f"create_{mapping_type}_{processor}"):
                create_new_mapping_file(file_path, columns)
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Error loading {mapping_type.lower()} mappings: {e}")

def add_new_mapping_form(file_path: str, columns: list, mapping_type: str, processor: str):
    """Form to add new mapping entries"""
    
    import pandas as pd
    
    with st.form(f"add_{mapping_type}_{processor}"):
        new_values = {}
        cols = st.columns(len(columns))
        
        for i, col_name in enumerate(columns):
            with cols[i]:
                new_values[col_name] = st.text_input(col_name, key=f"new_{col_name}_{processor}")
        
        submitted = st.form_submit_button("Add Mapping")
        
        if submitted and all(new_values.values()):
            try:
                df = pd.read_csv(file_path, dtype=str)
                new_row = pd.DataFrame([new_values])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                updated_df.to_csv(file_path, index=False)
                st.success(f"{mapping_type} mapping added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add mapping: {e}")

def save_uploaded_mapping(uploaded_file, file_path: str):
    """Save uploaded mapping file"""
    
    import os
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save the uploaded file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        st.success(f"✅ Mapping file saved to {file_path}")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Failed to save mapping file: {e}")

def create_new_mapping_file(file_path: str, columns: list):
    """Create a new empty mapping file"""
    
    import pandas as pd
    import os
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create empty DataFrame with specified columns
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)
        
        st.success(f"✅ Created new mapping file: {file_path}")
        
    except Exception as e:
        st.error(f"❌ Failed to create mapping file: {e}")

def show_editable_store_mappings(mapping_utils, sources, db_service):
    """Show editable store mappings interface"""
    
    # Source selector (excluding deprecated 'unfi')
    filtered_sources = [s for s in sources if s != 'unfi']
    selected_source = st.selectbox("Select Source", filtered_sources, key="store_source")
    
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
        
        # If no database mappings, try Excel files using database service
        if not store_mappings:
            store_mappings = db_service.get_store_mappings(selected_source)
        
        if store_mappings:
            if selected_source == 'unfi_east':
                st.write("**UNFI East Store Mappings:**")
                st.info("📋 **Vendor-to-Store Mapping**: These mappings determine which store is used for SaleStoreName and StoreName in the Xoro template based on the vendor number found in the PDF Order To field.")
                st.write("**Examples:**")
                st.write("- Vendor 85948 → PSS-NJ")
                st.write("- Vendor 85950 → K&L Richmond")
            else:
                source_display = selected_source.replace('_', ' ').title() if selected_source else "Unknown"
                st.write(f"**{source_display} Store Mappings:**")
            
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
    """Show editable customer mappings interface"""
    
    # Source selector (excluding deprecated 'unfi')
    filtered_sources = [s for s in sources if s != 'unfi']
    selected_source = st.selectbox("Select Source", filtered_sources, key="customer_source")
    
    # Special handling for different sources
    if selected_source == 'unfi_east':
        show_unfi_east_customer_mappings(db_service)
    elif selected_source == 'kehe':
        show_kehe_customer_mappings(db_service)
    else:
        source_display = selected_source.replace('_', ' ').title() if selected_source else "Unknown"
        st.info(f"Customer mappings for {source_display} are currently the same as store mappings. Use the Store Mapping tab to manage customer mappings.")

def show_unfi_east_customer_mappings(db_service):
    """Show UNFI East IOW customer mappings from Excel file"""
    
    try:
        import pandas as pd
        import os
        
        # Load IOW customer mapping from Excel file
        mapping_file = 'attached_assets/_xo10242_20250724095219_3675CE71_1754676225053.xlsx'
        customer_mappings = {}
        
        if os.path.exists(mapping_file):
            df = pd.read_excel(mapping_file)
            st.write("**UNFI East IOW Customer Mappings:**")
            st.write("These mappings are loaded from the Excel file and used by the parser to determine customer names from IOW location codes found in PDF Internal Ref Numbers.")
            
            # Display the mappings in a structured table format
            st.write("**Current IOW Customer Mappings:**")
            
            # Create a display DataFrame for better presentation
            display_data = []
            for _, row in df.iterrows():
                iow_code = str(row['UNFI East Customer']).strip()
                customer_name = str(row['XoroCompanyName']).strip()
                account_number = str(row['XoroCustomerAccountNumber']).strip()
                display_data.append({
                    'IOW Code': iow_code,
                    'Customer Name': customer_name,
                    'Account Number': account_number
                })
            
            # Display as a clean table
            display_df = pd.DataFrame(display_data)
            st.dataframe(display_df, use_container_width=True)
            
            st.info("💡 **How it works:**\n"
                   "- Parser extracts IOW code from Internal Ref Number (e.g., 'II-85948-H01' → 'II')\n"
                   "- IOW code is mapped to the corresponding Xoro customer name\n"
                   "- Example: 'II' → 'UNFI EAST IOWA CITY' (Account: 5150)")
            
            # Add section for mapping updates
            with st.expander("🔧 Update IOW Customer Mappings"):
                st.warning("⚠️ These mappings are currently loaded from the Excel file. To modify them:")
                st.write("1. Update the Excel file: `attached_assets/_xo10242_20250724095219_3675CE71_1754676225053.xlsx`")
                st.write("2. Restart the application to reload the mappings")
                st.write("3. Or contact the administrator to update the master mapping file")
                
                # Show current count
                st.success(f"✅ {len(display_data)} IOW customer mappings currently loaded")
        else:
            st.error("❌ IOW customer mapping file not found!")
            st.write("Expected file: `attached_assets/_xo10242_20250724095219_3675CE71_1754676225053.xlsx`")
            
    except Exception as e:
        st.error(f"Error loading UNFI East customer mappings: {e}")
        st.write("Using fallback mappings from parser...")

def show_kehe_customer_mappings(db_service):
    """Show KEHE customer mappings from CSV file"""
    
    try:
        import pandas as pd
        import os
        
        # Load KEHE customer mapping from CSV file
        mapping_file = 'mappings/kehe_customer_mapping.csv'
        
        if os.path.exists(mapping_file):
            # Force SPS Customer# to be read as string to preserve leading zeros
            df = pd.read_csv(mapping_file, dtype={'SPS Customer#': 'str'})
            st.write("**KEHE Customer Mappings:**")
            st.write("These mappings are loaded from the CSV file and used by the parser to determine customer names from Ship To Location numbers found in KEHE order files.")
            
            # Display the mappings in a structured table format
            st.write("**Current KEHE Customer Mappings:**")
            
            # Create a display DataFrame for better presentation
            display_data = []
            for _, row in df.iterrows():
                sps_customer = str(row['SPS Customer#']).strip()
                company_name = str(row['CompanyName']).strip()
                customer_id = str(row['CustomerId']).strip()
                account_number = str(row['AccountNumber']).strip()
                store_mapping = str(row['Store Mapping']).strip()
                display_data.append({
                    'Ship To Location': sps_customer,
                    'Customer Name': company_name,
                    'Customer ID': customer_id,
                    'Account Number': account_number,
                    'Store Mapping': store_mapping
                })
            
            # Display as a clean table
            display_df = pd.DataFrame(display_data)
            st.dataframe(display_df, use_container_width=True)
            
            st.info("💡 **How it works:**\n"
                   "- Parser extracts Ship To Location from KEHE order header (e.g., '0569813430019')\n"
                   "- Ship To Location is mapped to the corresponding Company Name\n"
                   "- Company Name is used as CustomerName in Xoro template (Column J)\n"
                   "- Example: '0569813430019' → 'KEHE DALLAS DC19'")
            
            # Add section for mapping updates
            with st.expander("🔧 Update KEHE Customer Mappings"):
                st.warning("⚠️ These mappings are currently loaded from the CSV file. To modify them:")
                st.write("1. Update the CSV file: `mappings/kehe_customer_mapping.csv`")
                st.write("2. Restart the application to reload the mappings")
                st.write("3. Or use the mapping management interface to add/edit mappings")
                
                # Show current count
                st.success(f"✅ {len(display_data)} KEHE customer mappings currently loaded")
                
                # Add new mapping interface
                st.write("**Add New KEHE Customer Mapping:**")
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                with col1:
                    new_ship_to = st.text_input("Ship To Location", key="new_kehe_ship_to")
                with col2:
                    new_company = st.text_input("Company Name", key="new_kehe_company")
                with col3:
                    new_customer_id = st.text_input("Customer ID", key="new_kehe_customer_id")
                with col4:
                    new_account = st.text_input("Account #", key="new_kehe_account")
                with col5:
                    new_store = st.text_input("Store Map", key="new_kehe_store")
                
                if st.button("Add KEHE Mapping", key="add_kehe_mapping"):
                    if new_ship_to and new_company:
                        try:
                            # Append to CSV file
                            new_row = pd.DataFrame([{
                                'SPS Customer#': new_ship_to,
                                'CustomerId': new_customer_id,
                                'AccountNumber': new_account,
                                'CompanyName': new_company,
                                'Store Mapping': new_store
                            }])
                            updated_df = pd.concat([df, new_row], ignore_index=True)
                            updated_df.to_csv(mapping_file, index=False)
                            st.success("KEHE customer mapping added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to add mapping: {e}")
                    else:
                        st.warning("Please provide at least Ship To Location and Company Name")
        else:
            st.error("❌ KEHE customer mapping file not found!")
            st.write("Expected file: `mappings/kehe_customer_mapping.csv`")
            
    except Exception as e:
        st.error(f"Error loading KEHE customer mappings: {e}")
        st.write("Using fallback mappings from parser...")
    
def show_editable_item_mappings(mapping_utils, sources, db_service):
    """Show editable item mappings interface"""
    
    # Source selector (excluding deprecated 'unfi')
    filtered_sources = [s for s in sources if s != 'unfi']
    selected_source = st.selectbox("Select Source", filtered_sources, key="item_source")
    
    try:
        # Special handling for KEHE - load from CSV file
        if selected_source == 'kehe':
            show_kehe_item_mappings()
            return
            
        # Get item mappings for other sources
        item_mappings = {}
        
        # Try to get mappings from database first
        try:
            with db_service.get_session() as session:
                mappings = session.query(db_service.ItemMapping).filter_by(source=selected_source).all()
                for mapping in mappings:
                    item_mappings[mapping.raw_item] = mapping.mapped_item
        except Exception:
            pass
        
        # If no database mappings, try Excel files using database service
        if not item_mappings:
            item_mappings = db_service.get_item_mappings(selected_source)
        
        if item_mappings:
            source_display = selected_source.replace('_', ' ').title() if selected_source else "Unknown"
            st.write(f"**{source_display} Item Mappings:**")
            
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

def show_kehe_item_mappings():
    """Show KEHE-specific item mappings from CSV file"""
    st.subheader("KEHE Item Mappings")
    
    try:
        import pandas as pd
        import os
        
        mapping_file = os.path.join('mappings', 'kehe_item_mapping.csv')
        if os.path.exists(mapping_file):
            # Load KEHE item mappings from CSV
            df = pd.read_csv(mapping_file, dtype={'KeHE Number': 'str'})
            
            st.info(f"✅ Loaded {len(df)} KEHE item mappings from CSV file")
            
            # Search functionality
            search_term = st.text_input("🔍 Search KEHE item mappings")
            
            # Filter mappings based on search
            if search_term:
                mask = df['KeHE Number'].str.contains(search_term, case=False, na=False) | \
                       df['ItemNumber'].str.contains(search_term, case=False, na=False) | \
                       df['Description'].str.contains(search_term, case=False, na=False)
                filtered_df = df[mask]
            else:
                filtered_df = df
            
            st.write(f"Showing {len(filtered_df)} of {len(df)} mappings")
            
            # Display mappings in a table format with pagination
            items_per_page = 20
            total_items = len(filtered_df)
            total_pages = (total_items + items_per_page - 1) // items_per_page
            
            if total_pages > 1:
                page = st.selectbox("Page", range(1, total_pages + 1)) - 1
            else:
                page = 0
            
            start_idx = page * items_per_page
            end_idx = min(start_idx + items_per_page, total_items)
            page_df = filtered_df.iloc[start_idx:end_idx]
            
            # Display mappings
            for index, row in page_df.iterrows():
                col1, col2, col3 = st.columns([2, 2, 3])
                
                with col1:
                    st.text_input("Raw Item (KeHE Number)", value=row['KeHE Number'], disabled=True, key=f"kehe_raw_{index}")
                
                with col2:
                    st.text_input("Mapped Item (Xoro Number)", value=row['ItemNumber'], disabled=True, key=f"kehe_mapped_{index}")
                
                with col3:
                    st.text(row['Description'][:50] + "..." if len(row['Description']) > 50 else row['Description'])
            
            st.text("Showing mappings for: KEHE (from CSV file)")
            st.info("📝 To modify KEHE item mappings, edit the CSV file: `mappings/kehe_item_mapping.csv`")
        else:
            st.warning("⚠️ KEHE item mapping CSV file not found")
            st.write("Expected file: `mappings/kehe_item_mapping.csv`")
            
    except Exception as e:
        st.error(f"❌ Error loading KEHE item mappings: {e}")

if __name__ == "__main__":
    main()
