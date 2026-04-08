# 🚀 Quick Deployment Checklist for Render

## ✅ Completed (by automated setup)
- [x] Created `requirements.txt` with all dependencies
- [x] Updated `settings.py` with environment-based configuration
- [x] Added WhiteNoise middleware for static files
- [x] Configured PostgreSQL database with dj-database-url
- [x] Created `Procfile` for Gunicorn
- [x] Created `build.sh` for build process
- [x] Created `runtime.txt` to specify Python version
- [x] Added security settings for HTTPS
- [x] Configured production/development CORS settings

## 📋 Manual Steps Required

### 1. Install Production Dependencies (Optional - for local testing)
```bash
cd backend\irsBackend
..\..\env\Scripts\activate
pip install gunicorn whitenoise dj-database-url psycopg2-binary
```

### 2. Generate SECRET_KEY
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Save this for the Render environment variables.

### 3. Test Locally (Optional but Recommended)
```bash
python manage.py collectstatic --noinput
python manage.py check --deploy
```

### 4. Make build.sh Executable
```bash
git update-index --chmod=+x build.sh
```

### 5. Push to GitHub
```bash
git add .
git commit -m "Configure for Render deployment"
git push origin main
```

### 6. Create PostgreSQL Database on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **PostgreSQL**
3. Fill in:
   - Name: `irs-postgres`
   - Database: `irs_db`
   - Plan: **Free**
4. Click **Create Database**
5. **Copy the Internal Database URL**

### 7. Create Web Service on Render
1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `irs-backend`
   - **Environment**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn irsBackend.wsgi --bind 0.0.0.0:$PORT --log-file -`
   - **Plan**: Free

### 8. Add Environment Variables in Render
In the Web Service's Environment tab, add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | (the key you generated in step 2) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` |
| `DATABASE_URL` | (Link the Postgres database or copy Internal URL) |
| `CORS_ORIGINS` | `https://your-frontend-url.vercel.app` |

### 9. Deploy!
Click **Create Web Service**. Monitor the logs.

### 10. Create Superuser (After deployment)
Use Render's Shell:
```bash
python manage.py createsuperuser
```

### 11. Test Your API
```bash
curl https://your-app-name.onrender.com/api/
```

## 🎯 Important Notes

**Repository Structure:**
Your Git repository is at `backend/irsBackend/` - this is what Render will see as the root.

**Free Tier Limitations:**
- Services spin down after 15 min of inactivity (30-60s cold start)
- 750 hours/month runtime limit
- Database data retention limited to 90 days

**Before Demos:**
- Hit your API URL to "warm up" the service

## 📚 Reference
See detailed guide: `../../backend/deployment_steps.md`
