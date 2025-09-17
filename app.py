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

# Utility functions
def parse_boolean(value):
    """Parse various boolean representations to actual boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on', 'active', 'enabled')
    if isinstance(value, (int, float)):
        return bool(value)
    return bool(value)

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
    
    # Add custom CSS for sleek UI
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        text-align: center;
        font-size: 1.6rem;
        font-weight: 600;
    }
    .main-header p {
        color: white;
        margin: 0.3rem 0 0 0;
        text-align: center;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }
    .stSelectbox > div > div {
        padding: 0.3rem 0.5rem;
        min-width: 200px !important;
    }
    .stSelectbox > div > div > div {
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    .stSelectbox [data-baseweb="select"] {
        min-width: 200px !important;
    }
    .stSelectbox [data-baseweb="select"] > div {
        min-width: 200px !important;
        white-space: nowrap !important;
    }
    .stButton > button {
        padding: 0.3rem 0.8rem;
        font-size: 0.9rem;
    }
    .stFileUploader > div {
        border: 2px dashed #667eea !important;
        border-radius: 8px !important;
        background-color: #f8f9fa !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    .stFileUploader > div:hover {
        border-color: #4f46e5 !important;
        background-color: #f0f2f6 !important;
    }
    .stFileUploader > div > div {
        text-align: center !important;
    }
    .stFileUploader > div > div > div {
        color: #667eea !important;
        font-weight: 500 !important;
    }
    .drag-over {
        border-color: #4f46e5 !important;
        background-color: #e0e7ff !important;
        transform: scale(1.02) !important;
    }
    .upload-zone {
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    .upload-zone:hover {
        border-color: #4f46e5 !important;
        background-color: #f0f2f6 !important;
    }
    /* Sidebar dropdown styling */
    .css-1d391kg .stSelectbox > div > div {
        min-width: 180px !important;
    }
    .css-1d391kg .stSelectbox [data-baseweb="select"] {
        min-width: 180px !important;
    }
    .css-1d391kg .stSelectbox [data-baseweb="select"] > div {
        min-width: 180px !important;
        white-space: nowrap !important;
    }
    /* Ensure dropdown options are visible */
    [data-baseweb="popover"] {
        min-width: 200px !important;
    }
    [data-baseweb="menu"] {
        min-width: 200px !important;
    }
    [data-baseweb="menu"] li {
        white-space: nowrap !important;
        overflow: visible !important;
    }
    /* Sidebar width adjustment */
    .css-1d391kg {
        min-width: 250px !important;
    }
    .css-1d391kg .stSelectbox {
        width: 100% !important;
    }
    /* Main content area adjustment */
    .main .block-container {
        padding-left: 1rem !important;
    }
    /* Additional dropdown fixes */
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__value-container"] {
        min-width: 180px !important;
        white-space: nowrap !important;
    }
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__single-value"] {
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    /* Ensure dropdown menu items are fully visible */
    [data-baseweb="menu"] [role="option"] {
        white-space: nowrap !important;
        padding: 0.5rem 1rem !important;
        min-width: 200px !important;
    }
    /* Fix dropdown menu positioning and visibility */
    [data-baseweb="popover"] {
        z-index: 9999 !important;
        min-width: 200px !important;
        max-width: none !important;
    }
    [data-baseweb="menu"] {
        min-width: 200px !important;
        max-width: none !important;
        overflow: visible !important;
    }
    /* Ensure dropdown options are fully visible */
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__menu"] {
        min-width: 200px !important;
        max-width: none !important;
    }
    /* Fix for deployed environment */
    div[data-testid="stSelectbox"] > div > div {
        min-width: 200px !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] {
        min-width: 200px !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
        min-width: 200px !important;
        white-space: nowrap !important;
    }
    /* Additional fixes for dropdown visibility */
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__dropdown"] {
        min-width: 200px !important;
        max-width: none !important;
    }
    /* Fix dropdown menu container */
    [data-baseweb="popover"] [data-baseweb="menu"] {
        min-width: 200px !important;
        max-width: none !important;
        overflow: visible !important;
    }
    /* Ensure all dropdown options are visible */
    [data-baseweb="menu"] li {
        min-width: 200px !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    /* Fix for Streamlit's internal dropdown styling */
    .stSelectbox > div > div > div {
        min-width: 200px !important;
    }
    /* Override any width restrictions */
    .stSelectbox [data-baseweb="select"] {
        width: auto !important;
        min-width: 200px !important;
    }
    
    /* Enhanced font sizing and readability for dropdowns */
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__single-value"] {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #333333 !important;
        line-height: 1.4 !important;
    }
    
    /* Dropdown menu options styling */
    [data-baseweb="menu"] [role="option"] {
        font-size: 14px !important;
        font-weight: 400 !important;
        color: #333333 !important;
        line-height: 1.5 !important;
        padding: 8px 12px !important;
        min-height: 36px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Hover state for dropdown options */
    [data-baseweb="menu"] [role="option"]:hover {
        background-color: #f0f2f6 !important;
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    
    /* Selected option styling */
    [data-baseweb="menu"] [role="option"][aria-selected="true"] {
        background-color: #667eea !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Dropdown container height and spacing */
    .stSelectbox [data-baseweb="select"] {
        min-height: 40px !important;
    }
    
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__value-container"] {
        min-height: 40px !important;
        padding: 4px 8px !important;
    }
    
    /* Dropdown arrow styling */
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__dropdown-indicator"] {
        padding: 8px !important;
    }
    
    /* Menu container with better spacing */
    [data-baseweb="popover"] [data-baseweb="menu"] {
        padding: 4px 0 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
        background-color: white !important;
    }
    
    /* Fix text truncation in all dropdown states */
    .stSelectbox * {
        text-overflow: unset !important;
        overflow: visible !important;
        white-space: nowrap !important;
    }
    
    /* Specific fixes for filter dropdowns */
    div[data-testid="stSelectbox"] label {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #374151 !important;
        margin-bottom: 4px !important;
    }
    
    /* Ensure proper contrast and visibility */
    .stSelectbox [data-baseweb="select__placeholder"] {
        font-size: 14px !important;
        color: #6b7280 !important;
    }
    
    /* Mobile responsiveness for dropdowns */
    @media (max-width: 768px) {
        .stSelectbox [data-baseweb="select"] {
            min-width: 150px !important;
        }
        [data-baseweb="menu"] [role="option"] {
            font-size: 13px !important;
            padding: 6px 10px !important;
        }
    }
    
    /* Sidebar specific dropdown improvements */
    .css-1d391kg .stSelectbox [data-baseweb="select"] [data-baseweb="select__single-value"] {
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #333333 !important;
    }
    
    /* Ensure sidebar dropdown menu options are readable */
    .css-1d391kg [data-baseweb="menu"] [role="option"] {
        font-size: 13px !important;
        font-weight: 400 !important;
        color: #333333 !important;
        padding: 6px 10px !important;
        min-height: 32px !important;
    }
    
    /* Main content area dropdown improvements */
    .main .stSelectbox [data-baseweb="select"] [data-baseweb="select__single-value"] {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #1f2937 !important;
    }
    
    /* Filter section specific styling */
    .stSelectbox[data-testid="stSelectbox"] [data-baseweb="select"] {
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        background-color: white !important;
        transition: border-color 0.2s ease !important;
    }
    
    .stSelectbox[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Ensure all text is visible and not cut off */
    [data-baseweb="select__value-container"] * {
        max-width: none !important;
        width: auto !important;
        flex-shrink: 0 !important;
    }
    
    /* Force text to be fully visible */
    .stSelectbox [data-baseweb="select"] [data-baseweb="select__single-value"] {
        max-width: none !important;
        width: auto !important;
        text-overflow: unset !important;
        overflow: visible !important;
        white-space: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sleek, compact header
    st.markdown("""
    <div class="main-header">
        <h1>🔄 Order Transformer</h1>
        <p>Convert sales orders into standardized Xoro CSV format</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database service
    db_service = DatabaseService()
    
    # Sidebar navigation system
    with st.sidebar:
        st.markdown("### 🎯 Client/Source")
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
        
        st.markdown("### ⚡ Action")
        actions = {
            "📝 Process Orders": "process",
            "📊 Order History": "history",
            "👁️ View Orders": "view",
            "⚙️ Manage Mappings": "mappings"
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
    
    # Compact system status in sidebar
    with st.sidebar:
        st.markdown("### ⚙️ System")
        st.success("✅ Database ready")
    
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
        
        # Source already selected, use it directly
        selected_order_source = selected_source_name
    
    # Initialize mapping utils and order sources
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
    
    # Single, functional file uploader with enhanced styling
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 8px; border: 2px dashed #667eea; text-align: center; margin-bottom: 1rem;">
        <h3 style="color: #667eea; margin: 0;">{file_icon} Upload Your Files</h3>
        <p style="color: #666; margin: 0.3rem 0; font-size: 0.9rem;">{help_text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # File uploader with proper drag and drop
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=accepted_types,
        accept_multiple_files=True,
        help=f"Upload {', '.join(accepted_types).upper()} files for {clean_source_name}",
        key=f"file_uploader_{clean_source_name}"
    )
    
    if uploaded_files:
        # Validate uploaded files
        valid_files = []
        invalid_files = []
        
        for file in uploaded_files:
            file_extension = file.name.lower().split('.')[-1]
            file_size_mb = len(file.getvalue()) / (1024 * 1024)  # MB
            
            # Check file type
            if file_extension not in accepted_types:
                invalid_files.append(f"{file.name} (unsupported format: .{file_extension})")
            # Check file size (200MB limit)
            elif file_size_mb > 200:
                invalid_files.append(f"{file.name} (too large: {file_size_mb:.1f}MB)")
            else:
                valid_files.append(file)
        
        # Show validation results
        if invalid_files:
            st.warning("⚠️ Some files have issues:")
            for invalid_file in invalid_files:
                st.error(f"❌ {invalid_file}")
        
        if valid_files:
            st.markdown("#### ✅ Files Ready for Processing")
            
            for file in valid_files:
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
                        process_orders(valid_files, order_sources[clean_source_name], clean_source_name, db_service)
                    else:
                        st.error(f"⚠️ Unknown source: {clean_source_name}. Please select a valid source.")
        else:
            st.error("❌ No valid files to process. Please check file formats and sizes.")

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
    
    # Compact mapping management header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0; text-align: center; font-size: 1.4rem; font-weight: 600;">⚙️ Mapping Management Center</h1>
        <p style="color: white; margin: 0.3rem 0 0 0; text-align: center; opacity: 0.9; font-size: 0.85rem;">Complete mapping management by order processor</p>
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
    
    # Compact processor overview card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 0.8rem 1.2rem; border-radius: 8px; margin-bottom: 1rem;
                border-left: 4px solid #4f46e5; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
        <h2 style="color: white; margin: 0; font-size: 1.2rem; font-weight: 600;">{processor_display} Mapping Management</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; font-size: 0.8rem;">
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
    """Enhanced Customer Mapping Management with Database Support"""
    
    st.markdown("### 👥 Customer Mapping")
    st.caption("Database-backed customer mapping with unified template for all processors")
    
    # Enhanced UI with filters and controls
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        # Source filter
        source_options = ['all', 'kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
        source_index = source_options.index(processor) if processor in source_options else 1
        selected_source = st.selectbox(
            "📍 Source Filter", 
            source_options, 
            index=source_index,
            key=f"customer_source_filter_{processor}"
        )
    
    with col2:
        # Customer type filter
        customer_type_options = ['all', 'store', 'distributor', 'warehouse']
        selected_customer_type = st.selectbox(
            "🏪 Customer Type", 
            customer_type_options,
            key=f"customer_type_filter_{processor}"
        )
    
    with col3:
        # Active status filter
        active_options = {'All': None, 'Active Only': True, 'Inactive Only': False}
        selected_active_name = st.selectbox(
            "✅ Status", 
            list(active_options.keys()),
            key=f"customer_active_filter_{processor}"
        )
        active_filter = active_options[selected_active_name]
    
    with col4:
        # Search filter
        search_term = st.text_input(
            "🔍 Search", 
            placeholder="Search customers...",
            key=f"customer_search_filter_{processor}"
        )
    
    st.markdown("---")
    
    # Action buttons row
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    
    with col1:
        if st.button("📥 Download Template", key=f"customer_download_template_{processor}"):
            show_customer_template_download()
    
    with col2:
        if st.button("📊 Export Current", key=f"customer_export_current_{processor}"):
            export_current_customer_mappings(db_service, selected_source if selected_source != 'all' else None)
    
    with col3:
        if st.button("📤 Upload Mappings", key=f"customer_upload_mappings_{processor}"):
            st.session_state[f'show_customer_upload_{processor}'] = True
    
    with col4:
        if st.button("➕ Add New Mapping", key=f"customer_add_new_{processor}"):
            st.session_state[f'show_customer_add_form_{processor}'] = True
    
    with col5:
        if st.button("🔄 Refresh Data", key=f"customer_refresh_data_{processor}"):
            st.rerun()
    
    # Show upload form if requested
    if st.session_state.get(f'show_customer_upload_{processor}', False):
        show_customer_mapping_upload_form(db_service, processor)
    
    # Show add form if requested  
    if st.session_state.get(f'show_customer_add_form_{processor}', False):
        show_add_customer_mapping_form(db_service, processor)
    
    st.markdown("---")
    
    # Get and display mappings
    try:
        # Apply filters
        source_param = selected_source if selected_source != 'all' else None
        customer_type_param = selected_customer_type if selected_customer_type != 'all' else None
        search_param = search_term if search_term.strip() else None
        
        # Get filtered mappings from database
        mappings = db_service.get_customer_mappings_advanced(
            source=source_param,
            active_only=False,  # We'll filter by active status below
            customer_type=customer_type_param,
            search_term=search_param
        )
        
        # Apply active filter if specified
        if active_filter is not None:
            mappings = [m for m in mappings if m['active'] == active_filter]
        
        if mappings:
            st.success(f"✅ Found {len(mappings)} customer mappings")
            
            # Display mode selection
            display_mode = st.radio(
                "Display Mode:",
                ["📋 Data Editor (Bulk Edit)", "📝 Row-by-Row (Individual Edit)"],
                horizontal=True,
                key=f"customer_display_mode_{processor}"
            )
            
            if display_mode == "📋 Data Editor (Bulk Edit)":
                show_customer_data_editor_mappings(mappings, db_service, processor)
            else:
                show_customer_row_by_row_mappings(mappings, db_service, processor)
                
        else:
            st.info("🔍 No customer mappings found with current filters")
            
            # Suggest creating new mappings
            st.markdown("### 🚀 Get Started")
            st.write("Start by downloading the template or adding your first mapping:")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download Empty Template", key=f"customer_download_empty_{processor}"):
                    show_customer_template_download()
            with col2:
                if st.button("➕ Add First Mapping", key=f"customer_add_first_{processor}"):
                    st.session_state[f'show_customer_add_form_{processor}'] = True
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading customer mappings: {e}")
        st.write("**Troubleshooting:**")
        st.write("1. Check database connection")
        st.write("2. Verify migration has been run")
        st.write("3. Check server logs for details")

def show_store_mapping_manager(processor: str, db_service: DatabaseService):
    """Enhanced Store Mapping Management with Database Support"""
    
    st.markdown("### 🏪 Store (Xoro) Mapping")
    st.caption("Database-backed store mapping with unified template for all processors")
    
    # Enhanced UI with filters and controls
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        # Source filter
        source_options = ['all', 'kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
        source_index = source_options.index(processor) if processor in source_options else 1
        selected_source = st.selectbox(
            "📍 Source Filter", 
            source_options, 
            index=source_index,
            key=f"store_source_filter_{processor}"
        )
    
    with col2:
        # Store type filter
        store_type_options = ['all', 'retail', 'warehouse', 'distribution']
        selected_store_type = st.selectbox(
            "🏪 Store Type", 
            store_type_options,
            key=f"store_type_filter_{processor}"
        )
    
    with col3:
        # Active status filter
        active_options = {'All': None, 'Active Only': True, 'Inactive Only': False}
        selected_active_name = st.selectbox(
            "✅ Status", 
            list(active_options.keys()),
            key=f"store_active_filter_{processor}"
        )
        active_filter = active_options[selected_active_name]
    
    with col4:
        # Search filter
        search_term = st.text_input(
            "🔍 Search", 
            placeholder="Search stores...",
            key=f"store_search_filter_{processor}"
        )
    
    st.markdown("---")
    
    # Action buttons row
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    
    with col1:
        if st.button("📥 Download Template", key=f"store_download_template_{processor}"):
            show_store_template_download()
    
    with col2:
        if st.button("📊 Export Current", key=f"store_export_current_{processor}"):
            export_current_store_mappings(db_service, selected_source if selected_source != 'all' else None)
    
    with col3:
        if st.button("📤 Upload Mappings", key=f"store_upload_mappings_{processor}"):
            st.session_state[f'show_store_upload_{processor}'] = True
    
    with col4:
        if st.button("➕ Add New Mapping", key=f"store_add_new_{processor}"):
            st.session_state[f'show_store_add_form_{processor}'] = True
    
    with col5:
        if st.button("🔄 Refresh Data", key=f"store_refresh_data_{processor}"):
            st.rerun()
    
    # Show upload form if requested
    if st.session_state.get(f'show_store_upload_{processor}', False):
        show_store_mapping_upload_form(db_service, processor)
    
    # Show add form if requested  
    if st.session_state.get(f'show_store_add_form_{processor}', False):
        show_add_store_mapping_form(db_service, processor)
    
    st.markdown("---")
    
    # Get and display mappings
    try:
        # Apply filters
        source_param = selected_source if selected_source != 'all' else None
        store_type_param = selected_store_type if selected_store_type != 'all' else None
        search_param = search_term if search_term.strip() else None
        
        # Get filtered mappings from database
        mappings = db_service.get_store_mappings_advanced(
            source=source_param,
            active_only=False,  # We'll filter by active status below
            store_type=store_type_param,
            search_term=search_param
        )
        
        # Apply active filter if specified
        if active_filter is not None:
            mappings = [m for m in mappings if m['active'] == active_filter]
        
        if mappings:
            st.success(f"✅ Found {len(mappings)} store mappings")
            
            # Display mode selection
            display_mode = st.radio(
                "Display Mode:",
                ["📋 Data Editor (Bulk Edit)", "📝 Row-by-Row (Individual Edit)"],
                horizontal=True,
                key=f"store_display_mode_{processor}"
            )
            
            if display_mode == "📋 Data Editor (Bulk Edit)":
                show_store_data_editor_mappings(mappings, db_service, processor)
            else:
                show_store_row_by_row_mappings(mappings, db_service, processor)
                
        else:
            st.info("🔍 No store mappings found with current filters")
            
            # Show helpful information about current filter state
            filter_info = []
            if source_param:
                filter_info.append(f"Source: **{source_param}**")
            if store_type_param:
                filter_info.append(f"Store Type: **{store_type_param}**")
            if search_param:
                filter_info.append(f"Search: **{search_param}**")
            
            if filter_info:
                st.write(f"Current filters: {', '.join(filter_info)}")
                st.write("Try clearing some filters or uploading mappings for this source.")
            else:
                st.write("No mappings exist yet for any source.")
            
            # Suggest creating new mappings
            st.markdown("### 🚀 Get Started")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📥 Download Template", key=f"store_download_empty_{processor}"):
                    show_store_template_download()
            with col2:
                if st.button("📤 Upload Mappings", key=f"store_upload_empty_{processor}"):
                    st.session_state[f'show_store_upload_{processor}'] = True
                    st.rerun()
            with col3:
                if st.button("➕ Add Manually", key=f"store_add_first_{processor}"):
                    st.session_state[f'show_store_add_form_{processor}'] = True
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading store mappings: {e}")
        st.write("**Troubleshooting:**")
        st.write("1. Check database connection")
        st.write("2. Verify migration has been run")
        st.write("3. Check server logs for details")

def show_item_mapping_manager(processor: str, db_service: DatabaseService):
    """Enhanced Item Mapping Management with Standard Template System"""
    
    st.markdown("### 📦 Item Mapping Template System")
    st.caption("Database-backed priority mapping with multiple key types (vendor_item, UPC, EAN, GTIN, SKU)")
    
    # Enhanced UI with filters and controls
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        # Source filter (processor is pre-selected but can be changed)
        source_options = ['all', 'kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
        source_index = source_options.index(processor) if processor in source_options else 1
        selected_source = st.selectbox(
            "📍 Source Filter", 
            source_options, 
            index=source_index,
            key=f"source_filter_{processor}"
        )
    
    with col2:
        # Key type filter
        key_type_options = ['all', 'vendor_item', 'upc', 'ean', 'gtin', 'sku_alias']
        selected_key_type = st.selectbox(
            "🔑 Key Type", 
            key_type_options,
            key=f"key_type_filter_{processor}"
        )
    
    with col3:
        # Active status filter
        active_options = {'All': None, 'Active Only': True, 'Inactive Only': False}
        selected_active_name = st.selectbox(
            "✅ Status", 
            list(active_options.keys()),
            key=f"active_filter_{processor}"
        )
        active_filter = active_options[selected_active_name]
    
    with col4:
        # Search filter
        search_term = st.text_input(
            "🔍 Search", 
            placeholder="Search items, vendors...",
            key=f"search_filter_{processor}"
        )
    
    st.markdown("---")
    
    # Action buttons row
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    
    with col1:
        if st.button("📥 Download Template", key=f"download_template_{processor}"):
            show_template_download()
    
    with col2:
        if st.button("📊 Export Current", key=f"export_current_{processor}"):
            export_current_mappings(db_service, selected_source if selected_source != 'all' else None)
    
    with col3:
        if st.button("📤 Upload Mappings", key=f"upload_mappings_{processor}"):
            st.session_state[f'show_upload_{processor}'] = True
    
    with col4:
        if st.button("➕ Add New Mapping", key=f"add_new_{processor}"):
            st.session_state[f'show_add_form_{processor}'] = True
    
    with col5:
        if st.button("🔄 Refresh Data", key=f"refresh_data_{processor}"):
            st.rerun()
    
    # Show upload form if requested
    if st.session_state.get(f'show_upload_{processor}', False):
        show_mapping_upload_form(db_service, processor)
    
    # Show add form if requested  
    if st.session_state.get(f'show_add_form_{processor}', False):
        show_add_mapping_form(db_service, processor)
    
    st.markdown("---")
    
    # Get and display mappings
    try:
        # Apply filters
        source_param = selected_source if selected_source != 'all' else None
        key_type_param = selected_key_type if selected_key_type != 'all' else None
        search_param = search_term if search_term.strip() else None
        
        # Get filtered mappings from database
        mappings = db_service.get_item_mappings_advanced(
            source=source_param,
            active_only=False,  # We'll filter by active status below
            key_type=key_type_param,
            search_term=search_param
        )
        
        # Apply active filter if specified
        if active_filter is not None:
            mappings = [m for m in mappings if m['active'] == active_filter]
        
        if mappings:
            st.success(f"✅ Found {len(mappings)} item mappings")
            
            # Display mode selection
            display_mode = st.radio(
                "Display Mode:",
                ["📋 Data Editor (Bulk Edit)", "📝 Row-by-Row (Individual Edit)"],
                horizontal=True,
                key=f"display_mode_{processor}"
            )
            
            if display_mode == "📋 Data Editor (Bulk Edit)":
                show_data_editor_mappings(mappings, db_service, processor)
            else:
                show_row_by_row_mappings(mappings, db_service, processor)
                
        else:
            st.info("🔍 No item mappings found with current filters")
            
            # Suggest creating new mappings
            st.markdown("### 🚀 Get Started")
            st.write("Start by downloading the template or adding your first mapping:")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download Empty Template", key=f"download_empty_{processor}"):
                    show_template_download()
            with col2:
                if st.button("➕ Add First Mapping", key=f"add_first_{processor}"):
                    st.session_state[f'show_add_form_{processor}'] = True
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading item mappings: {e}")
        st.write("**Troubleshooting:**")
        st.write("1. Check database connection")
        st.write("2. Verify migration has been run")
        st.write("3. Check server logs for details")

def show_template_download():
    """Show unified template download for all processors"""
    
    # Create unified template with examples for all processors
    unified_template_data = {
        'Source': ['kehe', 'kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
        'RawKeyType': ['vendor_item', 'upc', 'upc', 'vendor_item', 'vendor_item', 'vendor_item'], 
        'RawKeyValue': ['00110368', '728119098687', '123456789012', 'ABC123', 'XYZ789', 'TK001'],
        'MappedItemNumber': ['17-041-1', '17-041-1', 'XO-456', 'XO-789', 'XO-101', 'XO-202'],
        'Vendor': ['KEHE', 'KEHE', 'Whole Foods', 'UNFI', 'UNFI', 'TK Maxx'],
        'MappedDescription': ['BRUSCHETTA ARTICHOKE', 'BRUSCHETTA ARTICHOKE', 'Sample Product 2', 'Sample Product 3', 'Sample Product 4', 'Sample Product 5'],
        'Priority': [100, 200, 100, 100, 100, 100],
        'Active': [True, True, True, True, True, True],
        'Notes': ['Primary KEHE mapping', 'KEHE UPC backup', 'Whole Foods UPC', 'UNFI East vendor item', 'UNFI West vendor item', 'TK Maxx vendor item']
    }
    
    unified_template_df = pd.DataFrame(unified_template_data)
    unified_template_csv = unified_template_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Unified Template",
        data=unified_template_csv,
        file_name="unified_item_mapping_template.csv",
        mime="text/csv",
        help="Download unified item mapping template for all processors"
    )
    
    st.info("📋 **Unified Template Columns (All Processors):**")
    st.write("• **Source**: Order source (kehe, wholefoods, unfi_east, unfi_west, tkmaxx)")
    st.write("• **RawKeyType**: Type of key (vendor_item, upc, ean, gtin, sku_alias)")
    st.write("• **RawKeyValue**: Original item identifier (KEHE number, UPC, vendor item, etc.)")
    st.write("• **MappedItemNumber**: Target Xoro item number")
    st.write("• **Vendor**: Vendor name (optional)")
    st.write("• **MappedDescription**: Product description (optional)")
    st.write("• **Priority**: Resolution priority (100=highest, 999=lowest)")
    st.write("• **Active**: Whether mapping is active (true/false)")
    st.write("• **Notes**: Additional notes (optional)")
    
    st.markdown("---")
    
    # Show examples for each processor
    st.markdown("### 📝 **Examples by Processor:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**KEHE Examples:**")
        st.write("• `kehe, vendor_item, 00110368, 17-041-1` (KEHE number)")
        st.write("• `kehe, upc, 728119098687, 17-041-1` (UPC code)")
        
        st.markdown("**Whole Foods Examples:**")
        st.write("• `wholefoods, upc, 123456789012, XO-456` (UPC)")
        st.write("• `wholefoods, vendor_item, WF123, XO-456` (vendor item)")
    
    with col2:
        st.markdown("**UNFI Examples:**")
        st.write("• `unfi_east, vendor_item, ABC123, XO-789` (vendor item)")
        st.write("• `unfi_west, upc, 987654321098, XO-101` (UPC)")
        
        st.markdown("**TK Maxx Examples:**")
        st.write("• `tkmaxx, vendor_item, TK001, XO-202` (vendor item)")
        st.write("• `tkmaxx, sku_alias, SKU123, XO-202` (SKU alias)")

def export_current_mappings(db_service: DatabaseService, source_filter: str = None):
    """Export current mappings to CSV"""
    
    try:
        # Get current mappings from database
        df = db_service.export_item_mappings_to_dataframe(source=source_filter)
        
        if len(df) == 0:
            st.warning("⚠️ No mappings found to export")
            return
        
        # Generate filename
        source_part = f"_{source_filter}" if source_filter else "_all_sources"
        filename = f"item_mappings{source_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        csv_data = df.to_csv(index=False)
        
        st.download_button(
            label=f"📊 Download {len(df)} Mappings",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            help=f"Export {len(df)} current mappings to CSV"
        )
        
        st.success(f"✅ Ready to download {len(df)} mappings")
        
    except Exception as e:
        st.error(f"❌ Export failed: {e}")

def show_mapping_upload_form(db_service: DatabaseService, processor: str):
    """Show form for uploading mapping files"""
    
    with st.expander("📤 Upload Item Mappings", expanded=True):
        st.write("Upload a CSV file with the unified template format")
        st.info("💡 **Tip**: Use the 'Download Template' button to get the correct format with examples for all processors")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            key=f"upload_file_{processor}",
            help="Use the unified template format with Source, RawKeyType, RawKeyValue, MappedItemNumber columns"
        )
        
        if uploaded_file is not None:
            try:
                # Read and validate uploaded file
                df = pd.read_csv(uploaded_file)
                
                st.write(f"📋 **File Preview** ({len(df)} rows):")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Check if it's legacy KEHE format or unified format
                if 'KeHE Number' in df.columns and 'ItemNumber' in df.columns:
                    # Legacy KEHE format - convert to unified format
                    st.warning("⚠️ **Legacy KEHE Format Detected** - Converting to unified format")
                    converted_df = convert_kehe_to_standard_format(df)
                    st.write("📋 **Converted to Unified Format:**")
                    st.dataframe(converted_df.head(10), use_container_width=True)
                    
                    # Show upload options
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✅ Upload Converted Mappings", key=f"confirm_upload_{processor}"):
                            upload_mappings_to_database(converted_df, db_service, processor)
                    
                    with col2:
                        if st.button("❌ Cancel Upload", key=f"cancel_upload_{processor}"):
                            st.session_state[f'show_upload_{processor}'] = False
                            st.rerun()
                
                else:
                    # Unified format validation
                    required_columns = ['Source', 'RawKeyType', 'RawKeyValue', 'MappedItemNumber']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"❌ Missing required columns: {missing_columns}")
                        st.info("Required columns: Source, RawKeyType, RawKeyValue, MappedItemNumber")
                        st.info("Optional columns: Vendor, MappedDescription, Priority, Active, Notes")
                    else:
                        # Validate source values
                        valid_sources = ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx']
                        invalid_sources = df[~df['Source'].isin(valid_sources)]['Source'].unique()
                        
                        if len(invalid_sources) > 0:
                            st.error(f"❌ Invalid source values: {list(invalid_sources)}")
                            st.info(f"Valid sources: {valid_sources}")
                        else:
                            # Validate key types
                            valid_key_types = ['vendor_item', 'upc', 'ean', 'gtin', 'sku_alias']
                            invalid_key_types = df[~df['RawKeyType'].isin(valid_key_types)]['RawKeyType'].unique()
                            
                            if len(invalid_key_types) > 0:
                                st.error(f"❌ Invalid key types: {list(invalid_key_types)}")
                                st.info(f"Valid key types: {valid_key_types}")
                            else:
                                # Show upload options
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    if st.button("✅ Upload Mappings", key=f"confirm_upload_{processor}"):
                                        upload_mappings_to_database(df, db_service, processor)
                                
                                with col2:
                                    if st.button("❌ Cancel Upload", key=f"cancel_upload_{processor}"):
                                        st.session_state[f'show_upload_{processor}'] = False
                                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

def convert_kehe_to_standard_format(kehe_df: pd.DataFrame) -> pd.DataFrame:
    """Convert KEHE format to standard database format"""
    
    converted_data = []
    
    for _, row in kehe_df.iterrows():
        # Create multiple mappings for KEHE items
        kehe_number = str(row.get('KeHE Number', '')).strip()
        item_number = str(row.get('ItemNumber', '')).strip()
        description = str(row.get('Description', '')).strip()
        upc = str(row.get('UPC', '')).strip()
        
        if kehe_number and item_number:
            # Primary mapping using KEHE number as vendor_item
            converted_data.append({
                'Source': 'kehe',
                'RawKeyType': 'vendor_item',
                'RawKeyValue': kehe_number,
                'MappedItemNumber': item_number,
                'Vendor': 'KEHE',
                'MappedDescription': description if description else None,
                'Priority': 100,
                'Active': True,
                'Notes': 'KEHE vendor item mapping'
            })
            
            # Secondary mapping using UPC if available
            if upc and upc != 'nan' and upc.strip():
                converted_data.append({
                    'Source': 'kehe',
                    'RawKeyType': 'upc',
                    'RawKeyValue': upc,
                    'MappedItemNumber': item_number,
                    'Vendor': 'KEHE',
                    'MappedDescription': description if description else None,
                    'Priority': 200,
                    'Active': True,
                    'Notes': 'KEHE UPC mapping'
                })
    
    return pd.DataFrame(converted_data)

# Customer Mapping Template and Export Functions

def show_customer_template_download():
    """Show customer template download with unified format"""
    
    # Create unified customer template with examples for all processors
    customer_template_data = {
        'Source': ['kehe', 'kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
        'RawCustomerID': ['10005', '10006', 'WF001', 'UNFI001', 'UNFI002', 'TK001'],
        'MappedCustomerName': ['KL - Richmond', 'KL - Richmond', 'IDI - Richmond', 'UNFI East Store', 'UNFI West Store', 'TK Maxx Store'],
        'CustomerType': ['store', 'store', 'store', 'distributor', 'distributor', 'retail'],
        'Priority': [100, 100, 100, 100, 100, 100],
        'Active': [True, True, True, True, True, True],
        'Notes': ['KEHE SPS customer', 'KEHE SPS customer', 'Whole Foods store', 'UNFI East distributor', 'UNFI West distributor', 'TK Maxx retail store']
    }
    
    customer_template_df = pd.DataFrame(customer_template_data)
    customer_template_csv = customer_template_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Customer Template",
        data=customer_template_csv,
        file_name="customer_mapping_template.csv",
        mime="text/csv",
        help="Download unified customer mapping template for all processors"
    )
    
    st.info("📋 **Customer Template Columns (All Processors):**")
    st.write("• **Source**: Order source (kehe, wholefoods, unfi_east, unfi_west, tkmaxx)")
    st.write("• **RawCustomerID**: Original customer identifier from order files")
    st.write("• **MappedCustomerName**: Standardized customer name for Xoro")
    st.write("• **CustomerType**: Type of customer - Use one of:")
    st.write("  - **store**: Retail store location (most common)")
    st.write("  - **distributor**: Distribution center or warehouse")
    st.write("  - **retail**: General retail customer")
    st.write("  - **warehouse**: Storage/fulfillment facility")
    st.write("• **Priority**: Resolution priority (100=highest, 999=lowest)")
    st.write("• **Active**: Enable/disable mapping (True/False, 1/0, Yes/No)")
    st.write("• **Notes**: Optional description or comments")
    
    st.success("💡 **CustomerType Legend:**")
    st.write("📍 **store** = Individual retail store locations (e.g., 'Store #123', 'Richmond Location')")
    st.write("🏭 **distributor** = Distribution centers and warehouses (e.g., 'UNFI East DC', 'KeHe Nashville')")  
    st.write("🛍️ **retail** = General retail customers or chains (e.g., 'Target', 'Walmart')")
    st.write("📦 **warehouse** = Storage and fulfillment facilities (e.g., 'Amazon FC', 'Regional Warehouse')")

def export_current_customer_mappings(db_service: DatabaseService, source_filter: str = None):
    """Export current customer mappings to CSV"""
    
    try:
        # Get current mappings from database
        df = db_service.export_customer_mappings_to_dataframe(source=source_filter)
        
        if len(df) == 0:
            st.warning("⚠️ No customer mappings found to export")
            return
        
        # Generate filename
        source_part = f"_{source_filter}" if source_filter else "_all_sources"
        filename = f"customer_mappings{source_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        csv_data = df.to_csv(index=False)
        
        st.download_button(
            label=f"📊 Download {len(df)} Customer Mappings",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            help=f"Export {len(df)} current customer mappings to CSV"
        )
        
        st.success(f"✅ Ready to download {len(df)} customer mappings")
        
    except Exception as e:
        st.error(f"❌ Export failed: {e}")

# Store Mapping Template and Export Functions

def show_store_template_download():
    """Show store template download with unified format"""
    
    # Create unified store template with examples for all processors
    store_template_data = {
        'Source': ['kehe', 'kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
        'RawStoreID': ['10005', '10006', 'WF001', 'UNFI001', 'UNFI002', 'TK001'],
        'MappedStoreName': ['KL - Richmond', 'KL - Richmond', 'IDI - Richmond', 'UNFI East Store', 'UNFI West Store', 'TK Maxx Store'],
        'StoreType': ['retail', 'retail', 'retail', 'warehouse', 'warehouse', 'retail'],
        'Priority': [100, 100, 100, 100, 100, 100],
        'Active': [True, True, True, True, True, True],
        'Notes': ['KEHE SPS store', 'KEHE SPS store', 'Whole Foods store', 'UNFI East warehouse', 'UNFI West warehouse', 'TK Maxx retail store']
    }
    
    store_template_df = pd.DataFrame(store_template_data)
    store_template_csv = store_template_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Store Template",
        data=store_template_csv,
        file_name="store_mapping_template.csv",
        mime="text/csv",
        help="Download unified store mapping template for all processors"
    )
    
    st.info("📋 **Store Template Columns (All Processors):**")
    st.write("• **Source**: Order source (kehe, wholefoods, unfi_east, unfi_west, tkmaxx)")
    st.write("• **RawStoreID**: Original store identifier from order files")
    st.write("• **MappedStoreName**: Standardized store name for Xoro")
    st.write("• **StoreType**: Type of store location - Use one of:")
    st.write("  - **retail**: Individual retail store locations")
    st.write("  - **warehouse**: Storage and distribution facilities")
    st.write("  - **distribution**: Distribution centers")
    st.write("  - **corporate**: Corporate offices and headquarters")
    st.write("• **Priority**: Resolution priority (100=highest, 999=lowest)")
    st.write("• **Active**: Enable/disable mapping (True/False, 1/0, Yes/No)")
    st.write("• **Notes**: Optional description or comments")
    
    st.success("💡 **StoreType Legend:**")
    st.write("🏪 **retail** = Individual store locations (e.g., 'Store #123', 'Main Street Location', 'Downtown Branch')")
    st.write("📦 **warehouse** = Storage facilities (e.g., 'Regional Warehouse', 'Distribution Facility', 'Storage Center')")  
    st.write("🏭 **distribution** = Distribution centers (e.g., 'UNFI East DC', 'KeHe Nashville', 'Regional Distribution')")
    st.write("🏢 **corporate** = Corporate offices (e.g., 'Corporate HQ', 'Regional Office', 'Admin Center')")

def export_current_store_mappings(db_service: DatabaseService, source_filter: str = None):
    """Export current store mappings to CSV"""
    
    try:
        # Get current mappings from database
        df = db_service.export_store_mappings_to_dataframe(source=source_filter)
        
        if len(df) == 0:
            st.warning("⚠️ No store mappings found to export")
            return
        
        # Generate filename
        source_part = f"_{source_filter}" if source_filter else "_all_sources"
        filename = f"store_mappings{source_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        csv_data = df.to_csv(index=False)
        
        st.download_button(
            label=f"📊 Download {len(df)} Store Mappings",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            help=f"Export {len(df)} current store mappings to CSV"
        )
        
        st.success(f"✅ Ready to download {len(df)} store mappings")
        
    except Exception as e:
        st.error(f"❌ Export failed: {e}")

# Placeholder functions for customer and store mapping UI components
# These would need to be implemented similar to the item mapping functions

def show_customer_mapping_upload_form(db_service: DatabaseService, processor: str):
    """Show form for uploading customer mapping files"""
    
    with st.expander("📤 Upload Customer Mappings", expanded=True):
        st.write("Upload a CSV file with the unified customer mapping template format")
        
        st.info("💡 **Quick Reference - CustomerType Values:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("📍 **store** - Individual retail locations")
            st.write("🏭 **distributor** - Distribution centers")
        with col2:
            st.write("🛍️ **retail** - General retail customers") 
            st.write("📦 **warehouse** - Storage facilities")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            key=f"customer_upload_file_{processor}",
            help="Use the unified customer template format"
        )
        
        if uploaded_file is not None:
            try:
                # Read and validate uploaded file
                df = pd.read_csv(uploaded_file)
                
                st.write(f"📋 **File Preview** ({len(df)} rows):")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Validate required columns
                required_columns = ['Source', 'RawCustomerID', 'MappedCustomerName']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                    st.write("**Required columns:**")
                    for col in required_columns:
                        st.write(f"• {col}")
                else:
                    st.success("✅ File format is valid!")
                    
                    # Show column mapping
                    st.write("**Column Mapping:**")
                    col_mapping = {
                        'Source': 'source',
                        'RawCustomerID': 'raw_customer_id', 
                        'MappedCustomerName': 'mapped_customer_name',
                        'CustomerType': 'customer_type',
                        'Priority': 'priority',
                        'Active': 'active',
                        'Notes': 'notes'
                    }
                    
                    for csv_col, db_col in col_mapping.items():
                        if csv_col in df.columns:
                            st.write(f"• {csv_col} → {db_col}")
                    
                    # Upload button
                    if st.button("📤 Upload Customer Mappings", key=f"upload_customer_btn_{processor}"):
                        # Convert DataFrame to list of dictionaries
                        mappings_data = []
                        for _, row in df.iterrows():
                            mapping_data = {
                                'source': str(row.get('Source', processor)).strip(),
                                'raw_customer_id': str(row.get('RawCustomerID', '')).strip(),
                                'mapped_customer_name': str(row.get('MappedCustomerName', '')).strip(),
                                'customer_type': str(row.get('CustomerType', 'store')).strip(),
                                'priority': int(row.get('Priority', 100)),
                                'active': parse_boolean(row.get('Active', True)),
                                'notes': str(row.get('Notes', '')).strip() if pd.notna(row.get('Notes')) else ''
                            }
                            mappings_data.append(mapping_data)
                        
                        # Upload to database
                        with st.spinner("Uploading customer mappings..."):
                            result = db_service.bulk_upsert_customer_mappings(mappings_data)
                        
                        # Show results
                        if result['errors'] == 0:
                            st.success(f"✅ Successfully uploaded {result['added']} new mappings and updated {result['updated']} existing mappings!")
                        else:
                            st.warning(f"⚠️ Upload completed with {result['errors']} errors:")
                            for error in result['error_details']:
                                st.error(f"• {error}")
                        
                        # Clear the upload form
                        st.session_state[f'show_customer_upload_{processor}'] = False
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                st.write("**Troubleshooting:**")
                st.write("1. Make sure the file is a valid CSV")
                st.write("2. Check that all required columns are present")
                st.write("3. Verify the data format matches the template")

def show_add_customer_mapping_form(db_service: DatabaseService, processor: str):
    """Show form for adding new customer mapping"""
    
    with st.expander("➕ Add New Customer Mapping", expanded=True):
        st.write("Add a new customer mapping manually")
        
        with st.form(key=f"add_customer_form_{processor}"):
            col1, col2 = st.columns(2)
            
            with col1:
                source = st.selectbox(
                    "Source",
                    options=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
                    index=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'].index(processor) if processor in ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'] else 0,
                    key=f"add_customer_source_{processor}"
                )
                
                raw_customer_id = st.text_input(
                    "Raw Customer ID",
                    placeholder="e.g., 10005, WF001, UNFI001",
                    key=f"add_customer_raw_id_{processor}"
                )
                
                mapped_customer_name = st.text_input(
                    "Mapped Customer Name",
                    placeholder="e.g., KL - Richmond, IDI - Richmond",
                    key=f"add_customer_mapped_name_{processor}"
                )
            
            with col2:
                customer_type = st.selectbox(
                    "Customer Type",
                    options=['store', 'distributor', 'warehouse', 'retail'],
                    index=0,
                    key=f"add_customer_type_{processor}"
                )
                
                priority = st.number_input(
                    "Priority",
                    min_value=1,
                    max_value=999,
                    value=100,
                    help="Lower values = higher priority",
                    key=f"add_customer_priority_{processor}"
                )
                
                active = st.checkbox(
                    "Active",
                    value=True,
                    key=f"add_customer_active_{processor}"
                )
            
            notes = st.text_area(
                "Notes (Optional)",
                placeholder="Additional notes about this customer mapping...",
                key=f"add_customer_notes_{processor}"
            )
            
            # Submit button
            submitted = st.form_submit_button("➕ Add Customer Mapping", type="primary")
            
            if submitted:
                # Validate required fields
                if not raw_customer_id.strip():
                    st.error("❌ Raw Customer ID is required")
                elif not mapped_customer_name.strip():
                    st.error("❌ Mapped Customer Name is required")
                else:
                    # Create mapping data
                    mapping_data = [{
                        'source': source,
                        'raw_customer_id': raw_customer_id.strip(),
                        'mapped_customer_name': mapped_customer_name.strip(),
                        'customer_type': customer_type,
                        'priority': priority,
                        'active': active,
                        'notes': notes.strip() if notes.strip() else None
                    }]
                    
                    # Add to database
                    with st.spinner("Adding customer mapping..."):
                        result = db_service.bulk_upsert_customer_mappings(mapping_data)
                    
                    # Show results
                    if result['errors'] == 0:
                        st.success(f"✅ Successfully added customer mapping!")
                        # Clear the form
                        st.session_state[f'show_customer_add_form_{processor}'] = False
                        st.rerun()
                    else:
                        st.error(f"❌ Error adding customer mapping: {result['error_details'][0] if result['error_details'] else 'Unknown error'}")

def show_customer_data_editor_mappings(mappings: list, db_service: DatabaseService, processor: str):
    """Show customer mappings in data editor for bulk editing"""
    
    if not mappings:
        st.info("No customer mappings to display")
        return
    
    # Convert mappings to DataFrame for editing
    df_data = []
    for mapping in mappings:
        df_data.append({
            'ID': mapping['id'],
            'Source': mapping['source'],
            'Raw Customer ID': mapping['raw_customer_id'],
            'Mapped Customer Name': mapping['mapped_customer_name'],
            'Customer Type': mapping['customer_type'],
            'Priority': mapping['priority'],
            'Active': mapping['active'],
            'Notes': mapping['notes']
        })
    
    df = pd.DataFrame(df_data)
    
    # Display editable DataFrame
    st.write("**Edit customer mappings (double-click to edit):**")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        key=f"customer_data_editor_{processor}",
        column_config={
            "ID": st.column_config.NumberColumn("ID", disabled=True),
            "Source": st.column_config.SelectboxColumn(
                "Source",
                options=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
                required=True
            ),
            "Raw Customer ID": st.column_config.TextColumn("Raw Customer ID", required=True),
            "Mapped Customer Name": st.column_config.TextColumn("Mapped Customer Name", required=True),
            "Customer Type": st.column_config.SelectboxColumn(
                "Customer Type",
                options=['store', 'distributor', 'warehouse', 'retail'],
                required=True
            ),
            "Priority": st.column_config.NumberColumn("Priority", min_value=1, max_value=999, required=True),
            "Active": st.column_config.CheckboxColumn("Active"),
            "Notes": st.column_config.TextColumn("Notes")
        }
    )
    
    # Save changes button
    if st.button("💾 Save Changes", key=f"save_customer_changes_{processor}"):
        # Convert edited DataFrame back to mapping format
        updated_mappings = []
        for _, row in edited_df.iterrows():
            updated_mappings.append({
                'id': row['ID'],
                'source': row['Source'],
                'raw_customer_id': row['Raw Customer ID'],
                'mapped_customer_name': row['Mapped Customer Name'],
                'customer_type': row['Customer Type'],
                'priority': int(row['Priority']),
                'active': bool(row['Active']),
                'notes': row['Notes'] if pd.notna(row['Notes']) else None
            })
        
        # Update database
        with st.spinner("Saving changes..."):
            # For now, we'll use bulk upsert (this could be optimized for updates only)
            mappings_data = []
            for mapping in updated_mappings:
                mappings_data.append({
                    'source': mapping['source'],
                    'raw_customer_id': mapping['raw_customer_id'],
                    'mapped_customer_name': mapping['mapped_customer_name'],
                    'customer_type': mapping['customer_type'],
                    'priority': mapping['priority'],
                    'active': mapping['active'],
                    'notes': mapping['notes']
                })
            
            result = db_service.bulk_upsert_customer_mappings(mappings_data)
        
        if result['errors'] == 0:
            st.success(f"✅ Successfully saved changes! Updated {result['updated']} mappings.")
            st.rerun()
        else:
            st.error(f"❌ Error saving changes: {result['error_details']}")
    
    # Delete selected mappings
    st.markdown("---")
    st.write("**Delete Mappings:**")
    
    # Get IDs to delete
    delete_ids = st.multiselect(
        "Select mappings to delete:",
        options=[mapping['id'] for mapping in mappings],
        format_func=lambda x: f"ID {x}: {next(m['raw_customer_id'] for m in mappings if m['id'] == x)} → {next(m['mapped_customer_name'] for m in mappings if m['id'] == x)}",
        key=f"delete_customer_select_{processor}"
    )
    
    if delete_ids and st.button("🗑️ Delete Selected", type="secondary", key=f"delete_customer_btn_{processor}"):
        with st.spinner("Deleting mappings..."):
            # Note: We need to add a delete method to the database service
            st.info("Delete functionality will be implemented in the database service")
            # For now, just show what would be deleted
            st.write(f"Would delete {len(delete_ids)} mappings: {delete_ids}")

