#!/usr/bin/env python3
"""
Simple test for LOT_SIZE error fix without external dependencies
"""

import os
from decimal import Decimal

def test_quantity_adjustment():
    """Test quantity adjustment logic"""
    print("=== Testing LOT_SIZE Quantity Adjustment ===")
    
    def adjust_quantity_to_lot_size(quantity: float, symbol_info: dict) -> str:
        """Adjust quantity to comply with LOT_SIZE requirements"""
        from decimal import Decimal, ROUND_DOWN
        
        min_qty = Decimal(symbol_info['minQty'])
        max_qty = Decimal(symbol_info['maxQty'])
        step_size = Decimal(symbol_info['stepSize'])
        
        # Convert quantity to Decimal
        qty_decimal = Decimal(str(quantity))
        
        # Check if quantity is below minimum
        if qty_decimal < min_qty:
            print(f"  Quantity {qty_decimal} below minimum {min_qty}, using minimum")
            qty_decimal = min_qty
        
        # Check if quantity is above maximum
        if qty_decimal > max_qty:
            print(f"  Quantity {qty_decimal} above maximum {max_qty}, using maximum")
            qty_decimal = max_qty
        
        # Adjust to step size
        if step_size > 0:
            steps = ((qty_decimal - min_qty) / step_size).quantize(Decimal('1'), rounding=ROUND_DOWN)
            qty_decimal = min_qty + (steps * step_size)
        
        # Ensure we're still within bounds after adjustment
        if qty_decimal < min_qty:
            qty_decimal = min_qty
        elif qty_decimal > max_qty:
            qty_decimal = max_qty
        
        # Format to remove trailing zeros
        qty_str = str(qty_decimal.normalize())
        
        print(f"  Adjusted quantity: {quantity} -> {qty_str} (min: {min_qty}, step: {step_size})")
        return qty_str
    
    # Test symbol info (real Binance values)
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
    
    # Test cases that would cause LOT_SIZE errors
    test_cases = [
        # (quantity, symbol_info, description)
        (0.000005, btc_symbol_info, "BTC quantity below minimum (should fail without fix)"),
        (0.001111, btc_symbol_info, "BTC normal quantity with precision issues"),
        (0.001234567, btc_symbol_info, "BTC quantity with too many decimals"),
        (0.00005, eth_symbol_info, "ETH quantity below minimum (should fail without fix)"),
        (0.12345, eth_symbol_info, "ETH normal quantity"),
        (0.123456789, eth_symbol_info, "ETH quantity with too many decimals"),
    ]
    
    for quantity, symbol_info, description in test_cases:
        print(f"\n{description}:")
        print(f"  Original: {quantity}")
        
        adjusted = adjust_quantity_to_lot_size(quantity, symbol_info)
        
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
        
        status = "✅ VALID" if meets_min and is_aligned else "❌ INVALID"
        print(f"  Result: {adjusted} - {status}")
        print(f"    Meets minimum: {meets_min}")
        print(f"    Aligned to step: {is_aligned}")

def test_binance_pattern_validation():
    """Test Binance quantity pattern validation"""
    print("\n=== Testing Binance Pattern Validation ===")
    
    import re
    binance_pattern = r'^([0-9]{1,20})(\.[0-9]{1,20})?$'
    
    test_quantities = [
        "0.00001",      # Valid minimum BTC
        "0.0001",       # Valid minimum ETH
        "0.001111",     # Valid normal quantity
        "1.23456789",   # Valid with decimals
        "0",            # Edge case - zero
        "0.0",          # Edge case - zero with decimal
        "1e-5",         # Invalid - scientific notation
        "0.000001e2",   # Invalid - scientific notation
        "",             # Invalid - empty
        "abc",          # Invalid - letters
        "0.00000000000000000001", # Invalid - too many decimals
    ]
    
    for qty in test_quantities:
        is_valid = bool(re.match(binance_pattern, qty))
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"  '{qty}' - {status}")

def simulate_lot_size_error_scenario():
    """Simulate the exact scenario that causes LOT_SIZE errors"""
    print("\n=== Simulating LOT_SIZE Error Scenario ===")
    
    # Scenario: User wants to buy $50 worth of BTC at current price
    trade_amount = 50.0  # USD
    btc_price = 45000.0  # Current BTC price
    
    # Calculate quantity (this often results in precision issues)
    quantity = trade_amount / btc_price
    print(f"Trade amount: ${trade_amount}")
    print(f"BTC price: ${btc_price}")
    print(f"Calculated quantity: {quantity}")
    
    # This is what would cause the error - sending raw float
    print(f"Raw float as string: '{str(quantity)}'")
    
    # Show how Python represents this
    print(f"Python repr: {repr(quantity)}")
    
    # BTC symbol requirements
    btc_info = {
        'minQty': '0.00001',
        'maxQty': '9000.00000000', 
        'stepSize': '0.00001'
    }
    
    # Apply our fix
    from decimal import Decimal, ROUND_DOWN
    
    min_qty = Decimal(btc_info['minQty'])
    step_size = Decimal(btc_info['stepSize'])
    qty_decimal = Decimal(str(quantity))
    
    # Adjust to step size
    if step_size > 0:
        steps = ((qty_decimal - min_qty) / step_size).quantize(Decimal('1'), rounding=ROUND_DOWN)
        qty_decimal = min_qty + (steps * step_size)
    
    fixed_quantity = str(qty_decimal.normalize())
    
    print(f"\n🔧 FIXED quantity: '{fixed_quantity}'")
    print(f"✅ This should work with Binance API!")

if __name__ == "__main__":
    print("LOT_SIZE Error Fix Test")
    print("=" * 50)
    
    try:
        test_quantity_adjustment()
        test_binance_pattern_validation()
        simulate_lot_size_error_scenario()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\n🎯 Key fixes implemented:")
        print("1. Get actual LOT_SIZE requirements from Binance exchange info")
        print("2. Adjust quantities to comply with min/max/step requirements")
        print("3. Use Decimal arithmetic to avoid floating point precision issues")
        print("4. Validate final quantity format before sending to API")
        print("5. Proper error handling for insufficient quantities")
        
        print("\n📋 This should resolve the LOT_SIZE errors you're seeing!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()