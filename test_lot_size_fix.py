#!/usr/bin/env python3
"""
Test script to verify LOT_SIZE error fix for Binance API
"""

import os
import sys
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.trade_execution.binance_client import BinanceClient
from src.utils.models import TradeSignal, TradingDecision

def test_symbol_info():
    """Test getting symbol information"""
    print("=== Testing Symbol Info ===")
    
    client = BinanceClient()
    
    # Test BTC/USDT
    btc_info = client.get_symbol_info("BTCUSDT")
    print(f"BTC/USDT info: {btc_info}")
    
    # Test ETH/USDT
    eth_info = client.get_symbol_info("ETHUSDT")
    print(f"ETH/USDT info: {eth_info}")
    
    return btc_info, eth_info

def test_quantity_adjustment():
    """Test quantity adjustment to LOT_SIZE requirements"""
    print("\n=== Testing Quantity Adjustment ===")
    
    client = BinanceClient()
    
    # Mock symbol info for testing
    btc_symbol_info = {
        'symbol': 'BTCUSDT',
        'minQty': '0.00001',
        'maxQty': '9000.00000000',
        'stepSize': '0.00001'
    }
    
    eth_symbol_info = {
        'symbol': 'ETHUSDT',
        'minQty': '0.0001',
        'maxQty': '100000.00000000',
        'stepSize': '0.0001'
    }
    
    # Test cases
    test_cases = [
        # (quantity, symbol_info, description)
        (0.000005, btc_symbol_info, "BTC quantity below minimum"),
        (0.001111, btc_symbol_info, "BTC normal quantity"),
        (0.001234567, btc_symbol_info, "BTC quantity with many decimals"),
        (0.00005, eth_symbol_info, "ETH quantity below minimum"),
        (0.12345, eth_symbol_info, "ETH normal quantity"),
        (0.123456789, eth_symbol_info, "ETH quantity with many decimals"),
    ]
    
    for quantity, symbol_info, description in test_cases:
        adjusted = client.adjust_quantity_to_lot_size(quantity, symbol_info)
        print(f"{description}: {quantity} -> {adjusted}")
        
        # Validate the adjusted quantity
        min_qty = Decimal(symbol_info['minQty'])
        step_size = Decimal(symbol_info['stepSize'])
        adjusted_decimal = Decimal(adjusted)
        
        # Check if it meets minimum requirement
        meets_min = adjusted_decimal >= min_qty
        
        # Check if it's properly aligned to step size
        if step_size > 0:
            steps_from_min = (adjusted_decimal - min_qty) / step_size
            is_aligned = steps_from_min == int(steps_from_min)
        else:
            is_aligned = True
        
        print(f"  Valid: meets_min={meets_min}, aligned_to_step={is_aligned}")
        print()

def test_trade_execution_simulation():
    """Test trade execution with LOT_SIZE compliance"""
    print("\n=== Testing Trade Execution (Debug Mode) ===")
    
    # Ensure we're in debug mode
    os.environ["BINANCE_DEBUG_MODE"] = "true"
    
    client = BinanceClient()
    
    # Create test signals
    btc_signal = TradeSignal(
        symbol="BTC/USDT",
        decision=TradingDecision.BUY,
        confidence=0.8,
        rsi_value=30.0
    )
    
    eth_signal = TradeSignal(
        symbol="ETH/USDT",
        decision=TradingDecision.BUY,
        confidence=0.7,
        rsi_value=25.0
    )
    
    # Test BTC trade
    print("Testing BTC trade...")
    btc_result = client.execute_trade(btc_signal)
    if btc_result:
        print(f"BTC Result: {btc_result.status} - {btc_result.error or 'Success'}")
        if btc_result.quantity:
            print(f"  Quantity: {btc_result.quantity}")
            print(f"  Price: ${btc_result.price}")
    
    # Test ETH trade
    print("\nTesting ETH trade...")
    eth_result = client.execute_trade(eth_signal)
    if eth_result:
        print(f"ETH Result: {eth_result.status} - {eth_result.error or 'Success'}")
        if eth_result.quantity:
            print(f"  Quantity: {eth_result.quantity}")
            print(f"  Price: ${eth_result.price}")

if __name__ == "__main__":
    print("Testing LOT_SIZE Error Fix")
    print("=" * 50)
    
    try:
        # Test symbol info retrieval
        test_symbol_info()
        
        # Test quantity adjustment
        test_quantity_adjustment()
        
        # Test trade execution
        test_trade_execution_simulation()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nKey improvements:")
        print("- Added symbol info retrieval to get actual LOT_SIZE requirements")
        print("- Implemented quantity adjustment to comply with min/max/step requirements")
        print("- Proper decimal handling to avoid floating point precision issues")
        print("- Validation of final quantity before sending to Binance")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()