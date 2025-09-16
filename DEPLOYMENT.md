# 🚀 Railway Deployment Guide

This guide will help you deploy the Alibaba Product Updater to Railway.com.

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **Alibaba API Credentials**: You'll need valid API credentials

## 🚀 Deployment Steps

### 1. Connect to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `ragatex-api-updates` repository
5. Click "Deploy Now"

### 2. Set Environment Variables

In your Railway project dashboard:

1. Go to the "Variables" tab
2. Add the following environment variables:

```env
APP_KEY=your_actual_app_key
ACCESS_TOKEN=your_actual_access_token
APP_SECRET=your_actual_app_secret
BASE_URL=https://openapi-api.alibaba.com/rest
```

### 3. Configure the Service

Railway will automatically detect the Python application and use the `Procfile` to start it.

## 📁 Required Files for Deployment

The following files are included for Railway deployment:

- `Procfile` - Defines how to start the application
- `railway.json` - Railway-specific configuration
- `nixpacks.toml` - Build configuration
- `wsgi.py` - WSGI entry point for production
- `runtime.txt` - Python version specification
- `.railwayignore` - Files to exclude from deployment

## 🔧 Configuration Details

### Procfile
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 wsgi:app
```

### Railway.json
- Uses Nixpacks builder
- Configures gunicorn with 4 workers
- Sets 120-second timeout for long-running operations
- Enables auto-restart on failure

## 🌐 Accessing Your Application

1. After deployment, Railway will provide a URL like: `https://your-app-name.railway.app`
2. The application will be available at this URL
3. You can access the web interface and upload CSV files

## 📊 Monitoring

- Check the "Deployments" tab for build logs
- Monitor the "Metrics" tab for performance
- View logs in the "Logs" tab

## 🔒 Security Notes

- Environment variables are encrypted in Railway
- Never commit `.env` files to Git
- Use Railway's environment variable system for secrets

## 🐛 Troubleshooting

### Common Issues:

1. **Build Fails**: Check that all dependencies are in `requirements.txt`
2. **App Won't Start**: Verify environment variables are set correctly
3. **Port Issues**: Ensure the app binds to `0.0.0.0:$PORT`

### Debug Commands:

```bash
# Check if app starts locally
python3 wsgi.py

# Test with gunicorn locally
gunicorn --bind 0.0.0.0:8080 --workers 4 wsgi:app
```

## 📈 Performance

- **Workers**: 4 gunicorn workers for concurrent requests
- **Timeout**: 120 seconds for long-running operations
- **Memory**: Railway provides adequate memory for the application
- **Scaling**: Can be scaled up in Railway dashboard

## 🔄 Updates

To update your deployment:

1. Push changes to your GitHub repository
2. Railway will automatically detect and redeploy
3. Monitor the deployment in the Railway dashboard

## 📞 Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Project Issues: Create an issue in your GitHub repository

---

**🎉 Your Alibaba Product Updater is now live on Railway!**
