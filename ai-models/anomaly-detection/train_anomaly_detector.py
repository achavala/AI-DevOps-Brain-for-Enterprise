"""
Anomaly Detection Model Training
Supports multiple algorithms: Z-score, Prophet, Isolation Forest, LSTM
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from prophet import Prophet
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib
import json
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Unified anomaly detection interface"""
    
    def __init__(self, algorithm='isolation_forest'):
        self.algorithm = algorithm
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def train(self, data, labels=None):
        """Train the anomaly detection model"""
        logger.info(f"Training {self.algorithm} model...")
        
        if self.algorithm == 'z_score':
            self._train_zscore(data)
        elif self.algorithm == 'isolation_forest':
            self._train_isolation_forest(data)
        elif self.algorithm == 'prophet':
            self._train_prophet(data)
        elif self.algorithm == 'lstm':
            self._train_lstm(data, labels)
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")
        
        self.is_trained = True
        logger.info("Training completed")
        
    def _train_zscore(self, data):
        """Z-score based anomaly detection"""
        self.mean = np.mean(data, axis=0)
        self.std = np.std(data, axis=0)
        self.threshold = 3.0  # 3 standard deviations
        
    def _train_isolation_forest(self, data):
        """Isolation Forest anomaly detection"""
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        scaled_data = self.scaler.fit_transform(data)
        self.model.fit(scaled_data)
        
    def _train_prophet(self, data):
        """Prophet time-series forecasting"""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
            
        if 'ds' not in df.columns:
            df['ds'] = pd.date_range(start='2024-01-01', periods=len(df), freq='H')
        if 'y' not in df.columns:
            df['y'] = df.iloc[:, 0]
            
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.05
        )
        self.model.fit(df[['ds', 'y']])
        
    def _train_lstm(self, data, labels=None):
        """LSTM-based anomaly detection"""
        # Prepare sequences
        sequence_length = 60
        X, y = self._create_sequences(data, sequence_length, labels)
        
        # Scale data
        X_scaled = self.scaler.fit_transform(X.reshape(-1, X.shape[-1]))
        X_scaled = X_scaled.reshape(X.shape)
        
        # Build LSTM model
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(sequence_length, X.shape[-1])),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Train
        self.model.fit(
            X_scaled, y,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )
        
    def _create_sequences(self, data, seq_length, labels=None):
        """Create sequences for LSTM"""
        X, y = [], []
        for i in range(len(data) - seq_length):
            X.append(data[i:i+seq_length])
            if labels is not None:
                y.append(labels[i+seq_length])
            else:
                y.append(0)  # Default to normal
        return np.array(X), np.array(y)
        
    def predict(self, data):
        """Predict anomalies"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
            
        if self.algorithm == 'z_score':
            return self._predict_zscore(data)
        elif self.algorithm == 'isolation_forest':
            return self._predict_isolation_forest(data)
        elif self.algorithm == 'prophet':
            return self._predict_prophet(data)
        elif self.algorithm == 'lstm':
            return self._predict_lstm(data)
            
    def _predict_zscore(self, data):
        """Z-score prediction"""
        z_scores = np.abs((data - self.mean) / self.std)
        anomalies = np.any(z_scores > self.threshold, axis=1)
        return anomalies.astype(int)
        
    def _predict_isolation_forest(self, data):
        """Isolation Forest prediction"""
        scaled_data = self.scaler.transform(data)
        predictions = self.model.predict(scaled_data)
        # Convert -1 (anomaly) to 1, 1 (normal) to 0
        return (predictions == -1).astype(int)
        
    def _predict_prophet(self, data):
        """Prophet prediction"""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
            
        if 'ds' not in df.columns:
            df['ds'] = pd.date_range(start='2024-01-01', periods=len(df), freq='H')
            
        forecast = self.model.predict(df[['ds']])
        
        # Detect anomalies based on forecast vs actual
        if 'y' in df.columns:
            residuals = np.abs(df['y'] - forecast['yhat'])
            threshold = residuals.quantile(0.95)
            anomalies = (residuals > threshold).astype(int)
        else:
            anomalies = np.zeros(len(df))
            
        return anomalies
        
    def _predict_lstm(self, data):
        """LSTM prediction"""
        sequence_length = 60
        if len(data) < sequence_length:
            # Pad with zeros
            padding = np.zeros((sequence_length - len(data), data.shape[1]))
            data = np.vstack([padding, data])
            
        X = []
        for i in range(len(data) - sequence_length + 1):
            X.append(data[i:i+sequence_length])
        X = np.array(X)
        
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1]))
        X_scaled = X_scaled.reshape(X.shape)
        
        predictions = self.model.predict(X_scaled)
        # Threshold at 0.5
        anomalies = (predictions > 0.5).astype(int).flatten()
        
        return anomalies
        
    def save(self, path):
        """Save model to disk"""
        model_dir = Path(path)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        if self.algorithm == 'lstm':
            self.model.save(str(model_dir / 'model.h5'))
        else:
            joblib.dump(self.model, str(model_dir / 'model.pkl'))
            
        joblib.dump(self.scaler, str(model_dir / 'scaler.pkl'))
        
        metadata = {
            'algorithm': self.algorithm,
            'trained_at': datetime.now().isoformat(),
            'is_trained': self.is_trained
        }
        
        if hasattr(self, 'mean'):
            metadata['mean'] = self.mean.tolist()
        if hasattr(self, 'std'):
            metadata['std'] = self.std.tolist()
        if hasattr(self, 'threshold'):
            metadata['threshold'] = self.threshold
            
        with open(model_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Model saved to {path}")
        
    @classmethod
    def load(cls, path):
        """Load model from disk"""
        model_dir = Path(path)
        metadata_path = model_dir / 'metadata.json'
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        detector = cls(algorithm=metadata['algorithm'])
        detector.is_trained = metadata['is_trained']
        
        if metadata['algorithm'] == 'lstm':
            detector.model = tf.keras.models.load_model(str(model_dir / 'model.h5'))
        else:
            detector.model = joblib.load(str(model_dir / 'model.pkl'))
            
        detector.scaler = joblib.load(str(model_dir / 'scaler.pkl'))
        
        if 'mean' in metadata:
            detector.mean = np.array(metadata['mean'])
        if 'std' in metadata:
            detector.std = np.array(metadata['std'])
        if 'threshold' in metadata:
            detector.threshold = metadata['threshold']
            
        logger.info(f"Model loaded from {path}")
        return detector


def train_models(data_path, output_dir='models'):
    """Train all anomaly detection models"""
    logger.info(f"Loading data from {data_path}")
    
    # Load data (assuming CSV format)
    df = pd.read_csv(data_path)
    
    # Prepare features (exclude timestamp if present)
    feature_cols = [col for col in df.columns if col not in ['timestamp', 'label', 'anomaly']]
    X = df[feature_cols].values
    
    # Get labels if available
    labels = df['label'].values if 'label' in df.columns else None
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Train each algorithm
    algorithms = ['z_score', 'isolation_forest', 'prophet', 'lstm']
    
    for algo in algorithms:
        logger.info(f"Training {algo}...")
        detector = AnomalyDetector(algorithm=algo)
        
        try:
            detector.train(X, labels)
            detector.save(str(output_path / algo))
            
            # Evaluate
            predictions = detector.predict(X[:1000])  # Sample prediction
            logger.info(f"{algo} - Anomalies detected: {predictions.sum()}/{len(predictions)}")
            
        except Exception as e:
            logger.error(f"Error training {algo}: {e}")
            
    logger.info("All models trained successfully")


def simulate_data(output_path='data/simulated_metrics.csv', num_samples=10000):
    """Generate synthetic metrics data for local testing"""
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta
    
    logger.info(f"Generating {num_samples} synthetic data points...")
    
    # Generate timestamps
    start_time = datetime.now() - timedelta(days=7)
    timestamps = [start_time + timedelta(seconds=i*60) for i in range(num_samples)]
    
    # Generate normal metrics with some anomalies
    np.random.seed(42)
    
    # CPU usage (normal: 20-60%, anomalies: >80%)
    cpu_normal = np.random.normal(40, 15, num_samples)
    cpu_normal = np.clip(cpu_normal, 0, 100)
    # Inject anomalies (5% of data)
    anomaly_indices = np.random.choice(num_samples, size=int(num_samples * 0.05), replace=False)
    cpu_normal[anomaly_indices] = np.random.uniform(85, 100, len(anomaly_indices))
    
    # Memory usage (normal: 30-70%, anomalies: >90%)
    memory_normal = np.random.normal(50, 20, num_samples)
    memory_normal = np.clip(memory_normal, 0, 100)
    memory_normal[anomaly_indices] = np.random.uniform(90, 100, len(anomaly_indices))
    
    # Request latency (normal: 10-100ms, anomalies: >500ms)
    latency_normal = np.random.exponential(50, num_samples)
    latency_normal = np.clip(latency_normal, 5, 200)
    latency_normal[anomaly_indices] = np.random.uniform(500, 2000, len(anomaly_indices))
    
    # Error rate (normal: 0-2%, anomalies: >5%)
    error_rate = np.random.exponential(0.5, num_samples)
    error_rate = np.clip(error_rate, 0, 2)
    error_rate[anomaly_indices] = np.random.uniform(5, 15, len(anomaly_indices))
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'cpu_usage': cpu_normal,
        'memory_usage': memory_normal,
        'request_latency_ms': latency_normal,
        'error_rate_percent': error_rate,
        'anomaly': [1 if i in anomaly_indices else 0 for i in range(num_samples)]
    })
    
    # Save to CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"✅ Generated synthetic data: {output_path}")
    logger.info(f"   Total samples: {num_samples}")
    logger.info(f"   Anomalies: {len(anomaly_indices)} ({len(anomaly_indices)/num_samples*100:.1f}%)")
    
    return output_path


if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Train anomaly detection models')
    parser.add_argument('data_path', nargs='?', default='data/metrics.csv',
                       help='Path to training data CSV file')
    parser.add_argument('output_dir', nargs='?', default='models',
                       help='Output directory for trained models')
    parser.add_argument('--simulate', action='store_true',
                       help='Generate synthetic data for local testing (no AWS required)')
    
    args = parser.parse_args()
    
    if args.simulate:
        logger.info("🔬 Running in SIMULATION mode (local testing, no AWS required)")
        # Generate synthetic data
        data_path = simulate_data()
        # Train models on synthetic data
        train_models(str(data_path), args.output_dir)
        logger.info("✅ Simulation complete! Models trained on synthetic data.")
        logger.info("   Next: Test with real data or deploy to AWS")
    else:
        # Normal training mode
        train_models(args.data_path, args.output_dir)

