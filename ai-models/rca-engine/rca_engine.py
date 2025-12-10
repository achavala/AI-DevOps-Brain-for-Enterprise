"""
Root Cause Analysis (RCA) Engine
Correlates logs, events, and metrics to identify root causes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import networkx as nx
from typing import List, Dict, Tuple, Optional
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RCAEngine:
    """Root Cause Analysis Engine"""
    
    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.event_correlations = defaultdict(list)
        self.temporal_window = timedelta(minutes=5)
        
    def build_dependency_graph(self, services: List[Dict]):
        """Build service dependency graph"""
        logger.info("Building dependency graph...")
        
        for service in services:
            service_name = service['name']
            self.dependency_graph.add_node(service_name, **service)
            
            # Add dependencies
            for dep in service.get('dependencies', []):
                self.dependency_graph.add_edge(dep, service_name)
                
        logger.info(f"Dependency graph built: {len(self.dependency_graph.nodes)} nodes, "
                   f"{len(self.dependency_graph.edges)} edges")
        
    def correlate_events(self, logs: pd.DataFrame, metrics: pd.DataFrame, 
                        events: pd.DataFrame) -> List[Dict]:
        """Correlate logs, metrics, and events to find root causes"""
        logger.info("Correlating events...")
        
        # Merge dataframes on timestamp
        logs['timestamp'] = pd.to_datetime(logs['timestamp'])
        metrics['timestamp'] = pd.to_datetime(metrics['timestamp'])
        events['timestamp'] = pd.to_datetime(events['timestamp'])
        
        # Find anomalies in metrics
        metric_anomalies = self._detect_metric_anomalies(metrics)
        
        # Find errors in logs
        log_errors = self._extract_log_errors(logs)
        
        # Find critical events
        critical_events = self._find_critical_events(events)
        
        # Correlate within temporal window
        root_causes = []
        
        for event in critical_events:
            event_time = event['timestamp']
            window_start = event_time - self.temporal_window
            window_end = event_time + self.temporal_window
            
            # Find related anomalies
            related_anomalies = [
                a for a in metric_anomalies
                if window_start <= a['timestamp'] <= window_end
            ]
            
            # Find related log errors
            related_errors = [
                e for e in log_errors
                if window_start <= e['timestamp'] <= window_end
            ]
            
            # Build correlation
            if related_anomalies or related_errors:
                root_cause = self._build_root_cause(
                    event, related_anomalies, related_errors
                )
                root_causes.append(root_cause)
        
        # Rank by severity and confidence
        root_causes = sorted(root_causes, 
                           key=lambda x: (x['severity'], x['confidence']), 
                           reverse=True)
        
        logger.info(f"Found {len(root_causes)} potential root causes")
        return root_causes
    
    def _detect_metric_anomalies(self, metrics: pd.DataFrame) -> List[Dict]:
        """Detect anomalies in metrics"""
        anomalies = []
        
        if metrics.empty:
            return anomalies
        
        for metric_name in metrics.columns:
            if metric_name == 'timestamp':
                continue
            
            try:
                values = pd.to_numeric(metrics[metric_name], errors='coerce').values
                # Filter out NaN values
                values = values[~np.isnan(values)]
                
                if len(values) == 0:
                    continue
                
                mean = np.mean(values)
                std = np.std(values)
                
                # Avoid division by zero
                if std == 0:
                    continue
                
                threshold = mean + 3 * std
            
                anomaly_indices = np.where(values > threshold)[0]
                
                for idx in anomaly_indices:
                    # Get timestamp safely
                    timestamp = metrics.iloc[idx]['timestamp'] if 'timestamp' in metrics.columns else datetime.now()
                    anomalies.append({
                        'timestamp': timestamp,
                        'metric': metric_name,
                        'value': float(values[idx]),
                        'threshold': float(threshold),
                        'severity': 'high' if values[idx] > mean + 5 * std else 'medium'
                    })
            except Exception as e:
                logger.warning(f"Error processing metric {metric_name}: {e}")
                continue
        
        return anomalies
    
    def _extract_log_errors(self, logs: pd.DataFrame) -> List[Dict]:
        """Extract error patterns from logs"""
        errors = []
        
        error_keywords = ['error', 'exception', 'failed', 'timeout', 'crash', 
                         'panic', 'fatal', 'critical']
        
        for idx, row in logs.iterrows():
            log_message = str(row.get('message', '')).lower()
            
            for keyword in error_keywords:
                if keyword in log_message:
                    errors.append({
                        'timestamp': row['timestamp'],
                        'service': row.get('service', 'unknown'),
                        'message': row.get('message', ''),
                        'level': row.get('level', 'error'),
                        'severity': self._classify_error_severity(log_message)
                    })
                    break
        
        return errors
    
    def _classify_error_severity(self, message: str) -> str:
        """Classify error severity"""
        critical_keywords = ['fatal', 'panic', 'crash', 'out of memory']
        high_keywords = ['timeout', 'connection refused', 'database error']
        
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in critical_keywords):
            return 'critical'
        elif any(kw in message_lower for kw in high_keywords):
            return 'high'
        else:
            return 'medium'
    
    def _find_critical_events(self, events: pd.DataFrame) -> List[Dict]:
        """Find critical Kubernetes events"""
        critical_events = []
        
        critical_types = ['PodCrashLoopBackOff', 'PodEvicted', 'NodeNotReady',
                         'FailedScheduling', 'ImagePullBackOff']
        
        for idx, row in events.iterrows():
            event_type = row.get('type', '')
            reason = row.get('reason', '')
            
            if event_type == 'Warning' or reason in critical_types:
                critical_events.append({
                    'timestamp': row['timestamp'],
                    'type': event_type,
                    'reason': reason,
                    'object': row.get('object', ''),
                    'message': row.get('message', ''),
                    'severity': 'critical' if reason in critical_types else 'high'
                })
        
        return critical_events
    
    def _build_root_cause(self, event: Dict, anomalies: List[Dict], 
                         errors: List[Dict]) -> Dict:
        """Build root cause analysis"""
        
        # Trace dependency chain
        affected_service = event.get('object', '').split('/')[-1] if '/' in event.get('object', '') else 'unknown'
        
        # Find upstream dependencies
        upstream_services = []
        if affected_service in self.dependency_graph:
            upstream_services = list(self.dependency_graph.predecessors(affected_service))
        
        # Calculate confidence based on evidence
        evidence_count = len(anomalies) + len(errors)
        confidence = min(0.9, 0.3 + (evidence_count * 0.1))
        
        # Determine root cause
        root_cause_service = affected_service
        if upstream_services:
            # Check if upstream services have errors
            upstream_errors = [e for e in errors if e.get('service') in upstream_services]
            if upstream_errors:
                root_cause_service = upstream_errors[0]['service']
                confidence += 0.2
        
        return {
            'root_cause': root_cause_service,
            'affected_service': affected_service,
            'event': event,
            'related_anomalies': anomalies,
            'related_errors': errors,
            'upstream_services': upstream_services,
            'confidence': min(1.0, confidence),
            'severity': event.get('severity', 'high'),
            'timestamp': event['timestamp'],
            'recommendation': self._generate_recommendation(event, anomalies, errors)
        }
    
    def _generate_recommendation(self, event: Dict, anomalies: List[Dict], 
                                 errors: List[Dict]) -> str:
        """Generate fix recommendation"""
        reason = event.get('reason', '')
        
        if 'CrashLoopBackOff' in reason:
            return "Check pod logs for startup errors. Verify resource limits and environment variables."
        elif 'Evicted' in reason:
            return "Pod was evicted due to resource pressure. Check node capacity and resource requests."
        elif 'NotReady' in reason:
            return "Node is not ready. Check kubelet status and node conditions."
        elif 'FailedScheduling' in reason:
            return "Pod cannot be scheduled. Check resource availability and node selectors."
        elif anomalies:
            return f"Metric anomaly detected: {anomalies[0]['metric']}. Check service health and resource usage."
        elif errors:
            return f"Error in logs: {errors[0]['message'][:100]}. Review application code and dependencies."
        else:
            return "Investigate service health and dependencies."
    
    def get_root_cause_chain(self, service: str) -> List[str]:
        """Get the dependency chain leading to a service"""
        if service not in self.dependency_graph:
            return []
        
        # Get all ancestors (upstream dependencies)
        ancestors = list(nx.ancestors(self.dependency_graph, service))
        
        # Sort by dependency depth
        depths = {}
        for ancestor in ancestors:
            try:
                depth = nx.shortest_path_length(self.dependency_graph, ancestor, service)
                depths[ancestor] = depth
            except nx.NetworkXNoPath:
                continue
        
        sorted_ancestors = sorted(depths.items(), key=lambda x: x[1])
        return [ancestor for ancestor, _ in sorted_ancestors]
    
    def save_graph(self, path: str):
        """Save dependency graph"""
        nx.write_gml(self.dependency_graph, path)
        logger.info(f"Dependency graph saved to {path}")
    
    def load_graph(self, path: str):
        """Load dependency graph"""
        self.dependency_graph = nx.read_gml(path)
        logger.info(f"Dependency graph loaded from {path}")


def analyze_incident(logs_path: str, metrics_path: str, events_path: str,
                     services_path: str) -> List[Dict]:
    """Analyze an incident and return root causes"""
    
    # Load data
    logs = pd.read_csv(logs_path)
    metrics = pd.read_csv(metrics_path)
    events = pd.read_csv(events_path)
    
    with open(services_path, 'r') as f:
        services = json.load(f)
    
    # Build RCA engine
    rca = RCAEngine()
    rca.build_dependency_graph(services)
    
    # Correlate events
    root_causes = rca.correlate_events(logs, metrics, events)
    
    return root_causes


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python rca_engine.py <logs.csv> <metrics.csv> <events.csv> <services.json>")
        sys.exit(1)
    
    root_causes = analyze_incident(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    
    print(f"\nFound {len(root_causes)} root causes:\n")
    for i, rc in enumerate(root_causes, 1):
        print(f"{i}. Root Cause: {rc['root_cause']}")
        print(f"   Confidence: {rc['confidence']:.2%}")
        print(f"   Severity: {rc['severity']}")
        print(f"   Recommendation: {rc['recommendation']}")
        print()

