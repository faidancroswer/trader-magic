#!/bin/bash
# restart-low-risk.sh - Utility script to restart TraderMagic with low-risk settings

echo "=================================================="
echo "    TraderMagic - Low Risk Restart Utility        "
echo "=================================================="

# Stop all containers
echo "Stopping all TraderMagic containers..."
docker-compose -f docker-compose.low-risk.yml down

# Rebuild and start
echo "Building and starting TraderMagic with low-risk configuration..."
docker-compose -f docker-compose.low-risk.yml up -d --build

# Wait for services to start
echo "Waiting for services to initialize (15 seconds)..."
sleep 15

# Check if services are running
echo "Checking service status..."
docker-compose -f docker-compose.low-risk.yml ps

echo "=================================================="
echo "TraderMagic low-risk system is now running!"
echo "Web UI is available at: http://localhost:9753"
echo ""
echo "Use 'docker-compose -f docker-compose.low-risk.yml logs -f' to follow the logs"
echo "=================================================="