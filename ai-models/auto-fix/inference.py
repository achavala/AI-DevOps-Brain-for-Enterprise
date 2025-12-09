#!/usr/bin/env python3
"""
Auto-Fix Engine Inference Module
Real-time fix generation for incidents
"""

import os
import json
from typing import Dict, List, Optional
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from auto_fix_engine import AutoFixEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoFixInference:
    """Real-time auto-fix inference"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.fix_engine = AutoFixEngine(kubeconfig_path=kubeconfig_path)
        logger.info("Auto-fix engine initialized")
    
    def generate_fix(self, incident: Dict) -> Dict:
        """
        Generate fix for an incident
        
        Args:
            incident: Dict with incident information
                {
                    'id': str,
                    'namespace': str,
                    'service': str,
                    'anomaly_type': str,
                    'root_cause': str,
                    'suspected_root_cause': Dict,
                    'metrics': Dict,
                    'logs': List[Dict]
                }
        
        Returns:
            Dict with fix information
        """
        try:
            # Map incident to auto-fix issue format
            issue = self._incident_to_issue(incident)
            
            # Generate fix
            fix = self.fix_engine.generate_fix(issue)
            
            # Validate fix
            is_valid, message = self.fix_engine.validate_fix(fix)
            
            return {
                'success': is_valid,
                'fix': fix,
                'message': message,
                'confidence': self._calculate_fix_confidence(incident, fix),
                'risk_score': self._calculate_fix_risk(incident, fix),
                'recommended_action': self._get_recommended_action(fix)
            }
            
        except Exception as e:
            logger.error(f"Error generating fix: {e}")
            return {
                'success': False,
                'fix': None,
                'message': f"Error: {str(e)}",
                'confidence': 0.0,
                'risk_score': 1.0,
                'recommended_action': 'manual_review'
            }
    
    def _incident_to_issue(self, incident: Dict) -> Dict:
        """Convert incident to auto-fix issue format"""
        anomaly_type = incident.get('anomaly_type', 'unknown')
        namespace = incident.get('namespace', 'default')
        service = incident.get('service', 'unknown')
        
        # Map anomaly types to fix engine issue types
        issue_type_map = {
            'pod_failure': 'pod_crashloop',
            'excessive_restarts': 'pod_crashloop',
            'resource_limits': 'resource_limits',
            'image_pull_error': 'image_pull_error',
            'node_pressure': 'node_pressure',
            'high_cpu': 'resource_limits',
            'high_memory': 'resource_limits'
        }
        
        issue_type = issue_type_map.get(anomaly_type, 'unknown')
        
        # Build root cause dict
        root_cause = {
            'service': service,
            'namespace': namespace,
            'error': incident.get('root_cause', 'unknown')
        }
        
        # Add suspected root cause details
        suspected_rc = incident.get('suspected_root_cause', {})
        if suspected_rc:
            root_cause.update(suspected_rc)
        
        issue = {
            'type': issue_type,
            'namespace': namespace,
            'pod_name': service,
            'root_cause': root_cause
        }
        
        # Add metrics if available
        metrics = incident.get('metrics', {})
        if metrics:
            issue['current_cpu'] = metrics.get('cpu_usage', 0)
            issue['current_memory'] = metrics.get('memory_usage', 0)
            issue['metrics'] = metrics
        
        return issue
    
    def _calculate_fix_confidence(self, incident: Dict, fix: Dict) -> float:
        """Calculate confidence in the fix"""
        # Base confidence from incident
        incident_confidence = incident.get('confidence', 0.5)
        
        # Adjust based on fix type
        fix_type = fix.get('type', 'unknown')
        fix_confidence_map = {
            'scale_up': 0.8,
            'scale_down': 0.7,
            'restart': 0.6,
            'update_resource_limits': 0.75,
            'rollback': 0.9,
            'unknown': 0.5
        }
        
        fix_confidence = fix_confidence_map.get(fix_type, 0.5)
        
        # Combined confidence (weighted average)
        return (incident_confidence * 0.6) + (fix_confidence * 0.4)
    
    def _calculate_fix_risk(self, incident: Dict, fix: Dict) -> float:
        """Calculate risk score for the fix"""
        # Base risk from incident
        incident_risk = incident.get('risk_score', 0.5)
        
        # Adjust based on fix type
        fix_type = fix.get('type', 'unknown')
        fix_risk_map = {
            'scale_up': 0.2,
            'scale_down': 0.3,
            'restart': 0.4,
            'update_resource_limits': 0.5,
            'rollback': 0.1,
            'unknown': 0.7
        }
        
        fix_risk = fix_risk_map.get(fix_type, 0.5)
        
        # Namespace-based risk adjustment
        namespace = incident.get('namespace', 'default')
        high_risk_namespaces = ['finance', 'healthcare', 'banking']
        if namespace in high_risk_namespaces:
            fix_risk += 0.2
        
        # Combined risk (weighted average)
        return min(1.0, (incident_risk * 0.5) + (fix_risk * 0.5))
    
    def _get_recommended_action(self, fix: Dict) -> str:
        """Get recommended action based on fix"""
        fix_type = fix.get('type', 'unknown')
        
        action_map = {
            'scale_up': 'auto_apply',
            'scale_down': 'auto_apply',
            'restart': 'require_approval',
            'update_resource_limits': 'require_approval',
            'rollback': 'auto_apply',
            'unknown': 'manual_review'
        }
        
        return action_map.get(fix_type, 'manual_review')
    
    def apply_fix(self, fix: Dict, dry_run: bool = True) -> Dict:
        """Apply fix (with dry-run support)"""
        try:
            result = self.fix_engine.apply_fix(fix, dry_run=dry_run)
            return result
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }


def load_auto_fix_engine(kubeconfig_path: Optional[str] = None) -> AutoFixInference:
    """Convenience function to load auto-fix engine"""
    return AutoFixInference(kubeconfig_path=kubeconfig_path)


if __name__ == '__main__':
    # Test auto-fix
    auto_fix = load_auto_fix_engine()
    
    test_incident = {
        'id': 'test-123',
        'namespace': 'finance',
        'service': 'payment-service',
        'anomaly_type': 'pod_failure',
        'root_cause': 'out of memory',
        'confidence': 0.85,
        'risk_score': 0.3,
        'suspected_root_cause': {
            'type': 'resource',
            'name': 'memory',
            'confidence': 0.85
        },
        'metrics': {
            'cpu_usage': 50.0,
            'memory_usage': 95.0
        },
        'logs': []
    }
    
    result = auto_fix.generate_fix(test_incident)
    print(json.dumps(result, indent=2, default=str))

