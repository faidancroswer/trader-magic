# 🔧 Configuração da Binance Testnet

## ❌ Problema Identificado

As credenciais da API fornecidas não são válidas para a Binance Testnet. Erro: `-2015: Invalid API-key, IP, or permissions for action`

## ✅ Como Obter Credenciais Válidas

### 1. Acessar a Binance Testnet
- Acesse: https://testnet.binance.vision/
- Faça login com sua conta Binance (ou crie uma se não tiver)

### 2. Criar Chaves da API
1. No painel da testnet, vá para **API Management**
2. Clique em **Create API Key**
3. Dê um nome para sua API (ex: "TraderMagic")
4. **Importante**: Marque as permissões necessárias:
   - ✅ **Enable Reading** (para consultar saldo)
   - ✅ **Enable Spot & Margin Trading** (para fazer trades)
   - ❌ **Enable Futures** (não necessário para spot trading)
   - ❌ **Enable Withdrawals** (não recomendado)

### 3. Configurar IP (Opcional)
- Para maior segurança, você pode restringir o acesso por IP
- Se não configurar, deixe em branco para permitir qualquer IP

### 4. Copiar as Credenciais
- **API Key**: Uma string longa começando com letras/números
- **Secret Key**: Outra string longa (mostrada apenas uma vez)

### 5. Atualizar o arquivo .env
```env
# Binance Testnet API Keys (substitua pelos valores reais)
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=sua_secret_key_aqui
BINANCE_TESTNET=true
```

## 🧪 Testar a Conexão

Após configurar as credenciais corretas, execute:

```bash
docker compose run --rm trade_execution python /app/test_binance_connection.py
```

Você deve ver:
```
✅ Ping: {}
✅ Server time: {...}
✅ Account status: SPOT
✅ Balances: X assets with balance
🎉 Conexão com Binance Testnet bem-sucedida!
```

## 💰 Obter Saldo de Teste

Na Binance Testnet, você pode obter fundos de teste:
1. Acesse https://testnet.binance.vision/
2. Vá para **Wallet** > **Faucet**
3. Solicite BTC, ETH, USDT de teste
4. Os fundos aparecerão em sua conta em alguns minutos

## 🔄 Reiniciar o Sistema

Após configurar as credenciais corretas:

```bash
# Reiniciar o serviço
docker compose restart trade_execution

# Habilitar trading
docker exec redis redis-cli set trading_enabled true

# Verificar dashboard
# http://localhost:9753
```

## ⚠️ Notas Importantes

1. **Testnet vs Mainnet**: A testnet usa fundos falsos - nenhum dinheiro real está envolvido
2. **Credenciais Separadas**: As credenciais da testnet são diferentes da mainnet
3. **Permissões**: Certifique-se de que as permissões de trading estão habilitadas
4. **Segurança**: Nunca compartilhe suas credenciais da API