def show_customer_row_by_row_mappings(mappings: list, db_service: DatabaseService, processor: str):
    """Show customer mappings in row-by-row format"""
    
    if not mappings:
        st.info("No customer mappings to display")
        return
    
    st.write(f"**Customer Mappings ({len(mappings)} total):**")
    
    # Pagination
    items_per_page = 10
    total_pages = (len(mappings) - 1) // items_per_page + 1
    
    if total_pages > 1:
        page = st.selectbox("Page:", range(1, total_pages + 1), key=f"customer_page_{processor}")
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_mappings = mappings[start_idx:end_idx]
    else:
        page_mappings = mappings
    
    # Display mappings in cards
    for i, mapping in enumerate(page_mappings):
        with st.expander(f"ID {mapping['id']}: {mapping['raw_customer_id']} → {mapping['mapped_customer_name']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Source:** {mapping['source']}")
                st.write(f"**Raw Customer ID:** {mapping['raw_customer_id']}")
                st.write(f"**Mapped Customer Name:** {mapping['mapped_customer_name']}")
                st.write(f"**Customer Type:** {mapping['customer_type']}")
            
            with col2:
                st.write(f"**Priority:** {mapping['priority']}")
                st.write(f"**Active:** {'✅ Yes' if mapping['active'] else '❌ No'}")
                st.write(f"**Created:** {mapping['created_at'].strftime('%Y-%m-%d %H:%M') if mapping['created_at'] else 'N/A'}")
                st.write(f"**Updated:** {mapping['updated_at'].strftime('%Y-%m-%d %H:%M') if mapping['updated_at'] else 'N/A'}")
            
            if mapping['notes']:
                st.write(f"**Notes:** {mapping['notes']}")
            
            # Edit and delete buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✏️ Edit", key=f"edit_customer_{mapping['id']}_{processor}"):
                    st.session_state[f'edit_customer_{mapping["id"]}'] = True
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_customer_{mapping['id']}_{processor}"):
                    st.session_state[f'delete_customer_{mapping["id"]}'] = True
            
            with col3:
                if st.button("📋 Copy", key=f"copy_customer_{mapping['id']}_{processor}"):
                    st.session_state[f'copy_customer_{mapping["id"]}'] = True
            
            # Edit form (if edit button clicked)
            if st.session_state.get(f'edit_customer_{mapping["id"]}', False):
                st.markdown("---")
                st.write("**Edit Customer Mapping:**")
                
                with st.form(key=f"edit_customer_form_{mapping['id']}_{processor}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_source = st.selectbox(
                            "Source",
                            options=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
                            index=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'].index(mapping['source']),
                            key=f"edit_customer_source_{mapping['id']}_{processor}"
                        )
                        
                        edit_raw_id = st.text_input(
                            "Raw Customer ID",
                            value=mapping['raw_customer_id'],
                            key=f"edit_customer_raw_id_{mapping['id']}_{processor}"
                        )
                        
                        edit_mapped_name = st.text_input(
                            "Mapped Customer Name",
                            value=mapping['mapped_customer_name'],
                            key=f"edit_customer_mapped_name_{mapping['id']}_{processor}"
                        )
                    
                    with col2:
                        edit_type = st.selectbox(
                            "Customer Type",
                            options=['store', 'distributor', 'warehouse', 'retail'],
                            index=['store', 'distributor', 'warehouse', 'retail'].index(mapping['customer_type']),
                            key=f"edit_customer_type_{mapping['id']}_{processor}"
                        )
                        
                        edit_priority = st.number_input(
                            "Priority",
                            min_value=1,
                            max_value=999,
                            value=mapping['priority'],
                            key=f"edit_customer_priority_{mapping['id']}_{processor}"
                        )
                        
                        edit_active = st.checkbox(
                            "Active",
                            value=mapping['active'],
                            key=f"edit_customer_active_{mapping['id']}_{processor}"
                        )
                    
                    edit_notes = st.text_area(
                        "Notes",
                        value=mapping['notes'] or "",
                        key=f"edit_customer_notes_{mapping['id']}_{processor}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            # Update mapping
                            updated_mapping = [{
                                'source': edit_source,
                                'raw_customer_id': edit_raw_id.strip(),
                                'mapped_customer_name': edit_mapped_name.strip(),
                                'customer_type': edit_type,
                                'priority': edit_priority,
                                'active': edit_active,
                                'notes': edit_notes.strip() if edit_notes.strip() else None
                            }]
                            
                            with st.spinner("Saving changes..."):
                                result = db_service.bulk_upsert_customer_mappings(updated_mapping)
                            
                            if result['errors'] == 0:
                                st.success("✅ Customer mapping updated successfully!")
                                st.session_state[f'edit_customer_{mapping["id"]}'] = False
                                st.rerun()
                            else:
                                st.error(f"❌ Error updating mapping: {result['error_details'][0] if result['error_details'] else 'Unknown error'}")
                    
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state[f'edit_customer_{mapping["id"]}'] = False
                            st.rerun()
            
            # Delete confirmation (if delete button clicked)
            if st.session_state.get(f'delete_customer_{mapping["id"]}', False):
                st.markdown("---")
                st.warning(f"⚠️ Are you sure you want to delete this customer mapping?")
                st.write(f"**ID {mapping['id']}:** {mapping['raw_customer_id']} → {mapping['mapped_customer_name']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Delete", key=f"confirm_delete_customer_{mapping['id']}_{processor}"):
                        st.info("Delete functionality will be implemented in the database service")
                        st.session_state[f'delete_customer_{mapping["id"]}'] = False
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_delete_customer_{mapping['id']}_{processor}"):
                        st.session_state[f'delete_customer_{mapping["id"]}'] = False
                        st.rerun()
            
            # Copy functionality (if copy button clicked)
            if st.session_state.get(f'copy_customer_{mapping["id"]}', False):
                st.markdown("---")
                st.info("📋 Customer mapping copied to clipboard (functionality to be implemented)")
                st.session_state[f'copy_customer_{mapping["id"]}'] = False

def show_store_mapping_upload_form(db_service: DatabaseService, processor: str):
    """Show form for uploading store mapping files"""
    
    with st.expander("📤 Upload Store Mappings", expanded=True):
        st.write("Upload a CSV file with the unified store mapping template format")
        
        st.info("💡 **Quick Reference - StoreType Values:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("🏪 **retail** - Retail store locations")
            st.write("📦 **warehouse** - Storage facilities")
        with col2:
            st.write("🏭 **distribution** - Distribution centers") 
            st.write("🏢 **corporate** - Corporate offices")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            key=f"store_upload_file_{processor}",
            help="Use the unified store template format"
        )
        
        if uploaded_file is not None:
            try:
                # Read and validate uploaded file
                df = pd.read_csv(uploaded_file)
                
                st.write(f"📋 **File Preview** ({len(df)} rows):")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Validate required columns
                required_columns = ['Source', 'RawStoreID', 'MappedStoreName']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                    st.write("**Required columns:**")
                    for col in required_columns:
                        st.write(f"• {col}")
                else:
                    st.success("✅ File format is valid!")
                    
                    # Show column mapping
                    st.write("**Column Mapping:**")
                    col_mapping = {
                        'Source': 'source',
                        'RawStoreID': 'raw_store_id', 
                        'MappedStoreName': 'mapped_store_name',
                        'StoreType': 'store_type',
                        'Priority': 'priority',
                        'Active': 'active',
                        'Notes': 'notes'
                    }
                    
                    for csv_col, db_col in col_mapping.items():
                        if csv_col in df.columns:
                            st.write(f"• {csv_col} → {db_col}")
                    
                    # Upload button
                    if st.button("📤 Upload Store Mappings", key=f"upload_store_btn_{processor}"):
                        # Convert DataFrame to list of dictionaries
                        mappings_data = []
                        for _, row in df.iterrows():
                            mapping_data = {
                                'source': str(row.get('Source', processor)).strip(),
                                'raw_store_id': str(row.get('RawStoreID', '')).strip(),
                                'mapped_store_name': str(row.get('MappedStoreName', '')).strip(),
                                'store_type': str(row.get('StoreType', 'retail')).strip(),
                                'priority': int(row.get('Priority', 100)),
                                'active': parse_boolean(row.get('Active', True)),
                                'notes': str(row.get('Notes', '')).strip() if pd.notna(row.get('Notes')) else ''
                            }
                            mappings_data.append(mapping_data)
                        
                        # Upload to database
                        with st.spinner("Uploading store mappings..."):
                            result = db_service.bulk_upsert_store_mappings(mappings_data)
                        
                        # Show results
                        if result['errors'] == 0:
                            st.success(f"✅ Successfully uploaded {result['added']} new mappings and updated {result['updated']} existing mappings!")
                            st.info("🔄 Refreshing data to show updated mappings...")
                        else:
                            st.warning(f"⚠️ Upload completed with {result['errors']} errors:")
                            for error in result['error_details']:
                                st.error(f"• {error}")
                        
                        # Clear the upload form and refresh
                        st.session_state[f'show_store_upload_{processor}'] = False
                        
                        # Force a rerun to refresh the data
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                st.write("**Troubleshooting:**")
                st.write("1. Make sure the file is a valid CSV")
                st.write("2. Check that all required columns are present")
                st.write("3. Verify the data format matches the template")

def show_add_store_mapping_form(db_service: DatabaseService, processor: str):
    """Show form for adding new store mapping"""
    
    with st.expander("➕ Add New Store Mapping", expanded=True):
        st.write("Add a new store mapping manually")
        
        with st.form(key=f"add_store_form_{processor}"):
            col1, col2 = st.columns(2)
            
            with col1:
                source = st.selectbox(
                    "Source",
                    ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
                    index=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'].index(processor) if processor in ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'] else 0,
                    help="Order source system"
                )
                
                raw_store_id = st.text_input(
                    "Raw Store ID *",
                    placeholder="Enter original store ID from orders",
                    help="The store ID as it appears in the order files"
                )
                
                mapped_store_name = st.text_input(
                    "Mapped Store Name *", 
                    placeholder="Enter standardized store name",
                    help="The standardized store name for Xoro"
                )
                
            with col2:
                store_type = st.selectbox(
                    "Store Type",
                    ['retail', 'warehouse', 'distribution', 'corporate'],
                    help="Type of store location"
                )
                
                priority = st.number_input(
                    "Priority",
                    min_value=1,
                    max_value=999,
                    value=100,
                    help="Resolution priority (100=highest, 999=lowest)"
                )
                
                active = st.checkbox(
                    "Active",
                    value=True,
                    help="Enable this mapping"
                )
                
            notes = st.text_area(
                "Notes",
                placeholder="Optional notes about this store mapping",
                help="Additional information about this mapping"
            )
            
            submitted = st.form_submit_button("➕ Add Store Mapping")
            
            if submitted:
                if not raw_store_id or not mapped_store_name:
                    st.error("❌ Please fill in all required fields (marked with *)")
                else:
                    try:
                        # Create mapping data
                        mapping_data = [{
                            'source': source,
                            'raw_store_id': raw_store_id.strip(),
                            'mapped_store_name': mapped_store_name.strip(),
                            'store_type': store_type,
                            'priority': priority,
                            'active': active,
                            'notes': notes.strip() if notes else ''
                        }]
                        
                        # Add to database
                        with st.spinner("Adding store mapping..."):
                            result = db_service.bulk_upsert_store_mappings(mapping_data)
                        
                        # Show results
                        if result['errors'] == 0:
                            st.success(f"✅ Successfully added store mapping: {raw_store_id} → {mapped_store_name}")
                        else:
                            st.error(f"❌ Failed to add mapping:")
                            for error in result['error_details']:
                                st.error(f"• {error}")
                        
                        # Clear the form
                        st.session_state[f'show_store_add_form_{processor}'] = False
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error adding store mapping: {e}")
        
        # Cancel button
        if st.button("❌ Cancel", key=f"cancel_add_store_{processor}"):
            st.session_state[f'show_store_add_form_{processor}'] = False
            st.rerun()

