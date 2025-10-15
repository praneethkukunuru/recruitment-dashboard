# Deployment Guide for Recruitment Dashboard

## 🚀 **Recommended Deployment Options**

### **Option 1: Railway (Recommended)**
- **Free tier**: 500 hours/month
- **Persistent storage**: Yes
- **Easy setup**: Connect GitHub repo
- **Steps**:
  1. Push code to GitHub
  2. Connect Railway to GitHub
  3. Deploy automatically
  4. Set environment variables in Railway dashboard

### **Option 2: Render**
- **Free tier**: 750 hours/month
- **Persistent storage**: Yes
- **Steps**:
  1. Connect GitHub repo
  2. Choose "Web Service"
  3. Set build command: `pip install -r requirements.txt`
  4. Set start command: `python app.py`

### **Option 3: PythonAnywhere (Current Issue)**
- **Problem**: File system restrictions
- **Solution**: Use session-based storage (already implemented)
- **Steps**:
  1. Upload code via Git or file upload
  2. Install dependencies
  3. Configure web app
  4. **Note**: Data will persist only during active sessions

## 🔧 **Environment Variables**

Create a `.env` file or set in deployment platform:

```bash
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
FLASK_RUN_PORT=5000
```

## 📁 **Data Persistence Strategy**

The app now uses a **hybrid approach**:

1. **Primary**: File storage (when possible)
2. **Fallback**: Session storage (when file storage fails)
3. **Automatic**: Detects writable directories

### **For PythonAnywhere**:
- Data persists during active sessions
- Users need to re-upload data after server restart
- Consider upgrading to paid plan for persistent storage

### **For Railway/Render**:
- Data persists permanently
- File storage works reliably
- No data loss between deployments

## 🛠 **Deployment Steps**

### **Railway Deployment**:
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project
railway init

# 4. Deploy
railway up
```

### **Render Deployment**:
1. Go to [render.com](https://render.com)
2. Connect GitHub repository
3. Choose "Web Service"
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Environment**: Python 3

## 🔐 **Google OAuth Setup**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URIs:
   - `https://your-app.railway.app/auth/google`
   - `https://your-app.onrender.com/auth/google`
   - `https://yourusername.pythonanywhere.com/auth/google`

## 📊 **Monitoring**

Check logs for:
- Data directory selection
- Storage method (file vs session)
- User authentication
- Data persistence success/failure

## 🚨 **Troubleshooting**

### **PythonAnywhere Issues**:
- **Problem**: "Permission denied" errors
- **Solution**: App automatically falls back to session storage
- **Result**: Data persists during session only

### **Railway/Render Issues**:
- **Problem**: App crashes on startup
- **Solution**: Check environment variables
- **Debug**: View logs in dashboard

## 💡 **Best Practices**

1. **Always test locally first**
2. **Use environment variables for secrets**
3. **Monitor logs after deployment**
4. **Test data persistence**
5. **Verify Google OAuth redirect URIs**

## 🔄 **Migration from PythonAnywhere**

If moving from PythonAnywhere to Railway/Render:

1. **Export data**: Download any important files
2. **Update redirect URIs**: In Google Cloud Console
3. **Deploy to new platform**
4. **Test authentication and data persistence**
5. **Update DNS/domain if needed**
