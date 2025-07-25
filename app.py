import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
from parsers.wholefoods_parser import WholeFoodsParser
from parsers.unfi_west_parser import UNFIWestParser
from parsers.unfi_parser import UNFIParser
from parsers.tkmaxx_parser import TKMaxxParser
from utils.xoro_template import XoroTemplate

def main():
    st.title("Order Transformer - Multiple Sources to Xoro CSV")
    st.write("Convert sales orders from different sources into standardized Xoro import CSV format")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Order source selection
    order_sources = {
        "Whole Foods": WholeFoodsParser(),
        "UNFI West": UNFIWestParser(),
        "UNFI": UNFIParser(),
        "TK Maxx": TKMaxxParser()
    }
    
    selected_source = st.sidebar.selectbox(
        "Select Order Source",
        list(order_sources.keys())
    )
    
    st.subheader(f"Processing {selected_source} Orders")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload order files",
        type=['html', 'csv', 'xlsx'],
        accept_multiple_files=True,
        help=f"Upload {selected_source} order files for conversion"
    )
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} file(s)")
        
        # Process files button
        if st.button("Process Orders", type="primary"):
            process_orders(uploaded_files, order_sources[selected_source], selected_source)

def process_orders(uploaded_files, parser, source_name):
    """Process uploaded files and convert to Xoro format"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_converted_data = []
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
                # Convert to Xoro format
                xoro_template = XoroTemplate()
                converted_data = xoro_template.convert_to_xoro(parsed_data, source_name)
                all_converted_data.extend(converted_data)
                
                st.success(f"✅ Successfully processed {uploaded_file.name}")
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
        st.write(f"**Total Orders Processed:** {len(all_converted_data)}")
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

if __name__ == "__main__":
    main()