def show_store_data_editor_mappings(mappings: list, db_service: DatabaseService, processor: str):
    """Show store mappings in data editor for bulk editing"""
    
    if not mappings:
        st.info("📝 No store mappings found to edit")
        return
    
    st.write("### 📊 Bulk Edit Store Mappings")
    st.caption("Edit multiple store mappings at once using the data editor below")
    
    # Convert mappings to DataFrame for editing
    df_data = []
    for mapping in mappings:
        df_data.append({
            'ID': mapping['id'],
            'Source': mapping['source'],
            'RawStoreID': mapping['raw_store_id'],
            'MappedStoreName': mapping['mapped_store_name'],
            'StoreType': mapping['store_type'],
            'Priority': mapping['priority'],
            'Active': mapping['active'],
            'Notes': mapping.get('notes', '')
        })
    
    df = pd.DataFrame(df_data)
    
    # Data editor configuration
    column_config = {
        'ID': st.column_config.NumberColumn('ID', disabled=True, width='small'),
        'Source': st.column_config.SelectboxColumn(
            'Source',
            options=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
            width='medium'
        ),
        'RawStoreID': st.column_config.TextColumn('Raw Store ID', width='medium'),
        'MappedStoreName': st.column_config.TextColumn('Mapped Store Name', width='large'),
        'StoreType': st.column_config.SelectboxColumn(
            'Store Type',
            options=['retail', 'warehouse', 'distribution', 'corporate'],
            width='medium'
        ),
        'Priority': st.column_config.NumberColumn(
            'Priority',
            min_value=1,
            max_value=999,
            width='small'
        ),
        'Active': st.column_config.CheckboxColumn('Active', width='small'),
        'Notes': st.column_config.TextColumn('Notes', width='large')
    }
    
    # Show data editor
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic",
        key=f"store_data_editor_{processor}"
    )
    
    # Save changes button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Changes", key=f"save_store_bulk_{processor}"):
            try:
                # Convert edited DataFrame back to list of dictionaries
                updated_mappings = []
                for _, row in edited_df.iterrows():
                    mapping_data = {
                        'id': int(row['ID']),
                        'source': str(row['Source']).strip(),
                        'raw_store_id': str(row['RawStoreID']).strip(),
                        'mapped_store_name': str(row['MappedStoreName']).strip(),
                        'store_type': str(row['StoreType']).strip(),
                        'priority': int(row['Priority']),
                        'active': bool(row['Active']),
                        'notes': str(row['Notes']).strip() if pd.notna(row['Notes']) else ''
                    }
                    updated_mappings.append(mapping_data)
                
                # Update database
                with st.spinner("Saving changes..."):
                    result = db_service.bulk_upsert_store_mappings(updated_mappings)
                
                # Show results
                if result['errors'] == 0:
                    st.success(f"✅ Successfully updated {result['updated']} store mappings!")
                    st.rerun()
                else:
                    st.error(f"❌ Update failed with {result['errors']} errors:")
                    for error in result['error_details']:
                        st.error(f"• {error}")
                        
            except Exception as e:
                st.error(f"❌ Error saving changes: {e}")
    
    with col2:
        if st.button("🔄 Reset", key=f"reset_store_bulk_{processor}"):
            st.rerun()
    
    with col3:
        st.info("💡 **Tip**: Add new rows using the + button, edit cells directly, then click Save Changes")

