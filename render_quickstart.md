# 🚀 Render Deployment Quick Start

## 📦 **Ready-to-Deploy Files**

Your Order Transformation Platform is ready for Render deployment with:

- ✅ **Main App**: `app.py` (95KB Streamlit application)  
- ✅ **Dependencies**: `streamlit_requirements.txt` (rename to `requirements.txt` for Render)
- ✅ **Database**: Complete `database/` module with PostgreSQL support
- ✅ **Parsers**: All vendor parsers (KEHE, Whole Foods, UNFI, TK Maxx)
- ✅ **Mappings**: 180+ KEHE mappings ready for migration
- ✅ **Migration Scripts**: `render_migrate_database.py` for complete setup

## ⚡ **One-Click Render Setup**

### **1. Upload to GitHub/GitLab**
```bash
# Create new repository with these files:
app.py
requirements.txt                 # (rename from streamlit_requirements.txt)
.streamlit/config.toml
database/
parsers/
utils/
mappings/
render_migrate_database.py
init_database.py
```

### **2. Create Render Services**

#### **PostgreSQL Database:**
- Go to Render → New → PostgreSQL
- Choose plan → Create
- **Save External Database URL**

#### **Web Service:**
- Go to Render → New → Web Service  
- Connect your repo
- **Build**: `pip install -r requirements.txt`
- **Start**: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`

### **3. Environment Variables**
Set in Render Web Service settings:
```
DATABASE_URL=<your-postgresql-external-url>
ENVIRONMENT=production
```

### **4. Deploy & Migrate**
1. **Deploy** → Render automatically builds and starts your app
2. **Open Shell** in Render dashboard
3. **Run Migration**: `python render_migrate_database.py`
4. **Test**: Visit `https://your-app.onrender.com/?health=check`

## 📊 **Expected Results**

- **Database**: 5 tables created (orders, mappings, conversions)
- **KEHE Mappings**: ~180 item mappings migrated
- **Health Check**: Returns `{"status": "healthy", "database": "connected"}`
- **Order Processing**: Upload KEHE CSV → generates Xoro template

## 🎯 **Validation Checklist**

- [ ] App loads at your Render URL
- [ ] Health endpoint returns "healthy" status  
- [ ] Database shows 180+ KEHE mappings
- [ ] KEHE order file processes successfully
- [ ] Item Mapping UI shows database-backed mappings
- [ ] Export/import functions work

## 📞 **Support**

If migration fails:
1. Check Render logs in dashboard
2. Verify DATABASE_URL format
3. Run migration script in Render shell
4. Test health endpoint for database connectivity

**Your platform is production-ready for Render deployment!** 🎉