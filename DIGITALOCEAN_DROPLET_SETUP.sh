#!/bin/bash
# DigitalOcean Droplet Setup Script
# Run this on your droplet after SSH

echo "🌊 Setting up DigitalOcean Droplet for Text Extractor"

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Pull and run your image
docker pull abubakar486/text-extractor:latest

# Run container
docker run -d \
  --name text-extractor \
  --restart unless-stopped \
  -p 80:8501 \
  -v ~/output:/app/output \
  abubakar486/text-extractor:latest

echo "✅ Done! Your app is running on http://YOUR_DROPLET_IP"
echo "Check status: docker ps"
echo "View logs: docker logs text-extractor"