def show_store_row_by_row_mappings(mappings: list, db_service: DatabaseService, processor: str):
    """Show store mappings in row-by-row format for individual editing"""
    
    if not mappings:
        st.info("📝 No store mappings found to edit")
        return
    
    st.write("### 📝 Individual Store Mapping Editor")
    st.caption("Edit store mappings one by one with detailed controls")
    
    # Pagination controls
    items_per_page = 5
    total_pages = (len(mappings) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                f"Page (showing {items_per_page} per page)",
                range(1, total_pages + 1),
                key=f"store_page_selector_{processor}"
            )
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(mappings))
        page_mappings = mappings[start_idx:end_idx]
        
        st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(mappings)} store mappings")
    else:
        page_mappings = mappings
    
    # Display each mapping in an expandable section
    for i, mapping in enumerate(page_mappings):
        mapping_id = mapping['id']
        
        with st.expander(
            f"🏪 **{mapping['raw_store_id']}** → **{mapping['mapped_store_name']}** "
            f"({'✅ Active' if mapping['active'] else '❌ Inactive'})",
            expanded=False
        ):
            # Create form for this mapping
            with st.form(key=f"edit_store_form_{mapping_id}_{processor}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    source = st.selectbox(
                        "Source",
                        ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'],
                        index=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'].index(mapping['source']) if mapping['source'] in ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'] else 0,
                        key=f"store_source_{mapping_id}",
                        help="Order source system"
                    )
                    
                    raw_store_id = st.text_input(
                        "Raw Store ID",
                        value=mapping['raw_store_id'],
                        key=f"store_raw_id_{mapping_id}",
                        help="The store ID as it appears in order files"
                    )
                    
                    mapped_store_name = st.text_input(
                        "Mapped Store Name",
                        value=mapping['mapped_store_name'],
                        key=f"store_mapped_name_{mapping_id}",
                        help="The standardized store name for Xoro"
                    )
                
                with col2:
                    store_type = st.selectbox(
                        "Store Type",
                        ['retail', 'warehouse', 'distribution', 'corporate'],
                        index=['retail', 'warehouse', 'distribution', 'corporate'].index(mapping['store_type']) if mapping['store_type'] in ['retail', 'warehouse', 'distribution', 'corporate'] else 0,
                        key=f"store_type_{mapping_id}",
                        help="Type of store location"
                    )
                    
                    priority = st.number_input(
                        "Priority",
                        min_value=1,
                        max_value=999,
                        value=mapping['priority'],
                        key=f"store_priority_{mapping_id}",
                        help="Resolution priority (100=highest, 999=lowest)"
                    )
                    
                    active = st.checkbox(
                        "Active",
                        value=mapping['active'],
                        key=f"store_active_{mapping_id}",
                        help="Enable this mapping"
                    )
                
                notes = st.text_area(
                    "Notes",
                    value=mapping.get('notes', ''),
                    key=f"store_notes_{mapping_id}",
                    help="Additional information about this mapping"
                )
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    update_submitted = st.form_submit_button("💾 Update", type="primary")
                
                with col2:
                    delete_submitted = st.form_submit_button("🗑️ Delete", type="secondary")
                
                if update_submitted:
                    if not raw_store_id or not mapped_store_name:
                        st.error("❌ Raw Store ID and Mapped Store Name are required")
                    else:
                        try:
                            # Update mapping data
                            mapping_data = [{
                                'id': mapping_id,
                                'source': source,
                                'raw_store_id': raw_store_id.strip(),
                                'mapped_store_name': mapped_store_name.strip(),
                                'store_type': store_type,
                                'priority': priority,
                                'active': active,
                                'notes': notes.strip() if notes else ''
                            }]
                            
                            # Update database
                            with st.spinner("Updating store mapping..."):
                                result = db_service.bulk_upsert_store_mappings(mapping_data)
                            
                            # Show results
                            if result['errors'] == 0:
                                st.success(f"✅ Successfully updated store mapping: {raw_store_id} → {mapped_store_name}")
                                st.rerun()
                            else:
                                st.error(f"❌ Update failed:")
                                for error in result['error_details']:
                                    st.error(f"• {error}")
                                    
                        except Exception as e:
                            st.error(f"❌ Error updating store mapping: {e}")
                
                if delete_submitted:
                    try:
                        # Delete from database (implement this in db_service if needed)
                        st.warning("🗑️ Delete functionality - Implementation needed in database service")
                        
                    except Exception as e:
                        st.error(f"❌ Error deleting store mapping: {e}")
            
            # Show mapping metadata
            st.caption(f"**ID:** {mapping['id']} | **Created:** {mapping.get('created_at', 'N/A')} | **Updated:** {mapping.get('updated_at', 'N/A')}")
            
            # Copy functionality placeholder
            if st.button(f"📋 Copy Mapping", key=f"copy_store_{mapping_id}"):
                st.session_state[f'copy_store_{mapping_id}'] = True
            
            if st.session_state.get(f'copy_store_{mapping_id}', False):
                st.markdown("---")
                st.info("📋 Store mapping copied to clipboard (functionality to be implemented)")
                st.session_state[f'copy_store_{mapping_id}'] = False

