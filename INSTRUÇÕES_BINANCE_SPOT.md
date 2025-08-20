# Instruções para Operar na Conta Real da Binance Spot

Este documento fornece instruções detalhadas para configurar e operar o sistema TraderMagic na conta real da Binance Spot usando a estratégia RSI.

## Visão Geral

O TraderMagic é um sistema de trading automatizado que utiliza análise de RSI (Índice de Força Relativa) para tomar decisões de compra e venda. O sistema está configurado para operar com os pares BTC/USDT e ETH/USDT.

## Configuração Inicial

### 1. Credenciais da API da Binance

Para operar na conta real da Binance, você precisa configurar as credenciais da API:

1. Acesse a Binance e vá para **User Center** > **API Management**
2. Clique em **Create API Key**
3. Dê um nome para sua API (ex: "TraderMagic")
4. **Importante**: Marque as permissões necessárias:
   - ✅ **Enable Reading** (para consultar saldo)
   - ✅ **Enable Spot & Margin Trading** (para fazer trades)
   - ❌ **Enable Futures** (não necessário para spot trading)
   - ❌ **Enable Withdrawals** (não recomendado)
5. Copie as credenciais geradas:
   - **API Key**: Uma string longa começando com letras/números
   - **Secret Key**: Outra string longa

### 2. Configuração do Arquivo .env

Atualize o arquivo `.env` com as seguintes configurações:

```env
# Binance API Keys (substitua pelos valores reais)
BINANCE_API_KEY=sua_api_key_real
BINANCE_API_SECRET=sua_secret_key_real
BINANCE_TESTNET=false
BINANCE_BASE_URL=https://api.binance.com
BINANCE_DEBUG_MODE=false

# Trading Configuration
SYMBOLS=BTC/USDT,ETH/USDT
TRADE_PERCENTAGE=1.0
TRADE_FIXED_AMOUNT=50.0
TRADE_USE_FIXED=false
RSI_PERIOD=14
POLL_INTERVAL=300
TRADING_EXCHANGE=binance
```

### 3. Configurações de Trading

O sistema suporta dois modos para determinar o tamanho dos trades:

#### Modo de Porcentagem (Padrão)
- TRADE_PERCENTAGE=1.0 (1% da carteira para cada trade)
- TRADE_USE_FIXED=false

#### Modo de Valor Fixo
- TRADE_FIXED_AMOUNT=50.0 ($50 fixos por trade)
- TRADE_USE_FIXED=true

## Testando a Conexão

Para testar a conexão com a API da Binance em modo real, execute:

```bash
python test_binance_connection.py
```

Você deve ver uma mensagem de sucesso semelhante a:
```
✅ Ping: {}
✅ Server time: {...}
✅ Account status: SPOT
✅ Balances: X assets with balance
🎉 Conexão com Binance bem-sucedida!
```

## Executando o Sistema

### 1. Iniciar o Sistema

```bash
docker compose up -d
```

### 2. Acessar o Dashboard

Abra o navegador e acesse: http://localhost:9753

### 3. Executar Testes Iniciais em Modo Simulado

Antes de habilitar o trading real, execute testes em modo simulado:

1. Certifique-se de que `BINANCE_DEBUG_MODE=true` no arquivo .env
2. Inicie o sistema
3. Monitore o dashboard para verificar se os sinais de trading estão sendo gerados corretamente

### 4. Habilitar Trading Real

Para habilitar o trading real:

1. Certifique-se de que `BINANCE_DEBUG_MODE=false` no arquivo .env
2. Reinicie o sistema: `docker compose restart`
3. Acesse o dashboard
4. Clique no botão verde "Start Trading"

Alternativamente, você pode usar o script:
```bash
./force_trading_enabled.sh
```

## Monitorando o Sistema

### Dashboard

O dashboard web em http://localhost:9753 mostra:

- Status da conta e saldos
- Sinais de trading gerados
- Histórico de trades executados
- Gráficos de preços com indicadores RSI

### Logs

Para monitorar os logs do sistema:

```bash
docker compose logs -f
```

## Segurança

### Recursos de Segurança

1. **Trading desabilitado por padrão**: O sistema inicia com trading desabilitado por segurança
2. **Controle manual**: O usuário deve habilitar explicitamente o trading através do dashboard
3. **Modo debug**: Permite testar o sistema sem executar trades reais

### Boas Práticas

1. **Teste sempre primeiro em modo simulado**
2. **Monitore constantemente os primeiros trades reais**
3. **Mantenha as credenciais da API em local seguro**
4. **Não compartilhe suas credenciais com ninguém**
5. **Verifique regularmente os saldos e posições**

## Resolução de Problemas

### Erros Comuns

1. **"Filter failure: LOT_SIZE"**: As quantidades calculadas não estão em conformidade com os requisitos da Binance. O sistema já está configurado para ajustar automaticamente as quantidades.

2. **"Invalid API-key, IP, or permissions"**: Verifique se as credenciais da API estão corretas e se as permissões necessárias estão habilitadas.

3. **Conexão falhando**: Verifique se a URL da API está correta (https://api.binance.com para conta real).

### Suporte

Para problemas não resolvidos, consulte a documentação em `docs/` ou entre em contato com o suporte técnico.

## Considerações Finais

- Este sistema é fornecido apenas para fins educacionais e de pesquisa
- Sempre faça sua própria pesquisa e considere consultar um consultor financeiro antes de tomar decisões de investimento
- Trading envolve riscos significativos e pode resultar em perdas financeiras
- Nunca invista mais do que você pode perder