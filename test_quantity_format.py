#!/usr/bin/env python3
"""
Teste para verificar a formatação de quantidade para a API do Binance
"""

def format_quantity(quantity):
    """Formatar quantidade para evitar notação científica e caracteres ilegais"""
    if quantity >= 1:
        quantity_str = f"{quantity:.6f}".rstrip('0').rstrip('.')
    else:
        # Para quantidades pequenas, usar mais precisão mas evitar notação científica
        quantity_str = f"{quantity:.8f}".rstrip('0').rstrip('.')
    
    # Garantir que não temos uma string vazia após remover zeros
    if not quantity_str or quantity_str == '':
        quantity_str = "0"
    
    return quantity_str

# Testes com diferentes valores
test_values = [
    0.001,
    0.000001,
    0.123456789,
    1.0,
    1.5,
    10.0,
    0.0001234,
    1e-6,  # Notação científica
    1.23e-5,  # Notação científica
]

print("Testando formatação de quantidade:")
print("=" * 50)

for value in test_values:
    formatted = format_quantity(value)
    print(f"Original: {value:>15} -> Formatado: '{formatted}'")

# Verificar se o formato está correto para a API do Binance
import re
binance_pattern = r'^([0-9]{1,20})(\.[0-9]{1,20})?$'

print("\nVerificando conformidade com padrão da API Binance:")
print("=" * 50)

for value in test_values:
    formatted = format_quantity(value)
    is_valid = bool(re.match(binance_pattern, formatted))
    status = "✅ VÁLIDO" if is_valid else "❌ INVÁLIDO"
    print(f"'{formatted}' -> {status}")