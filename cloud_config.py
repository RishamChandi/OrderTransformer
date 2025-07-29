"""
Configuration for Streamlit Cloud deployment
"""
import os
import streamlit as st

def get_database_url():
    """Get database URL from environment or Streamlit secrets"""
    # Try environment variable first (for local development)
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Try Streamlit secrets (for cloud deployment)
        try:
            database_url = st.secrets["postgres"]["DATABASE_URL"]
        except (KeyError, FileNotFoundError):
            st.error("Database configuration not found. Please set DATABASE_URL in secrets.")
            st.stop()
    
    return database_url

def is_cloud_deployment():
    """Check if running on Streamlit Cloud"""
    return "streamlit.io" in os.getenv("HOSTNAME", "")