#!/bin/bash
# start-low-risk.sh - Start TraderMagic in low-risk mode

echo "=================================================="
echo "    TraderMagic - Low Risk Startup                "
echo "=================================================="

# Check if .env.low-risk exists
if [ ! -f ".env.low-risk" ]; then
    echo "Error: .env.low-risk file not found!"
    echo "Please create .env.low-risk file with your configuration"
    exit 1
fi

# Copy low-risk config to main .env
echo "Setting up low-risk configuration..."
cp .env.low-risk .env

# Start the system
echo "Starting TraderMagic with low-risk configuration..."
docker-compose -f docker-compose.low-risk.yml up -d

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