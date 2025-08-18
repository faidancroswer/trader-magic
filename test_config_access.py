#!/usr/bin/env python3
"""
Teste para verificar se a configuração está sendo acessada corretamente
"""

from src.config import config

print("Testando acesso à configuração:")
print("=" * 40)

print(f"use_fixed_amount: {config.trading.use_fixed_amount}")
print(f"trade_fixed_amount: {config.trading.trade_fixed_amount}")
print(f"trade_percentage: {config.trading.trade_percentage}")

# Simular o cálculo
if config.trading.use_fixed_amount:
    trade_amount = config.trading.trade_fixed_amount
    print(f"Using fixed amount: {trade_amount}")
else:
    # Simular cash_balance
    cash_balance = 10000.0
    trade_amount = cash_balance * (config.trading.trade_percentage / 100)
    print(f"Using percentage amount: {trade_amount}")

# Simular preço do BTC
current_price = 45000.0
quantity = trade_amount / current_price

print(f"Current price: {current_price}")
print(f"Trade amount: {trade_amount}")
print(f"Calculated quantity: {quantity}")
print(f"Rounded quantity: {round(quantity, 6)}")

# Testar formatação
from decimal import Decimal, ROUND_DOWN

quantity_decimal = Decimal(str(round(quantity, 6)))
quantity_decimal = quantity_decimal.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
quantity_str = str(quantity_decimal)

print(f"Formatted quantity: '{quantity_str}'")

# Verificar padrão Binance
import re
binance_pattern = r'^([0-9]{1,20})(\.[0-9]{1,20})?$'
is_valid = bool(re.match(binance_pattern, quantity_str))
print(f"Valid for Binance: {is_valid}")