import os
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import uuid
from decimal import Decimal, ROUND_DOWN

from src.config import config
from src.utils import get_logger, TradeSignal, TradingDecision, TradeResult, risk_manager, redis_client

logger = get_logger("binance_client")

class BinanceClient:
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
                logger.error(f"Failed to initialize Binance client: {e}")
                # Fall back to debug mode if connection fails
                logger.warning("Falling back to debug mode due to connection issues")
                self.debug_mode = True
                self.client = None
        else:
            self.client = None  # No real client in debug mode
        
        if self.debug_mode:
            logger.info("Connected to Binance API (DEBUG MODE - no actual connection)")
            self.account_info = {
                'balances': [
                    {'asset': 'USDT', 'free': '10000.0', 'locked': '0.0'},
                    {'asset': 'BTC', 'free': '0.0', 'locked': '0.0'},
                    {'asset': 'ETH', 'free': '0.0', 'locked': '0.0'}
                ]
            }
            logger.info("DEBUG MODE: Using mock account data")
        else:
            logger.info("Connected to Binance API")
            
            if self.client:  # Only if client was created successfully
                try:
                    # Test connection and get account info with very large recvWindow
                    self.account_info = self.client.get_account(recvWindow=10000)  # 10 seconds
                    logger.info("Successfully connected to Binance")
                    
                    # Log account balances for major assets
                    balances = {asset['asset']: float(asset['free']) for asset in self.account_info['balances'] 
                               if float(asset['free']) > 0}
                    logger.info(f"Account balances: {balances}")
                    
                except BinanceAPIException as e:
                    logger.error(f"Failed to get account info from Binance: {e}")
                    # Don't raise, just log the error and continue in debug mode
                    logger.warning("Continuing in debug mode due to API error")
                    self.debug_mode = True
                    self.client = None
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary information"""
        if self.debug_mode:
            return {
                "portfolio_value": 10000.0,
                "cash_balance": 10000.0,
                "buying_power": 10000.0,
                "daily_change": 0.0,
                "positions": []
            }
            
        try:
            account = self.client.get_account(recvWindow=60000)
            
            # Calculate total portfolio value in USDT
            total_value = 0.0
            usdt_balance = 0.0
            positions = []
            
            # Only consider major assets to speed up calculation
            major_assets = ['USDT', 'BTC', 'ETH', 'BNB', 'USDC', 'TUSD', 'FDUSD', 'DAI']
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    if asset == 'USDT':
                        usdt_balance = total
                        total_value += total
                    elif asset in major_assets:
                        # For major assets, try to get USDT price
                        try:
                            ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                            price = float(ticker['price'])
                            asset_value = total * price
                            total_value += asset_value
                            
                            # Add to positions if significant amount
                            if asset_value > 1.0:  # Only show positions worth more than $1
                                # Calculate P/L based on estimated prices (simplified for now)
                                unrealized_pl = self._calculate_simple_pl(asset, total, price)
                                
                                positions.append({
                                    'symbol': f"{asset}/USDT",
                                    'quantity': total,
                                    'market_value': asset_value,
                                    'unrealized_pl': unrealized_pl
                                })
                        except:
                            # If we can't get price, skip this asset
                            pass
            
            # Daily change is not directly available for Binance Spot via a simple API call.
            # It requires complex calculations involving historical trades and prices.
            # For now, we will set it to 0.0 to avoid displaying incorrect information.
            daily_change = 0.0
            daily_change_percent = 0.0
            
            return {
                "portfolio_value": total_value,
                "cash": usdt_balance,  # Frontend expects 'cash'
                "cash_balance": usdt_balance,  # Keep both for compatibility
                "equity": total_value,  # Frontend expects 'equity'
                "buying_power": usdt_balance,
                "daily_change": daily_change,
                "daily_change_percent": daily_change_percent,
                "position_value": total_value - usdt_balance,  # Value of non-cash positions
                "positions": positions,
                "status": "available",
                "paper_trading": True  # We're using testnet
            }
            
        except BinanceAPIException as e:
            logger.error(f"Error getting account summary: {e}")
            return {
                "portfolio_value": 0.0,
                "cash_balance": 0.0,
                "buying_power": 0.0,
                "daily_change": 0.0
            }
    
    def _calculate_position_pl(self, asset: str, quantity: float, current_price: float) -> float:
        """Calculate P/L for a position based on recent trades or estimated prices"""
        try:
            if self.debug_mode:
                return 0.0
            
            # First try to get recent trades
            try:
                symbol = f"{asset}USDT"
                trades = self.client.get_my_trades(symbol=symbol, limit=50, recvWindow=60000)
                
                if trades:
                    # Calculate weighted average buy price from trades
                    total_buy_quantity = 0.0
                    total_buy_cost = 0.0
                    
                    for trade in trades:
                        if trade['isBuyer']:  # Only consider buy trades
                            trade_quantity = float(trade['qty'])
                            trade_price = float(trade['price'])
                            total_buy_quantity += trade_quantity
                            total_buy_cost += trade_quantity * trade_price
                    
                    if total_buy_quantity > 0:
                        avg_buy_price = total_buy_cost / total_buy_quantity
                        unrealized_pl = (current_price - avg_buy_price) * quantity
                        return unrealized_pl
            except Exception as e:
                logger.debug(f"Could not get trades for {asset}, using estimated P/L: {e}")
            
            # Fallback: Use estimated initial prices for testnet assets
            # These are rough estimates of when assets were first credited to testnet accounts
            estimated_initial_prices = {
                'BTC': 100000.0,  # Estimated initial BTC price
                'ETH': 3500.0,    # Estimated initial ETH price
                'BNB': 700.0,     # Estimated initial BNB price
            }
            
            if asset in estimated_initial_prices:
                estimated_buy_price = estimated_initial_prices[asset]
                unrealized_pl = (current_price - estimated_buy_price) * quantity
                return unrealized_pl
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating P/L for {asset}: {e}")
            return 0.0
    
    def _calculate_simple_pl(self, asset: str, quantity: float, current_price: float) -> float:
        """Calculate P/L using estimated initial prices (fast method)"""
        try:
            # Use estimated initial prices for testnet assets
            estimated_initial_prices = {
                'BTC': 100000.0,  # Estimated initial BTC price
                'ETH': 3500.0,    # Estimated initial ETH price
                'BNB': 700.0,     # Estimated initial BNB price
                'USDC': 1.0,      # Stablecoin
                'TUSD': 1.0,      # Stablecoin
                'FDUSD': 1.0,     # Stablecoin
            }
            
            if asset in estimated_initial_prices:
                estimated_buy_price = estimated_initial_prices[asset]
                unrealized_pl = (current_price - estimated_buy_price) * quantity
                return unrealized_pl
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating simple P/L for {asset}: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information including LOT_SIZE filters"""
        try:
            if self.debug_mode:
                # Return mock symbol info for debug mode
                return {
                    'symbol': symbol,
                    'minQty': '0.00001',
                    'maxQty': '9000.00000000',
                    'stepSize': '0.00001',
                    'minNotional': '5.0',  # Default to 5 USDT (Binance real minimum)
                    'maxNotional': '9000000.0' # Default max notional
                }
            
            exchange_info = self.client.get_exchange_info()
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    # Extract LOT_SIZE filter
                    # Extract LOT_SIZE and NOTIONAL filters
                    symbol_filters = {
                        'symbol': symbol,
                        'minQty': '0.00001',
                        'maxQty': '9000.00000000',
                        'stepSize': '0.00001',
                        'minNotional': '5.0',  # Default to 5 USDT (Binance real minimum)
                        'maxNotional': '9000000.0' # Default max notional
                    }
                    for filter_info in symbol_info['filters']:
                        if filter_info['filterType'] == 'LOT_SIZE':
                            symbol_filters['minQty'] = filter_info['minQty']
                            symbol_filters['maxQty'] = filter_info['maxQty']
                            symbol_filters['stepSize'] = filter_info['stepSize']
                        elif filter_info['filterType'] == 'NOTIONAL':
                            symbol_filters['minNotional'] = filter_info['minNotional']
                            symbol_filters['maxNotional'] = filter_info['maxNotional']
                    return symbol_filters
            
            # Fallback if not found
            return {
                'symbol': symbol,
                'minQty': '0.00001',
                'maxQty': '9000.00000000',
                'stepSize': '0.00001',
                'minNotional': '5.0',  # Default to 5 USDT (Binance real minimum)
                'maxNotional': '9000000.0' # Default max notional
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            # Return safe defaults
            return {
                'symbol': symbol,
                'minQty': '0.00001',
                'maxQty': '9000.00000000',
                'stepSize': '0.00001',
                'minNotional': '5.0',  # Default to 5 USDT (Binance real minimum)
                'maxNotional': '9000000.0' # Default max notional
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

    def execute_trade(self, signal: TradeSignal) -> Optional[TradeResult]:
        """Execute a trade based on a signal"""
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
            
            # Get symbol information for LOT_SIZE requirements
            symbol_info = self.get_symbol_info(symbol)
            logger.info(f"Symbol info for {symbol}: {symbol_info}")
            
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
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
            logger.info(f"Available balance: ${available_balance}")
            
            if config.trading.use_fixed_amount:
                trade_amount = config.trading.trade_fixed_amount
                logger.info(f"Using fixed amount: ${trade_amount}")
                
                # Check if we have sufficient balance
                if trade_amount > available_balance:
                    logger.warning(f"Insufficient balance. Available: ${available_balance}, Required: ${trade_amount}")
                    return TradeResult(
                        symbol=signal.symbol,
                        decision=signal.decision,
                        order_id=None,
                        quantity=None,
                        price=current_price,
                        status="failed",
                        error=f"Insufficient balance. Available: ${available_balance}, Required: ${trade_amount}",
                        timestamp=datetime.now()
                    )
                
                # If trade amount is below minimum notional, adjust or skip
                if trade_amount < buffered_min_notional:
                    logger.warning(f"Trade amount ${trade_amount} is below buffered minimum notional ${buffered_min_notional:.2f}")
                    if config.trading.allow_min_notional_adjustment:
                        trade_amount = buffered_min_notional
                        logger.info(f"Adjusted trade amount to buffered minimum notional: ${trade_amount:.2f}")
                        
                        # Check if we have sufficient balance after adjustment
                        if trade_amount > available_balance:
                            logger.warning(f"Insufficient balance after adjustment. Available: ${available_balance}, Required: ${trade_amount}")
                            return TradeResult(
                                symbol=signal.symbol,
                                decision=signal.decision,
                                order_id=None,
                                quantity=None,
                                price=current_price,
                                status="failed",
                                error=f"Insufficient balance after adjustment. Available: ${available_balance}, Required: ${trade_amount}",
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
                trade_amount = account_summary["cash_balance"] * (config.trading.trade_percentage / 100)
                logger.info(f"Using {config.trading.trade_percentage}% of balance: ${trade_amount}")
                
                # Check if we have sufficient balance
                if trade_amount > available_balance:
                    logger.warning(f"Insufficient balance. Available: ${available_balance}, Required: ${trade_amount}")
                    return TradeResult(
                        symbol=signal.symbol,
                        decision=signal.decision,
                        order_id=None,
                        quantity=None,
                        price=current_price,
                        status="failed",
                        error=f"Insufficient balance. Available: ${available_balance}, Required: ${trade_amount}",
                        timestamp=datetime.now()
                    )
                
                # For percentage-based trades, adjust to minimum notional if needed
                if trade_amount < buffered_min_notional:
                    trade_amount = buffered_min_notional
                    logger.info(f"Adjusted trade amount to buffered minimum notional: ${trade_amount:.2f}")
                    
                    # Check if we have sufficient balance after adjustment
                    if trade_amount > available_balance:
                        logger.warning(f"Insufficient balance after adjustment. Available: ${available_balance}, Required: ${trade_amount}")
                        return TradeResult(
                            symbol=signal.symbol,
                            decision=signal.decision,
                            order_id=None,
                            quantity=None,
                            price=current_price,
                            status="failed",
                            error=f"Insufficient balance after adjustment. Available: ${available_balance}, Required: ${trade_amount}",
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
            
            # Determine order side using effective decision
            side = "BUY" if effective_decision == TradingDecision.BUY else "SELL"
            
            logger.info(f"Placing {side} order for {quantity_str} {symbol} at ~${current_price:.2f}")
            
            # Log the exact parameters being sent to Binance
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity_str,
                'recvWindow': 60000
            }
            logger.info(f"DEBUG: Sending order to Binance with params: {order_params}")
            
            # Place market order using create_order for better control
            try:
                order = self.client.create_order(**order_params)
                logger.info(f"DEBUG: Order successful with create_order")
            except Exception as order_error:
                logger.error(f"Failed with create_order: {order_error}")
                logger.info(f"DEBUG: Trying fallback methods...")
                
                # Fallback to specific buy/sell methods
                try:
                    if side == "BUY":
                        logger.info(f"DEBUG: Trying order_market_buy with quantity: '{quantity_str}'")
                        order = self.client.order_market_buy(
                            symbol=symbol,
                            quantity=quantity_str,
                            recvWindow=60000
                        )
                    else:
                        logger.info(f"DEBUG: Trying order_market_sell with quantity: '{quantity_str}'")
                        order = self.client.order_market_sell(
                            symbol=symbol,
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
                price=float(order['fills'][0]['price']) if order.get('fills') else current_price,
                status="executed",
                error=None,
                timestamp=datetime.now()
            )
            
            # Update position information
            if result.status == "executed":
                if side == "BUY":
                    risk_manager.update_position(signal.symbol, final_quantity, current_price, TradingDecision.BUY)
                else:
                    # Remove position when selling
                    positions_key = "current_positions"
                    positions_data = redis_client.get_json(positions_key)
                    if positions_data and signal.symbol in positions_data:
                        del positions_data[signal.symbol]
                        redis_client.set_json(positions_key, positions_data, ttl=86400)
            
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
        """Get current positions"""
        try:
            if self.debug_mode:
                # Return mock positions for debug mode
                return []
            
            account = self.client.get_account()
            positions = []
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0 and asset != 'USDT':
                    try:
                        ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                        price = float(ticker['price'])
                        value = total * price
                        
                        positions.append({
                            'symbol': f"{asset}/USDT",
                            'quantity': total,
                            'market_value': value,
                            'avg_entry_price': price,  # This is current price, not entry price
                            'unrealized_pl': 0.0  # Would need historical data
                        })
                    except:
                        pass
            
            return positions
            
        except BinanceAPIException as e:
            logger.error(f"Error getting positions: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting positions: {e}")
            return []

# Create singleton instance
binance_client = BinanceClient()