#!/bin/bash

echo "🔐 Testing Google OAuth Configuration"
echo "====================================="

# Test if .env file exists
if [ -f .env ]; then
    echo "✅ .env file found"
    echo "📄 Contents:"
    cat .env
else
    echo "❌ .env file not found"
    exit 1
fi

echo ""
echo "🌐 Testing Auth Config Endpoint"
echo "==============================="

# Test auth config endpoint
response=$(curl -s http://localhost:5006/auth/config)
echo "Response: $response"

# Extract client ID from response
client_id=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin)['client_id'])")
echo "Client ID from API: $client_id"

# Check if it matches the new one
if [[ "$client_id" == "698166460427-nh1pooookkaka1t0odc7jmck1fjpq4nf.apps.googleusercontent.com" ]]; then
    echo "✅ Google Client ID is correct!"
else
    echo "❌ Google Client ID mismatch!"
fi

echo ""
echo "🔗 Login Page Test"
echo "=================="

# Test login page
if curl -s http://localhost:5006/login | grep -q "Recruitment Dashboard"; then
    echo "✅ Login page is accessible"
else
    echo "❌ Login page not accessible"
fi

echo ""
echo "🎯 Ready to test Google OAuth!"
echo "Visit: http://localhost:5006/login"