def upload_mappings_to_database(df: pd.DataFrame, db_service: DatabaseService, processor: str):
    """Upload mappings from DataFrame to database"""
    
    try:
        # Convert DataFrame to list of dictionaries
        mappings_data = []
        for _, row in df.iterrows():
            mapping = {
                'source': str(row.get('Source', '')).strip(),
                'raw_item': str(row.get('RawKeyValue', '')).strip(),
                'mapped_item': str(row.get('MappedItemNumber', '')).strip(),
                'key_type': str(row.get('RawKeyType', 'vendor_item')).strip(),
                'priority': int(row.get('Priority', 100)),
                'active': bool(row.get('Active', True)),
                'vendor': str(row.get('Vendor', '')).strip() if pd.notna(row.get('Vendor')) else None,
                'mapped_description': str(row.get('MappedDescription', '')).strip() if pd.notna(row.get('MappedDescription')) else None,
                'notes': str(row.get('Notes', '')).strip() if pd.notna(row.get('Notes')) else None
            }
            mappings_data.append(mapping)
        
        # Bulk upload to database
        results = db_service.bulk_upsert_item_mappings(mappings_data)
        
        # Show results
        if results['errors'] == 0:
            st.success(f"✅ Successfully uploaded {results['added']} new mappings and updated {results['updated']} existing mappings")
        else:
            st.warning(f"⚠️ Upload completed with {results['errors']} errors. Added: {results['added']}, Updated: {results['updated']}")
            with st.expander("❌ Error Details"):
                for error in results['error_details']:
                    st.write(f"• {error}")
        
        # Close upload form and refresh
        st.session_state[f'show_upload_{processor}'] = False
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")

