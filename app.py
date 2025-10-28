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
    
    # Fixed sleek header with dynamic screen usage
    st.markdown("""
    <style>
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-bottom: 3px solid rgba(255,255,255,0.2);
    }
    
    .header-content {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
    }
    
    .header-title {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        margin: 0;
        font-size: 1rem;
        font-weight: 400;
    }
    
    .header-stats {
        display: flex;
        gap: 1rem;
        align-items: center;
        color: white;
        font-size: 0.9rem;
    }
    
    .stat-item {
        background: rgba(255,255,255,0.1);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        backdrop-filter: blur(10px);
    }
    
    .main-content {
        margin-top: 120px;
        padding: 0 1rem;
    }
    
    /* Fix sidebar to start below header */
    .sidebar {
        width: 280px !important;
        min-width: 280px;
        padding-top: 120px !important;
    }
    
    /* Target Streamlit sidebar container */
    [data-testid="stSidebar"] {
        padding-top: 120px !important;
    }
    
    /* Target sidebar content area */
    [data-testid="stSidebar"] > div {
        padding-top: 120px !important;
    }
    
    /* Alternative approach - adjust the main content area */
    .main .block-container {
        padding-top: 120px !important;
    }
    
    /* Ensure the entire app content starts below header */
    .stApp > div:first-child {
        padding-top: 120px !important;
    }
    
    .main-container {
        display: flex;
        gap: 1rem;
        max-width: 1600px;
        margin: 0 auto;
    }
    
    .content-area {
        flex: 1;
        min-width: 0;
    }
    
    @media (max-width: 1200px) {
        .header-content {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .header-stats {
            flex-wrap: wrap;
            justify-content: center;
        }
    }
    
    @media (max-width: 768px) {
        .fixed-header {
            padding: 0.8rem 1rem;
        }
        
        .header-title {
            font-size: 1.5rem;
        }
        
        .main-content {
            margin-top: 100px;
        }
    }
    </style>
    
    <div class="fixed-header">
        <div class="header-content">
            <div>
                <h1 class="header-title">🔄 Order Transformer</h1>
                <p class="header-subtitle">Convert sales orders into standardized Xoro CSV format</p>
            </div>
            <div class="header-stats">
                <div class="stat-item">📊 Multi-Client</div>
                <div class="stat-item">🔄 Real-time</div>
                <div class="stat-item">📈 Analytics</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database service
    db_service = DatabaseService()
    
    # Main content wrapper for better space utilization
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
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
                mappings = session.query(db_service.StoreMapping).filter_by(source=processor).all()
                data = []
                for m in mappings:
                    data.append({
                        'Source': m.source,
                        'Raw Customer ID': m.raw_name,
                        'Mapped Customer Name': m.mapped_name,
                        'Customer Type': m.store_type,
                        'Priority': m.priority,
                        'Active': m.active,
                        'Notes': m.notes or ''
                    })
            elif mapping_type == "store":
                mappings = session.query(db_service.StoreMapping).filter_by(source=processor).all()
                data = []
                for m in mappings:
                    data.append({
                        'Source': m.source,
                        'Raw Store ID': m.raw_name,
                        'Mapped Store Name': m.mapped_name,
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
                        'Item Description': getattr(m, 'item_description', ''),
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
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Upload Mappings", key=f"confirm_upload_{mapping_type}_{processor}"):
                        upload_mappings_to_database(df, db_service, processor, mapping_type)
                        st.session_state[f'show_{mapping_type}_upload_{processor}'] = False
                        st.rerun()
                
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
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).all()
                elif mapping_type == "store":
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).all()
                elif mapping_type == "item":
                    mappings = session.query(db_service.ItemMapping).filter_by(source=processor).all()
                
                if mappings:
                    # Create selection interface
                    mapping_data = []
                    for m in mappings:
                        if mapping_type in ["customer", "store"]:
                            mapping_data.append({
                                'ID': m.id,
                                'Raw Name': m.raw_name,
                                'Mapped Name': m.mapped_name,
                                'Type': m.store_type,
                                'Active': m.active
                            })
                        else:  # item
                            mapping_data.append({
                                'ID': m.id,
                                'Raw Item': m.raw_item,
                                'Mapped Item': m.mapped_item,
                                'Active': getattr(m, 'active', True)
                            })
                    
                    df = pd.DataFrame(mapping_data)
                    selected_rows = st.dataframe(df, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Delete Selected", key=f"delete_selected_{mapping_type}_{processor}"):
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
                if mapping_type in ["customer", "store"]:
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).all()
                else:
                    mappings = session.query(db_service.ItemMapping).filter_by(source=processor).all()
                
                if mappings:
                    # Create editable dataframe
                    mapping_data = []
                    for m in mappings:
                        if mapping_type in ["customer", "store"]:
                            mapping_data.append({
                                'ID': m.id,
                                'Raw Name': m.raw_name,
                                'Mapped Name': m.mapped_name,
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
                                'Description': getattr(m, 'item_description', ''),
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
                if mapping_type in ["customer", "store"]:
                    mappings = session.query(db_service.StoreMapping).filter_by(source=processor).all()
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
                                    raw_name = st.text_input("Raw Name", value=mapping.raw_name, key=f"raw_{mapping.id}_{processor}")
                                    mapped_name = st.text_input("Mapped Name", value=mapping.mapped_name, key=f"mapped_{mapping.id}_{processor}")
                                    mapping_type_val = st.text_input("Type", value=mapping.store_type, key=f"type_{mapping.id}_{processor}")
                                else:  # item
                                    raw_item = st.text_input("Raw Item", value=mapping.raw_item, key=f"raw_{mapping.id}_{processor}")
                                    mapped_item = st.text_input("Mapped Item", value=mapping.mapped_item, key=f"mapped_{mapping.id}_{processor}")
                                    description = st.text_input("Description", value=getattr(mapping, 'item_description', ''), key=f"desc_{mapping.id}_{processor}")
                                
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
            if mapping_type in ["customer", "store"]:
                mappings = session.query(db_service.StoreMapping).filter_by(source=processor).all()
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
                            'Raw Name': m.raw_name,
                            'Mapped Name': m.mapped_name,
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
                            'Description': getattr(m, 'item_description', ''),
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
def upload_mappings_to_database(df: pd.DataFrame, db_service: DatabaseService, processor: str, mapping_type: str):
    """Upload mappings to database"""
    try:
        mappings_data = []
        for _, row in df.iterrows():
            if mapping_type in ["customer", "store"]:
                mappings_data.append({
                    'source': processor,
                    'raw_name': str(row.get('Raw Customer ID' if mapping_type == 'customer' else 'Raw Store ID', '')).strip(),
                    'mapped_name': str(row.get('Mapped Customer Name' if mapping_type == 'customer' else 'Mapped Store Name', '')).strip(),
                    'store_type': str(row.get('Customer Type' if mapping_type == 'customer' else 'Store Type', 'distributor')).strip(),
                    'priority': int(row.get('Priority', 100)),
                    'active': bool(row.get('Active', True)),
                    'notes': str(row.get('Notes', '')).strip()
                })
            else:  # item
                mappings_data.append({
                    'source': processor,
                    'raw_item': str(row.get('Raw Item', '')).strip(),
                    'mapped_item': str(row.get('Mapped Item', '')).strip(),
                    'item_description': str(row.get('Item Description', '')).strip(),
                    'priority': int(row.get('Priority', 100)),
                    'active': bool(row.get('Active', True)),
                    'notes': str(row.get('Notes', '')).strip()
                })
        
        if mapping_type in ["customer", "store"]:
            result = db_service.bulk_upsert_store_mappings(mappings_data)
        else:
            result = db_service.bulk_upsert_item_mappings(mappings_data)
        
        if result['success']:
            st.success(f"✅ Successfully uploaded {result['inserted']} new {mapping_type} mappings")
            if result['updated'] > 0:
                st.info(f"Updated {result['updated']} existing mappings")
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
                'item_description': form_data['item_description'],
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
                mapping.raw_name = form_data['raw_name']
                mapping.mapped_name = form_data['mapped_name']
                mapping.store_type = form_data['mapping_type_val']
                mapping.priority = form_data['priority']
                mapping.active = form_data['active']
                mapping.notes = form_data['notes']
            else:  # item
                mapping.raw_item = form_data['raw_item']
                mapping.mapped_item = form_data['mapped_item']
                mapping.item_description = form_data['description']
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

    # Close main content wrapper
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
