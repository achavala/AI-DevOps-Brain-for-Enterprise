#!/usr/bin/env python3
"""
Anomaly Detection Inference Module
Loads trained models and performs real-time anomaly detection
"""

import os
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import json

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from train_anomaly_detector import AnomalyDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetectionInference:
    """Real-time anomaly detection inference"""
    
    def __init__(self, model_dir: str = "ai-models/models", algorithm: str = "isolation_forest"):
        self.model_dir = Path(model_dir)
        self.algorithm = algorithm
        self.detector = None
        self.model_path = self.model_dir / algorithm
        self._load_model()
    
    def _load_model(self):
        """Load trained model"""
        try:
            metadata_path = self.model_path / "metadata.json"
            if not metadata_path.exists():
                logger.warning(f"Model not found at {self.model_path}, using default detector")
                self.detector = AnomalyDetector(algorithm=self.algorithm)
                return
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Load detector
            self.detector = AnomalyDetector(algorithm=self.algorithm)
            
            if self.algorithm == 'z_score':
                self.detector.mean = np.array(metadata.get('mean', []))
                self.detector.std = np.array(metadata.get('std', []))
                self.detector.threshold = metadata.get('threshold', 3.0)
                self.detector.is_trained = True
            
            elif self.algorithm == 'isolation_forest':
                model_path = self.model_path / "model.pkl"
                scaler_path = self.model_path / "scaler.pkl"
                
                if model_path.exists() and scaler_path.exists():
                    self.detector.model = joblib.load(model_path)
                    self.detector.scaler = joblib.load(scaler_path)
                    self.detector.is_trained = True
                else:
                    logger.warning(f"Model files not found, using default")
            
            elif self.algorithm == 'prophet':
                model_path = self.model_path / "model.pkl"
                if model_path.exists():
                    self.detector.model = joblib.load(model_path)
                    self.detector.is_trained = True
            
            elif self.algorithm == 'lstm':
                try:
                    import tensorflow as tf
                    model_path = self.model_path / "model.h5"
                    scaler_path = self.model_path / "scaler.pkl"
                    
                    if model_path.exists() and scaler_path.exists():
                        self.detector.model = tf.keras.models.load_model(model_path)
                        self.detector.scaler = joblib.load(scaler_path)
                        self.detector.is_trained = True
                except ImportError:
                    logger.warning("TensorFlow not available, LSTM model cannot be loaded")
            
            logger.info(f"Loaded {self.algorithm} model from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            # Fallback to default detector
            self.detector = AnomalyDetector(algorithm=self.algorithm)
    
    def detect(self, metrics: Dict, window_size: int = 60) -> Dict:
        """
        Detect anomalies in real-time metrics
        
        Args:
            metrics: Dict with metric names and values
                Example: {'cpu_usage': 85.0, 'memory_usage': 90.0, 'error_rate': 2.5}
            window_size: Number of historical points to consider (for time-series models)
        
        Returns:
            Dict with anomaly detection results
        """
        if not self.detector or not self.detector.is_trained:
            logger.warning("Model not trained, using threshold-based detection")
            return self._threshold_based_detection(metrics)
        
        try:
            # Convert metrics to feature vector
            feature_vector = self._metrics_to_features(metrics)
            
            if self.algorithm == 'z_score':
                result = self._detect_zscore(feature_vector)
            elif self.algorithm == 'isolation_forest':
                result = self._detect_isolation_forest(feature_vector)
            elif self.algorithm == 'prophet':
                result = self._detect_prophet(metrics)
            elif self.algorithm == 'lstm':
                result = self._detect_lstm(feature_vector, window_size)
            else:
                result = self._threshold_based_detection(metrics)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return self._threshold_based_detection(metrics)
    
    def _metrics_to_features(self, metrics: Dict) -> np.ndarray:
        """Convert metrics dict to feature vector"""
        # Standard features - match training data format
        # Training uses: cpu_usage, memory_usage, request_latency_ms, error_rate_percent
        # But we'll map common metric names to these
        feature_order = [
            'cpu_usage', 'memory_usage', 'error_rate', 
            'latency_p95', 'latency_p99', 'request_rate',
            'pod_restarts', 'network_errors'
        ]
        
        features = []
        for feat in feature_order:
            # Map common metric names
            if feat == 'error_rate':
                value = metrics.get('error_rate', metrics.get('error_rate_percent', 0.0))
            elif feat == 'latency_p95':
                value = metrics.get('latency_p95', metrics.get('request_latency_ms', 0.0))
            elif feat == 'latency_p99':
                value = metrics.get('latency_p99', metrics.get('request_latency_ms', 0.0))
            else:
                value = metrics.get(feat, 0.0)
            features.append(float(value))
        
        feature_array = np.array(features).reshape(1, -1)
        
        # If scaler expects fewer features, use only the first N
        if hasattr(self.detector, 'scaler') and self.detector.scaler is not None:
            expected_features = self.detector.scaler.n_features_in_ if hasattr(self.detector.scaler, 'n_features_in_') else None
            if expected_features and feature_array.shape[1] != expected_features:
                # Use only the first N features that match training
                if expected_features <= feature_array.shape[1]:
                    feature_array = feature_array[:, :expected_features]
                else:
                    # Pad with zeros if we have fewer features
                    padding = np.zeros((1, expected_features - feature_array.shape[1]))
                    feature_array = np.hstack([feature_array, padding])
        
        return feature_array
    
    def _detect_zscore(self, features: np.ndarray) -> Dict:
        """Z-score based detection"""
        z_scores = np.abs((features - self.detector.mean) / (self.detector.std + 1e-8))
        max_z_score = np.max(z_scores)
        is_anomaly = max_z_score > self.detector.threshold
        
        return {
            'is_anomaly': bool(is_anomaly),
            'anomaly_score': float(max_z_score / self.detector.threshold),
            'confidence': min(1.0, max_z_score / (self.detector.threshold * 2)),
            'method': 'z_score',
            'max_z_score': float(max_z_score)
        }
    
    def _detect_isolation_forest(self, features: np.ndarray) -> Dict:
        """Isolation Forest detection"""
        try:
            # Ensure feature count matches scaler
            if hasattr(self.detector, 'scaler') and self.detector.scaler is not None:
                expected_features = self.detector.scaler.n_features_in_ if hasattr(self.detector.scaler, 'n_features_in_') else features.shape[1]
                if features.shape[1] != expected_features:
                    if features.shape[1] > expected_features:
                        features = features[:, :expected_features]
                    else:
                        padding = np.zeros((1, expected_features - features.shape[1]))
                        features = np.hstack([features, padding])
            
            scaled_features = self.detector.scaler.transform(features)
            anomaly_score = self.detector.model.decision_function(scaled_features)[0]
            prediction = self.detector.model.predict(scaled_features)[0]
            
            # Isolation Forest: -1 = anomaly, 1 = normal
            is_anomaly = prediction == -1
            
            # Convert score to 0-1 range (higher = more anomalous)
            # decision_function returns negative for anomalies
            normalized_score = (1.0 - (anomaly_score + 0.5)) if is_anomaly else 0.0
            
            return {
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(normalized_score),
                'confidence': float(abs(anomaly_score)),
                'method': 'isolation_forest',
                'raw_score': float(anomaly_score)
            }
        except Exception as e:
            logger.error(f"Error in isolation forest detection: {e}")
            # Fallback to threshold-based
            return self._threshold_based_detection({})
    
    def _detect_prophet(self, metrics: Dict) -> Dict:
        """Prophet time-series detection"""
        # Simplified - would use historical data
        # For now, use threshold-based
        return self._threshold_based_detection(metrics)
    
    def _detect_lstm(self, features: np.ndarray, window_size: int) -> Dict:
        """LSTM-based detection"""
        # Would need historical window
        # For now, use threshold-based
        return self._threshold_based_detection(features.flatten().tolist())
    
    def _threshold_based_detection(self, metrics: Dict) -> Dict:
        """Fallback threshold-based detection"""
        thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'error_rate': 5.0,
            'latency_p95': 1000.0,
            'pod_restarts': 3
        }
        
        anomalies = []
        max_severity = 0.0
        
        for metric, value in metrics.items():
            if isinstance(value, (int, float)):
                threshold = thresholds.get(metric, float('inf'))
                if value > threshold:
                    severity = min(1.0, value / (threshold * 1.5))
                    anomalies.append({
                        'metric': metric,
                        'value': value,
                        'threshold': threshold,
                        'severity': severity
                    })
                    max_severity = max(max_severity, severity)
        
        return {
            'is_anomaly': len(anomalies) > 0,
            'anomaly_score': max_severity,
            'confidence': max_severity,
            'method': 'threshold',
            'anomalies': anomalies
        }
    
    def batch_detect(self, metrics_list: List[Dict]) -> List[Dict]:
        """Detect anomalies for a batch of metrics"""
        return [self.detect(metrics) for metrics in metrics_list]


def load_detector(algorithm: str = "isolation_forest", model_dir: str = "ai-models/models") -> AnomalyDetectionInference:
    """Convenience function to load detector"""
    return AnomalyDetectionInference(model_dir=model_dir, algorithm=algorithm)


if __name__ == '__main__':
    # Test inference
    detector = load_detector()
    
    # Test metrics
    test_metrics = {
        'cpu_usage': 85.0,
        'memory_usage': 90.0,
        'error_rate': 2.5,
        'latency_p95': 500.0,
        'pod_restarts': 0
    }
    
    result = detector.detect(test_metrics)
    print(json.dumps(result, indent=2))