def show_add_mapping_form(db_service: DatabaseService, processor: str):
    """Show form for adding new mapping"""
    
    with st.expander("➕ Add New Item Mapping", expanded=True):
        with st.form(f"add_mapping_form_{processor}"):
            col1, col2 = st.columns(2)
            
            with col1:
                source = st.selectbox("Source", ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'], 
                                    index=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'].index(processor) if processor in ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'] else 0)
                key_type = st.selectbox("Key Type", ['vendor_item', 'upc', 'ean', 'gtin', 'sku_alias'])
                raw_item = st.text_input("Raw Key Value *", placeholder="e.g., 00110368")
                mapped_item = st.text_input("Mapped Item Number *", placeholder="e.g., XO-123")
                
            with col2:
                vendor = st.text_input("Vendor", placeholder="Optional")
                mapped_description = st.text_input("Description", placeholder="Optional")
                priority = st.number_input("Priority", min_value=1, max_value=999, value=100, help="Lower = higher priority")
                active = st.checkbox("Active", value=True)
                notes = st.text_area("Notes", placeholder="Optional notes")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("✅ Add Mapping")
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state[f'show_add_form_{processor}'] = False
                    st.rerun()
            
            if submitted:
                if raw_item and mapped_item:
                    try:
                        mapping_data = [{
                            'source': source,
                            'raw_item': raw_item,
                            'mapped_item': mapped_item,
                            'key_type': key_type,
                            'priority': priority,
                            'active': active,
                            'vendor': vendor if vendor.strip() else None,
                            'mapped_description': mapped_description if mapped_description.strip() else None,
                            'notes': notes if notes.strip() else None
                        }]
                        
                        results = db_service.bulk_upsert_item_mappings(mapping_data)
                        
                        if results['errors'] == 0:
                            st.success("✅ Mapping added successfully!")
                            st.session_state[f'show_add_form_{processor}'] = False
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to add mapping: {results['error_details']}")
                            
                    except Exception as e:
                        st.error(f"❌ Error adding mapping: {e}")
                else:
                    st.error("❌ Raw Key Value and Mapped Item Number are required")

