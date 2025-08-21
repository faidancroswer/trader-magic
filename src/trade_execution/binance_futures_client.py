import os
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import uuid
from decimal import Decimal, ROUND_DOWN

from src.config import config
from src.utils import get_logger, TradeSignal, TradingDecision, TradeResult, risk_manager, redis_client

logger = get_logger("binance_futures_client")

class BinanceFuturesClient:
    def __init__(self):
        # Get API credentials from environment
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
        self.debug_mode = os.getenv("BINANCE_DEBUG_MODE", "false").lower() == "true"
        
        # Validate credentials 
        if not self.api_key or not self.api_secret:
            logger.error("Binance API credentials not set")
            raise ValueError("Binance API credentials not set")
        
        # Log credentials (masked)
        logger.debug(f"Using Binance API key: {self.api_key[:4]}...{self.api_key[-4:]}")
        logger.debug(f"Using Binance API secret: {self.api_secret[:4]}...{self.api_secret[-4:]}")
        logger.info(f"Using Binance Testnet: {self.testnet}")
        logger.info(f"Debug mode: {self.debug_mode}")
        
        # Only create the client if not in debug mode
        if not self.debug_mode:
            try:
                # Create the client with timestamp synchronization
                # For futures, we need to use the futures API
                self.client = Client(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    testnet=self.testnet
                )
                
                # Sync with server time to avoid timestamp issues
                server_time = self.client.get_server_time()
                logger.info(f"Binance server time synced: {server_time}")
                
                # Calculate time offset between local and server time
                import time
                local_time = int(time.time() * 1000)
                server_timestamp = server_time['serverTime']
                time_offset = server_timestamp - local_time
                
                # Set timestamp offset to sync with server
                self.client.timestamp_offset = time_offset
                logger.info(f"Set timestamp offset: {time_offset}ms")
                
                # Small delay to ensure timestamp sync
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to initialize Binance Futures client: {e}")
                # Fall back to debug mode if connection fails
                logger.warning("Falling back to debug mode due to connection issues")
                self.debug_mode = True
                self.client = None
        else:
            self.client = None  # No real client in debug mode
        
        if self.debug_mode:
            logger.info("Connected to Binance Futures API (DEBUG MODE - no actual connection)")
            self.account_info = {
                'assets': [
                    {'asset': 'USDT', 'availableBalance': '10000.0', 'walletBalance': '10000.0'}
                ],
                'positions': []
            }
            logger.info("DEBUG MODE: Using mock account data")
        else:
            logger.info("Connected to Binance Futures API")
            
            if self.client:  # Only if client was created successfully
                try:
                    # Test connection and get account info with very large recvWindow
                    self.account_info = self.client.futures_account(recvWindow=10000)  # 10 seconds
                    logger.info("Successfully connected to Binance Futures")
                    
                    # Log account balances for major assets
                    balances = {asset['asset']: float(asset['availableBalance']) for asset in self.account_info['assets'] 
                               if float(asset['availableBalance']) > 0}
                    logger.info(f"Account balances: {balances}")
                    
                except BinanceAPIException as e:
                    logger.error(f"Failed to get account info from Binance Futures: {e}")
                    # Don't raise, just log the error and continue in debug mode
                    logger.warning("Continuing in debug mode due to API error")
                    self.debug_mode = True
                    self.client = None
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary information for futures"""
        if self.debug_mode:
            return {
                "portfolio_value": 10000.0,
                "cash_balance": 10000.0,
                "buying_power": 10000.0,
                "daily_change": 0.0,
                "positions": [],
                "leverage": 10  # Default leverage
            }
            
        try:
            account = self.client.futures_account(recvWindow=60000)
            
            # Calculate total portfolio value in USDT
            total_value = 0.0
            usdt_balance = 0.0
            positions = []
            
            # Get USDT balance
            for asset in account['assets']:
                if asset['asset'] == 'USDT':
                    usdt_balance = float(asset['availableBalance'])
                    wallet_balance = float(asset['walletBalance'])
                    total_value = wallet_balance
                    break
            
            # Get open positions
            for position in account['positions']:
                symbol = position['symbol']
                position_amt = float(position['positionAmt'])
                entry_price = float(position['entryPrice'])
                unrealized_profit = float(position['unrealizedProfit'])
                
                if position_amt != 0:  # Only show open positions
                    # Get current price
                    try:
                        ticker = self.client.futures_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                        
                        positions.append({
                            'symbol': symbol,
                            'quantity': abs(position_amt),
                            'market_value': abs(position_amt * current_price),
                            'avg_entry_price': entry_price,
                            'unrealized_pl': unrealized_profit,
                            'side': 'LONG' if position_amt > 0 else 'SHORT'
                        })
                    except:
                        # If we can't get price, use available data
                        positions.append({
                            'symbol': symbol,
                            'quantity': abs(position_amt),
                            'market_value': abs(position_amt * entry_price),  # Approximate
                            'avg_entry_price': entry_price,
                            'unrealized_pl': unrealized_profit,
                            'side': 'LONG' if position_amt > 0 else 'SHORT'
                        })
            
            # Get leverage info
            leverage = 10  # Default
            if account['positions']:
                # Use leverage from first position as example
                try:
                    leverage = int(float(account['positions'][0]['leverage']))
                except:
                    leverage = 10
            
            return {
                "portfolio_value": total_value,
                "cash": usdt_balance,
                "cash_balance": usdt_balance,
                "equity": total_value,
                "buying_power": usdt_balance * leverage,  # Account for leverage
                "daily_change": 0.0,
                "positions": positions,
                "leverage": leverage,
                "status": "available",
                "paper_trading": self.testnet
            }
            
        except BinanceAPIException as e:
            logger.error(f"Error getting account summary: {e}")
            return {
                "portfolio_value": 0.0,
                "cash_balance": 0.0,
                "buying_power": 0.0,
                "daily_change": 0.0,
                "leverage": 10
            }
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information including LOT_SIZE filters for futures"""
        try:
            if self.debug_mode:
                # Return mock symbol info for debug mode
                return {
                    'symbol': symbol,
                    'minQty': '0.001',
                    'maxQty': '1000.0',
                    'stepSize': '0.001',
                    'minNotional': '5.0',  # Default to 5 USDT
                    'maxNotional': '1000000.0'
                }
            
            exchange_info = self.client.futures_exchange_info()
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    # Extract LOT_SIZE and NOTIONAL filters
                    symbol_filters = {
                        'symbol': symbol,
                        'minQty': '0.001',
                        'maxQty': '1000.0',
                        'stepSize': '0.001',
                        'minNotional': '5.0',  # Default to 5 USDT
                        'maxNotional': '1000000.0'
                    }
                    for filter_info in symbol_info['filters']:
                        if filter_info['filterType'] == 'LOT_SIZE':
                            symbol_filters['minQty'] = filter_info['minQty']
                            symbol_filters['maxQty'] = filter_info['maxQty']
                            symbol_filters['stepSize'] = filter_info['stepSize']
                        elif filter_info['filterType'] == 'MIN_NOTIONAL':
                            symbol_filters['minNotional'] = filter_info['notional']
                    return symbol_filters
            
            # Fallback if not found
            return {
                'symbol': symbol,
                'minQty': '0.001',
                'maxQty': '1000.0',
                'stepSize': '0.001',
                'minNotional': '5.0',
                'maxNotional': '1000000.0'
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            # Return safe defaults
            return {
                'symbol': symbol,
                'minQty': '0.001',
                'maxQty': '1000.0',
                'stepSize': '0.001',
                'minNotional': '5.0',
                'maxNotional': '1000000.0'
            }
    
    def adjust_quantity_to_lot_size(self, quantity: float, symbol_info: Dict[str, Any]) -> str:
        """Adjust quantity to comply with LOT_SIZE requirements"""
        
        min_qty = Decimal(symbol_info['minQty'])
        max_qty = Decimal(symbol_info['maxQty'])
        step_size = Decimal(symbol_info['stepSize'])
        
        # Convert quantity to Decimal
        qty_decimal = Decimal(str(quantity))
        
        # Check if quantity is below minimum
        if qty_decimal < min_qty:
            logger.warning(f"Quantity {qty_decimal} below minimum {min_qty}, using minimum")
            qty_decimal = min_qty
        
        # Check if quantity is above maximum
        if qty_decimal > max_qty:
            logger.warning(f"Quantity {qty_decimal} above maximum {max_qty}, using maximum")
            qty_decimal = max_qty
        
        # Adjust to step size
        # Formula: quantity = min_qty + (floor((quantity - min_qty) / step_size) * step_size)
        if step_size > 0:
            steps = ((qty_decimal - min_qty) / step_size).quantize(Decimal('1'), rounding=ROUND_DOWN)
            qty_decimal = min_qty + (steps * step_size)
        
        # Ensure we're still within bounds after adjustment
        if qty_decimal < min_qty:
            qty_decimal = min_qty
        elif qty_decimal > max_qty:
            qty_decimal = max_qty
        
        # Format to remove trailing zeros
        qty_str = str(qty_decimal.normalize())
        
        logger.info(f"Adjusted quantity: {quantity} -> {qty_str} (min: {min_qty}, step: {step_size})")
        return qty_str

    def adjust_quantity_to_meet_notional(self, quantity: float, price: float, symbol_info: Dict[str, Any]) -> Tuple[str, float]:
        """Adjust quantity to meet both LOT_SIZE and NOTIONAL requirements"""
        from decimal import Decimal, ROUND_DOWN
        
        min_notional = Decimal(symbol_info.get('minNotional', '5.0'))
        step_size = Decimal(symbol_info['stepSize'])
        min_qty = Decimal(symbol_info['minQty'])
        max_qty = Decimal(symbol_info['maxQty'])
        
        # Convert to Decimal for precision
        qty_decimal = Decimal(str(quantity))
        price_decimal = Decimal(str(price))
        
        # First, ensure we meet LOT_SIZE requirements
        qty_decimal = self._adjust_to_lot_size_decimal(qty_decimal, min_qty, step_size, max_qty)
        
        # Check if we meet NOTIONAL requirements
        notional_value = qty_decimal * price_decimal
        
        # If not, iteratively increase quantity until we meet NOTIONAL requirement
        while notional_value < min_notional and qty_decimal < max_qty:
            # Add one step size
            qty_decimal += step_size
            # Re-adjust to LOT_SIZE if needed
            qty_decimal = self._adjust_to_lot_size_decimal(qty_decimal, min_qty, step_size, max_qty)
            # Recalculate notional value
            notional_value = qty_decimal * price_decimal
            
            # Safety check to prevent infinite loop
            if qty_decimal > max_qty:
                break
        
        # Final check
        if notional_value < min_notional:
            raise ValueError(f"Cannot meet minimum notional value of {min_notional} with max quantity {max_qty}")
        
        return str(qty_decimal.normalize()), float(notional_value)

    def _adjust_to_lot_size_decimal(self, qty: 'Decimal', min_qty: 'Decimal', step_size: 'Decimal', max_qty: 'Decimal') -> 'Decimal':
        """Adjust quantity to comply with LOT_SIZE requirements using Decimal arithmetic"""
        # Ensure minimum quantity
        if qty < min_qty:
            qty = min_qty
        
        # Ensure maximum quantity
        if qty > max_qty:
            qty = max_qty
        
        # Adjust to step size
        if step_size > 0:
            # Formula: quantity = min_qty + (floor((quantity - min_qty) / step_size) * step_size)
            steps = ((qty - min_qty) / step_size).quantize(Decimal('1'), rounding=ROUND_DOWN)
            qty = min_qty + (steps * step_size)
        
        return qty

    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol"""
        try:
            if self.debug_mode:
                logger.info(f"DEBUG MODE: Would set leverage for {symbol} to {leverage}x")
                return
            
            # Set leverage (1-125x depending on symbol)
            response = self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info(f"Set leverage for {symbol} to {leverage}x")
            return response
        except Exception as e:
            logger.error(f"Error setting leverage for {symbol}: {e}")
            return None

    def set_position_mode(self, dual_side_position: bool = False):
        """Set position mode for futures trading
        Args:
            dual_side_position: False for One-way Mode, True for Hedge Mode
        """
        try:
            if self.debug_mode:
                logger.info(f"DEBUG MODE: Would set position mode to {'Hedge Mode' if dual_side_position else 'One-way Mode'}")
                return
            
            # Set position mode
            response = self.client.futures_change_position_mode(dualSidePosition=dual_side_position)
            mode = "Hedge Mode" if dual_side_position else "One-way Mode"
            logger.info(f"Set position mode to {mode}")
            return response
        except Exception as e:
            # If the error is that the position mode is already set, we can ignore it
            if "No need to change position side" in str(e):
                mode = "Hedge Mode" if dual_side_position else "One-way Mode"
                logger.info(f"Position mode is already set to {mode}")
                return {"msg": f"Position mode is already set to {mode}"}
            else:
                logger.error(f"Error setting position mode: {e}")
                return None

    def execute_trade(self, signal: TradeSignal) -> Optional[TradeResult]:
        """Execute a trade based on a signal in futures market"""
        try:
            symbol = signal.symbol.replace("/", "")  # Convert BTC/USDT to BTCUSDT
            
            if self.debug_mode:
                # Simulate trade execution
                mock_price = 45000.0 if "BTC" in symbol else 3000.0
                mock_quantity = 0.001 if "BTC" in symbol else 0.01
                
                result = TradeResult(
                    symbol=signal.symbol,
                    decision=signal.decision,
                    order_id=f"debug-{uuid.uuid4()}",
                    quantity=mock_quantity,
                    price=mock_price,
                    status="executed",
                    error=None,
                    timestamp=datetime.now()
                )
                
                logger.info(f"DEBUG MODE: Simulated {signal.decision.value} order for {signal.symbol}")
                return result
            
            # Set position mode to One-way Mode to avoid position side conflicts
            self.set_position_mode(dual_side_position=False)
            
            # Get symbol information for LOT_SIZE requirements
            symbol_info = self.get_symbol_info(symbol)
            logger.info(f"Symbol info for {symbol}: {symbol_info}")
            
            # Get current price
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            # Check stop loss and take profit before executing any trade
            exit_decision = risk_manager.check_stop_loss_take_profit(signal.symbol, current_price)
            if exit_decision:
                # Create an opposite signal to close the position
                logger.info(f"Executing {exit_decision.value} order to close position based on stop loss/take profit")
                # We'll continue with the trade but with the exit decision instead
                effective_decision = exit_decision
            else:
                # Check position limits
                if not risk_manager.check_position_limits(signal.symbol):
                    logger.warning(f"Position limit reached for {signal.symbol}")
                    return TradeResult(
                        symbol=signal.symbol,
                        decision=signal.decision,
                        order_id=None,
                        quantity=None,
                        price=current_price,
                        status="failed",
                        error="Position limit reached",
                        timestamp=datetime.now()
                    )
                
                # Check daily limits
                if not risk_manager.check_daily_limits():
                    logger.warning(f"Daily limits reached")
                    return TradeResult(
                        symbol=signal.symbol,
                        decision=signal.decision,
                        order_id=None,
                        quantity=None,
                        price=current_price,
                        status="failed",
                        error="Daily trading limits reached",
                        timestamp=datetime.now()
                    )
                
                effective_decision = signal.decision
            
            # CHECK MIN NOTIONAL BEFORE CALCULATING QUANTITY
            # Get symbol information for NOTIONAL requirements
            min_notional = float(symbol_info.get('minNotional', 5.0))
            
            # Apply buffer percentage if configured
            buffer_percent = config.trading.min_notional_buffer_percent
            buffered_min_notional = min_notional * (1 + buffer_percent / 100)
            logger.info(f"Min notional: {min_notional}, Buffered min notional: {buffered_min_notional:.2f} ({buffer_percent}% buffer)")
            
            # Calculate quantity based on configuration
            account_summary = self.get_account_summary()
            available_balance = account_summary["cash_balance"]
            leverage = account_summary.get("leverage", 10)  # Default to 10x leverage
            logger.info(f"Available balance: ${available_balance}, Leverage: {leverage}x")
            
            # Set leverage for the symbol
            self.set_leverage(symbol, leverage)
            
            if config.trading.use_fixed_amount:
                trade_amount = config.trading.trade_fixed_amount
                logger.info(f"Using fixed amount: ${trade_amount}")
                
                # Check if we have sufficient balance
                if trade_amount > available_balance * leverage:  # Account for leverage
                    logger.warning(f"Insufficient balance. Available: ${available_balance} (x{leverage} = ${available_balance * leverage}), Required: ${trade_amount}")
                    return TradeResult(
                        symbol=signal.symbol,
                        decision=signal.decision,
                        order_id=None,
                        quantity=None,
                        price=current_price,
                        status="failed",
                        error=f"Insufficient balance. Available: ${available_balance} (x{leverage}), Required: ${trade_amount}",
                        timestamp=datetime.now()
                    )
                
                # If trade amount is below minimum notional, adjust or skip
                if trade_amount < buffered_min_notional:
                    logger.warning(f"Trade amount ${trade_amount} is below buffered minimum notional ${buffered_min_notional:.2f}")
                    if config.trading.allow_min_notional_adjustment:
                        trade_amount = buffered_min_notional
                        logger.info(f"Adjusted trade amount to buffered minimum notional: ${trade_amount:.2f}")
                        
                        # Check if we have sufficient balance after adjustment
                        if trade_amount > available_balance * leverage:
                            logger.warning(f"Insufficient balance after adjustment. Available: ${available_balance} (x{leverage}), Required: ${trade_amount}")
                            return TradeResult(
                                symbol=signal.symbol,
                                decision=signal.decision,
                                order_id=None,
                                quantity=None,
                                price=current_price,
                                status="failed",
                                error=f"Insufficient balance after adjustment. Available: ${available_balance} (x{leverage}), Required: ${trade_amount}",
                                timestamp=datetime.now()
                            )
                    else:
                        logger.error(f"Trade amount ${trade_amount} below buffered minimum notional ${buffered_min_notional:.2f} and adjustment not allowed")
                        return TradeResult(
                            symbol=signal.symbol,
                            decision=signal.decision,
                            order_id=None,
                            quantity=None,
                            price=current_price,
                            status="failed",
                            error=f"Trade amount ${trade_amount} below minimum notional ${buffered_min_notional:.2f}",
                            timestamp=datetime.now()
                        )
            else:
                trade_amount = account_summary["cash_balance"] * (config.trading.trade_percentage / 100) * leverage
                logger.info(f"Using {config.trading.trade_percentage}% of balance with {leverage}x leverage: ${trade_amount}")
                
                # Check if we have sufficient balance
                if trade_amount > available_balance * leverage:
                    logger.warning(f"Insufficient balance. Available: ${available_balance} (x{leverage} = ${available_balance * leverage}), Required: ${trade_amount}")
                    return TradeResult(
                        symbol=signal.symbol,
                        decision=signal.decision,
                        order_id=None,
                        quantity=None,
                        price=current_price,
                        status="failed",
                        error=f"Insufficient balance. Available: ${available_balance} (x{leverage}), Required: ${trade_amount}",
                        timestamp=datetime.now()
                    )
                
                # For percentage-based trades, adjust to minimum notional if needed
                if trade_amount < buffered_min_notional:
                    trade_amount = buffered_min_notional
                    logger.info(f"Adjusted trade amount to buffered minimum notional: ${trade_amount:.2f}")
                    
                    # Check if we have sufficient balance after adjustment
                    if trade_amount > available_balance * leverage:
                        logger.warning(f"Insufficient balance after adjustment. Available: ${available_balance} (x{leverage}), Required: ${trade_amount}")
                        return TradeResult(
                            symbol=signal.symbol,
                            decision=signal.decision,
                            order_id=None,
                            quantity=None,
                            price=current_price,
                            status="failed",
                            error=f"Insufficient balance after adjustment. Available: ${available_balance} (x{leverage}), Required: ${trade_amount}",
                            timestamp=datetime.now()
                        )
            
            quantity = trade_amount / current_price
            logger.info(f"Initial calculated quantity: {quantity} {symbol.replace('USDT', '')} (${trade_amount:.2f} ÷ ${current_price})")
            
            # Adjust quantity to meet both LOT_SIZE and NOTIONAL requirements
            try:
                quantity_str, final_notional = self.adjust_quantity_to_meet_notional(quantity, current_price, symbol_info)
                logger.info(f"Adjusted quantity to meet NOTIONAL requirements: {quantity_str} (${final_notional:.2f})")
            except ValueError as e:
                logger.error(f"Could not adjust quantity to meet NOTIONAL requirements: {e}")
                return TradeResult(
                    symbol=signal.symbol,
                    decision=signal.decision,
                    order_id=None,
                    quantity=None,
                    price=current_price,
                    status="failed",
                    error=str(e),
                    timestamp=datetime.now()
                )
            
            # Validate final quantity
            final_quantity = float(quantity_str)
            min_quantity = float(symbol_info['minQty'])
    
            if final_quantity <= 0:
                logger.warning(f"Final quantity is 0 for {signal.symbol}")
                return TradeResult(
                    symbol=signal.symbol,
                    decision=signal.decision,
                    order_id=None,
                    quantity=None,
                    price=current_price,
                    status="failed",
                    error="Insufficient balance or quantity too small",
                    timestamp=datetime.now()
                )
            
            if final_quantity < min_quantity:
                logger.warning(f"Final quantity {final_quantity} is below minimum {min_quantity} for {signal.symbol}")
                return TradeResult(
                    symbol=signal.symbol,
                    decision=signal.decision,
                    order_id=None,
                    quantity=None,
                    price=current_price,
                    status="failed",
                    error=f"Quantity {final_quantity} below minimum {min_quantity}",
                    timestamp=datetime.now()
                )
            
            # Validate final quantity format
            import re
            binance_pattern = r'^([0-9]{1,20})(\.[0-9]{1,20})?$'
    
            is_valid = bool(re.match(binance_pattern, quantity_str))
            
            logger.info(f"Final quantity: '{quantity_str}' (valid: {is_valid})")
            
            if not is_valid:
                logger.error(f"INVALID quantity format: '{quantity_str}' does not match Binance pattern")
                return TradeResult(
                    symbol=signal.symbol,
                    decision=signal.decision,
                    order_id=None,
                    quantity=None,
                    price=current_price,
                    status="failed",
                    error=f"Invalid quantity format: '{quantity_str}'",
                    timestamp=datetime.now()
                )
            
            # Determine order side and position side using effective decision
            side = "BUY" if effective_decision == TradingDecision.BUY else "SELL"
            
            logger.info(f"Placing {side} order for {quantity_str} {symbol} at ~${current_price:.2f}")
            
            # Log the exact parameters being sent to Binance
            # For One-way Mode, we don't need to specify positionSide
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity_str,
                'recvWindow': 60000
            }
            logger.info(f"DEBUG: Sending order to Binance with params: {order_params}")
            
            # Place market order using futures_create_order for better control
            try:
                order = self.client.futures_create_order(**order_params)
                logger.info(f"DEBUG: Order successful with futures_create_order")
            except Exception as order_error:
                logger.error(f"Failed with futures_create_order: {order_error}")
                logger.info(f"DEBUG: Trying fallback methods...")
                
                # Fallback to specific buy/sell methods
                try:
                    if side == "BUY":
                        logger.info(f"DEBUG: Trying futures_create_order with BUY")
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side="BUY",
                            type='MARKET',
                            quantity=quantity_str,
                            recvWindow=60000
                        )
                    else:
                        logger.info(f"DEBUG: Trying futures_create_order with SELL")
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side="SELL",
                            type='MARKET',
                            quantity=quantity_str,
                            recvWindow=60000
                        )
                    logger.info(f"DEBUG: Fallback method successful")
                except Exception as fallback_error:
                    logger.error(f"Fallback method also failed: {fallback_error}")
                    raise fallback_error
            
            logger.info(f"Placed {side} order for {quantity_str} {symbol} at ~${current_price:.2f}")
            
            # Create the trade result
            result = TradeResult(
                symbol=signal.symbol,
                decision=effective_decision,  # Use effective decision (could be stop loss/take profit)
                order_id=order['orderId'],
                quantity=float(order['executedQty']) if 'executedQty' in order else final_quantity,
                price=float(order['avgPrice']) if 'avgPrice' in order else current_price,
                status="executed",
                error=None,
                timestamp=datetime.now()
            )
            
            # Update position information
            if result.status == "executed":
                if side == "BUY":
                    risk_manager.update_position(signal.symbol, final_quantity, current_price, TradingDecision.BUY)
                else:
                    # For short positions, we also update the position
                    risk_manager.update_position(signal.symbol, final_quantity, current_price, TradingDecision.SELL)
            
            # Update daily stats
            risk_manager.update_daily_stats(result)
            
            return result
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error executing trade: {e}")
            return TradeResult(
                symbol=signal.symbol,
                decision=signal.decision,
                order_id=None,
                quantity=None,
                price=None,
                status="failed",
                error=str(e),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Unexpected error executing trade: {e}")
            return TradeResult(
                symbol=signal.symbol,
                decision=signal.decision,
                order_id=None,
                quantity=None,
                price=None,
                status="failed",
                error=str(e),
                timestamp=datetime.now()
            )
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current futures positions"""
        try:
            if self.debug_mode:
                # Return mock positions for debug mode
                return []
            
            account = self.client.futures_account()
            positions = []
            
            for position in account['positions']:
                symbol = position['symbol']
                position_amt = float(position['positionAmt'])
                entry_price = float(position['entryPrice'])
                unrealized_profit = float(position['unrealizedProfit'])
                
                if position_amt != 0:  # Only show open positions
                    try:
                        ticker = self.client.futures_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                        value = abs(position_amt * current_price)
                        
                        positions.append({
                            'symbol': symbol,
                            'quantity': abs(position_amt),
                            'market_value': value,
                            'avg_entry_price': entry_price,
                            'unrealized_pl': unrealized_profit,
                            'side': 'LONG' if position_amt > 0 else 'SHORT'
                        })
                    except:
                        # If we can't get price, use available data
                        positions.append({
                            'symbol': symbol,
                            'quantity': abs(position_amt),
                            'market_value': abs(position_amt * entry_price),  # Approximate
                            'avg_entry_price': entry_price,
                            'unrealized_pl': unrealized_profit,
                            'side': 'LONG' if position_amt > 0 else 'SHORT'
                        })
            
            return positions
            
        except BinanceAPIException as e:
            logger.error(f"Error getting positions: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting positions: {e}")
            return []

# Create singleton instance
binance_futures_client = BinanceFuturesClient()