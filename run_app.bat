@echo off
set ENVIRONMENT=local
set DATABASE_URL=sqlite:///./orderparser_dev.db
streamlit run app.py
