# Instruções para Operar na Conta Real da Binance Futures

Este documento fornece instruções detalhadas para configurar e operar o sistema TraderMagic na conta real da Binance Futures usando a estratégia RSI com alavancagem.

## Visão Geral

O TraderMagic é um sistema de trading automatizado que utiliza análise de RSI (Índice de Força Relativa) para tomar decisões de compra e venda. Com o modo Futures, você pode:
- Realizar operações a descoberto (short selling)
- Usar alavancagem para ampliar potenciais lucros (e perdas)
- Implementar estratégias mais avançadas de trading

O sistema está configurado para operar com os pares BTC/USDT e ETH/USDT.

## Configuração Inicial

### 1. Credenciais da API da Binance

Para operar na conta real da Binance Futures, você precisa configurar as credenciais da API:

1. Acesse a Binance e vá para **User Center** > **API Management**
2. Clique em **Create API Key**
3. Dê um nome para sua API (ex: "TraderMagic")
4. **Importante**: Marque as permissões necessárias:
   - ✅ **Enable Reading** (para consultar saldo)
   - ✅ **Enable Futures** (para fazer trades de futures)
   - ✅ **Enable Spot & Margin Trading** (recomendado para compatibilidade)
   - ❌ **Enable Withdrawals** (não recomendado)
5. Copie as credenciais geradas:
   - **API Key**: Uma string longa começando com letras/números
   - **Secret Key**: Outra string longa

### 2. Configuração do Arquivo .env

Atualize o arquivo `.env` com as seguintes configurações:

```env
# Binance API Keys - Conta Real
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=sua_secret_key_aqui
BINANCE_TESTNET=false
BINANCE_BASE_URL=https://fapi.binance.com

# Binance Futures Configuration
BINANCE_FUTURES_MODE=true
BINANCE_FUTURES_LEVERAGE=10
```

### 3. Configuração de Alavancagem

A alavancagem determina quanto você pode ampliar sua posição:
- **2x**: Dobro do capital (menos risco)
- **5x**: 5 vezes o capital (risco moderado)
- **10x**: 10 vezes o capital (risco elevado)
- **20x**: 20 vezes o capital (alto risco)

Recomenda-se começar com alavancagem baixa (2-5x) até se familiarizar com o sistema.

## Modo Futures vs Spot

### Vantagens do Modo Futures:
1. **Short Selling**: Venda ativos que você não possui
2. **Alavancagem**: Controle posições maiores com menos capital
3. **Proteção**: Hedge contra quedas de mercado

### Riscos do Modo Futures:
1. **Perdas Ampliadas**: Alavancagem também amplia perdas
2. **Margin Call**: Risco de ser liquidado se o mercado se mover contra você
3. **Financiamento**: Custos de manter posições longas/noturnas

## Estratégias Recomendadas

### 1. Conservadora (Iniciantes)
- Alavancagem: 2-5x
- Stop-loss: 1-2%
- Take-profit: 2-3%
- Par de moedas: BTC/USDT (mais estável)

### 2. Moderada (Intermediários)
- Alavancagem: 5-10x
- Stop-loss: 2-3%
- Take-profit: 3-5%
- Pares: BTC/USDT, ETH/USDT

### 3. Agressiva (Avançados)
- Alavancagem: 10-20x
- Stop-loss: 3-5%
- Take-profit: 5-10%
- Múltiplos pares e estratégias complexas

## Gerenciamento de Risco

### Stop-loss Automático
O sistema implementa stop-loss automático com base nos parâmetros de risco:
- Configurável no `src/utils/risk_management.py`
- Padrão: 2% de perda

### Take-profit Automático
Take-profit automático para proteger lucros:
- Configurável no `src/utils/risk_management.py`
- Padrão: 4% de lucro

### Limites de Posição
- Máximo de 1 posição simultânea por padrão
- Configurável no sistema de gerenciamento de risco

## Monitoramento

### Interface Web
Acesse o dashboard em `http://localhost:9753` para:
- Monitorar posições abertas
- Ver histórico de trades
- Verificar status da conta

### Logs
Os logs estão disponíveis em:
- `logs/trade_execution.log`
- `logs/binance_client.log`

## Considerações Finais

### Comece com Valores Pequenos
- Use pequenas quantias até se familiarizar com o sistema
- Teste primeiro em modo paper trading (testnet)

### Educação Contínua
- Estude sobre alavancagem e riscos do trading de futures
- Mantenha-se atualizado sobre as condições de mercado

### Responsabilidade
- Nunca invista mais do que pode perder
- O sistema automatizado não elimina o risco de perdas
- Monitoramento constante é essencial, especialmente com alavancagem

## Suporte

Para problemas técnicos, consulte:
- Documentação em `docs/binance_futures_mode.md`
- Logs do sistema
- Comunidade no GitHub

Lembre-se: "O lucro verdadeiro vem da gestão de risco, não da busca por lucros maiores."