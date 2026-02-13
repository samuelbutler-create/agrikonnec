# Railway Deployment Guide for Agrikonnect Backend

## Quick Deploy to Railway

1. **Sign up/Login to Railway**: 
   - Go to https://railway.app
   - Sign in with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `agrikonnect-backend` repository

3. **Add PostgreSQL Database**:
   - In your Railway project dashboard
   - Click "+ New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically create and connect the database

4. **Configure Environment Variables**:
   Go to your service settings and add these variables:
   
   ```
   DATABASE_URL=${DATABASE_URL}  # Auto-populated by Railway
   SECRET_KEY=<generate-random-secret-key>
   JWT_SECRET_KEY=<generate-random-jwt-secret>
   FLASK_ENV=production
   CORS_ORIGINS=https://agrikonnect-frontend.vercel.app,http://localhost:5173
   FRONTEND_URL=https://agrikonnect-frontend.vercel.app
   NOTIFICATION_SERVICE_URL=<your-notification-service-url>
   ```

   **Generate secure keys:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Deploy**:
   - Railway will automatically detect the configuration
   - Migrations will run automatically on startup
   - Your app will be deployed!

6. **Get Your Live URL**:
   - Go to Settings → "Generate Domain"
   - Your backend will be available at: `https://agrikonnect-backend-production.up.railway.app`

## Your Backend Will Be Live At:
- Main API: `https://<your-service>.railway.app/api/v1`
- Swagger Docs: `https://<your-service>.railway.app/api/swagger`

## Environment Variables Required:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Auto-set by Railway |
| `SECRET_KEY` | Flask secret key | Random 32-char string |
| `JWT_SECRET_KEY` | JWT signing key | Random 32-char string |
| `FLASK_ENV` | Environment | `production` |
| `CORS_ORIGINS` | Allowed origins | `https://agrikonnect-frontend.vercel.app` |
| `FRONTEND_URL` | Frontend URL | `https://agrikonnect-frontend.vercel.app` |

## Troubleshooting:

### If migrations fail:
```bash
# Access Railway CLI
railway login
railway link
railway run flask db upgrade
```

### Check logs:
```bash
railway logs
```

### Redeploy:
```bash
git push origin main
# Railway auto-deploys on push
```
