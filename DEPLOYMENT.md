# Deployment Guide

## Quick Start with Docker (Recommended)

1. **Clone/Extract the project files**
2. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```
3. **Access the application at http://localhost:5000**

## Manual Deployment

### 1. Database Setup
Set up PostgreSQL database:
```sql
CREATE DATABASE orderdb;
CREATE USER orderuser WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE orderdb TO orderuser;
```

### 2. Environment Variables
Create a `.env` file:
```bash
DATABASE_URL=postgresql://orderuser:your_password@localhost:5432/orderdb
ENVIRONMENT=production
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python init_database.py
```

### 5. Run Application
```bash
streamlit run app.py --server.port 5000
```

## Cloud Deployment Options

### Streamlit Cloud
1. Push code to GitHub repository
2. Connect to Streamlit Cloud
3. Add DATABASE_URL to secrets
4. Deploy directly

### Heroku
1. Add Procfile: `web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
2. Add Heroku Postgres addon
3. Configure DATABASE_URL environment variable
4. Deploy via Git

### AWS/DigitalOcean/GCP
- Use the provided Dockerfile
- Set up managed PostgreSQL instance
- Configure environment variables
- Deploy container

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (required)
- `ENVIRONMENT`: deployment environment (optional: production/development/local)
- `STREAMLIT_SERVER_PORT`: port number (default: 5000)

## Database Schema
The application automatically creates required tables:
- customers
- stores  
- items
- mappings
- orders

## Mapping Files
Ensure these CSV files are present in the `mappings/` directory:
- `kehe_customer_mapping.csv`
- `kehe_item_mapping.csv`

## Health Check
Access `http://your-domain/?health=check` to verify deployment status.