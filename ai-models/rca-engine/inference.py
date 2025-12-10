#!/usr/bin/env python3
"""
RCA Engine Inference Module
Real-time root cause analysis for incidents
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from rca_engine import RCAEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RCAInference:
    """Real-time RCA inference"""
    
    def __init__(self):
        self.rca_engine = RCAEngine()
        self.services_cache = {}
        self._load_services()
    
    def _load_services(self):
        """Load service definitions (would come from K8s or config)"""
        # Simplified - in production, load from K8s API or config
        default_services = [
            {
                'name': 'payment-service',
                'namespace': 'finance',
                'dependencies': ['database', 'redis']
            },
            {
                'name': 'emr-api',
                'namespace': 'healthcare',
                'dependencies': ['database']
            }
        ]
        
        self.rca_engine.build_dependency_graph(default_services)
        logger.info("RCA engine initialized with default services")
    
    def analyze_incident(self, incident_data: Dict) -> Dict:
        """
        Analyze an incident and return root cause
        
        Args:
            incident_data: Dict with incident information
                {
                    'namespace': str,
                    'service': str,
                    'anomalies': List[Dict],
                    'logs': List[Dict],
                    'events': List[Dict],
                    'metrics': Dict
                }
        
        Returns:
            Dict with root cause analysis
        """
        try:
            # Extract data
            namespace = incident_data.get('namespace', 'default')
            service = incident_data.get('service', 'unknown')
            anomalies = incident_data.get('anomalies', [])
            logs = incident_data.get('logs', [])
            events = incident_data.get('events', [])
            metrics = incident_data.get('metrics', {})
            
            # Convert to DataFrames for RCA engine
            logs_df = self._logs_to_dataframe(logs)
            metrics_df = self._metrics_to_dataframe(metrics)
            events_df = self._events_to_dataframe(events)
            
            # Run RCA
            root_causes = self.rca_engine.correlate_events(
                logs_df, metrics_df, events_df
            )
            
            # Get best root cause
            if root_causes:
                best_rc = max(root_causes, key=lambda x: x.get('confidence', 0.0))
                return {
                    'root_cause': best_rc.get('root_cause', 'unknown'),
                    'confidence': best_rc.get('confidence', 0.0),
                    'severity': best_rc.get('severity', 'medium'),
                    'recommendation': best_rc.get('recommendation', ''),
                    'affected_service': best_rc.get('affected_service', service),
                    'upstream_services': best_rc.get('upstream_services', []),
                    'related_anomalies': best_rc.get('related_anomalies', []),
                    'related_errors': best_rc.get('related_errors', []),
                    'all_root_causes': root_causes
                }
            else:
                # Fallback analysis
                return self._fallback_rca(incident_data)
                
        except Exception as e:
            logger.error(f"Error in RCA analysis: {e}")
            return self._fallback_rca(incident_data)
    
    def _logs_to_dataframe(self, logs: List[Dict]) -> pd.DataFrame:
        """Convert logs to DataFrame"""
        if not logs:
            return pd.DataFrame(columns=['timestamp', 'level', 'message', 'service'])
        
        df = pd.DataFrame(logs)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def _metrics_to_dataframe(self, metrics: Dict) -> pd.DataFrame:
        """Convert metrics to DataFrame"""
        if not metrics:
            return pd.DataFrame(columns=['timestamp'])
        
        # Create time series from metrics - format expected by RCA engine
        # RCA engine expects columns to be metric names, not 'metric' and 'value'
        from datetime import timezone
        timestamp = datetime.now(timezone.utc)
        
        # Create a single row with all metrics as columns
        data = {'timestamp': timestamp}
        for metric_name, value in metrics.items():
            # Ensure numeric values
            try:
                data[metric_name] = float(value) if value is not None else 0.0
            except (ValueError, TypeError):
                data[metric_name] = 0.0
        
        return pd.DataFrame([data])
    
    def _events_to_dataframe(self, events: List[Dict]) -> pd.DataFrame:
        """Convert events to DataFrame"""
        if not events:
            return pd.DataFrame(columns=['timestamp', 'type', 'object', 'reason', 'severity'])
        
        df = pd.DataFrame(events)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def _fallback_rca(self, incident_data: Dict) -> Dict:
        """Fallback RCA when engine fails"""
        namespace = incident_data.get('namespace', 'default')
        service = incident_data.get('service', 'unknown')
        anomalies = incident_data.get('anomalies', [])
        
        # Simple heuristic-based RCA
        if anomalies:
            # Find most severe anomaly
            worst_anomaly = max(anomalies, key=lambda x: x.get('severity', 0.0))
            
            root_cause = worst_anomaly.get('metric', 'unknown')
            if 'cpu' in root_cause.lower():
                root_cause = 'CPU saturation'
            elif 'memory' in root_cause.lower():
                root_cause = 'Memory pressure'
            elif 'error' in root_cause.lower():
                root_cause = 'Error rate spike'
            else:
                root_cause = f"{root_cause} anomaly"
            
            return {
                'root_cause': root_cause,
                'confidence': 0.6,
                'severity': worst_anomaly.get('severity', 'medium'),
                'recommendation': f"Investigate {root_cause} in {service}",
                'affected_service': service,
                'upstream_services': [],
                'related_anomalies': [worst_anomaly],
                'related_errors': []
            }
        
        return {
            'root_cause': 'unknown',
            'confidence': 0.3,
            'severity': 'low',
            'recommendation': 'Manual investigation required',
            'affected_service': service,
            'upstream_services': [],
            'related_anomalies': [],
            'related_errors': []
        }
    
    def update_services(self, services: List[Dict]):
        """Update service dependency graph"""
        self.rca_engine.build_dependency_graph(services)
        logger.info(f"Updated dependency graph with {len(services)} services")


def load_rca_engine() -> RCAInference:
    """Convenience function to load RCA engine"""
    return RCAInference()


if __name__ == '__main__':
    # Test RCA
    rca = load_rca_engine()
    
    test_incident = {
        'namespace': 'finance',
        'service': 'payment-service',
        'anomalies': [
            {'metric': 'cpu_usage', 'value': 95.0, 'severity': 0.9}
        ],
        'logs': [],
        'events': [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'Warning',
                'object': 'pod/payment-service-123',
                'reason': 'Unhealthy',
                'severity': 'high'
            }
        ],
        'metrics': {
            'cpu_usage': 95.0,
            'memory_usage': 80.0
        }
    }
    
    result = rca.analyze_incident(test_incident)
    print(json.dumps(result, indent=2, default=str))

