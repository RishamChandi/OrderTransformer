import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
import sys

# Configure Streamlit for better deployment
st.set_page_config(
    page_title="Order Transformer",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    # Modern responsive header (not fixed)
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .header-responsive {
            padding: 1rem !important;
        }
        .header-responsive h1 {
            font-size: 2rem !important;
        }
        .header-responsive .stats-container {
            flex-direction: column !important;
            gap: 0.5rem !important;
        }
    }
    @media (max-width: 480px) {
        .header-responsive h1 {
            font-size: 1.5rem !important;
        }
        .header-responsive .stats-container {
            flex-wrap: wrap !important;
        }
    }
    </style>
    <div class="header-responsive" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 0.5rem;">
                    🔄 Order Transformer
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem; font-weight: 400;">
                    Convert sales orders into standardized Xoro CSV format
                </p>
            </div>
            <div class="stats-container" style="display: flex; gap: 1rem; align-items: center; color: white; font-size: 0.9rem;">
                <div style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 25px; backdrop-filter: blur(10px);">
                    📊 Multi-Client
            </div>
                <div style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 25px; backdrop-filter: blur(10px);">
                    🔄 Real-time
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 25px; backdrop-filter: blur(10px);">
                    📈 Analytics
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database service
    db_service = DatabaseService()
    
    # Sidebar navigation system
    with st.sidebar:
        st.markdown("## 🎯 Client/Source")
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
            index=0
        )
        selected_source = sources[selected_source_name]
        source_display_name = selected_source_name.replace("🌐 ", "").replace("🛒 ", "").replace("📦 ", "").replace("🏭 ", "").replace("📋 ", "").replace("🏬 ", "")
        
        st.markdown("---")
        
        st.markdown("## ⚡ Action")
        actions = {
            "📝 Process Orders": "process",
            "📊 Order History": "history",
            "👁️ View Orders": "view",
            "⚙️ Manage Mappings": "mappings",
            "📋 Mapping Documentation": "mapping_docs"
        }
        
        selected_action_name = st.selectbox(
            "Choose your action:",
            list(actions.keys()),
            index=0
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
    elif action == "mapping_docs":
        mapping_documentation_page(db_service, selected_source)

def process_orders_page(db_service: DatabaseService, selected_source: str = "all", selected_source_name: str = "All Sources"):
    """Main order processing page with optimized screen usage"""
    
    # Enhanced container for better space utilization
    st.markdown("""
    <style>
    .main-content-container {
        max-width: 1600px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .content-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 2rem;
        margin-top: 1rem;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .card-icon {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
    }
    
    .card-description {
        color: #6c757d;
        font-size: 1rem;
        line-height: 1.6;
        margin: 0;
    }
    
    @media (min-width: 1200px) {
        .content-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (min-width: 1600px) {
        .content-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced content container
    st.markdown('<div class="main-content-container">', unsafe_allow_html=True)
    
    if selected_source != "all":
        # Source-specific processing page with enhanced layout
        source_names = {
            "wholefoods": "Whole Foods",
            "unfi_west": "UNFI West", 
            "unfi_east": "UNFI East",
            "kehe": "KEHE - SPS",
            "tkmaxx": "TK Maxx"
        }
        clean_selected_name = selected_source_name.replace("🛒 ", "").replace("📦 ", "").replace("🏭 ", "").replace("📋 ", "").replace("🏬 ", "").replace("🌐 ", "")
        
        # Enhanced header for specific source
        st.markdown(f"""
        <div class="feature-card">
            <div class="card-header">
                <div class="card-icon">🎯</div>
                <div>
                    <h2 class="card-title">Process {clean_selected_name} Orders</h2>
                    <p class="card-description">Ready to process {clean_selected_name} files with advanced parsing</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        selected_order_source = source_names[selected_source]
    else:
        # All sources overview with enhanced layout
        st.markdown("""
        <div class="feature-card">
            <div class="card-header">
                <div class="card-icon">🌐</div>
                <div>
                    <h2 class="card-title">All Sources Overview</h2>
                    <p class="card-description">Choose your order source and upload files for processing</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced overview cards with better spacing
        st.markdown('<div class="content-grid">', unsafe_allow_html=True)
        
        # Source cards
        st.markdown("""
        <div class="feature-card">
            <div class="card-header">
                <div class="card-icon">🛒</div>
                <div>
                    <h3 class="card-title">Whole Foods</h3>
                    <p class="card-description">HTML order processing with advanced parsing</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="card-header">
                <div class="card-icon">📦</div>
                <div>
                    <h3 class="card-title">UNFI West</h3>
                    <p class="card-description">HTML order processing with mapping integration</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="card-header">
                <div class="card-icon">🏭</div>
                <div>
                    <h3 class="card-title">UNFI East</h3>
                    <p class="card-description">PDF order processing with OCR capabilities</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="card-header">
                <div class="card-icon">📋</div>
                <div>
                    <h3 class="card-title">KEHE - SPS</h3>
                    <p class="card-description">CSV order processing with data validation</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="card-header">
                <div class="card-icon">🏬</div>
                <div>
                    <h3 class="card-title">TK Maxx</h3>
                    <p class="card-description">Multi-format order processing (CSV/Excel)</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Initialize mapping utils
        mapping_utils = MappingUtils()
        
        # Order source selection with modern styling
        order_sources = {
            "Whole Foods": WholeFoodsParser(db_service),
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
        "Whole Foods": WholeFoodsParser(db_service),
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
    
    # Close main content container
    st.markdown('</div>', unsafe_allow_html=True)

def manage_mappings_page(db_service: DatabaseService, selected_source: str = "all"):
    """Enhanced mapping management page with optimized screen usage"""
    
    # Enhanced content container
    st.markdown('<div class="main-content-container">', unsafe_allow_html=True)
    
    # Enhanced header for mapping management
    st.markdown("""
    <div class="feature-card">
        <div class="card-header">
            <div class="card-icon">⚙️</div>
            <div>
                <h2 class="card-title">Mapping Management Center</h2>
                <p class="card-description">Complete mapping management by order processor with advanced features</p>
            </div>
        </div>
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
    
    # Close main content container
    st.markdown('</div>', unsafe_allow_html=True)

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

def show_enhanced_mapping_interface(processor: str, db_service: DatabaseService, mapping_type: str):
    """Enhanced mapping management interface with all features"""
    
    # Action buttons row
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        if st.button("📥 Download Template", key=f"{mapping_type}_download_template_{processor}"):
            download_mapping_template(processor, mapping_type)
    
    with col2:
        if st.button("📊 Download Current", key=f"{mapping_type}_download_current_{processor}"):
            download_current_mappings(db_service, processor, mapping_type)
    
    with col3:
        if st.button("📤 Upload Mapping", key=f"{mapping_type}_upload_{processor}"):
            st.session_state[f'show_{mapping_type}_upload_{processor}'] = True
            st.rerun()
    
    with col4:
        if st.button("🗑️ Delete Mapping", key=f"{mapping_type}_delete_{processor}"):
            st.session_state[f'show_{mapping_type}_delete_{processor}'] = True
            st.rerun()
    
    with col5:
        if st.button("➕ Add New", key=f"{mapping_type}_add_new_{processor}"):
            st.session_state[f'show_{mapping_type}_add_{processor}'] = True
            st.rerun()
    
    with col6:
        if st.button("📝 Bulk Editor", key=f"{mapping_type}_bulk_editor_{processor}"):
            st.session_state[f'show_{mapping_type}_bulk_{processor}'] = True
            st.rerun()
    
    with col7:
        if st.button("📋 Row by Row", key=f"{mapping_type}_row_by_row_{processor}"):
            st.session_state[f'show_{mapping_type}_row_by_row_{processor}'] = True
            st.rerun()
    
    st.markdown("---")
    
    # Show upload result if available
    if st.session_state.get(f'upload_result_{mapping_type}_{processor}'):
        upload_result = st.session_state[f'upload_result_{mapping_type}_{processor}']
        
        if upload_result['success']:
            st.success(f"✅ Successfully uploaded {upload_result['inserted']} new {mapping_type} mappings")
            if upload_result['updated'] > 0:
                st.info(f"Updated {upload_result['updated']} existing mappings")
            if upload_result['skipped_rows']:
                st.warning(f"Skipped {len(upload_result['skipped_rows'])} rows due to missing required data:")
                for skip_reason in upload_result['skipped_rows'][:5]:  # Show first 5 skipped rows
                    st.write(f"- {skip_reason}")
                if len(upload_result['skipped_rows']) > 5:
                    st.write(f"- ... and {len(upload_result['skipped_rows']) - 5} more")
        else:
            st.error(f"❌ Upload failed: {upload_result['error']}")
        
        # Clear the result from session state
        del st.session_state[f'upload_result_{mapping_type}_{processor}']
    
    # Show appropriate interface based on selection
    if st.session_state.get(f'show_{mapping_type}_upload_{processor}', False):
        show_upload_mapping_form(db_service, processor, mapping_type)
    elif st.session_state.get(f'show_{mapping_type}_delete_{processor}', False):
        show_delete_mapping_interface(db_service, processor, mapping_type)
    elif st.session_state.get(f'show_{mapping_type}_add_{processor}', False):
        show_add_new_mapping_form(db_service, processor, mapping_type)
    elif st.session_state.get(f'show_{mapping_type}_bulk_{processor}', False):
        show_bulk_editor_interface(db_service, processor, mapping_type)
    elif st.session_state.get(f'show_{mapping_type}_row_by_row_{processor}', False):
        show_row_by_row_interface(db_service, processor, mapping_type)
    else:
        # Default view - show current mappings
        show_current_mappings_view(db_service, processor, mapping_type)

def show_customer_mapping_manager(processor: str, db_service: DatabaseService):
    """Enhanced Customer mapping management with comprehensive features"""
    
    st.subheader("👥 Customer Mapping")
    st.write("Maps raw customer identifiers to Xoro customer names")
    
    # Enhanced mapping management interface
    show_enhanced_mapping_interface(processor, db_service, "customer")

def show_store_mapping_manager(processor: str, db_service: DatabaseService):
    """Enhanced Store (Xoro) mapping management with comprehensive features"""
    
    st.subheader("🏪 Store (Xoro) Mapping")
    st.write("Maps raw store identifiers to Xoro store names")
    
    # Enhanced mapping management interface
    show_enhanced_mapping_interface(processor, db_service, "store")

def show_item_mapping_manager(processor: str, db_service: DatabaseService):
    """Enhanced Item Mapping Management with comprehensive features"""
    
    st.subheader("📦 Item Mapping")
    st.write("Maps raw item identifiers to Xoro item numbers and descriptions")
    
    # Enhanced mapping management interface
    show_enhanced_mapping_interface(processor, db_service, "item")

# Enhanced Mapping Management Functions

def download_mapping_template(processor: str, mapping_type: str):
    """Download CSV template for mapping type"""
    import pandas as pd
    
    if mapping_type == "customer":
        template_data = {
            'Source': [processor],
            'Raw Customer ID': ['EXAMPLE_CUSTOMER_ID'],
            'Mapped Customer Name': ['EXAMPLE_MAPPED_NAME'],
            'Customer Type': ['distributor'],
            'Priority': [100],
            'Active': [True],
            'Notes': ['Example mapping']
        }
        filename = f"{processor}_customer_mapping_template.csv"
    elif mapping_type == "store":
        template_data = {
            'Source': [processor],
            'Raw Store ID': ['EXAMPLE_STORE_ID'],
            'Mapped Store Name': ['EXAMPLE_MAPPED_STORE'],
            'Store Type': ['distributor'],
            'Priority': [100],
            'Active': [True],
            'Notes': ['Example store mapping']
        }
        filename = f"{processor}_store_mapping_template.csv"
    elif mapping_type == "item":
        template_data = {
            'Source': [processor],
            'Raw Item': ['EXAMPLE_ITEM_ID'],
            'Mapped Item': ['EXAMPLE_MAPPED_ITEM'],
            'Item Description': ['Example item description'],
            'Priority': [100],
            'Active': [True],
            'Notes': ['Example item mapping']
        }
        filename = f"{processor}_item_mapping_template.csv"
    
    df = pd.DataFrame(template_data)
    csv = df.to_csv(index=False)
    
    st.download_button(
        "💾 Download Template",
        csv,
        filename,
        "text/csv",
        key=f"download_template_{mapping_type}_{processor}"
    )

def download_current_mappings(db_service: DatabaseService, processor: str, mapping_type: str):
    """Download current mappings from database"""
    import pandas as pd
    
    try:
        with db_service.get_session() as session:
            if mapping_type == "customer":
                # Use StoreMapping table for customer mappings with store_type = "customer"
                mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type == "customer").all()
                data = []
                for m in mappings:
                    # Use StoreMapping field names for customer mappings
                    data.append({
                        'Source': m.source,
                        'Raw Customer ID': m.raw_store_id,
                        'Mapped Customer Name': m.mapped_store_name,
                        'Customer Type': m.store_type,
                        'Priority': m.priority,
                        'Active': m.active,
                        'Notes': m.notes or ''
                    })
            elif mapping_type == "store":
                mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type.in_(["store", "retail", "wholesaler"])).all()
                data = []
                for m in mappings:
                    data.append({
                        'Source': m.source,
                        'Raw Store ID': m.raw_store_id,
                        'Mapped Store Name': m.mapped_store_name,
                        'Store Type': m.store_type,
                        'Priority': m.priority,
                        'Active': m.active,
                        'Notes': m.notes or ''
                    })
            elif mapping_type == "item":
                mappings = session.query(db_service.ItemMapping).filter_by(source=processor).all()
                data = []
                for m in mappings:
                    data.append({
                        'Source': m.source,
                        'Raw Item': m.raw_item,
                        'Mapped Item': m.mapped_item,
                        'Item Description': getattr(m, 'mapped_description', ''),
                        'Priority': getattr(m, 'priority', 100),
                        'Active': getattr(m, 'active', True),
                        'Notes': getattr(m, 'notes', '')
                    })
            
            if data:
                df = pd.DataFrame(data)
                csv = df.to_csv(index=False)
                filename = f"{processor}_{mapping_type}_mappings_{pd.Timestamp.now().strftime('%Y%m%d')}.csv"
                
                st.download_button(
                    "💾 Download Current Mappings",
                    csv,
                    filename,
                    "text/csv",
                    key=f"download_current_{mapping_type}_{processor}"
                )
                st.success(f"✅ Ready to download {len(data)} {mapping_type} mappings")
            else:
                st.warning(f"⚠️ No {mapping_type} mappings found")
                
    except Exception as e:
        st.error(f"❌ Download failed: {e}")

def show_upload_mapping_form(db_service: DatabaseService, processor: str, mapping_type: str):
    """Show upload form for mappings"""
    import pandas as pd
    
    with st.expander("📤 Upload Mapping File", expanded=True):
        st.write(f"Upload a CSV file with {mapping_type} mapping data:")
        
        # Show template format
        if mapping_type == "customer":
            st.code("""Source,Raw Customer ID,Mapped Customer Name,Customer Type,Priority,Active,Notes
kehe,CUST001,Example Customer,distributor,100,True,Example mapping""")
        elif mapping_type == "store":
            st.code("""Source,Raw Store ID,Mapped Store Name,Store Type,Priority,Active,Notes
kehe,STORE001,Example Store,distributor,100,True,Example store mapping""")
        elif mapping_type == "item":
            st.code("""Source,Raw Item,Mapped Item,Item Description,Priority,Active,Notes
kehe,ITEM001,MAPPED001,Example item,100,True,Example item mapping""")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            key=f"upload_{mapping_type}_{processor}"
        )
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("**File Preview:**")
                st.dataframe(df.head())
                
                # Debug: Show available columns
                st.write("**Available Columns:**")
                st.write(list(df.columns))
                
                # Check if we have the required columns for different mapping types
                if mapping_type == "item":
                    expected_columns = ['RawKeyValue', 'MappedItemNumber', 'MappedDescription']
                    st.info("**Expected columns for item mapping:** RawKeyValue, MappedItemNumber, MappedDescription")
                elif mapping_type == "customer":
                    expected_columns = ['Raw Customer ID', 'RawCustomerID', 'Mapped Customer Name', 'MappedCustomerName', 'Customer Type', 'CustomerType']
                    st.info("**Expected columns for customer mapping:** Raw Customer ID (or RawCustomerID), Mapped Customer Name (or MappedCustomerName), Customer Type (or CustomerType)")
                elif mapping_type == "store":
                    expected_columns = ['Raw Store ID', 'RawStoreID', 'Mapped Store Name', 'MappedStoreName', 'Store Type', 'StoreType']
                    st.info("**Expected columns for store mapping:** Raw Store ID (or RawStoreID), Mapped Store Name (or MappedStoreName), Store Type (or StoreType)")
                
                # Check for missing columns - improved logic to handle both formats
                missing_columns = []
                if mapping_type == "customer":
                    # Check if we have at least one format of each required field
                    has_raw_id = any(col in df.columns for col in ['Raw Customer ID', 'RawCustomerID', 'Raw Customer', 'Customer ID', 'Raw ID'])
                    has_mapped_name = any(col in df.columns for col in ['Mapped Customer Name', 'MappedCustomerName', 'Customer Name', 'Mapped Name', 'Name'])
                    has_type = any(col in df.columns for col in ['Customer Type', 'CustomerType', 'Type'])
                    
                    if not has_raw_id:
                        missing_columns.append('Raw Customer ID (or RawCustomerID)')
                    if not has_mapped_name:
                        missing_columns.append('Mapped Customer Name (or MappedCustomerName)')
                    if not has_type:
                        missing_columns.append('Customer Type (or CustomerType)')
                        
                elif mapping_type == "store":
                    # Check if we have at least one format of each required field
                    has_raw_id = any(col in df.columns for col in ['Raw Store ID', 'RawStoreID', 'Raw Store', 'Store ID', 'Raw ID'])
                    has_mapped_name = any(col in df.columns for col in ['Mapped Store Name', 'MappedStoreName', 'Store Name', 'Mapped Name', 'Name'])
                    has_type = any(col in df.columns for col in ['Store Type', 'StoreType', 'Type'])
                    
                    if not has_raw_id:
                        missing_columns.append('Raw Store ID (or RawStoreID)')
                    if not has_mapped_name:
                        missing_columns.append('Mapped Store Name (or MappedStoreName)')
                    if not has_type:
                        missing_columns.append('Store Type (or StoreType)')
                        
                elif mapping_type == "item":
                    # Check if we have at least one format of each required field
                    has_raw_item = any(col in df.columns for col in ['Raw Item', 'RawKeyValue', 'Raw Item Number'])
                    has_mapped_item = any(col in df.columns for col in ['Mapped Item', 'MappedItemNumber', 'Mapped Item Number'])
                    has_description = any(col in df.columns for col in ['Item Description', 'MappedDescription', 'Description'])
                    
                    if not has_raw_item:
                        missing_columns.append('Raw Item (or RawKeyValue)')
                    if not has_mapped_item:
                        missing_columns.append('Mapped Item (or MappedItemNumber)')
                    if not has_description:
                        missing_columns.append('Item Description (or MappedDescription)')
                
                if missing_columns:
                    st.warning(f"⚠️ Missing required columns: {missing_columns}")
                    st.info("The upload will attempt to map available columns to the required fields.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Upload Mappings", key=f"confirm_upload_{mapping_type}_{processor}"):
                        with st.spinner("Uploading mappings..."):
                            try:
                                # Store upload result in session state instead of showing immediately
                                upload_result = upload_mappings_to_database_silent(df, db_service, processor, mapping_type)
                                st.session_state[f'upload_result_{mapping_type}_{processor}'] = upload_result
                                st.session_state[f'show_{mapping_type}_upload_{processor}'] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Upload failed: {str(e)}")
                                st.exception(e)
                
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_upload_{mapping_type}_{processor}"):
                        st.session_state[f'show_{mapping_type}_upload_{processor}'] = False
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

def show_delete_mapping_interface(db_service: DatabaseService, processor: str, mapping_type: str):
    """Show delete mapping interface"""
    with st.expander("🗑️ Delete Mappings", expanded=True):
        st.warning("⚠️ Select mappings to delete")
        
        # Load current mappings
        try:
            with db_service.get_session() as session:
                if mapping_type == "customer":
                    # Check if CustomerMapping table exists, use fallback if not
                    try:
                        # Try to query the CustomerMapping table to see if it exists
                        with db_service.get_session() as test_session:
                            test_session.query(db_service.CustomerMapping).first()
                        # If we get here, the table exists, use CustomerMapping
                        mappings = session.query(db_service.CustomerMapping).filter_by(source=processor).all()
                    except Exception:
                        # CustomerMapping table doesn't exist, use StoreMapping fallback
                        mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type == "customer").all()
                elif mapping_type == "store":
                    # Store mappings: filter by store_type that indicates store entities  
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type.in_(["store", "retail", "wholesaler"])).all()
                elif mapping_type == "item":
                    mappings = session.query(db_service.ItemMapping).filter_by(source=processor).all()
                
                if mappings:
                    # Initialize session state for selected mappings if not exists
                    if f'selected_mappings_{mapping_type}_{processor}' not in st.session_state:
                        st.session_state[f'selected_mappings_{mapping_type}_{processor}'] = []
                    
                    # Create selection interface with checkboxes
                    st.write("**Select mappings to delete:**")
                    
                    # Add select all/none buttons
                    col_select_all, col_select_none, col_space = st.columns([1, 1, 4])
                    with col_select_all:
                        if st.button("Select All", key=f"select_all_{mapping_type}_{processor}"):
                            st.session_state[f'selected_mappings_{mapping_type}_{processor}'] = [m.id for m in mappings]
                            st.rerun()
                    with col_select_none:
                        if st.button("Select None", key=f"select_none_{mapping_type}_{processor}"):
                            st.session_state[f'selected_mappings_{mapping_type}_{processor}'] = []
                            st.rerun()
                    
                    # Display mappings with checkboxes
                    selected_count = 0
                    for i, m in enumerate(mappings):
                        col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 2, 1])
                        
                        with col1:
                            is_selected = m.id in st.session_state[f'selected_mappings_{mapping_type}_{processor}']
                            checkbox_value = st.checkbox("", value=is_selected, key=f"select_{mapping_type}_{processor}_{m.id}")
                            
                            # Update selection state based on checkbox change
                            if checkbox_value and m.id not in st.session_state[f'selected_mappings_{mapping_type}_{processor}']:
                                st.session_state[f'selected_mappings_{mapping_type}_{processor}'].append(m.id)
                            elif not checkbox_value and m.id in st.session_state[f'selected_mappings_{mapping_type}_{processor}']:
                                st.session_state[f'selected_mappings_{mapping_type}_{processor}'].remove(m.id)
                        
                        with col2:
                            if mapping_type == "customer":
                                # Use StoreMapping field names for customer mappings
                                st.write(f"**{m.raw_store_id}**")
                            elif mapping_type == "store":
                                st.write(f"**{m.raw_store_id}**")
                            else:  # item
                                st.write(f"**{m.raw_item}**")
                        
                        with col3:
                            if mapping_type == "customer":
                                # Use StoreMapping field names for customer mappings
                                st.write(f"{m.mapped_store_name}")
                            elif mapping_type == "store":
                                st.write(f"{m.mapped_store_name}")
                            else:  # item
                                st.write(f"{m.mapped_item}")
                        
                        with col4:
                            if mapping_type == "customer":
                                # Use StoreMapping field names for customer mappings
                                st.write(f"{m.store_type}")
                            elif mapping_type == "store":
                                st.write(f"{m.store_type}")
                            else:  # item
                                st.write("Item")
                        
                        with col5:
                            status = "✅" if getattr(m, 'active', True) else "❌"
                            st.write(status)
                        
                        if m.id in st.session_state[f'selected_mappings_{mapping_type}_{processor}']:
                            selected_count += 1
                    
                    # Calculate current selection count
                    current_selected = len(st.session_state[f'selected_mappings_{mapping_type}_{processor}'])
                    st.write(f"**Selected: {current_selected} mapping(s)**")
                    
                    # Add refresh button to update selection count
                    if st.button("🔄 Refresh Selection", key=f"refresh_selection_{mapping_type}_{processor}"):
                        st.rerun()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        delete_disabled = len(st.session_state[f'selected_mappings_{mapping_type}_{processor}']) == 0
                        if st.button("🗑️ Delete Selected", key=f"delete_selected_{mapping_type}_{processor}", disabled=delete_disabled):
                            if st.session_state[f'selected_mappings_{mapping_type}_{processor}']:
                                st.session_state[f'confirm_delete_{mapping_type}_{processor}'] = True
                                st.rerun()
                    
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_delete_{mapping_type}_{processor}"):
                            st.session_state[f'show_{mapping_type}_delete_{processor}'] = False
                            st.rerun()
                else:
                    st.info(f"No {mapping_type} mappings found")
                    
        except Exception as e:
            st.error(f"❌ Error loading mappings: {e}")

    # Handle delete confirmation
    if st.session_state.get(f'confirm_delete_{mapping_type}_{processor}', False):
        show_delete_confirmation(db_service, processor, mapping_type)

def show_delete_confirmation(db_service: DatabaseService, processor: str, mapping_type: str):
    """Show delete confirmation dialog"""
    selected_ids = st.session_state.get(f'selected_mappings_{mapping_type}_{processor}', [])
    
    if not selected_ids:
        st.error("No mappings selected for deletion")
        st.session_state[f'confirm_delete_{mapping_type}_{processor}'] = False
        return
    
    st.warning(f"⚠️ Are you sure you want to delete {len(selected_ids)} mapping(s)?")
    
    # Show what will be deleted
    try:
        with db_service.get_session() as session:
            if mapping_type == "item":
                mappings = session.query(db_service.ItemMapping).filter(db_service.ItemMapping.id.in_(selected_ids)).all()
            else:
                mappings = session.query(db_service.StoreMapping).filter(db_service.StoreMapping.id.in_(selected_ids)).all()
            
            st.write("**Mappings to be deleted:**")
            for m in mappings:
                if mapping_type == "item":
                    st.write(f"- {m.raw_item} → {m.mapped_item}")
                else:
                    if mapping_type == "customer":
                        st.write(f"- {m.raw_store_id} → {m.mapped_store_name}")
                    else:  # store
                        st.write(f"- {m.raw_store_id} → {m.mapped_store_name}")
    
    except Exception as e:
        st.error(f"❌ Error loading mapping details: {e}")
        return
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Confirm Delete", key=f"confirm_delete_yes_{mapping_type}_{processor}", type="primary"):
            delete_selected_mappings(db_service, processor, mapping_type, selected_ids)
            st.session_state[f'confirm_delete_{mapping_type}_{processor}'] = False
            st.session_state[f'selected_mappings_{mapping_type}_{processor}'] = []
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key=f"confirm_delete_no_{mapping_type}_{processor}"):
            st.session_state[f'confirm_delete_{mapping_type}_{processor}'] = False
            st.rerun()

def delete_selected_mappings(db_service: DatabaseService, processor: str, mapping_type: str, selected_ids: list):
    """Delete selected mappings from database"""
    try:
        with db_service.get_session() as session:
            deleted_count = 0
            for mapping_id in selected_ids:
                if mapping_type == "item":
                    mapping = session.query(db_service.ItemMapping).filter_by(id=mapping_id).first()
                else:
                    mapping = session.query(db_service.StoreMapping).filter_by(id=mapping_id).first()
                
                if mapping:
                    session.delete(mapping)
                    deleted_count += 1
            
            session.commit()
            st.success(f"✅ Successfully deleted {deleted_count} mapping(s)!")
            
    except Exception as e:
        st.error(f"❌ Failed to delete mappings: {e}")

def show_add_new_mapping_form(db_service: DatabaseService, processor: str, mapping_type: str):
    """Show form to add new mapping"""
    with st.expander("➕ Add New Mapping", expanded=True):
        st.write(f"Add a new {mapping_type} mapping:")
        
        with st.form(f"add_{mapping_type}_form_{processor}"):
            if mapping_type == "customer":
                raw_name = st.text_input("Raw Customer ID", key=f"raw_customer_{processor}")
                mapped_name = st.text_input("Mapped Customer Name", key=f"mapped_customer_{processor}")
                customer_type = st.selectbox("Customer Type", ["distributor", "retailer", "wholesaler"], key=f"customer_type_{processor}")
            elif mapping_type == "store":
                raw_name = st.text_input("Raw Store ID", key=f"raw_store_{processor}")
                mapped_name = st.text_input("Mapped Store Name", key=f"mapped_store_{processor}")
                store_type = st.selectbox("Store Type", ["distributor", "retailer", "wholesaler"], key=f"store_type_{processor}")
            elif mapping_type == "item":
                raw_item = st.text_input("Raw Item", key=f"raw_item_{processor}")
                mapped_item = st.text_input("Mapped Item", key=f"mapped_item_{processor}")
                item_description = st.text_input("Item Description", key=f"item_description_{processor}")
            
            priority = st.number_input("Priority", min_value=0, max_value=1000, value=100, key=f"priority_{mapping_type}_{processor}")
            active = st.checkbox("Active", value=True, key=f"active_{mapping_type}_{processor}")
            notes = st.text_area("Notes", key=f"notes_{mapping_type}_{processor}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Add Mapping"):
                    add_new_mapping_to_database(db_service, processor, mapping_type, locals())
                    st.session_state[f'show_{mapping_type}_add_{processor}'] = False
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state[f'show_{mapping_type}_add_{processor}'] = False
                    st.rerun()

def show_bulk_editor_interface(db_service: DatabaseService, processor: str, mapping_type: str):
    """Show bulk editor interface"""
    with st.expander("📝 Bulk Editor", expanded=True):
        st.write(f"Edit multiple {mapping_type} mappings at once:")
        
        # Load current mappings
        try:
            with db_service.get_session() as session:
                if mapping_type == "customer":
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type.in_(["customer", "store", "distributor"])).all()
                elif mapping_type == "store":
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type.in_(["store", "retail", "wholesaler"])).all()
                else:
                    mappings = session.query(db_service.ItemMapping).filter_by(source=processor).all()
                
                if mappings:
                    # Create editable dataframe
                    mapping_data = []
                    for m in mappings:
                        if mapping_type == "customer":
                            mapping_data.append({
                                'ID': m.id,
                                'Raw Customer ID': m.raw_store_id,
                                'Mapped Customer Name': m.mapped_store_name,
                                'Customer Type': m.store_type,
                                'Priority': m.priority,
                                'Active': m.active,
                                'Notes': m.notes or ''
                            })
                        elif mapping_type == "store":
                            mapping_data.append({
                                'ID': m.id,
                                'Raw Store ID': m.raw_store_id,
                                'Mapped Store Name': m.mapped_store_name,
                                'Store Type': m.store_type,
                                'Priority': m.priority,
                                'Active': m.active,
                                'Notes': m.notes or ''
                            })
                        else:  # item
                            mapping_data.append({
                                'ID': m.id,
                                'Raw Item': m.raw_item,
                                'Mapped Item': m.mapped_item,
                                'Description': getattr(m, 'mapped_description', ''),
                                'Priority': getattr(m, 'priority', 100),
                                'Active': getattr(m, 'active', True),
                                'Notes': getattr(m, 'notes', '')
                            })
                    
                    df = pd.DataFrame(mapping_data)
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        num_rows="dynamic",
                        key=f"bulk_editor_{mapping_type}_{processor}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save Changes", key=f"save_bulk_{mapping_type}_{processor}"):
                            save_bulk_changes(edited_df, db_service, processor, mapping_type)
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_bulk_{mapping_type}_{processor}"):
                            st.session_state[f'show_{mapping_type}_bulk_{processor}'] = False
                            st.rerun()
                else:
                    st.info(f"No {mapping_type} mappings found")
                    
        except Exception as e:
            st.error(f"❌ Error loading mappings: {e}")

def show_row_by_row_interface(db_service: DatabaseService, processor: str, mapping_type: str):
    """Show row by row interface"""
    with st.expander("📋 Row by Row Editor", expanded=True):
        st.write(f"Edit {mapping_type} mappings one by one:")
        
        # Load current mappings with pagination
        try:
            with db_service.get_session() as session:
                if mapping_type == "customer":
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type.in_(["customer", "store", "distributor"])).all()
                elif mapping_type == "store":
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(db_service.StoreMapping.store_type.in_(["store", "retail", "wholesaler"])).all()
                else:
                    mappings = session.query(db_service.ItemMapping).filter_by(source=processor).all()
                
                if mappings:
                    # Pagination
                    items_per_page = 10
                    total_items = len(mappings)
                    total_pages = (total_items + items_per_page - 1) // items_per_page
                    
                    if total_pages > 1:
                        page = st.selectbox("Page", range(1, total_pages + 1), key=f"page_{mapping_type}_{processor}") - 1
                    else:
                        page = 0
                    
                    start_idx = page * items_per_page
                    end_idx = min(start_idx + items_per_page, total_items)
                    page_mappings = mappings[start_idx:end_idx]
                    
                    # Show each mapping with edit form
                    for i, mapping in enumerate(page_mappings):
                        with st.container():
                            st.write(f"**{mapping_type.title()} Mapping {start_idx + i + 1}**")
                            
                            with st.form(f"edit_{mapping_type}_{mapping.id}_{processor}"):
                                if mapping_type in ["customer", "store"]:
                                    if mapping_type == "customer":
                                        raw_name = st.text_input("Raw Customer ID", value=mapping.raw_store_id, key=f"raw_{mapping.id}_{processor}")
                                        mapped_name = st.text_input("Mapped Customer Name", value=mapping.mapped_store_name, key=f"mapped_{mapping.id}_{processor}")
                                    else:  # store
                                        raw_name = st.text_input("Raw Store ID", value=mapping.raw_store_id, key=f"raw_{mapping.id}_{processor}")
                                        mapped_name = st.text_input("Mapped Store Name", value=mapping.mapped_store_name, key=f"mapped_{mapping.id}_{processor}")
                                    mapping_type_val = st.text_input("Type", value=mapping.store_type, key=f"type_{mapping.id}_{processor}")
                                else:  # item
                                    raw_item = st.text_input("Raw Item", value=mapping.raw_item, key=f"raw_{mapping.id}_{processor}")
                                    mapped_item = st.text_input("Mapped Item", value=mapping.mapped_item, key=f"mapped_{mapping.id}_{processor}")
                                    description = st.text_input("Description", value=getattr(mapping, 'mapped_description', ''), key=f"desc_{mapping.id}_{processor}")
                                
                                priority = st.number_input("Priority", value=mapping.priority, key=f"priority_{mapping.id}_{processor}")
                                active = st.checkbox("Active", value=mapping.active, key=f"active_{mapping.id}_{processor}")
                                notes = st.text_area("Notes", value=mapping.notes or '', key=f"notes_{mapping.id}_{processor}")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    if st.form_submit_button("💾 Save"):
                                        save_row_changes(mapping, locals(), db_service, processor, mapping_type)
                                        st.rerun()
                                
                                with col2:
                                    if st.form_submit_button("🗑️ Delete"):
                                        delete_single_mapping(mapping, db_service, processor, mapping_type)
                                        st.rerun()
                                
                                with col3:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.rerun()
                            
                            st.markdown("---")
                else:
                    st.info(f"No {mapping_type} mappings found")
                    
        except Exception as e:
            st.error(f"❌ Error loading mappings: {e}")

def show_current_mappings_view(db_service: DatabaseService, processor: str, mapping_type: str):
    """Show current mappings in read-only view"""
    try:
        with db_service.get_session() as session:
            if mapping_type == "customer":
                # Customer mappings: filter by store_type values that indicate customer entities
                mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(
                    db_service.StoreMapping.store_type.in_(["customer", "store", "distributor"])
                ).all()
            elif mapping_type == "store":
                # Store mappings: filter by store_type values that indicate store entities  
                mappings = session.query(db_service.StoreMapping).filter_by(source=processor).filter(
                    db_service.StoreMapping.store_type.in_(["store", "retail", "wholesaler"])
                ).all()
            else:
                mappings = session.query(db_service.ItemMapping).filter_by(source=processor).all()
            
            if mappings:
                st.success(f"✅ Found {len(mappings)} {mapping_type} mappings")
                
                # Display mappings
                mapping_data = []
                for m in mappings:
                    if mapping_type in ["customer", "store"]:
                        mapping_data.append({
                            'ID': m.id,
                            'Raw Name': m.raw_store_id,
                            'Mapped Name': m.mapped_store_name,
                            'Type': m.store_type,
                            'Priority': m.priority,
                            'Active': m.active,
                            'Notes': m.notes or ''
                        })
                    else:  # item
                        mapping_data.append({
                            'ID': m.id,
                            'Raw Item': m.raw_item,
                            'Mapped Item': m.mapped_item,
                            'Description': getattr(m, 'mapped_description', ''),
                            'Priority': getattr(m, 'priority', 100),
                            'Active': getattr(m, 'active', True),
                            'Notes': getattr(m, 'notes', '')
                        })
                
                df = pd.DataFrame(mapping_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"No {mapping_type} mappings found")
                
    except Exception as e:
        st.error(f"❌ Error loading mappings: {e}")

# Helper functions for the enhanced interface
def upload_mappings_to_database_silent(df: pd.DataFrame, db_service: DatabaseService, processor: str, mapping_type: str):
    """Upload mappings to database and return result without showing messages"""
    try:
        mappings_data = []
        skipped_rows = []
        
        for index, row in df.iterrows():
            if mapping_type in ["customer", "store"]:
                # Handle different column name formats for customer/store mappings
                raw_name = str(row.get('Raw Customer ID' if mapping_type == 'customer' else 'Raw Store ID', '') or
                           row.get('RawCustomerID' if mapping_type == 'customer' else 'RawStoreID', '') or
                           row.get('Raw Customer' if mapping_type == 'customer' else 'Raw Store', '') or
                           row.get('Customer ID' if mapping_type == 'customer' else 'Store ID', '') or
                           row.get('Raw ID', '') or
                           '').strip()
                
                mapped_name = str(row.get('Mapped Customer Name' if mapping_type == 'customer' else 'Mapped Store Name', '') or
                              row.get('MappedCustomerName' if mapping_type == 'customer' else 'MappedStoreName', '') or
                              row.get('Customer Name' if mapping_type == 'customer' else 'Store Name', '') or
                              row.get('Mapped Name', '') or
                              row.get('Name', '') or
                              '').strip()
                
                # Ensure distinct store_type values for customer vs store mappings
                if mapping_type == 'customer':
                    store_type = str(row.get('Customer Type', '') or
                                 row.get('CustomerType', '') or
                                 row.get('Type', 'customer') or
                                 'customer').strip()
                else:  # store
                    store_type = str(row.get('Store Type', '') or
                                 row.get('StoreType', '') or
                                 row.get('Type', 'store') or
                                 'store').strip()
                
                # Handle priority - try different column names
                priority = 100
                for col in ['Priority', 'priority']:
                    if col in row and pd.notna(row[col]):
                        try:
                            priority = int(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle active status - try different column names
                active = True
                for col in ['Active', 'active', 'Active Status']:
                    if col in row and pd.notna(row[col]):
                        try:
                            active = bool(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle notes - try different column names
                notes = str(row.get('Notes', '') or 
                        row.get('notes', '') or 
                        row.get('Note', '') or 
                        '').strip()
                
                # Skip rows with empty required fields
                if not raw_name or not mapped_name:
                    skipped_rows.append(f"Row {index + 1}: Missing raw_name or mapped_name")
                    continue
                
                if mapping_type == "customer":
                    mappings_data.append({
                        'source': processor,
                        'raw_store_id': raw_name,
                        'mapped_store_name': mapped_name,
                        'store_type': store_type,
                        'priority': priority,
                        'active': active,
                        'notes': notes
                    })
                else:  # store
                    mappings_data.append({
                        'source': processor,
                        'raw_store_id': raw_name,
                        'mapped_store_name': mapped_name,
                        'store_type': store_type,
                        'priority': priority,
                        'active': active,
                        'notes': notes
                    })
            else:  # item
                # Handle different column name formats
                raw_item = str(row.get('Raw Item', '') or 
                           row.get('RawKeyValue', '') or 
                           row.get('Raw Item Number', '') or 
                           '').strip()
                
                mapped_item = str(row.get('Mapped Item', '') or 
                              row.get('MappedItemNumber', '') or 
                              row.get('Mapped Item Number', '') or 
                              '').strip()
                
                item_description = str(row.get('Item Description', '') or 
                                   row.get('MappedDescription', '') or 
                                   row.get('Description', '') or 
                                   '').strip()
                
                # Handle priority - try different column names
                priority = 100
                for col in ['Priority', 'priority']:
                    if col in row and pd.notna(row[col]):
                        try:
                            priority = int(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle active status - try different column names
                active = True
                for col in ['Active', 'active', 'Active Status']:
                    if col in row and pd.notna(row[col]):
                        try:
                            active = bool(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle notes - try different column names
                notes = str(row.get('Notes', '') or 
                        row.get('notes', '') or 
                        row.get('Note', '') or 
                        '').strip()
                
                # Skip rows with empty required fields
                if not raw_item or not mapped_item:
                    skipped_rows.append(f"Row {index + 1}: Missing raw_item or mapped_item")
                    continue
                
                mappings_data.append({
                    'source': processor,
                    'raw_item': raw_item,
                    'mapped_item': mapped_item,
                    'mapped_description': item_description,
                    'priority': priority,
                    'active': active,
                    'notes': notes
                })
        
        if mapping_type in ["customer", "store"]:
                if mapping_type == "customer":
                    # Force use of StoreMapping table for customer mappings until CustomerMapping table is created
                    # Normalize keys to those expected by bulk_upsert_store_mappings
                    for data in mappings_data:
                        if 'raw_customer_id' in data:
                            data['raw_store_id'] = data.pop('raw_customer_id')
                        if 'mapped_customer_name' in data:
                            data['mapped_store_name'] = data.pop('mapped_customer_name')
                        # Prefer provided store_type; otherwise map from customer_type; default to 'customer'
                        if 'customer_type' in data and 'store_type' not in data:
                            data['store_type'] = data.pop('customer_type') or 'customer'
                        elif 'store_type' not in data:
                            data['store_type'] = 'customer'
                        # Remove any fields that don't exist in StoreMapping model
                        data.pop('raw_name', None)
                        data.pop('mapped_name', None)
                        # Ensure we have the required fields
                        if 'raw_store_id' not in data or not data['raw_store_id']:
                            data['raw_store_id'] = data.get('RawCustomerID', '')
                        if 'mapped_store_name' not in data or not data['mapped_store_name']:
                            data['mapped_store_name'] = data.get('MappedCustomerName', '')
                    try:
                        result = db_service.bulk_upsert_store_mappings(mappings_data)
                    except Exception as e:
                        if "raw_name" in str(e) or "mapped_name" in str(e):
                            st.error("❌ Database schema issue detected. Using fallback method...")
                            
                            # Fallback: insert one by one to bypass bulk insert issues
                            try:
                                with db_service.get_session() as session:
                                    # Clear existing wholefoods customer mappings
                                    session.query(db_service.StoreMapping).filter_by(source='wholefoods', store_type='store').delete()
                                    
                                    # Insert new mappings one by one
                                    inserted_count = 0
                                    for data in mappings_data:
                                        mapping = db_service.StoreMapping(
                                            source=data['source'],
                                            raw_store_id=data['raw_store_id'],
                                            mapped_store_name=data['mapped_store_name'],
                                            store_type=data['store_type'],
                                            priority=data['priority'],
                                            active=data['active'],
                                            notes=data['notes']
                                        )
                                        session.add(mapping)
                                        inserted_count += 1
                                    
                                    session.commit()
                                    
                                    st.success(f"✅ Successfully uploaded {inserted_count} customer mappings using fallback method!")
                                    
                                    return {
                                        'success': True,
                                        'inserted': inserted_count,
                                        'updated': 0,
                                        'errors': 0,
                                        'error_details': [],
                                        'skipped_rows': []
                                    }
                                    
                            except Exception as fallback_error:
                                st.error(f"❌ Fallback method also failed: {str(fallback_error)}")
                                return {
                                    'success': False,
                                    'inserted': 0,
                                    'updated': 0,
                                    'errors': len(mappings_data),
                                    'error_details': [f"Both bulk and fallback methods failed: {str(fallback_error)}"],
                                    'skipped_rows': []
                                }
                        else:
                            raise
                else:
                    result = db_service.bulk_upsert_store_mappings(mappings_data)
        else:
            result = db_service.bulk_upsert_item_mappings(mappings_data)
        
        # Return result with additional info
        return {
            'success': result.get('errors', 0) == 0,  # Success if no errors
            'inserted': result.get('added', 0),
            'updated': result.get('updated', 0),
            'error': '; '.join(result.get('error_details', [])) if result.get('error_details') else '',
            'skipped_rows': skipped_rows,
            'total_processed': len(mappings_data)
        }
            
    except Exception as e:
        return {
            'success': False,
            'inserted': 0,
            'updated': 0,
            'error': str(e),
            'skipped_rows': [],
            'total_processed': 0
        }

def upload_mappings_to_database(df: pd.DataFrame, db_service: DatabaseService, processor: str, mapping_type: str):
    """Upload mappings to database"""
    try:
        mappings_data = []
        skipped_rows = []
        
        st.write(f"Processing {len(df)} rows...")
        
        for index, row in df.iterrows():
            if mapping_type in ["customer", "store"]:
                # Handle different column name formats for customer/store mappings
                raw_name = str(row.get('Raw Customer ID' if mapping_type == 'customer' else 'Raw Store ID', '') or
                           row.get('RawCustomerID' if mapping_type == 'customer' else 'RawStoreID', '') or
                           row.get('Raw Customer' if mapping_type == 'customer' else 'Raw Store', '') or
                           row.get('Customer ID' if mapping_type == 'customer' else 'Store ID', '') or
                           row.get('Raw ID', '') or
                           '').strip()
                
                mapped_name = str(row.get('Mapped Customer Name' if mapping_type == 'customer' else 'Mapped Store Name', '') or
                              row.get('MappedCustomerName' if mapping_type == 'customer' else 'MappedStoreName', '') or
                              row.get('Customer Name' if mapping_type == 'customer' else 'Store Name', '') or
                              row.get('Mapped Name', '') or
                              row.get('Name', '') or
                              '').strip()
                
                # Ensure distinct store_type values for customer vs store mappings
                if mapping_type == 'customer':
                    store_type = str(row.get('Customer Type', '') or
                                 row.get('CustomerType', '') or
                                 row.get('Type', 'customer') or
                                 'customer').strip()
                else:  # store
                    store_type = str(row.get('Store Type', '') or
                                 row.get('StoreType', '') or
                                 row.get('Type', 'store') or
                                 'store').strip()
                
                # Handle priority - try different column names
                priority = 100
                for col in ['Priority', 'priority']:
                    if col in row and pd.notna(row[col]):
                        try:
                            priority = int(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle active status - try different column names
                active = True
                for col in ['Active', 'active', 'Active Status']:
                    if col in row and pd.notna(row[col]):
                        try:
                            active = bool(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle notes - try different column names
                notes = str(row.get('Notes', '') or 
                        row.get('notes', '') or 
                        row.get('Note', '') or 
                        '').strip()
                
                # Skip rows with empty required fields
                if not raw_name or not mapped_name:
                    skipped_rows.append(f"Row {index + 1}: Missing raw_name or mapped_name")
                    continue
                
                if mapping_type == "customer":
                    mappings_data.append({
                        'source': processor,
                        'raw_store_id': raw_name,
                        'mapped_store_name': mapped_name,
                        'store_type': store_type,
                        'priority': priority,
                        'active': active,
                        'notes': notes
                    })
                else:  # store
                    mappings_data.append({
                        'source': processor,
                        'raw_store_id': raw_name,
                        'mapped_store_name': mapped_name,
                        'store_type': store_type,
                        'priority': priority,
                        'active': active,
                        'notes': notes
                })
            else:  # item
                # Handle different column name formats
                raw_item = str(row.get('Raw Item', '') or 
                           row.get('RawKeyValue', '') or 
                           row.get('Raw Item Number', '') or 
                           '').strip()
                
                mapped_item = str(row.get('Mapped Item', '') or 
                              row.get('MappedItemNumber', '') or 
                              row.get('Mapped Item Number', '') or 
                              '').strip()
                
                item_description = str(row.get('Item Description', '') or 
                                   row.get('MappedDescription', '') or 
                                   row.get('Description', '') or 
                                   '').strip()
                
                # Handle priority - try different column names
                priority = 100
                for col in ['Priority', 'priority']:
                    if col in row and pd.notna(row[col]):
                        try:
                            priority = int(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle active status - try different column names
                active = True
                for col in ['Active', 'active', 'Active Status']:
                    if col in row and pd.notna(row[col]):
                        try:
                            active = bool(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Handle notes - try different column names
                notes = str(row.get('Notes', '') or 
                        row.get('notes', '') or 
                        row.get('Note', '') or 
                        '').strip()
                
                # Skip rows with empty required fields
                if not raw_item or not mapped_item:
                    skipped_rows.append(f"Row {index + 1}: Missing raw_item or mapped_item")
                    continue
                
                mappings_data.append({
                    'source': processor,
                    'raw_item': raw_item,
                    'mapped_item': mapped_item,
                    'mapped_description': item_description,
                    'priority': priority,
                    'active': active,
                    'notes': notes
                })
        
        if mapping_type in ["customer", "store"]:
            result = db_service.bulk_upsert_store_mappings(mappings_data)
        else:
            result = db_service.bulk_upsert_item_mappings(mappings_data)
        
        if result['success']:
            st.success(f"✅ Successfully uploaded {result['inserted']} new {mapping_type} mappings")
            if result['updated'] > 0:
                st.info(f"Updated {result['updated']} existing mappings")
            if skipped_rows:
                st.warning(f"Skipped {len(skipped_rows)} rows due to missing required data:")
                for skip_reason in skipped_rows[:5]:  # Show first 5 skipped rows
                    st.write(f"- {skip_reason}")
                if len(skipped_rows) > 5:
                    st.write(f"- ... and {len(skipped_rows) - 5} more")
        else:
            st.error(f"❌ Upload failed: {result['error']}")
            
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")

def add_new_mapping_to_database(db_service: DatabaseService, processor: str, mapping_type: str, form_data: dict):
    """Add new mapping to database"""
    try:
        if mapping_type in ["customer", "store"]:
            mapping_data = {
                'source': processor,
                'raw_name': form_data['raw_name'],
                'mapped_name': form_data['mapped_name'],
                'store_type': form_data.get('customer_type' if mapping_type == 'customer' else 'store_type', 'distributor'),
                'priority': form_data['priority'],
                'active': form_data['active'],
                'notes': form_data['notes']
            }
            result = db_service.bulk_upsert_store_mappings([mapping_data])
        else:  # item
            mapping_data = {
                'source': processor,
                'raw_item': form_data['raw_item'],
                'mapped_item': form_data['mapped_item'],
                'mapped_description': form_data['description'],
                'priority': form_data['priority'],
                'active': form_data['active'],
                'notes': form_data['notes']
            }
            result = db_service.bulk_upsert_item_mappings([mapping_data])
        
        if result['success']:
            st.success(f"✅ Successfully added new {mapping_type} mapping")
        else:
            st.error(f"❌ Failed to add mapping: {result['error']}")
            
    except Exception as e:
        st.error(f"❌ Failed to add mapping: {e}")

def save_bulk_changes(edited_df: pd.DataFrame, db_service: DatabaseService, processor: str, mapping_type: str):
    """Save bulk changes to database"""
    try:
        with db_service.get_session() as session:
            for idx, row in edited_df.iterrows():
                if pd.notna(row['ID']):
                    if mapping_type in ["customer", "store"]:
                        mapping = session.query(db_service.StoreMapping).filter_by(id=int(row['ID'])).first()
                        if mapping:
                            mapping.raw_name = str(row['Raw Name'])
                            mapping.mapped_name = str(row['Mapped Name'])
                            mapping.store_type = str(row['Type'])
                            mapping.priority = int(row['Priority'])
                            mapping.active = bool(row['Active'])
                            mapping.notes = str(row['Notes'])
                    else:  # item
                        mapping = session.query(db_service.ItemMapping).filter_by(id=int(row['ID'])).first()
                        if mapping:
                            mapping.raw_item = str(row['Raw Item'])
                            mapping.mapped_item = str(row['Mapped Item'])
                            mapping.item_description = str(row['Description'])
                            mapping.priority = int(row['Priority'])
                            mapping.active = bool(row['Active'])
                            mapping.notes = str(row['Notes'])
            session.commit()
            st.success("✅ Bulk changes saved successfully!")
            
    except Exception as e:
        st.error(f"❌ Failed to save bulk changes: {e}")

def save_row_changes(mapping, form_data: dict, db_service: DatabaseService, processor: str, mapping_type: str):
    """Save changes to a single mapping row"""
    try:
        with db_service.get_session() as session:
            if mapping_type in ["customer", "store"]:
                mapping.raw_store_id = form_data['raw_name']
                mapping.mapped_store_name = form_data['mapped_name']
                mapping.store_type = form_data['mapping_type_val']
                mapping.priority = form_data['priority']
                mapping.active = form_data['active']
                mapping.notes = form_data['notes']
            else:  # item
                mapping.raw_item = form_data['raw_item']
                mapping.mapped_item = form_data['mapped_item']
                mapping.mapped_description = form_data['description']
                mapping.priority = form_data['priority']
                mapping.active = form_data['active']
                mapping.notes = form_data['notes']
            session.commit()
            st.success("✅ Mapping updated successfully!")
            
    except Exception as e:
        st.error(f"❌ Failed to update mapping: {e}")

def delete_single_mapping(mapping, db_service: DatabaseService, processor: str, mapping_type: str):
    """Delete a single mapping"""
    try:
        with db_service.get_session() as session:
            session.delete(mapping)
            session.commit()
            st.success("✅ Mapping deleted successfully!")
            
    except Exception as e:
        st.error(f"❌ Failed to delete mapping: {e}")


def mapping_documentation_page(db_service: DatabaseService, selected_source: str):
    """Comprehensive mapping documentation page for each client"""
    
    # Client-specific mapping information
    client_mappings = {
        "wholefoods": {
            "name": "Whole Foods Market",
            "description": "Natural and organic grocery retailer with complex store hierarchy",
            "file_format": "HTML/CSV",
            "order_structure": "Multi-store orders with detailed item information",
            "mapping_fields": {
                "customer": {
                    "source_field": "Store ID / Customer ID",
                    "target_field": "Xoro Customer Name",
                    "description": "Maps store locations to customer accounts",
                    "example": "Store #10005 → WHOLE FOODS #10005 PALO ALTO"
                },
                "store": {
                    "source_field": "Store Location / DC",
                    "target_field": "Xoro Store Name", 
                    "description": "Maps distribution centers and store locations",
                    "example": "DC12 → KEHE AURORA CO DC12"
                },
                "item": {
                    "source_field": "Vendor Item Number",
                    "target_field": "Xoro Item Number + Description",
                    "description": "Maps vendor SKUs to standardized item numbers with descriptions",
                    "example": "12-046-2 → 12-046-2 (Loacker Quadratini- Chocolate)"
                }
            },
            "process_flow": [
                "Parse HTML order files for store and item data",
                "Extract customer information from store headers",
                "Map store IDs to customer names using customer mappings",
                "Map distribution centers to store names using store mappings", 
                "Map vendor item numbers to Xoro format using item mappings",
                "Validate all mappings exist before processing",
                "Generate standardized Xoro CSV output"
            ],
            "validation_points": [
                "Verify customer mapping exists for each store ID",
                "Check store mapping for distribution center references",
                "Ensure item mapping covers all vendor SKUs",
                "Validate priority and active status of mappings",
                "Confirm description fields are populated"
            ]
        },
        "kehe": {
            "name": "KEHE SPS",
            "description": "Specialty food distributor serving independent retailers",
            "file_format": "CSV",
            "order_structure": "Direct store orders with detailed product information",
            "mapping_fields": {
                "customer": {
                    "source_field": "Customer Account Number",
                    "target_field": "Xoro Customer Name",
                    "description": "Maps KEHE customer accounts to Xoro customers",
                    "example": "569813430012 → KEHE AURORA CO DC12"
                },
                "store": {
                    "source_field": "Store Location Code",
                    "target_field": "Xoro Store Name",
                    "description": "Maps store location codes to retail store names",
                    "example": "DC12 → KEHE AURORA CO DC12"
                },
                "item": {
                    "source_field": "Product Code",
                    "target_field": "Xoro Item Number",
                    "description": "Maps KEHE product codes to standardized item numbers",
                    "example": "12345 → 12-345-6 (Product Description)"
                }
            },
            "process_flow": [
                "Parse CSV order files for customer and product data",
                "Extract customer account information",
                "Map customer accounts to customer names using customer mappings",
                "Map store codes to store names using store mappings",
                "Map product codes to item numbers using item mappings",
                "Validate mapping completeness and accuracy",
                "Generate standardized Xoro CSV output"
            ],
            "validation_points": [
                "Verify customer mapping exists for each account number",
                "Check store mapping for location codes",
                "Ensure item mapping covers all product codes",
                "Validate customer type (distributor vs retail)",
                "Confirm store type (retail vs wholesale)"
            ]
        },
        "unfi_east": {
            "name": "UNFI East",
            "description": "United Natural Foods East Coast distribution",
            "file_format": "PDF/CSV",
            "order_structure": "Regional distribution with multi-location orders",
            "mapping_fields": {
                "customer": {
                    "source_field": "Customer ID",
                    "target_field": "Xoro Customer Name",
                    "description": "Maps UNFI East customer IDs to customer names",
                    "example": "CUST001 → UNFI EAST CUSTOMER"
                },
                "store": {
                    "source_field": "Store Number",
                    "target_field": "Xoro Store Name",
                    "description": "Maps store numbers to store locations",
                    "example": "ST001 → UNFI EAST STORE 001"
                },
                "item": {
                    "source_field": "Item Code",
                    "target_field": "Xoro Item Number",
                    "description": "Maps UNFI item codes to standardized numbers",
                    "example": "UNFI123 → 12-345-6 (Item Description)"
                }
            },
            "process_flow": [
                "Parse PDF/CSV files for customer and store data",
                "Extract customer identification information",
                "Map customer IDs to customer names using customer mappings",
                "Map store numbers to store names using store mappings",
                "Map item codes to item numbers using item mappings",
                "Validate regional distribution requirements",
                "Generate standardized Xoro CSV output"
            ],
            "validation_points": [
                "Verify customer mapping exists for each customer ID",
                "Check store mapping for store numbers",
                "Ensure item mapping covers all item codes",
                "Validate customer type separation (store vs distributor)",
                "Confirm store type classification"
            ]
        },
        "unfi_west": {
            "name": "UNFI West",
            "description": "United Natural Foods West Coast distribution",
            "file_format": "PDF/CSV",
            "order_structure": "Regional distribution with multi-location orders",
            "mapping_fields": {
                "customer": {
                    "source_field": "Customer ID",
                    "target_field": "Xoro Customer Name",
                    "description": "Maps UNFI West customer IDs to customer names",
                    "example": "CUST001 → UNFI WEST CUSTOMER"
                },
                "store": {
                    "source_field": "Store Number",
                    "target_field": "Xoro Store Name",
                    "description": "Maps store numbers to store locations",
                    "example": "ST001 → UNFI WEST STORE 001"
                },
                "item": {
                    "source_field": "Item Code",
                    "target_field": "Xoro Item Number",
                    "description": "Maps UNFI item codes to standardized numbers",
                    "example": "UNFI123 → 12-345-6 (Item Description)"
                }
            },
            "process_flow": [
                "Parse PDF/CSV files for customer and store data",
                "Extract customer identification information",
                "Map customer IDs to customer names using customer mappings",
                "Map store numbers to store names using store mappings",
                "Map item codes to item numbers using item mappings",
                "Validate regional distribution requirements",
                "Generate standardized Xoro CSV output"
            ],
            "validation_points": [
                "Verify customer mapping exists for each customer ID",
                "Check store mapping for store numbers",
                "Ensure item mapping covers all item codes",
                "Validate customer type separation (store vs distributor)",
                "Confirm store type classification"
            ]
        },
        "tkmaxx": {
            "name": "TK Maxx",
            "description": "Off-price retail chain with unique product sourcing",
            "file_format": "CSV",
            "order_structure": "Store-specific orders with fashion/retail items",
            "mapping_fields": {
                "customer": {
                    "source_field": "Store ID",
                    "target_field": "Xoro Customer Name",
                    "description": "Maps TK Maxx store IDs to customer accounts",
                    "example": "TK001 → TK MAXX STORE 001"
                },
                "store": {
                    "source_field": "Store Location",
                    "target_field": "Xoro Store Name",
                    "description": "Maps store locations to store names",
                    "example": "LOC001 → TK MAXX LOCATION 001"
                },
                "item": {
                    "source_field": "SKU",
                    "target_field": "Xoro Item Number",
                    "description": "Maps TK Maxx SKUs to standardized item numbers",
                    "example": "TK123 → 12-345-6 (Fashion Item Description)"
                }
            },
            "process_flow": [
                "Parse CSV order files for store and SKU data",
                "Extract store identification information",
                "Map store IDs to customer names using customer mappings",
                "Map store locations to store names using store mappings",
                "Map SKUs to item numbers using item mappings",
                "Validate fashion/retail specific requirements",
                "Generate standardized Xoro CSV output"
            ],
            "validation_points": [
                "Verify customer mapping exists for each store ID",
                "Check store mapping for store locations",
                "Ensure item mapping covers all SKUs",
                "Validate retail-specific mapping requirements",
                "Confirm fashion item descriptions"
            ]
        }
    }
    
    if selected_source == "all":
        st.error("Please select a specific client to view mapping documentation.")
        return
    
    client_info = client_mappings.get(selected_source, {})
    if not client_info:
        st.error(f"No mapping documentation available for {selected_source}")
        return
    
    # Beautiful header with client branding
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 50%; font-size: 2rem;">
                📋
            </div>
            <div>
                <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">
                    {client_info['name']} Mapping Documentation
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                    {client_info['description']}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Client overview cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #667eea;">
            <h3 style="color: #667eea; margin-top: 0;">📄 File Format</h3>
            <p style="font-size: 1.1rem; margin-bottom: 0;"><strong>{client_info['file_format']}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #764ba2;">
            <h3 style="color: #764ba2; margin-top: 0;">🏗️ Order Structure</h3>
            <p style="font-size: 1rem; margin-bottom: 0;">{client_info['order_structure']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #f093fb;">
            <h3 style="color: #f093fb; margin-top: 0;">🔄 Processing</h3>
            <p style="font-size: 1rem; margin-bottom: 0;">Real-time mapping validation</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Mapping fields section
    st.markdown("## 🗺️ Field Mapping Overview")
    st.markdown("This section shows how each field from the client's order file maps to the standardized Xoro format.")
    
    # Create mapping cards for each type
    mapping_types = ['customer', 'store', 'item']
    mapping_colors = ['#667eea', '#764ba2', '#f093fb']
    mapping_icons = ['👥', '🏪', '📦']
    
    for i, mapping_type in enumerate(mapping_types):
        mapping_info = client_info['mapping_fields'][mapping_type]
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {mapping_colors[i]}20 0%, {mapping_colors[i]}10 100%); padding: 2rem; border-radius: 15px; margin: 1rem 0; border-left: 5px solid {mapping_colors[i]};">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                <div style="background: {mapping_colors[i]}; padding: 0.5rem; border-radius: 50%; font-size: 1.5rem;">
                    {mapping_icons[i]}
                </div>
                <h3 style="color: {mapping_colors[i]}; margin: 0; text-transform: capitalize;">{mapping_type.title()} Mapping</h3>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1rem;">
                <div style="background: white; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #333; margin-top: 0;">📥 Source Field</h4>
                    <p style="font-weight: bold; color: #667eea;">{mapping_info['source_field']}</p>
                </div>
                <div style="background: white; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #333; margin-top: 0;">📤 Target Field</h4>
                    <p style="font-weight: bold; color: #764ba2;">{mapping_info['target_field']}</p>
                </div>
            </div>
            
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color: #333; margin-top: 0;">📝 Description</h4>
                <p style="margin-bottom: 0;">{mapping_info['description']}</p>
            </div>
            
            <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 8px; border-left: 3px solid {mapping_colors[i]};">
                <h4 style="color: #333; margin-top: 0;">💡 Example</h4>
                <code style="background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: block;">{mapping_info['example']}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Process flow section
    st.markdown("## 🔄 Processing Flow")
    st.markdown("The step-by-step process of how orders are transformed using the mappings.")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea20 0%, #764ba210 100%); padding: 2rem; border-radius: 15px; margin: 1rem 0;">
        <h3 style="color: #667eea; margin-top: 0;">📋 Processing Steps</h3>
    """, unsafe_allow_html=True)
    
    for i, step in enumerate(client_info['process_flow'], 1):
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin: 1rem 0; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="background: #667eea; color: white; padding: 0.5rem; border-radius: 50%; min-width: 2rem; text-align: center; font-weight: bold;">
                {i}
            </div>
            <p style="margin: 0; font-size: 1rem;">{step}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Validation checkpoints section
    st.markdown("## ✅ Validation Checkpoints")
    st.markdown("Critical points where mapping validation occurs to ensure data integrity.")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f093fb20 0%, #667eea10 100%); padding: 2rem; border-radius: 15px; margin: 1rem 0;">
        <h3 style="color: #f093fb; margin-top: 0;">🔍 Validation Points</h3>
    """, unsafe_allow_html=True)
    
    for i, checkpoint in enumerate(client_info['validation_points'], 1):
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin: 1rem 0; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #f093fb;">
            <div style="background: #f093fb; color: white; padding: 0.5rem; border-radius: 50%; min-width: 2rem; text-align: center; font-weight: bold;">
                ✓
            </div>
            <p style="margin: 0; font-size: 1rem;">{checkpoint}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Best practices section
    st.markdown("## 💡 Best Practices")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #667eea;">
            <h3 style="color: #667eea; margin-top: 0;">📊 Mapping Management</h3>
            <ul style="margin-bottom: 0;">
                <li>Keep mappings up-to-date with client changes</li>
                <li>Use descriptive names for better clarity</li>
                <li>Set appropriate priority values</li>
                <li>Mark inactive mappings instead of deleting</li>
                <li>Add notes for complex mapping logic</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #764ba2;">
            <h3 style="color: #764ba2; margin-top: 0;">🔧 Troubleshooting</h3>
            <ul style="margin-bottom: 0;">
                <li>Check mapping completeness before processing</li>
                <li>Validate field formats match expectations</li>
                <li>Review skipped rows in upload results</li>
                <li>Use bulk editor for mass updates</li>
                <li>Test mappings with sample data first</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer with quick actions
    st.markdown("---")
    st.markdown("## 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⚙️ Manage Mappings", use_container_width=True):
            st.session_state['action'] = 'mappings'
            st.rerun()
    
    with col2:
        if st.button("📊 Process Orders", use_container_width=True):
            st.session_state['action'] = 'process'
            st.rerun()
    
    with col3:
        if st.button("👁️ View Orders", use_container_width=True):
            st.session_state['action'] = 'view'
            st.rerun()


# Health check endpoint for Render
@st.cache_data
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    main()
