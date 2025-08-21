#!/bin/bash
# check-positions-container.sh - Check positions from within the container

echo "=== Current Trading Positions ==="

# Execute the check_positions.py script inside the trade_execution container
docker-compose -f docker-compose.low-risk.yml exec trade_execution python check_positions.py