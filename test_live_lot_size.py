#!/usr/bin/env python3
"""
Teste ao vivo da correção LOT_SIZE com o sistema em execução
"""

import os
import sys
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_live_lot_size_fix():
    """Testa a correção LOT_SIZE com o sistema real"""
    print("=== TESTE AO VIVO - CORREÇÃO LOT_SIZE ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Set environment variables to match production
    os.environ["BINANCE_DEBUG_MODE"] = "false"
    os.environ["BINANCE_TESTNET"] = "true"
    
    # Get API keys from environment (should be set in Docker)
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Credenciais da Binance não encontradas")
        return False
    
    print(f"✅ Usando API Key: {api_key[:4]}...{api_key[-4:]}")
    print(f"✅ Testnet: {os.getenv('BINANCE_TESTNET', 'true')}")
    
    try:
        from src.trade_execution.binance_client import BinanceClient
        from src.utils.models import TradeSignal, TradingDecision
        
        # Create client (should connect to real testnet)
        client = BinanceClient()
        print(f"✅ Cliente criado (debug mode: {client.debug_mode})")
        
        if client.debug_mode:
            print("⚠️  ATENÇÃO: Cliente está em modo debug!")
            return False
        
        # Test symbol info retrieval
        print("\n--- Testando informações do símbolo ---")
        btc_info = client.get_symbol_info("BTCUSDT")
        print(f"BTC Info: {btc_info}")
        
        eth_info = client.get_symbol_info("ETHUSDT")
        print(f"ETH Info: {eth_info}")
        
        # Test quantity adjustment with problematic values
        print("\n--- Testando ajuste de quantidade ---")
        problematic_quantities = [
            0.001111111111111111,  # Muitas casas decimais
            0.123456789,           # Não alinhado com stepSize
            0.000001,              # Muito pequeno
            1.23456789012345       # Grande com muitas casas
        ]
        
        for qty in problematic_quantities:
            adjusted_btc = client.adjust_quantity_to_lot_size(qty, btc_info)
            adjusted_eth = client.adjust_quantity_to_lot_size(qty, eth_info)
            print(f"  {qty} -> BTC: {adjusted_btc}, ETH: {adjusted_eth}")
        
        # Test actual trade execution with small amount
        print("\n--- Testando execução de trade ---")
        test_signal = TradeSignal(
            symbol="BTC/USDT",
            decision=TradingDecision.BUY,
            confidence=0.8,
            rsi_value=30.0
        )
        
        print("Executando trade de teste...")
        result = client.execute_trade(test_signal)
        
        if result:
            print(f"✅ Resultado do trade:")
            print(f"   Status: {result.status}")
            print(f"   Quantidade: {result.quantity}")
            print(f"   Preço: ${result.price}")
            print(f"   Order ID: {result.order_id}")
            print(f"   Erro: {result.error or 'Nenhum'}")
            
            if result.status == "executed":
                print("🎉 TRADE EXECUTADO COM SUCESSO!")
                return True
            elif "LOT_SIZE" in str(result.error):
                print("❌ ERRO LOT_SIZE AINDA PRESENTE!")
                return False
            else:
                print(f"⚠️  Trade falhou por outro motivo: {result.error}")
                return False
        else:
            print("❌ Nenhum resultado retornado")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_live_lot_size_fix()
    
    if success:
        print("\n🎉 CORREÇÃO LOT_SIZE FUNCIONANDO CORRETAMENTE!")
    else:
        print("\n❌ CORREÇÃO LOT_SIZE PRECISA DE AJUSTES")
        
    print("\n📝 Para monitorar o sistema:")
    print("   docker-compose logs -f trade_execution")
    print("   docker-compose exec redis redis-cli get 'trade_result:BTC/USDT'")