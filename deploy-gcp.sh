#!/bin/bash

# Google Cloud Deployment Script for Recruitment Dashboard
# Make sure you have gcloud CLI installed and authenticated

set -e

# Configuration
PROJECT_ID="your-project-id"  # Replace with your actual project ID
SERVICE_NAME="recruitment-dashboard"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting Google Cloud deployment for Recruitment Dashboard..."

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push the image
echo "🏗️  Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to Google Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars "FLASK_ENV=production,PORT=8080" \
    --timeout 300

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Your dashboard is available at: $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo "1. Set up your Google OAuth credentials:"
echo "   - Go to Google Cloud Console > APIs & Services > Credentials"
echo "   - Create OAuth 2.0 Client ID"
echo "   - Add $SERVICE_URL to authorized redirect URIs"
echo "2. Update your environment variables with the OAuth credentials"
echo "3. Test your deployment!"
