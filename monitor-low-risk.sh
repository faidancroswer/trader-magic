#!/bin/bash
# monitor-low-risk.sh - Monitor script for TraderMagic low-risk system

echo "=================================================="
echo "    TraderMagic - Low Risk Monitoring             "
echo "=================================================="

# Show running containers
echo "Running containers:"
docker-compose -f docker-compose.low-risk.yml ps

echo ""
echo "=================================================="
echo "Following logs (Ctrl+C to stop):"
echo "=================================================="

# Follow logs
docker-compose -f docker-compose.low-risk.yml logs -f