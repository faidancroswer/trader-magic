# Modo de Baixo Risco para TraderMagic

Este documento descreve como configurar e operar o TraderMagic no modo de baixo risco, ideal para contas com saldo limitado.

## Visão Geral

O modo de baixo risco foi projetado especificamente para contas com saldo pequeno (como $24 USD) e implementa várias estratégias de gerenciamento de risco para proteger o capital.

## Configurações de Baixo Risco

### 1. Configuração do Arquivo .env.low-risk

```env
# Valor fixo muito conservador - apenas $2 por trade (8% do saldo de $24)
TRADE_PERCENTAGE=1.0
TRADE_FIXED_AMOUNT=2.0
TRADE_USE_FIXED=true

# Apenas 1 símbolo para reduzir exposição
SYMBOLS=BTC/USDT

# Intervalo maior para evitar overtrading - 10 minutos
POLL_INTERVAL=600

# NOTIONAL Filter Configuration - Configuração segura
ALLOW_MIN_NOTIONAL_ADJUSTMENT=true
MIN_NOTIONAL_BUFFER_PERCENT=20.0  # Buffer maior para segurança
```

### 2. Estratégias de Gerenciamento de Risco Implementadas

1. **Verificação de Saldo**: Antes de cada trade, o sistema verifica se há saldo suficiente.
2. **Limites de Posição**: Apenas uma posição pode estar aberta por vez.
3. **Stop Loss Automático**: 2% de perda máxima por trade.
4. **Take Profit Automático**: 4% de lucro alvo por trade.
5. **Limites Diários**: Máximo de 10 trades por dia e $10 de perda máxima.

## Scripts Disponíveis

### 1. start-low-risk.sh
Inicia o sistema com configurações de baixo risco:
```bash
bash start-low-risk.sh
```

### 2. restart-low-risk.sh
Reinicia o sistema com configurações de baixo risco:
```bash
bash restart-low-risk.sh
```

### 3. monitor-low-risk.sh
Monitora os logs do sistema em tempo real:
```bash
bash monitor-low-risk.sh
```

### 4. check_balance.py
Verifica o saldo atual da conta Binance:
```bash
python check_balance.py
```

### 5. check_positions.py
Verifica as posições atuais e estatísticas diárias:
```bash
python check_positions.py
```

## Recomendações de Uso

1. **Monitore constantemente**: Verifique o saldo e as posições regularmente.
2. **Não aumente os valores**: Mantenha os valores de trade baixos até ter mais experiência.
3. **Entenda os riscos**: Mesmo com proteções, trading envolve riscos significativos.
4. **Ajuste conforme necessário**: Se o saldo diminuir muito, reduza ainda mais os valores.

## Configurações Avançadas

Para ajustar os parâmetros de risco, edite o arquivo `src/utils/risk_management.py`:

```python
class RiskManager:
    def __init__(self):
        # Default risk parameters
        self.max_positions = 1  # Máximo de posições simultâneas
        self.stop_loss_percent = 2.0  # Stop loss em porcentagem
        self.take_profit_percent = 4.0  # Take profit em porcentagem
        self.max_daily_loss = 10.0  # Perda máxima diária em USD
        self.max_daily_trades = 10  # Máximo de trades por dia
```

## Segurança

- **Trading desabilitado por padrão**: O sistema inicia com trading desabilitado.
- **Verificação de saldo**: Nunca arriscará mais do que o saldo disponível.
- **Limites estritos**: Impede overtrading e perdas excessivas.