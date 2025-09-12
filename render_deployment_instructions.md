# Render Deployment Instructions

## 📦 **Project Files for Render Deployment**

### **Core Application Structure:**
```
order-transformation-platform/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .streamlit/config.toml          # Streamlit configuration
├── database/                       # Database module
│   ├── models.py                   # SQLAlchemy models
│   ├── connection.py               # Database connections
│   ├── env_config.py              # Environment configuration
│   └── service.py                 # Database service methods
├── parsers/                        # Order parsers for each vendor
├── utils/                          # Utility functions
├── mappings/                       # CSV mapping data for seeding
├── migrate_kehe_mappings.py        # KEHE migration script
├── migrate_mappings.py             # All mappings migration script
└── init_database.py               # Database initialization
```

## 🚀 **Render Setup Steps**

### **1. Provision Render Resources**

#### **A. Create PostgreSQL Database:**
1. Go to Render Dashboard → "New" → "PostgreSQL"
2. Choose plan and region
3. Save the **External Database URL** (starts with `postgresql://`)

#### **B. Create Web Service:**
1. Go to Render Dashboard → "New" → "Web Service"
2. Connect your GitHub repo
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
   - **Python Version:** 3.11

### **2. Environment Configuration**

Set these environment variables in Render Web Service:

```bash
DATABASE_URL=<your-render-postgresql-external-url>
ENVIRONMENT=production
REPL_ID=render-deployment
```

### **3. Database Migration Options**

#### **Option A: Full Database Copy (Recommended if <100MB)**
```bash
# From your current database to Render
pg_dump $SOURCE_DATABASE_URL | psql $RENDER_DATABASE_URL
```

#### **Option B: Schema + Mapping Seed (Recommended)**
1. **Initialize Schema:** The app will auto-create tables on first run
2. **Seed Mappings:** Upload and run migration scripts:

```bash
# After deployment, run these via Render shell or manually:
python init_database.py
python migrate_kehe_mappings.py
python migrate_mappings.py
```

### **4. Validation Steps**

1. **Health Check:** Visit `https://your-app.onrender.com/?health=check`
2. **Database Connectivity:** Should return `{"status": "healthy", "database": "connected"}`
3. **Test KEHE Processing:** Upload a KEHE order file and verify mapping resolution

## 📊 **Expected Migration Results**

- **KEHE Mappings:** ~180 vendor item mappings
- **Store Mappings:** Customer and store location mappings
- **All Processors:** KEHE, Whole Foods, UNFI East/West, TK Maxx

## 🔧 **Render-Specific Configurations**

### **Streamlit Port Binding**
The `.streamlit/config.toml` is configured for development (port 5000), but Render overrides this with the start command using `$PORT`.

### **Database SSL**
The `env_config.py` automatically sets `sslmode=require` for production environments, which is compatible with Render PostgreSQL.

### **Auto-Initialization**
The app includes health checks and will initialize the database schema automatically on first startup.