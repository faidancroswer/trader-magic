#!/usr/bin/env python3
"""
Teste específico para debug da formatação de quantidade do Binance
"""

from decimal import Decimal, ROUND_DOWN
import re

def format_quantity_new(quantity):
    """Nova formatação usando Decimal"""
    # Convert to Decimal for precise handling
    quantity_decimal = Decimal(str(quantity))
    
    # Round to 8 decimal places (Binance standard) and remove trailing zeros
    quantity_decimal = quantity_decimal.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
    
    # Convert to string and ensure it's in the right format
    quantity_str = str(quantity_decimal)
    
    # Ensure we have a valid number (not empty or just a dot)
    if not quantity_str or quantity_str in ['', '.', '0.', '0.00000000']:
        quantity_str = "0"
    
    # Clean the string of any potential invisible characters
    quantity_str = ''.join(c for c in quantity_str if c.isprintable())
    quantity_str = quantity_str.strip()
    
    return quantity_str

def format_quantity_old(quantity):
    """Formatação antiga para comparação"""
    if quantity >= 1:
        quantity_str = f"{quantity:.6f}".rstrip('0').rstrip('.')
    else:
        quantity_str = f"{quantity:.8f}".rstrip('0').rstrip('.')
    
    if not quantity_str or quantity_str == '':
        quantity_str = "0"
    
    return quantity_str

# Teste com valores que podem estar causando problemas
test_values = [
    0.001,
    0.000001,
    0.123456789,
    1.0,
    1.5,
    10.0,
    0.0001234,
    1e-6,
    1.23e-5,
    # Valores que podem estar sendo calculados no sistema
    10000 / 45000,  # trade_amount / current_price para BTC
    1000 / 45000,   # Valor menor
    100 / 45000,    # Valor ainda menor
    10 / 45000,     # Valor muito pequeno
]

binance_pattern = r'^([0-9]{1,20})(\.[0-9]{1,20})?$'

print("Comparação de formatação de quantidade:")
print("=" * 80)
print(f"{'Original':<15} {'Método Antigo':<20} {'Método Novo':<20} {'Válido Antigo':<12} {'Válido Novo':<12}")
print("-" * 80)

for value in test_values:
    old_format = format_quantity_old(value)
    new_format = format_quantity_new(value)
    
    old_valid = bool(re.match(binance_pattern, old_format))
    new_valid = bool(re.match(binance_pattern, new_format))
    
    old_status = "✅" if old_valid else "❌"
    new_status = "✅" if new_valid else "❌"
    
    print(f"{value:<15} {old_format:<20} {new_format:<20} {old_status:<12} {new_status:<12}")

print("\nTeste específico com valor problemático:")
print("=" * 50)

# Simular o cálculo real que pode estar causando problema
trade_amount = 1000.0  # USDT
current_price = 45000.0  # BTC price
calculated_quantity = trade_amount / current_price

print(f"Trade amount: {trade_amount} USDT")
print(f"Current price: {current_price} USD")
print(f"Calculated quantity: {calculated_quantity}")
print(f"Calculated quantity repr: {repr(calculated_quantity)}")

# Aplicar round como no código original
rounded_quantity = round(calculated_quantity, 6)
print(f"Rounded quantity: {rounded_quantity}")
print(f"Rounded quantity repr: {repr(rounded_quantity)}")

# Testar formatação
old_formatted = format_quantity_old(rounded_quantity)
new_formatted = format_quantity_new(rounded_quantity)

print(f"Old format: '{old_formatted}' (valid: {bool(re.match(binance_pattern, old_formatted))})")
print(f"New format: '{new_formatted}' (valid: {bool(re.match(binance_pattern, new_formatted))})")

# Verificar bytes
print(f"Old format bytes: {old_formatted.encode('utf-8')}")
print(f"New format bytes: {new_formatted.encode('utf-8')}")