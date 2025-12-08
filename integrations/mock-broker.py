"""
Mock Broker for offline trading testing
Simulates Alpaca/IB broker behavior without real trades
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import psycopg2
from config import load_config


@dataclass
class Order:
    """Represents a trading order"""
    id: str
    symbol: str
    quantity: int
    order_type: str  # market, limit
    side: str  # buy, sell
    status: str  # pending, filled, cancelled
    price: Optional[float] = None
    filled_price: Optional[float] = None
    filled_quantity: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MockBroker:
    """
    Mock broker that simulates trading without real money
    
    Features:
    - Accepts orders
    - Simulates fills with realistic prices
    - Stores trades in PostgreSQL
    - Responds exactly like Alpaca/IB
    """
    
    def __init__(self, config_profile='local'):
        """Initialize mock broker with local config"""
        self.config = load_config(config_profile)
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, int] = {}  # symbol -> quantity
        self.db_conn = None
        self._connect_db()
        self._init_db()
    
    def _connect_db(self):
        """Connect to local PostgreSQL"""
        try:
            self.db_conn = psycopg2.connect(
                host=self.config['database']['local_host'],
                port=self.config['database']['port'],
                database=self.config['database']['name'],
                user=self.config['database']['user'],
                password=self.config['database']['password']
            )
        except Exception as e:
            print(f"⚠️  Could not connect to database: {e}")
            print("   Orders will be stored in memory only")
    
    def _init_db(self):
        """Initialize database tables"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            
            # Create orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mock_orders (
                    id VARCHAR(100) PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    quantity INTEGER NOT NULL,
                    order_type VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    price DECIMAL(10,2),
                    filled_price DECIMAL(10,2),
                    filled_quantity INTEGER DEFAULT 0,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mock_positions (
                    symbol VARCHAR(10) PRIMARY KEY,
                    quantity INTEGER NOT NULL,
                    avg_price DECIMAL(10,2),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            print(f"⚠️  Database initialization error: {e}")
    
    def _get_mock_price(self, symbol: str) -> float:
        """
        Get mock price for a symbol
        In real implementation, this would use historical data or market simulation
        """
        # Simple mock: return a base price with some variation
        base_prices = {
            'AAPL': 150.0,
            'GOOGL': 140.0,
            'MSFT': 380.0,
            'TSLA': 250.0,
            'AMZN': 150.0,
        }
        
        base = base_prices.get(symbol.upper(), 100.0)
        # Add small random variation
        import random
        variation = random.uniform(-0.02, 0.02)  # ±2%
        return round(base * (1 + variation), 2)
    
    def place_order(self, symbol: str, quantity: int, order_type: str = 'market', 
                   side: str = 'buy', limit_price: Optional[float] = None) -> Order:
        """
        Place an order (simulated)
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            order_type: 'market' or 'limit'
            side: 'buy' or 'sell'
            limit_price: Required for limit orders
        
        Returns:
            Order object
        """
        order_id = f"mock_{int(time.time() * 1000)}"
        
        # Determine fill price
        if order_type == 'market':
            fill_price = self._get_mock_price(symbol)
        elif order_type == 'limit':
            fill_price = limit_price if limit_price else self._get_mock_price(symbol)
        else:
            raise ValueError(f"Unknown order type: {order_type}")
        
        # Create order
        order = Order(
            id=order_id,
            symbol=symbol.upper(),
            quantity=abs(quantity),
            order_type=order_type,
            side=side.lower(),
            status='filled',  # Mock broker fills immediately
            price=limit_price,
            filled_price=fill_price,
            filled_quantity=abs(quantity)
        )
        
        # Store order
        self.orders[order_id] = order
        
        # Update positions
        if side.lower() == 'buy':
            self.positions[symbol.upper()] = self.positions.get(symbol.upper(), 0) + abs(quantity)
        else:  # sell
            self.positions[symbol.upper()] = self.positions.get(symbol.upper(), 0) - abs(quantity)
        
        # Store in database
        self._save_order(order)
        self._update_position(symbol.upper())
        
        print(f"✅ Order {order_id}: {side.upper()} {abs(quantity)} {symbol} @ ${fill_price:.2f}")
        
        return order
    
    def _save_order(self, order: Order):
        """Save order to database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO mock_orders 
                (id, symbol, quantity, order_type, side, status, price, filled_price, filled_quantity, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    filled_price = EXCLUDED.filled_price,
                    filled_quantity = EXCLUDED.filled_quantity
            """, (
                order.id, order.symbol, order.quantity, order.order_type,
                order.side, order.status, order.price, order.filled_price,
                order.filled_quantity, order.timestamp
            ))
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            print(f"⚠️  Error saving order: {e}")
    
    def _update_position(self, symbol: str):
        """Update position in database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            quantity = self.positions.get(symbol, 0)
            
            if quantity == 0:
                cursor.execute("DELETE FROM mock_positions WHERE symbol = %s", (symbol,))
            else:
                # Calculate average price from recent orders
                cursor.execute("""
                    SELECT AVG(filled_price) 
                    FROM mock_orders 
                    WHERE symbol = %s AND status = 'filled'
                """, (symbol,))
                avg_price = cursor.fetchone()[0] or 0.0
                
                cursor.execute("""
                    INSERT INTO mock_positions (symbol, quantity, avg_price)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (symbol) DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        avg_price = EXCLUDED.avg_price,
                        updated_at = CURRENT_TIMESTAMP
                """, (symbol, quantity, avg_price))
            
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            print(f"⚠️  Error updating position: {e}")
    
    def get_positions(self) -> Dict[str, int]:
        """Get current positions"""
        return self.positions.copy()
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders"""
        return list(self.orders.values())
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == 'pending':
                order.status = 'cancelled'
                self._save_order(order)
                return True
        return False
    
    def close(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()


# Example usage
if __name__ == '__main__':
    # Initialize mock broker
    broker = MockBroker()
    
    # Place some test orders
    print("🧪 Testing Mock Broker")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    
    # Buy orders
    order1 = broker.place_order('AAPL', 100, 'market', 'buy')
    order2 = broker.place_order('GOOGL', 50, 'market', 'buy')
    
    # Sell order
    order3 = broker.place_order('AAPL', 50, 'market', 'sell')
    
    print("")
    print("📊 Current Positions:")
    for symbol, quantity in broker.get_positions().items():
        print(f"  {symbol}: {quantity} shares")
    
    print("")
    print("✅ Mock broker test complete")
    
    broker.close()

