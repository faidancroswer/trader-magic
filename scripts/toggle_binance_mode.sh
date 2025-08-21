#!/bin/bash
# Script to toggle between Binance Spot and Futures mode

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file from .env.sample first."
    exit 1
fi

# Check current mode
if grep -q "BINANCE_FUTURES_MODE=true" .env; then
    CURRENT_MODE="FUTURES"
    NEW_MODE="SPOT"
    NEW_VALUE="false"
else
    CURRENT_MODE="SPOT"
    NEW_MODE="FUTURES"
    NEW_VALUE="true"
fi

echo "Current mode: $CURRENT_MODE"
echo "Switching to: $NEW_MODE"

# Update the .env file
sed -i "s/BINANCE_FUTURES_MODE=.*/BINANCE_FUTURES_MODE=$NEW_VALUE/" .env

# Also update the base URL for futures
if [ "$NEW_MODE" = "FUTURES" ]; then
    sed -i "s/BINANCE_BASE_URL=.*/BINANCE_BASE_URL=https:\/\/fapi.binance.com/" .env
    echo "Updated Binance base URL to futures API"
else
    sed -i "s/BINANCE_BASE_URL=.*/BINANCE_BASE_URL=https:\/\/api.binance.com/" .env
    echo "Updated Binance base URL to spot API"
fi

echo "✅ Successfully switched to $NEW_MODE mode!"
echo "Please restart the services for changes to take effect:"
echo "  docker-compose down"
echo "  docker-compose up -d"