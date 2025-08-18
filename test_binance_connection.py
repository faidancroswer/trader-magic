#!/usr/bin/env python3
"""
Script para testar a conexão com a Binance Testnet
"""
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Carregar credenciais do .env
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

print(f"API Key: {api_key[:4]}...{api_key[-4:] if api_key else 'None'}")
print(f"API Secret: {api_secret[:4]}...{api_secret[-4:] if api_secret else 'None'}")

if not api_key or not api_secret:
    print("❌ Credenciais não encontradas!")
    exit(1)

try:
    # Testar conexão com testnet
    client = Client(api_key=api_key, api_secret=api_secret, testnet=True)
    
    print("🔄 Testando conexão com Binance Testnet...")
    
    # Testar ping
    ping = client.ping()
    print(f"✅ Ping: {ping}")
    
    # Testar tempo do servidor
    server_time = client.get_server_time()
    print(f"✅ Server time: {server_time}")
    
    # Testar informações da conta
    print("🔄 Testando get_account...")
    account = client.get_account(recvWindow=60000)  # 60 segundos
    print(f"✅ Account status: {account.get('accountType', 'Unknown')}")
    
    # Mostrar saldos
    balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
    print(f"✅ Balances: {len(balances)} assets with balance")
    for balance in balances[:5]:  # Mostrar apenas os primeiros 5
        print(f"   {balance['asset']}: {balance['free']} (free) + {balance['locked']} (locked)")
    
    print("🎉 Conexão com Binance Testnet bem-sucedida!")
    
except BinanceAPIException as e:
    print(f"❌ Erro da API Binance: {e}")
    print(f"   Código: {e.code}")
    print(f"   Mensagem: {e.message}")
except Exception as e:
    print(f"❌ Erro geral: {e}")