def show_data_editor_mappings(mappings: list, db_service: DatabaseService, processor: str):
    """Show mappings in Streamlit data editor for bulk editing"""
    
    try:
        # Convert to DataFrame for data editor
        df_data = []
        for mapping in mappings:
            df_data.append({
                'ID': mapping['id'],
                'Source': mapping['source'],
                'Key Type': mapping['key_type'],
                'Raw Value': mapping['raw_item'],
                'Mapped Item': mapping['mapped_item'],
                'Vendor': mapping['vendor'],
                'Description': mapping['mapped_description'],
                'Priority': mapping['priority'],
                'Active': mapping['active'],
                'Notes': mapping['notes']
            })
        
        if not df_data:
            st.info("No mappings to display")
            return
        
        df = pd.DataFrame(df_data)
        
        # Configure column types for data editor
        column_config = {
            'ID': st.column_config.NumberColumn('ID', disabled=True, width='small'),
            'Source': st.column_config.SelectboxColumn('Source', 
                options=['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'], width='medium'),
            'Key Type': st.column_config.SelectboxColumn('Key Type',
                options=['vendor_item', 'upc', 'ean', 'gtin', 'sku_alias'], width='medium'),
            'Raw Value': st.column_config.TextColumn('Raw Value', width='medium'),
            'Mapped Item': st.column_config.TextColumn('Mapped Item', width='medium'),
            'Vendor': st.column_config.TextColumn('Vendor', width='medium'),
            'Description': st.column_config.TextColumn('Description', width='large'),
            'Priority': st.column_config.NumberColumn('Priority', min_value=1, max_value=999, width='small'),
            'Active': st.column_config.CheckboxColumn('Active', width='small'),
            'Notes': st.column_config.TextColumn('Notes', width='large')
        }
        
        # Show data editor
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            key=f"data_editor_{processor}"
        )
        
        # Show action buttons
        col1, col2, col3 = st.columns([2, 2, 6])
        
        with col1:
            if st.button("💾 Save Changes", key=f"save_bulk_{processor}"):
                save_bulk_changes(edited_df, df, db_service, processor)
        
        with col2:
            if st.button("🗑️ Delete Selected", key=f"delete_bulk_{processor}"):
                st.session_state[f'show_delete_confirm_{processor}'] = True
        
        # Show delete confirmation if requested
        if st.session_state.get(f'show_delete_confirm_{processor}', False):
            show_bulk_delete_confirmation(edited_df, db_service, processor)
            
    except Exception as e:
        st.error(f"❌ Error displaying data editor: {e}")

def show_row_by_row_mappings(mappings: list, db_service: DatabaseService, processor: str):
    """Show mappings in row-by-row format with individual edit/delete buttons"""
    
    try:
        # Pagination for large datasets
        items_per_page = 10
        total_items = len(mappings)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            page = st.selectbox(
                "Page", 
                range(1, total_pages + 1), 
                key=f"page_selector_{processor}"
            ) - 1
        else:
            page = 0
        
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_mappings = mappings[start_idx:end_idx]
        
        st.write(f"Showing {len(page_mappings)} of {total_items} mappings (Page {page + 1} of {total_pages})")
        
        # Display each mapping as a card with edit/delete options
        for i, mapping in enumerate(page_mappings):
            with st.container():
                # Create a border using markdown
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 1rem; margin: 0.5rem 0; 
                           background-color: {'#f0f8f0' if mapping['active'] else '#f8f0f0'}">
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([6, 2, 2])
                
                with col1:
                    # Main mapping info
                    st.write(f"**{mapping['source'].upper()}** • {mapping['key_type']}")
                    st.write(f"**Raw:** `{mapping['raw_item']}` → **Mapped:** `{mapping['mapped_item']}`")
                    
                    if mapping['vendor']:
                        st.write(f"🏭 **Vendor:** {mapping['vendor']}")
                    if mapping['mapped_description']:
                        st.write(f"📝 **Description:** {mapping['mapped_description']}")
                    if mapping['notes']:
                        st.write(f"💬 **Notes:** {mapping['notes']}")
                    
                    # Status and priority info
                    status_color = "🟢" if mapping['active'] else "🔴"
                    st.write(f"{status_color} **Status:** {'Active' if mapping['active'] else 'Inactive'} • **Priority:** {mapping['priority']}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{mapping['id']}_{processor}"):
                        st.session_state[f'edit_mapping_{processor}'] = mapping
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{mapping['id']}_{processor}"):
                        st.session_state[f'delete_mapping_{processor}'] = mapping
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Show edit form if a mapping is being edited
        if st.session_state.get(f'edit_mapping_{processor}'):
            show_edit_mapping_form(st.session_state[f'edit_mapping_{processor}'], db_service, processor)
        
        # Show delete confirmation if a mapping is being deleted
        if st.session_state.get(f'delete_mapping_{processor}'):
            show_delete_confirmation(st.session_state[f'delete_mapping_{processor}'], db_service, processor)
            
    except Exception as e:
        st.error(f"❌ Error displaying mappings: {e}")

def save_bulk_changes(edited_df: pd.DataFrame, original_df: pd.DataFrame, db_service: DatabaseService, processor: str):
    """Save bulk changes from data editor"""
    
    try:
        changes_made = False
        mappings_data = []
        
        for idx, row in edited_df.iterrows():
            original_row = original_df.iloc[idx]
            
            # Check if any changes were made to this row
            if not row.equals(original_row):
                changes_made = True
                
                mapping = {
                    'source': str(row['Source']).strip(),
                    'raw_item': str(row['Raw Value']).strip(),
                    'mapped_item': str(row['Mapped Item']).strip(),
                    'key_type': str(row['Key Type']).strip(),
                    'priority': int(row['Priority']),
                    'active': bool(row['Active']),
                    'vendor': str(row['Vendor']).strip() if pd.notna(row['Vendor']) and str(row['Vendor']).strip() else None,
                    'mapped_description': str(row['Description']).strip() if pd.notna(row['Description']) and str(row['Description']).strip() else None,
                    'notes': str(row['Notes']).strip() if pd.notna(row['Notes']) and str(row['Notes']).strip() else None
                }
                mappings_data.append(mapping)
        
        if changes_made:
            results = db_service.bulk_upsert_item_mappings(mappings_data)
            
            if results['errors'] == 0:
                st.success(f"✅ Successfully saved {len(mappings_data)} changes!")
                st.rerun()
            else:
                st.error(f"❌ {results['errors']} errors occurred while saving changes")
                with st.expander("Error Details"):
                    for error in results['error_details']:
                        st.write(f"• {error}")
        else:
            st.info("ℹ️ No changes detected")
            
    except Exception as e:
        st.error(f"❌ Error saving changes: {e}")

def show_edit_mapping_form(mapping: dict, db_service: DatabaseService, processor: str):
    """Show form to edit individual mapping"""
    
    with st.expander("✏️ Edit Item Mapping", expanded=True):
        with st.form(f"edit_mapping_form_{processor}"):
            col1, col2 = st.columns(2)
            
            with col1:
                source = st.selectbox("Source", ['kehe', 'wholefoods', 'unfi_east', 'unfi_west', 'tkmaxx'], 
                                    value=mapping['source'])
                key_type = st.selectbox("Key Type", ['vendor_item', 'upc', 'ean', 'gtin', 'sku_alias'],
                                      value=mapping['key_type'])
                raw_item = st.text_input("Raw Key Value *", value=mapping['raw_item'])
                mapped_item = st.text_input("Mapped Item Number *", value=mapping['mapped_item'])
                
            with col2:
                vendor = st.text_input("Vendor", value=mapping['vendor'] or "")
                mapped_description = st.text_input("Description", value=mapping['mapped_description'] or "")
                priority = st.number_input("Priority", min_value=1, max_value=999, value=mapping['priority'])
                active = st.checkbox("Active", value=mapping['active'])
                notes = st.text_area("Notes", value=mapping['notes'] or "")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Save Changes")
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    del st.session_state[f'edit_mapping_{processor}']
                    st.rerun()
            
            if submitted:
                try:
                    mapping_data = [{
                        'source': source,
                        'raw_item': raw_item,
                        'mapped_item': mapped_item,
                        'key_type': key_type,
                        'priority': priority,
                        'active': active,
                        'vendor': vendor if vendor.strip() else None,
                        'mapped_description': mapped_description if mapped_description.strip() else None,
                        'notes': notes if notes.strip() else None
                    }]
                    
                    results = db_service.bulk_upsert_item_mappings(mapping_data)
                    
                    if results['errors'] == 0:
                        st.success("✅ Mapping updated successfully!")
                        del st.session_state[f'edit_mapping_{processor}']
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to update mapping: {results['error_details']}")
                        
                except Exception as e:
                    st.error(f"❌ Error updating mapping: {e}")

