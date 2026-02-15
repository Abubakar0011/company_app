#!/bin/bash

# Production Deployment Script for Digital Ocean
# Run this script on your Digital Ocean droplet

set -e  # Exit on any error

echo "🚀 Starting Production Deployment..."
echo "=================================="

# Step 1: Stop the current running container
echo ""
echo "📦 Step 1: Stopping current container..."
docker stop text-extractor-app 2>/dev/null || echo "No running container found"
docker rm text-extractor-app 2>/dev/null || echo "No container to remove"

# Step 2: Pull the latest image from Docker Hub
echo ""
echo "📥 Step 2: Pulling latest image from Docker Hub..."
docker pull abubakar486/text-extractor:latest

# Step 3: Clean up old images (optional)
echo ""
echo "🧹 Step 3: Cleaning up old images..."
docker image prune -f

# Step 4: Start the new container
echo ""
echo "🚀 Step 4: Starting new container with latest fixes..."
docker run -d \
  --name text-extractor-app \
  --restart unless-stopped \
  -p 8501:8501 \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  abubakar486/text-extractor:latest

# Step 5: Wait for container to be healthy
echo ""
echo "⏳ Step 5: Waiting for container to start..."
sleep 5

# Step 6: Check container status
echo ""
echo "✅ Step 6: Checking container status..."
docker ps | grep text-extractor-app

# Step 7: Show logs
echo ""
echo "📋 Step 7: Showing recent logs..."
docker logs --tail 50 text-extractor-app

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo ""
echo "🌐 Application URLs:"
echo "   - Streamlit Frontend: http://YOUR_DROPLET_IP:8501"
echo "   - FastAPI Backend: http://YOUR_DROPLET_IP:8000"
echo ""
echo "📊 To view logs: docker logs -f text-extractor-app"
echo "🛑 To stop: docker stop text-extractor-app"
echo "🔄 To restart: docker restart text-extractor-app"
echo ""
