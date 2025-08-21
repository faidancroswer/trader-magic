#!/usr/bin/env python3
"""
Script to test Binance Futures functionality
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from src.trade_execution.binance_futures_client import BinanceFuturesClient
from src.utils import TradeSignal, TradingDecision
from datetime import datetime

def test_futures_client():
    """Test the Binance Futures client functionality"""
    print("Testing Binance Futures Client...")
    
    try:
        # Create the client
        client = BinanceFuturesClient()
        print("[OK] Binance Futures client created successfully")
        
        # Test account summary
        print("\n--- Account Summary ---")
        account_summary = client.get_account_summary()
        print(f"Portfolio Value: ${account_summary['portfolio_value']:.2f}")
        print(f"Cash Balance: ${account_summary['cash_balance']:.2f}")
        print(f"Buying Power: ${account_summary['buying_power']:.2f}")
        print(f"Leverage: {account_summary.get('leverage', 10)}x")
        
        # Test symbol info
        print("\n--- Symbol Info (BTCUSDT) ---")
        symbol_info = client.get_symbol_info("BTCUSDT")
        print(f"Min Quantity: {symbol_info['minQty']}")
        print(f"Max Quantity: {symbol_info['maxQty']}")
        print(f"Step Size: {symbol_info['stepSize']}")
        print(f"Min Notional: ${symbol_info['minNotional']}")
        
        # Test quantity adjustment
        print("\n--- Quantity Adjustment ---")
        quantity = 0.0001
        price = 45000.0
        adjusted_qty, notional = client.adjust_quantity_to_meet_notional(quantity, price, symbol_info)
        print(f"Original quantity: {quantity}")
        print(f"Adjusted quantity: {adjusted_qty}")
        print(f"Notional value: ${notional:.2f}")
        
        # Test mock trade execution
        print("\n--- Mock Trade Execution ---")
        signal = TradeSignal(
            symbol="BTC/USDT",
            decision=TradingDecision.BUY,
            rsi_value=30.0,
            timestamp=datetime.now().timestamp()
        )
        
        # Enable debug mode for testing
        client.debug_mode = True
        result = client.execute_trade(signal)
        
        if result:
            print(f"Trade result: {result.status}")
            print(f"Order ID: {result.order_id}")
            print(f"Quantity: {result.quantity}")
            print(f"Price: ${result.price}")
        else:
            print("[ERROR] Trade execution failed")
            
        print("\n[OK] All tests completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_futures_client()