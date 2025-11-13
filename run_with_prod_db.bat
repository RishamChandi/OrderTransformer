@echo off
REM Script to run Streamlit app connected to production database
REM Use this for testing locally before deploying

echo ========================================
echo Connecting to PRODUCTION database
echo ========================================
echo.
echo WARNING: You are connecting to the PRODUCTION database!
echo Any changes you make will affect production data.
echo.
pause

set ENVIRONMENT=production
set DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db

echo Starting Streamlit application...
echo.
python -m streamlit run app.py --server.port 8502

pause

