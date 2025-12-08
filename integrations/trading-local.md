# 🔗 Trading/AI Integration Guide

How to connect your trading and AI work with the local AI DevOps Brain infrastructure.

---

## 🎯 Integration Pattern

Keep your **brokers real** (Alpaca, IB) but use **local infrastructure** for everything else:

```
┌─────────────────────────────────────────┐
│   Your Trading/AI Application          │
├─────────────────────────────────────────┤
│                                         │
│  Real Brokers (Alpaca, IB)             │
│  ↓                                      │
│  Local Infrastructure:                   │
│  - PostgreSQL (signals, results)       │
│  - Redis (cache, rate limits)           │
│  - Kafka (events, orders)               │
│  - MinIO (model artifacts, logs)        │
│  - AI Models (anomaly detection)        │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📊 Database Schema for Trading

### Signals Table
```sql
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,  -- buy, sell, hold
    confidence DECIMAL(5,2),
    price DECIMAL(10,2),
    metadata JSONB
);
```

### Results Table
```sql
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    strategy_name VARCHAR(100),
    symbol VARCHAR(10),
    entry_price DECIMAL(10,2),
    exit_price DECIMAL(10,2),
    pnl DECIMAL(10,2),
    metadata JSONB
);
```

### History Table
```sql
CREATE TABLE history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(10),
    price DECIMAL(10,2),
    volume BIGINT,
    indicators JSONB
);
```

---

## 🔌 Connection Examples

### Python - PostgreSQL
```python
import psycopg2
from config import load_config

config = load_config('local')  # Loads config/local.yaml

conn = psycopg2.connect(
    host=config['database']['local_host'],
    port=config['database']['port'],
    database=config['database']['name'],
    user=config['database']['user'],
    password=config['database']['password']
)

# Store signal
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO signals (timestamp, symbol, signal_type, confidence, price)
    VALUES (%s, %s, %s, %s, %s)
""", (datetime.now(), 'AAPL', 'buy', 0.85, 150.25))
conn.commit()
```

### Python - Redis
```python
import redis
from config import load_config

config = load_config('local')

r = redis.Redis(
    host=config['redis']['local_host'],
    port=config['redis']['port'],
    db=config['redis']['db']
)

# Cache rate limit
r.setex('rate_limit:AAPL', 60, '1')  # 1 request per minute
```

### Python - Kafka
```python
from kafka import KafkaProducer
from config import load_config
import json

config = load_config('local')

producer = KafkaProducer(
    bootstrap_servers=config['kafka']['local_brokers'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Publish order event
producer.send('ai-devops-events', {
    'type': 'order',
    'symbol': 'AAPL',
    'action': 'buy',
    'quantity': 100,
    'timestamp': datetime.now().isoformat()
})
```

### Python - MinIO (S3-compatible)
```python
from minio import Minio
from config import load_config

config = load_config('local')

client = Minio(
    config['storage']['local_endpoint'].replace('http://', ''),
    access_key=config['storage']['access_key'],
    secret_key=config['storage']['secret_key'],
    secure=False
)

# Store model artifact
client.fput_object(
    config['storage']['bucket'],
    'models/strategy_v1.pkl',
    'local_model.pkl'
)
```

---

## 🎭 Mock Broker for Offline Testing

Create a mock broker service for completely offline testing:

```python
# integrations/mock_broker.py

class MockBroker:
    """Mock broker that records orders without executing"""
    
    def __init__(self):
        self.orders = []
        self.positions = {}
    
    def place_order(self, symbol, quantity, order_type='market'):
        order = {
            'id': f"mock_{len(self.orders)}",
            'symbol': symbol,
            'quantity': quantity,
            'type': order_type,
            'status': 'filled',
            'timestamp': datetime.now(),
            'price': self._get_mock_price(symbol)
        }
        self.orders.append(order)
        return order
    
    def _get_mock_price(self, symbol):
        # Return mock price based on symbol
        return 150.0  # Simplified
```

---

## 🔄 Weekend Testing Replay System

Use local infrastructure for replay:

```python
# integrations/replay_system.py

def replay_weekend_testing():
    """Replay trading signals against local infrastructure"""
    
    # Load historical data
    signals = load_signals_from_db()
    
    # Replay through local infrastructure
    for signal in signals:
        # Store in local PostgreSQL
        store_signal(signal)
        
        # Publish to local Kafka
        publish_event('signal', signal)
        
        # Check with AI models
        anomaly_score = check_anomaly(signal)
        
        # Store results
        store_result(signal, anomaly_score)
```

---

## 📈 Monitoring Integration

### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram

orders_total = Counter('trading_orders_total', 'Total orders')
order_latency = Histogram('trading_order_latency_seconds', 'Order latency')

# In your trading code
orders_total.inc()
with order_latency.time():
    place_order(symbol, quantity)
```

### Grafana Dashboards
Create dashboards showing:
- Order volume over time
- PnL by strategy
- Signal accuracy
- Anomaly detection alerts

---

## 🧪 Testing Workflow

### 1. Development (Local)
```bash
# Start local environment
./scripts/start-local.sh

# Run your trading code
python your_trading_app.py --config local

# All data goes to local PostgreSQL, Redis, Kafka
```

### 2. Testing (Local + Mock Broker)
```bash
# Use mock broker for safety
python your_trading_app.py --config local --mock-broker

# Test with real brokers but local infra
python your_trading_app.py --config local --real-brokers
```

### 3. Production (AWS)
```bash
# When ready, switch to AWS
python your_trading_app.py --config aws-dev
```

---

## 🔐 Configuration Management

Use environment-based config:

```python
# config/__init__.py

import yaml
import os

def load_config(profile='local'):
    """Load configuration based on profile"""
    env = os.getenv('APP_PROFILE', profile)
    config_path = f'config/{env}.yaml'
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Usage
config = load_config('local')  # or 'aws-dev'
```

---

## 📊 Data Flow

```
Trading App
    ↓
Real Broker (Alpaca/IB)
    ↓
Local PostgreSQL (store results)
    ↓
Local Kafka (publish events)
    ↓
AI Models (anomaly detection)
    ↓
Local MinIO (store artifacts)
    ↓
Grafana (visualize)
```

---

## 🎯 Benefits

✅ **Safe Testing**: No real trades, no cloud costs
✅ **Full Observability**: All data in local Prometheus/Grafana
✅ **Fast Iteration**: Quick feedback loops
✅ **Production-Ready**: Same patterns work in AWS
✅ **Cost-Free**: $0 for development

---

**Your trading/AI work can now leverage the full AI DevOps Brain infrastructure locally!**

