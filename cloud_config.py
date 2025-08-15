"""
Configuration for Replit deployment
"""
import os
import streamlit as st

def get_database_url():
    """Get database URL from environment variables (prioritizes Replit environment)"""
    # Always prioritize environment variables for Replit deployment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Only fall back to Streamlit secrets if running on Streamlit Cloud
        if is_streamlit_cloud():
            try:
                database_url = st.secrets["postgres"]["DATABASE_URL"]
            except (KeyError, FileNotFoundError):
                st.error("Database configuration not found. Please set DATABASE_URL environment variable.")
                st.stop()
        else:
            st.error("DATABASE_URL environment variable not found. Please configure your database connection.")
            st.stop()
    
    return database_url

def is_cloud_deployment():
    """Check if running on any cloud deployment (Replit or Streamlit Cloud)"""
    return is_replit_deployment() or is_streamlit_cloud()

def is_replit_deployment():
    """Check if running on Replit"""
    return bool(
        os.getenv('REPL_ID') or 
        os.getenv('REPLIT_DB_URL') or 
        os.getenv('REPL_SLUG') or 
        os.getenv('REPL_OWNER') or
        '/home/runner' in os.getcwd()
    )

def is_streamlit_cloud():
    """Check if running on Streamlit Cloud"""
    return (
        "streamlit.io" in os.getenv("HOSTNAME", "") or
        os.getenv('STREAMLIT_SHARING') or 
        os.getenv('STREAMLIT_CLOUD')
    )

def get_deployment_environment():
    """Get the current deployment environment"""
    if is_replit_deployment():
        return "replit"
    elif is_streamlit_cloud():
        return "streamlit_cloud"
    else:
        return "local"