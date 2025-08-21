from typing import Optional, Dict, Any
from src.utils import get_logger, redis_client
from src.utils.models import TradeSignal, TradeResult, TradingDecision
import json

logger = get_logger("risk_management")

class RiskManager:
    def __init__(self):
        # Default risk parameters
        self.max_positions = 1  # Maximum number of simultaneous positions
        self.stop_loss_percent = 2.0  # Stop loss percentage
        self.take_profit_percent = 4.0  # Take profit percentage
        self.max_daily_loss = 10.0  # Maximum daily loss in USD
        self.max_daily_trades = 10  # Maximum daily trades
        
    def check_position_limits(self, symbol: str) -> bool:
        """
        Check if we can open a new position based on position limits
        """
        try:
            # Get current positions from Redis
            positions_key = "current_positions"
            positions_data = redis_client.get_json(positions_key)
            
            if not positions_data:
                positions_data = {}
                
            # Count current positions
            current_positions = len(positions_data)
            
            if current_positions >= self.max_positions:
                logger.warning(f"Position limit reached. Current: {current_positions}, Max: {self.max_positions}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error checking position limits: {e}")
            return True  # Allow trade if we can't check limits
            
    def check_daily_limits(self) -> bool:
        """
        Check if we've exceeded daily trading limits
        """
        try:
            # Get daily stats from Redis
            daily_stats_key = "daily_stats"
            stats = redis_client.get_json(daily_stats_key)
            
            if not stats:
                stats = {"trades": 0, "loss": 0.0}
                
            # Check daily trade limit
            if stats.get("trades", 0) >= self.max_daily_trades:
                logger.warning(f"Daily trade limit reached. Trades: {stats['trades']}, Max: {self.max_daily_trades}")
                return False
                
            # Check daily loss limit
            if stats.get("loss", 0.0) >= self.max_daily_loss:
                logger.warning(f"Daily loss limit reached. Loss: ${stats['loss']}, Max: ${self.max_daily_loss}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error checking daily limits: {e}")
            return True  # Allow trade if we can't check limits
            
    def update_position(self, symbol: str, quantity: float, price: float, decision: TradingDecision):
        """
        Update position information in Redis
        """
        try:
            positions_key = "current_positions"
            positions_data = redis_client.get_json(positions_key)
            
            if not positions_data:
                positions_data = {}
                
            # Update position
            # For futures, we need to track both long and short positions
            position_type = "LONG" if decision == TradingDecision.BUY else "SHORT"
            
            positions_data[symbol] = {
                "quantity": quantity,
                "entry_price": price,
                "decision": decision.value,
                "position_type": position_type,
                "stop_loss": price * (1 - self.stop_loss_percent/100) if decision == TradingDecision.BUY else price * (1 + self.stop_loss_percent/100),
                "take_profit": price * (1 + self.take_profit_percent/100) if decision == TradingDecision.BUY else price * (1 - self.take_profit_percent/100)
            }
            
            # Save to Redis
            redis_client.set_json(positions_key, positions_data, ttl=86400)  # 24 hour TTL
            logger.info(f"Updated position for {symbol} ({position_type})")
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> Optional[TradingDecision]:
        """
        Check if we should exit a position based on stop loss or take profit
        """
        try:
            positions_key = "current_positions"
            positions_data = redis_client.get_json(positions_key)
            
            if not positions_data or symbol not in positions_data:
                return None
                
            position = positions_data[symbol]
            decision = position["decision"]
            position_type = position.get("position_type", "LONG")  # Default to LONG for backward compatibility
            stop_loss = position["stop_loss"]
            take_profit = position["take_profit"]
            
            # Check stop loss
            if position_type == "LONG":  # Traditional long position
                if current_price <= stop_loss:
                    logger.info(f"Stop loss triggered for {symbol} (LONG). Current price: ${current_price}, Stop loss: ${stop_loss}")
                    return TradingDecision.SELL
                elif current_price >= take_profit:
                    logger.info(f"Take profit triggered for {symbol} (LONG). Current price: ${current_price}, Take profit: ${take_profit}")
                    return TradingDecision.SELL
            else:  # SHORT position
                if current_price >= stop_loss:
                    logger.info(f"Stop loss triggered for {symbol} (SHORT). Current price: ${current_price}, Stop loss: ${stop_loss}")
                    return TradingDecision.BUY
                elif current_price <= take_profit:
                    logger.info(f"Take profit triggered for {symbol} (SHORT). Current price: ${current_price}, Take profit: ${take_profit}")
                    return TradingDecision.BUY
                
            return None
        except Exception as e:
            logger.error(f"Error checking stop loss/take profit: {e}")
            return None
            
    def update_daily_stats(self, result: TradeResult):
        """
        Update daily trading statistics
        """
        try:
            daily_stats_key = "daily_stats"
            stats = redis_client.get_json(daily_stats_key)
            
            if not stats:
                stats = {"trades": 0, "loss": 0.0}
                
            # Update stats
            stats["trades"] += 1
            
            # If it's a failed trade, add to losses
            if result.status == "failed" and result.error:
                # Estimate loss from error message if possible
                if "Insufficient balance" in result.error:
                    # Extract required amount from error message
                    try:
                        parts = result.error.split("Required: $")
                        if len(parts) > 1:
                            required = float(parts[1])
                            stats["loss"] += required
                    except:
                        # If we can't parse, add a default amount
                        stats["loss"] += 2.0  # Default $2 loss
                        
            # Save to Redis
            redis_client.set_json(daily_stats_key, stats, ttl=86400)  # 24 hour TTL
            logger.info(f"Updated daily stats. Trades: {stats['trades']}, Loss: ${stats['loss']}")
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")

# Create singleton instance
risk_manager = RiskManager()