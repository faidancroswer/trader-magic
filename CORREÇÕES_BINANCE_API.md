# Correções para Erro LOT_SIZE da API Binance

## Problema Principal: Erro LOT_SIZE

O erro `APIError(code=-1013): Filter failure: LOT_SIZE` ocorre quando a quantidade da ordem não atende aos requisitos específicos do par de negociação na Binance. Cada par tem:

- **minQty**: Quantidade mínima permitida
- **maxQty**: Quantidade máxima permitida  
- **stepSize**: Incremento mínimo permitido

## Problemas Identificados

1. **Erro LOT_SIZE**: Quantidades não conformes com os filtros do símbolo
2. **Erro de formatação da quantidade**: A API do Binance rejeitou o parâmetro 'quantity' devido a caracteres ilegais
3. **Erro de validação do TradeResult**: O campo `order_id` era obrigatório mas estava sendo definido como `None` em casos de erro
4. **Erro de configuração**: O código tentava acessar `config.trading.fixed_amount` mas o campo correto é `trade_fixed_amount`

## Correções Implementadas

### 1. Correção Completa do LOT_SIZE (src/trade_execution/binance_client.py)

**Problema**: Quantidades calculadas não respeitavam os filtros LOT_SIZE da Binance.

**Solução**: Implementado sistema completo de conformidade:

```python
def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
    """Get symbol information including LOT_SIZE filters"""
    exchange_info = self.client.get_exchange_info()
    for symbol_info in exchange_info['symbols']:
        if symbol_info['symbol'] == symbol:
            for filter_info in symbol_info['filters']:
                if filter_info['filterType'] == 'LOT_SIZE':
                    return {
                        'symbol': symbol,
                        'minQty': filter_info['minQty'],
                        'maxQty': filter_info['maxQty'],
                        'stepSize': filter_info['stepSize']
                    }

def adjust_quantity_to_lot_size(self, quantity: float, symbol_info: Dict[str, Any]) -> str:
    """Adjust quantity to comply with LOT_SIZE requirements"""
    from decimal import Decimal, ROUND_DOWN
    
    min_qty = Decimal(symbol_info['minQty'])
    max_qty = Decimal(symbol_info['maxQty'])
    step_size = Decimal(symbol_info['stepSize'])
    
    qty_decimal = Decimal(str(quantity))
    
    # Ensure minimum quantity
    if qty_decimal < min_qty:
        qty_decimal = min_qty
    
    # Ensure maximum quantity
    if qty_decimal > max_qty:
        qty_decimal = max_qty
    
    # Adjust to step size
    if step_size > 0:
        steps = ((qty_decimal - min_qty) / step_size).quantize(Decimal('1'), rounding=ROUND_DOWN)
        qty_decimal = min_qty + (steps * step_size)
    
    return str(qty_decimal.normalize())
```

### 2. Integração no Fluxo de Execução

**Modificado**: O método `execute_trade` agora usa informações reais do símbolo:

```python
# Get symbol information for LOT_SIZE requirements
symbol_info = self.get_symbol_info(symbol)

# Calculate initial quantity
quantity = trade_amount / current_price

# Adjust quantity to comply with LOT_SIZE requirements
quantity_str = self.adjust_quantity_to_lot_size(quantity, symbol_info)
```

### 3. Correção do Nome do Campo de Configuração

**Problema**: O código tentava acessar `config.trading.fixed_amount` que não existe.

**Solução**: Corrigido para usar o nome correto do campo:

```python
if config.trading.use_fixed_amount:
    trade_amount = config.trading.trade_fixed_amount  # Corrigido
else:
    trade_amount = account_summary["cash_balance"] * (config.trading.trade_percentage / 100)
```

### 4. Correção do Modelo TradeResult (src/utils/models.py)

**Problema**: O campo `order_id` era obrigatório, mas em casos de erro era definido como `None`.

**Solução**: Tornado o campo `order_id` opcional:

```python
class TradeResult(BaseModel):
    order_id: Optional[str] = None  # Optional to handle error cases
```

## Exemplos de Correção

### Cenário: Compra de $50 em BTC

**Antes (causava erro LOT_SIZE)**:
```
Preço BTC: $45,000
Quantidade calculada: 0.0011111111111111111
Erro: Filter failure: LOT_SIZE
```

**Depois (funciona corretamente)**:
```
Preço BTC: $45,000
Quantidade inicial: 0.0011111111111111111
Informações do símbolo:
  - minQty: 0.00001
  - stepSize: 0.00001
Quantidade ajustada: 0.00111
✅ Ordem executada com sucesso
```

## Validação

- ✅ Teste `test_lot_size_simple.py` confirma correção completa do LOT_SIZE
- ✅ Quantidades são ajustadas automaticamente para conformidade
- ✅ Suporte para BTC (stepSize: 0.00001) e ETH (stepSize: 0.0001)
- ✅ Tratamento de quantidades abaixo do mínimo
- ✅ Formatação correta usando aritmética Decimal

## Resultado Esperado

- ✅ Eliminação completa do erro "Filter failure: LOT_SIZE"
- ✅ Eliminação do erro "Illegal characters found in parameter 'quantity'"
- ✅ Eliminação do erro "1 validation error for TradeResult"
- ✅ Cálculo correto da quantidade usando valor fixo de $50
- ✅ Execução bem-sucedida de trades no Binance testnet
- ✅ Conformidade automática com todos os filtros LOT_SIZE da Binance