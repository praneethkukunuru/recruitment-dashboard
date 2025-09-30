# Deployment Guide for Recruitment Dashboard

## Option 1: PythonAnywhere (Recommended - Free Tier Available)

### Steps:
1. Go to https://www.pythonanywhere.com/
2. Create a free account
3. Upload your files via the Files tab
4. Create a new Web App (Flask)
5. Point it to your app.py file
6. Set up a virtual environment and install requirements.txt

### Files to upload:
- app.py
- requirements.txt
- templates/ folder
- static/ folder
- All other project files

## Option 2: Render (Free Tier Available)

### Steps:
1. Go to https://render.com/
2. Connect your GitHub repository
3. Use the render.yaml configuration file
4. Deploy automatically

## Option 3: Fly.io (Free Tier Available)

### Steps:
1. Install flyctl CLI
2. Run: flyctl auth login
3. Run: flyctl launch
4. Run: flyctl deploy

## Option 4: Heroku (Paid - $5/month)

### Steps:
1. Install Heroku CLI
2. Run: heroku create your-app-name
3. Run: git push heroku main

## Environment Variables to Set:
- SECRET_KEY: Generate a random secret key
- PORT: Will be set automatically by the platform

## Notes:
- All platforms will automatically install dependencies from requirements.txt
- The app is configured to use environment variables for production
- Uploads folder will be created automatically
- Database files will persist on most platforms
