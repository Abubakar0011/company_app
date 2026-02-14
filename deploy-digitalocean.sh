#!/bin/bash
# DigitalOcean Droplet Deployment Script
# Run this on your DigitalOcean Droplet after SSH

echo "🚀 Deploying Text Extractor to DigitalOcean Droplet..."

# Update system
echo "📦 Updating system..."
apt-get update
apt-get upgrade -y

# Install Docker (if not already installed)
echo "🐳 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Pull your image from Docker Hub
echo "⬇️ Pulling image from Docker Hub..."
docker pull abubakar486/text-extractor:latest

# Stop and remove existing container (if any)
echo "🛑 Stopping existing container..."
docker stop text-extractor 2>/dev/null || true
docker rm text-extractor 2>/dev/null || true

# Run the container
echo "🏃 Starting container..."
docker run -d \
  --name text-extractor \
  --restart unless-stopped \
  -p 80:8501 \
  -v /root/output:/app/output \
  abubakar486/text-extractor:latest

# Check if container is running
echo "✅ Checking container status..."
docker ps | grep text-extractor

# Get droplet IP
DROPLET_IP=$(curl -s ifconfig.me)

echo ""
echo "🎉 Deployment Complete!"
echo "================================"
echo "Your app is now accessible at:"
echo "http://$DROPLET_IP"
echo ""
echo "Useful commands:"
echo "  docker logs -f text-extractor    # View logs"
echo "  docker restart text-extractor    # Restart app"
echo "  docker stop text-extractor       # Stop app"
echo "================================"
