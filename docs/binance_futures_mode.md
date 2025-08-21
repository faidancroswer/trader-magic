# Modo Binance Futures

Este documento explica como configurar e usar o modo Binance Futures no TraderMagic.

## Visão Geral

O modo Binance Futures permite:
- Realizar operações a descoberto (short)
- Usar alavancagem para potencialmente aumentar lucros
- Implementar gerenciamento de risco com stop-loss e take-profit

## Configuração

### 1. Atualizar variáveis de ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# Modo Futures
BINANCE_FUTURES_MODE=true
BINANCE_FUTURES_LEVERAGE=10

# Certifique-se de que está usando a URL correta para futures
BINANCE_BASE_URL=https://fapi.binance.com
```

### 2. Configuração de Alavancagem

A alavancagem padrão é 10x, mas você pode ajustá-la conforme necessário (1-125x):

```env
BINANCE_FUTURES_LEVERAGE=20  # Para 20x de alavancagem
```

## Vantagens do Modo Futures

### 1. Operações Short
Com o modo futures, você pode:
- Vender ativos que não possui ("vender a descoberto")
- Lucrar quando o preço cai
- Proteger sua carteira contra quedas de mercado

### 2. Alavancagem
A alavancagem permite:
- Controlar posições maiores com menos capital
- Potencialmente aumentar lucros
- Importante: Também aumenta o risco de perdas

### 3. Gerenciamento de Risco
O sistema inclui:
- Stop-loss automático
- Take-profit automático
- Limites de posição
- Limites diários de perda

## Riscos e Considerações

### 1. Alavancagem Dupla Edged
- A alavancagem amplia tanto ganhos quanto perdas
- Uma posição com 10x de alavancagem pode resultar em perdas 10x maiores
- Use com cautela e sempre com stop-loss

### 2. Requisitos de Margem
- Futures requer manter margem suficiente
- Se o preço se mover contra você, pode ocorrer "margin call"
- O sistema inclui proteções automáticas

### 3. Financiamento
- Posições longas/noturnas pagam/recebem financiamento
- O sistema não gerencia automaticamente o financiamento

## Estratégias Recomendadas

### 1. Conserservadora
- Alavancagem baixa (2-5x)
- Stop-loss apertado (1-2%)
- Take-profit conservador (2-3%)

### 2. Moderada
- Alavancagem média (5-10x)
- Stop-loss moderado (2-3%)
- Take-profit moderado (3-5%)

### 3. Agressiva
- Alavancagem alta (10-20x)
- Stop-loss flexível (3-5%)
- Take-profit agressivo (5-10%)
- Apenas para traders experientes

## Monitoramento

### 1. Posições Abertas
Monitore suas posições em tempo real através da interface web.

### 2. Nível de Margem
Verifique regularmente seu nível de margem para evitar liquidations.

### 3. Desempenho
Acompanhe o desempenho de suas estratégias e ajuste conforme necessário.

## Conclusão

O modo Binance Futures oferece oportunidades significativas para aumentar seus ganhos, mas também apresenta riscos maiores. Use-o com responsabilidade, comece com alavancagem baixa e sempre utilize stop-loss.

Lembre-se: "O lucro vem da gestão de risco, não da busca por lucros maiores."