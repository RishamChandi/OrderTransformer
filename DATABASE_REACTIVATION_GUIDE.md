# Database Connection Error - Resolution Guide

## Error Summary

**Error Message**: `The endpoint has been disabled. Enable it using Neon API and retry.`

**Root Cause**: Your Neon PostgreSQL database endpoint has been automatically disabled (likely due to inactivity or Neon's free tier auto-suspension policy).

## How to Fix

### Option 1: Reactivate via Neon Dashboard (Recommended)
1. Go to [Neon Console](https://console.neon.tech/)
2. Select your project
3. Navigate to the **Compute** or **Database** section
4. Find your endpoint (ep-dawn-bar-af52gewg)
5. Click **"Enable"** or **"Resume"** button
6. Wait ~30 seconds for the endpoint to become active
7. Restart your Replit application

### Option 2: Use Neon API
```bash
# Get your Neon API key from: https://console.neon.tech/app/settings/api-keys
curl -X POST \
  'https://console.neon.tech/api/v2/projects/{project_id}/endpoints/{endpoint_id}/start' \
  -H 'Authorization: Bearer YOUR_NEON_API_KEY' \
  -H 'Content-Type: application/json'
```

### Option 3: Create New Database in Replit
If you're deploying to Render or another platform, create a new PostgreSQL database:
1. In Replit: Use the Database pane to create a new Postgres instance
2. Update `DATABASE_URL` environment variable
3. Run migration script: `python render_migrate_database.py`

## After Reactivation

Once the database is reactivated:
1. The application should automatically reconnect
2. All 180 KEHE mappings will be available
3. Order processing will resume normal operation

## Prevention

**For Development**: Keep the Replit database active by using it regularly

**For Production**: Consider upgrading to:
- Neon's paid tier (no auto-suspension)
- Render PostgreSQL (always-on instances)
- Other managed PostgreSQL providers