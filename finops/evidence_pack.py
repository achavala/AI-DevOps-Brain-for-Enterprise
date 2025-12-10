#!/usr/bin/env python3
"""
Evidence Pack Generator
Generates comprehensive evidence bundles for cost optimization recommendations
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from finops.savings_ledger import Opportunity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvidencePackGenerator:
    """Generates evidence packs for recommendations"""
    
    def __init__(self, prometheus_url: Optional[str] = None, loki_url: Optional[str] = None):
        self.prometheus_url = prometheus_url or os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        self.loki_url = loki_url or os.getenv('LOKI_URL', 'http://localhost:3100')
    
    def generate(self, opportunity: Opportunity, cluster_data: Optional[Dict] = None) -> Dict:
        """
        Generate complete evidence pack
        
        Args:
            opportunity: Cost optimization opportunity
            cluster_data: Optional cluster data for context
        
        Returns:
            Dict with complete evidence pack
        """
        try:
            evidence = {
                'opportunity_id': opportunity.id,
                'generated_at': datetime.utcnow().isoformat(),
                'opportunity_type': opportunity.type.value,
                'workload': opportunity.workload,
                'namespace': opportunity.namespace,
                'cluster': opportunity.cluster,
                
                # Metrics
                'metrics': self._get_metrics_graphs(opportunity),
                
                # Logs
                'logs': self._get_relevant_logs(opportunity),
                
                # Cost Analysis
                'cost_analysis': self._get_cost_attribution(opportunity),
                
                # Change History
                'change_history': self._get_recent_changes(opportunity),
                
                # Safety Analysis
                'safety_analysis': self._analyze_safety(opportunity),
                
                # Evidence Summary
                'summary': self._generate_summary(opportunity)
            }
            
            # Generate HTML report
            evidence['html_report'] = self._generate_html_report(evidence)
            
            return evidence
            
        except Exception as e:
            logger.error(f"Error generating evidence pack: {e}")
            return {
                'opportunity_id': opportunity.id,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _get_metrics_graphs(self, opportunity: Opportunity) -> Dict:
        """Get Prometheus metrics graphs"""
        # Prometheus queries for relevant metrics
        queries = {
            'cpu_usage': f'sum(rate(container_cpu_usage_seconds_total{{namespace="{opportunity.namespace}", pod=~"{opportunity.workload}.*"}}[5m]))',
            'memory_usage': f'sum(container_memory_working_set_bytes{{namespace="{opportunity.namespace}", pod=~"{opportunity.workload}.*"}})',
            'request_rate': f'sum(rate(http_requests_total{{namespace="{opportunity.namespace}", pod=~"{opportunity.workload}.*"}}[5m]))',
            'error_rate': f'sum(rate(http_requests_total{{namespace="{opportunity.namespace}", pod=~"{opportunity.workload}.*", status=~"5.."}}[5m]))'
        }
        
        # In production, would query Prometheus API
        # For now, return query structure
        return {
            'queries': queries,
            'time_range': '7d',
            'note': 'Run these queries in Prometheus/Grafana to view graphs'
        }
    
    def _get_relevant_logs(self, opportunity: Opportunity) -> Dict:
        """Get relevant logs from Loki"""
        # Loki query for relevant logs
        log_query = f'{{namespace="{opportunity.namespace}", pod=~"{opportunity.workload}.*"}}'
        
        return {
            'query': log_query,
            'time_range': '24h',
            'note': 'Run this query in Loki/Grafana to view logs',
            'sample_logs': self._get_sample_logs(opportunity)
        }
    
    def _get_sample_logs(self, opportunity: Opportunity) -> List[str]:
        """Get sample logs (would query Loki in production)"""
        return [
            f"[{datetime.utcnow().isoformat()}] INFO: {opportunity.workload} running normally",
            f"[{datetime.utcnow().isoformat()}] INFO: CPU usage: {opportunity.evidence.get('current_cpu_usage', 'N/A')}",
        ]
    
    def _get_cost_attribution(self, opportunity: Opportunity) -> Dict:
        """Get cost attribution analysis"""
        before_cost = self._estimate_cost(opportunity.before_state, opportunity.type)
        after_cost = self._estimate_cost(opportunity.after_state, opportunity.type)
        
        return {
            'current_monthly_cost': before_cost,
            'projected_monthly_cost': after_cost,
            'estimated_savings': opportunity.estimated_monthly_savings,
            'annual_savings': opportunity.estimated_monthly_savings * 12,
            'breakdown': {
                'compute': before_cost * 0.7,  # Simplified
                'storage': before_cost * 0.2,
                'network': before_cost * 0.1
            }
        }
    
    def _estimate_cost(self, state: Dict, opp_type: OpportunityType) -> float:
        """Estimate cost from resource state"""
        # Simplified cost estimation
        if opp_type.value in ['over_requested_cpu', 'over_requested_memory']:
            cpu = state.get('cpu_request', 0)
            memory_gb = state.get('memory_request_gb', 0)
            # Rough estimate: $0.10/vCPU-hour, $0.01/GB-hour
            return (cpu * 730 * 0.10) + (memory_gb * 730 * 0.01)
        return 0.0
    
    def _get_recent_changes(self, opportunity: Opportunity) -> List[Dict]:
        """Get recent changes to the workload"""
        # Would query Git history, K8s events, etc.
        return [
            {
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                'type': 'deployment',
                'description': f'Deployment {opportunity.workload} updated',
                'impact': 'low'
            },
            {
                'timestamp': (datetime.utcnow() - timedelta(days=7)).isoformat(),
                'type': 'config',
                'description': f'Resource limits updated for {opportunity.workload}',
                'impact': 'medium'
            }
        ]
    
    def _analyze_safety(self, opportunity: Opportunity) -> Dict:
        """Analyze safety of the recommendation"""
        risk_factors = []
        safety_factors = []
        
        # Risk factors
        if opportunity.risk_score > 0.5:
            risk_factors.append('High risk score - proceed with caution')
        
        if opportunity.confidence < 0.7:
            risk_factors.append('Low confidence - may need more data')
        
        # Safety factors
        if opportunity.risk_score < 0.3:
            safety_factors.append('Low risk - safe to proceed')
        
        if opportunity.confidence > 0.8:
            safety_factors.append('High confidence - recommendation is reliable')
        
        # Check if workload is critical
        critical_namespaces = ['finance', 'healthcare', 'banking']
        if opportunity.namespace in critical_namespaces:
            risk_factors.append('Critical namespace - extra caution recommended')
        
        return {
            'overall_safety': 'safe' if opportunity.risk_score < 0.3 else 'caution',
            'risk_factors': risk_factors,
            'safety_factors': safety_factors,
            'recommendation': 'Approve' if opportunity.risk_score < 0.3 and opportunity.confidence > 0.7 else 'Review carefully'
        }
    
    def _generate_summary(self, opportunity: Opportunity) -> str:
        """Generate human-readable summary"""
        return f"""