def show_delete_confirmation(mapping: dict, db_service: DatabaseService, processor: str):
    """Show delete confirmation dialog"""
    
    with st.expander("🗑️ Confirm Delete", expanded=True):
        st.warning(f"Are you sure you want to delete this mapping?")
        st.write(f"**Source:** {mapping['source']}")
        st.write(f"**Raw Value:** {mapping['raw_item']}")
        st.write(f"**Mapped Item:** {mapping['mapped_item']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Confirm Delete", key=f"confirm_delete_{processor}"):
                try:
                    count = db_service.delete_item_mappings([mapping['id']])
                    if count > 0:
                        st.success("✅ Mapping deleted successfully!")
                        del st.session_state[f'delete_mapping_{processor}']
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete mapping")
                except Exception as e:
                    st.error(f"❌ Error deleting mapping: {e}")
        
        with col2:
            if st.button("❌ Cancel Delete", key=f"cancel_delete_{processor}"):
                del st.session_state[f'delete_mapping_{processor}']
                st.rerun()

def show_bulk_delete_confirmation(df: pd.DataFrame, db_service: DatabaseService, processor: str):
    """Show bulk delete confirmation"""
    
    with st.expander("🗑️ Bulk Delete Confirmation", expanded=True):
        st.warning("This will delete ALL currently displayed mappings. This action cannot be undone!")
        st.write(f"**Total mappings to delete:** {len(df)}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Confirm Bulk Delete", key=f"confirm_bulk_delete_{processor}"):
                try:
                    mapping_ids = df['ID'].tolist()
                    count = db_service.delete_item_mappings(mapping_ids)
                    if count > 0:
                        st.success(f"✅ Successfully deleted {count} mappings!")
                        del st.session_state[f'show_delete_confirm_{processor}']
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete mappings")
                except Exception as e:
                    st.error(f"❌ Error deleting mappings: {e}")
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_bulk_delete_{processor}"):
                del st.session_state[f'show_delete_confirm_{processor}']
                st.rerun()

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
            
            # Display mappings with edit/delete functionality
            if len(page_df) > 0:
                # Toggle between table view and data editor view
                view_option = st.radio(
                    "View Mode:",
                    ["📋 Data Editor View", "📝 Row-by-Row Edit View"],
                    horizontal=True,
                    key=f"view_mode_{mapping_type}_{processor}"
                )
                
                if view_option == "📋 Data Editor View":
                    display_data_editor_mappings(filtered_df, file_path, columns, mapping_type, processor)
                else:
                    display_editable_mappings_table(page_df, file_path, columns, mapping_type, processor, page, items_per_page)
                
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
        column_names = list(columns) if not isinstance(columns, list) else columns
        df = pd.DataFrame(data=None, index=[], columns=column_names)
        df.to_csv(file_path, index=False)
        
        st.success(f"✅ Created new mapping file: {file_path}")
        
    except Exception as e:
        st.error(f"❌ Failed to create mapping file: {e}")

def display_editable_mappings_table(page_df, file_path: str, columns: list, mapping_type: str, processor: str, page: int, items_per_page: int):
    """Display mappings table with inline editing and delete functionality"""
    
    import pandas as pd
    
    # Load full dataframe for operations
    full_df = pd.read_csv(file_path, dtype=str)
    
    # Create columns for table display
    table_cols = st.columns([0.7, 0.15, 0.15])  # Main table, Edit, Delete
    
    with table_cols[0]:
        st.write("**Mappings**")
    with table_cols[1]:
        st.write("**Edit**")
    with table_cols[2]:
        st.write("**Delete**")
    
    # Display each row with edit/delete options
    for idx, (_, row) in enumerate(page_df.iterrows()):
        actual_index = (page * items_per_page) + idx
        
        # Create columns for this row
        row_cols = st.columns([0.7, 0.15, 0.15])
        
        with row_cols[0]:
            # Display row data in a container
            with st.container():
                row_data = []
                for col in columns:
                    row_data.append(f"**{col}**: {row[col] if pd.notna(row[col]) else 'None'}")
                st.write(" | ".join(row_data))
        
        with row_cols[1]:
            # Edit button
            if st.button("✏️ Edit", key=f"edit_{mapping_type}_{processor}_{actual_index}"):
                st.session_state[f"editing_{mapping_type}_{processor}_{actual_index}"] = True
                st.rerun()
        
        with row_cols[2]:
            # Delete button
            if st.button("🗑️ Delete", key=f"delete_{mapping_type}_{processor}_{actual_index}"):
                delete_mapping_row(file_path, actual_index, mapping_type, processor)
        
        # Show edit form if in edit mode
        if st.session_state.get(f"editing_{mapping_type}_{processor}_{actual_index}", False):
            with st.form(f"edit_form_{mapping_type}_{processor}_{actual_index}"):
                st.write(f"**Edit {mapping_type} Mapping**")
                
                edit_cols = st.columns(len(columns))
                new_values = {}
                
                for i, col in enumerate(columns):
                    with edit_cols[i]:
                        current_value = row[col] if pd.notna(row[col]) else ""
                        new_values[col] = st.text_input(col, value=current_value, key=f"edit_{col}_{actual_index}")
                
                submit_cols = st.columns(2)
                with submit_cols[0]:
                    if st.form_submit_button("💾 Save Changes"):
                        save_mapping_edit(file_path, actual_index, new_values, mapping_type, processor)
                        del st.session_state[f"editing_{mapping_type}_{processor}_{actual_index}"]
                        st.rerun()
                
                with submit_cols[1]:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state[f"editing_{mapping_type}_{processor}_{actual_index}"]
                        st.rerun()
        
        # Add divider between rows
        st.divider()

def delete_mapping_row(file_path: str, row_index: int, mapping_type: str, processor: str):
    """Delete a mapping row"""
    
    import pandas as pd
    
    try:
        df = pd.read_csv(file_path, dtype=str)
        
        # Remove the row at the specified index
        if 0 <= row_index < len(df):
            deleted_row = df.iloc[row_index]
            df = df.drop(index=row_index).reset_index(drop=True)
            df.to_csv(file_path, index=False)
            
            st.success(f"✅ Deleted {mapping_type.lower()} mapping: {deleted_row.iloc[0]}")
            st.rerun()
        else:
            st.error("❌ Invalid row index for deletion")
            
    except Exception as e:
        st.error(f"❌ Failed to delete mapping: {e}")

def save_mapping_edit(file_path: str, row_index: int, new_values: dict, mapping_type: str, processor: str):
    """Save edited mapping values"""
    
    import pandas as pd
    
    try:
        df = pd.read_csv(file_path, dtype=str)
        
        # Update the row at the specified index
        if 0 <= row_index < len(df):
            for col, value in new_values.items():
                if col in df.columns:
                    df.at[row_index, col] = value.strip() if value else ""
            
            df.to_csv(file_path, index=False)
            st.success(f"✅ Updated {mapping_type.lower()} mapping successfully")
        else:
            st.error("❌ Invalid row index for editing")
            
    except Exception as e:
        st.error(f"❌ Failed to save mapping edit: {e}")

def display_data_editor_mappings(df, file_path: str, columns: list, mapping_type: str, processor: str):
    """Display mappings using Streamlit data editor for easy bulk editing"""
    
    import pandas as pd
    
    st.write(f"**Data Editor - Edit multiple {mapping_type.lower()} mappings at once**")
    
    # Instructions for using the data editor
    with st.expander("ℹ️ How to use Data Editor"):
        st.markdown("""
        **Editing:**
        - Click any cell to edit its value
        - Press Enter to confirm changes
        
        **Adding Rows:**
        - Click the ➕ button at the bottom to add new rows
        - Fill in the required fields for new mappings
        
        **Deleting Rows:**
        - Click the row number (left side) to select entire rows
        - Hold Ctrl/Cmd to select multiple rows
        - Press Delete key or use the 🗑️ button to remove selected rows
        
        **Saving:**
        - Click "💾 Save All Changes" to save your modifications
        """)
    
    # Use data editor for bulk editing with enhanced configuration
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",  # Allow adding/deleting rows
        key=f"data_editor_{mapping_type}_{processor}",
        column_config={
            col: st.column_config.TextColumn(
                col,
                width="medium",
                required=True,
                help=f"Enter the {col.lower()}"
            ) for col in columns
        },
        hide_index=False,  # Show row numbers for easier selection
    )
    
    # Save changes button and controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button(f"💾 Save All Changes", key=f"save_all_{mapping_type}_{processor}"):
            save_bulk_mapping_changes(edited_df, file_path, mapping_type, processor)
    
    with col2:
        # Show changes summary
        original_count = len(df)
        edited_count = len(edited_df)
        
        if original_count != edited_count:
            if edited_count > original_count:
                st.success(f"📈 Added {edited_count - original_count} rows (Total: {edited_count})")
            elif edited_count < original_count:
                st.warning(f"📉 Removed {original_count - edited_count} rows (Total: {edited_count})")
        
        # Check for changes in existing rows
        if original_count > 0 and edited_count > 0:
            min_rows = min(original_count, edited_count)
            try:
                changes_detected = not df.iloc[:min_rows].equals(edited_df.iloc[:min_rows])
                if changes_detected:
                    st.info("✏️ Content changes detected")
            except:
                st.info("✏️ Changes detected")
    
    with col3:
        # Quick delete all button with confirmation
        if st.button("🗑️ Clear All", key=f"clear_all_{mapping_type}_{processor}"):
            st.session_state[f"confirm_clear_{mapping_type}_{processor}"] = True
        
        if st.session_state.get(f"confirm_clear_{mapping_type}_{processor}", False):
            st.warning("⚠️ Delete all mappings?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Yes", key=f"confirm_yes_{mapping_type}_{processor}"):
                    clear_all_mappings(file_path, mapping_type, processor)
                    del st.session_state[f"confirm_clear_{mapping_type}_{processor}"]
                    st.rerun()
            with col_no:
                if st.button("❌ No", key=f"confirm_no_{mapping_type}_{processor}"):
                    del st.session_state[f"confirm_clear_{mapping_type}_{processor}"]
                    st.rerun()

def save_bulk_mapping_changes(edited_df, file_path: str, mapping_type: str, processor: str):
    """Save bulk changes from data editor"""
    
    try:
        # Clean the dataframe - remove empty rows and strip whitespace
        cleaned_df = edited_df.dropna(how='all').copy()
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
        
        # Save to CSV
        cleaned_df.to_csv(file_path, index=False)
        
        st.success(f"✅ Successfully saved {len(cleaned_df)} {mapping_type.lower()} mappings")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Failed to save bulk changes: {e}")

def clear_all_mappings(file_path: str, mapping_type: str, processor: str):
    """Clear all mappings from the file"""
    
    import pandas as pd
    import os
    
    try:
        # Get column names from existing file
        if os.path.exists(file_path):
            existing_df = pd.read_csv(file_path, nrows=0)  # Just get headers
            columns = existing_df.columns.tolist()
        else:
            # Fallback columns based on mapping type
            if mapping_type.lower() == "customer":
                columns = ["Raw Customer ID", "Mapped Customer Name"]
            elif mapping_type.lower() == "store":
                columns = ["Raw Store ID", "Xoro Store Name"]
            else:
                columns = ["Raw Item Number", "Mapped Item Number"]
        
        # Create empty DataFrame
        column_names = list(columns) if not isinstance(columns, list) else columns
        empty_df = pd.DataFrame(data=None, index=[], columns=column_names)
        empty_df.to_csv(file_path, index=False)
        
        st.success(f"✅ Cleared all {mapping_type.lower()} mappings")
        
    except Exception as e:
        st.error(f"❌ Failed to clear mappings: {e}")

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
