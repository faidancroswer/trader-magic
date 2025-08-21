#!/usr/bin/env python3
"""
check_positions.py - Check current trading positions from Redis
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import redis_client
import json

def check_positions():
    try:
        # Get current positions from Redis
        positions_key = "current_positions"
        positions_data = redis_client.get_json(positions_key)
        
        print("=== Current Trading Positions ===")
        
        if not positions_data or not positions_data:
            print("No active positions")
            return
            
        for symbol, position in positions_data.items():
            print(f"\nSymbol: {symbol}")
            print(f"  Quantity: {position.get('quantity', 0)}")
            print(f"  Entry Price: ${position.get('entry_price', 0):.2f}")
            print(f"  Decision: {position.get('decision', 'unknown')}")
            print(f"  Stop Loss: ${position.get('stop_loss', 0):.2f}")
            print(f"  Take Profit: ${position.get('take_profit', 0):.2f}")
            
        # Get daily stats
        daily_stats_key = "daily_stats"
        stats = redis_client.get_json(daily_stats_key)
        
        if stats:
            print(f"\n=== Daily Statistics ===")
            print(f"Trades executed: {stats.get('trades', 0)}")
            print(f"Losses: ${stats.get('loss', 0.0):.2f}")
        
    except Exception as e:
        print(f"Error checking positions: {e}")

if __name__ == "__main__":
    check_positions()