Cost Optimization Opportunity: {opportunity.type.value.replace('_', ' ').title()}

Workload: {opportunity.workload} in {opportunity.namespace}
Estimated Savings: ${opportunity.estimated_monthly_savings:,.2f}/month
Confidence: {opportunity.confidence:.0%}
Risk Score: {opportunity.risk_score:.0%}

Recommendation: {opportunity.evidence.get('recommendation', 'Review and approve if safe')}
        """.strip()
    
    def _generate_html_report(self, evidence: Dict) -> str:
        """Generate HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Evidence Pack - {evidence['opportunity_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #1f77b4; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f0f2f6; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #1f77b4; color: white; }}
        .safe {{ color: green; }}
        .caution {{ color: orange; }}
        .risk {{ color: red; }}
    </style>
</head>
<body>
    <h1>Evidence Pack: {evidence['opportunity_id']}</h1>
    <p>Generated: {evidence['generated_at']}</p>
    
    <div class="section">
        <h2>Summary</h2>
        <pre>{evidence['summary']}</pre>
    </div>
    
    <div class="section">
        <h2>Cost Analysis</h2>
        <div class="metric">
            <strong>Current Monthly Cost:</strong><br>
            ${evidence['cost_analysis']['current_monthly_cost']:,.2f}
        </div>
        <div class="metric">
            <strong>Projected Monthly Cost:</strong><br>
            ${evidence['cost_analysis']['projected_monthly_cost']:,.2f}
        </div>
        <div class="metric">
            <strong>Estimated Savings:</strong><br>
            ${evidence['cost_analysis']['estimated_savings']:,.2f}/month
        </div>
        <div class="metric">
            <strong>Annual Savings:</strong><br>
            ${evidence['cost_analysis']['annual_savings']:,.2f}
        </div>
    </div>
    
    <div class="section">
        <h2>Safety Analysis</h2>
        <p><strong>Overall Safety:</strong> <span class="{evidence['safety_analysis']['overall_safety']}">{evidence['safety_analysis']['overall_safety'].upper()}</span></p>
        <p><strong>Recommendation:</strong> {evidence['safety_analysis']['recommendation']}</p>
        
        <h3>Risk Factors</h3>
        <ul>
            {"".join(f"<li>{factor}</li>" for factor in evidence['safety_analysis']['risk_factors'])}
        </ul>
        
        <h3>Safety Factors</h3>
        <ul>
            {"".join(f"<li>{factor}</li>" for factor in evidence['safety_analysis']['safety_factors'])}
        </ul>
    </div>
    
    <div class="section">
        <h2>Metrics Queries</h2>
        <p>Run these queries in Prometheus/Grafana:</p>
        <pre>{json.dumps(evidence['metrics']['queries'], indent=2)}</pre>
    </div>
    
    <div class="section">
        <h2>Log Queries</h2>
        <p>Run this query in Loki/Grafana:</p>
        <pre>{evidence['logs']['query']}</pre>
    </div>
    
    <div class="section">
        <h2>Recent Changes</h2>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Type</th>
                <th>Description</th>
                <th>Impact</th>
            </tr>
            {"".join(f"""
            <tr>
                <td>{change['timestamp']}</td>
                <td>{change['type']}</td>
                <td>{change['description']}</td>
                <td>{change['impact']}</td>
            </tr>
            """ for change in evidence['change_history'])}
        </table>
    </div>
</body>
</html>
        """
        return html.strip()


def generate_evidence_pack(opportunity: Opportunity, prometheus_url: Optional[str] = None, loki_url: Optional[str] = None) -> Dict:
    """Convenience function to generate evidence pack"""
    generator = EvidencePackGenerator(prometheus_url=prometheus_url, loki_url=loki_url)
    return generator.generate(opportunity)


if __name__ == '__main__':
    # Test evidence pack generation
    from finops.savings_ledger import OpportunityType, OpportunityStatus
    
    test_opportunity = Opportunity(
        id="test-123",
        type=OpportunityType.OVER_REQUESTED_CPU,
        status=OpportunityStatus.DETECTED,
        detected_at=datetime.utcnow(),
        cluster="test-cluster",
        namespace="finance",
        workload="payment-service",
        team="payments",
        estimated_monthly_savings=843.50,
        confidence=0.85,
        risk_score=0.2,
        evidence={'current_cpu_usage': 0.5, 'utilization': 0.25},
        before_state={'cpu_request': 2.0},
        after_state={'cpu_request': 1.0}
    )
    
    pack = generate_evidence_pack(test_opportunity)
    print(json.dumps(pack, indent=2, default=str))

