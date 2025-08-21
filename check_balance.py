#!/usr/bin/env python3
"""
check_balance.py - Check Binance account balance
"""

import os
import sys
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException

def check_balance():
    # Get API credentials from environment
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in environment variables")
        return
    
    # Create Binance client
    client = Client(api_key, api_secret)
    
    try:
        # Sync time with Binance server
        server_time = client.get_server_time()
        client.timestamp_offset = server_time['serverTime'] - int(time.time() * 1000)
        
        # Get account information with larger recvWindow
        account = client.get_account(recvWindow=60000)
        
        print("=== Binance Account Balance ===")
        
        # Filter and display non-zero balances
        total_usdt_value = 0.0
        
        for balance in account['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                # For USDT, just show the amount
                if asset == 'USDT':
                    print(f"{asset}: {total:.2f} (Free: {free:.2f}, Locked: {locked:.2f})")
                    total_usdt_value += total
                else:
                    # For other assets, try to get USDT value
                    try:
                        ticker = client.get_symbol_ticker(symbol=f"{asset}USDT")
                        price = float(ticker['price'])
                        value = total * price
                        total_usdt_value += value
                        print(f"{asset}: {total:.6f} (Free: {free:.6f}, Locked: {locked:.6f}) - Value: ${value:.2f} @ ${price:.2f}")
                    except:
                        # If we can't get price, just show the amount
                        print(f"{asset}: {total:.6f} (Free: {free:.6f}, Locked: {locked:.6f}) - Value: Unknown")
        
        print(f"\nTotal Portfolio Value: ${total_usdt_value:.2f}")
        
    except BinanceAPIException as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    check_balance()