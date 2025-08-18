#!/bin/bash
# Force trading to be enabled
docker exec redis redis-cli set trading_enabled true
echo "Forced trading to ENABLED state"