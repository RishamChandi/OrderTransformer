@echo off
REM Script to run Streamlit app
REM NOTE: This script does NOT set DATABASE_URL - use .env file instead
REM The .env file should contain your Render database URL

echo ========================================
echo Starting Order Transformer App
echo ========================================
echo.
echo NOTE: This app requires a Render database.
echo Make sure DATABASE_URL is set in .env file.
echo.

streamlit run app.py --server.port 8502
