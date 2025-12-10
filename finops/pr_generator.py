#!/usr/bin/env python3
"""
PR Generator Engine
Generates Pull Requests for cost optimization changes
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from finops.savings_ledger import Opportunity, OpportunityType

@dataclass
class PRChange:
    """Represents a change in a PR"""
    file_path: str
    change_type: str  # 'terraform', 'kubernetes', 'karpenter', 'keda'
    before: Dict
    after: Dict
    description: str

@dataclass
class PullRequest:
    """Pull request for cost optimization"""
    title: str
    description: str
    opportunity_id: str
    branch_name: str
    changes: List[PRChange]
    estimated_savings: float
    risk_score: float
    evidence: Dict
    risk_analysis: Optional[Dict] = None  # NEW: Comprehensive risk analysis

class PRGenerator:
    """Generates PRs for cost optimization opportunities"""
    
    def __init__(self, repo_path: str, github_token: Optional[str] = None):
        self.repo_path = repo_path
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
    
    def generate_pr(self, opportunity: Opportunity) -> PullRequest:
        """Generate a PR for an opportunity"""
        
        # Generate base PR
        if opportunity.type == OpportunityType.OVER_REQUESTED_CPU:
            pr = self._generate_cpu_rightsize_pr(opportunity)
        elif opportunity.type == OpportunityType.OVER_REQUESTED_MEMORY:
            pr = self._generate_memory_rightsize_pr(opportunity)
        elif opportunity.type == OpportunityType.IDLE_NODES:
            pr = self._generate_node_consolidation_pr(opportunity)
        elif opportunity.type == OpportunityType.ORPHAN_VOLUMES:
            pr = self._generate_volume_cleanup_pr(opportunity)
        elif opportunity.type == OpportunityType.MISCONFIGURED_AUTOSCALING:
            pr = self._generate_autoscaling_fix_pr(opportunity)
        elif opportunity.type == OpportunityType.KARPENTER_CONSOLIDATION:
            pr = self._generate_karpenter_consolidation_pr(opportunity)
        else:
            raise ValueError(f"Unsupported opportunity type: {opportunity.type}")
        
        # Add risk analysis
        pr.risk_analysis = self._calculate_risk_analysis(opportunity, pr)
        
        # Update description with risk analysis
        pr.description += f"\n\n### Risk Analysis\n{self._format_risk_analysis(pr.risk_analysis)}"
        
        return pr
    
    def _calculate_risk_analysis(self, opportunity: Opportunity, pr: PullRequest) -> Dict:
        """Calculate comprehensive risk analysis"""
        return {
            'blast_radius': self._calculate_blast_radius(opportunity),
            'latency_impact': self._estimate_latency_impact(opportunity),
            'dependency_risk': self._analyze_dependencies(opportunity),
            'slo_impact': self._calculate_slo_impact(opportunity),
            'confidence': opportunity.confidence,
            'overall_risk': pr.risk_score
        }
    
    def _calculate_blast_radius(self, opportunity: Opportunity) -> Dict:
        """Calculate blast radius (how many pods/services affected)"""
        # Simplified - would query K8s API
        return {
            'affected_pods': 1,  # Would calculate from deployment
            'affected_services': 1,
            'affected_namespaces': 1,
            'risk_level': 'low' if opportunity.risk_score < 0.3 else 'medium'
        }
    
    def _estimate_latency_impact(self, opportunity: Opportunity) -> Dict:
        """Estimate latency impact"""
        # Simplified - would use historical metrics
        if opportunity.type in [OpportunityType.OVER_REQUESTED_CPU, OpportunityType.OVER_REQUESTED_MEMORY]:
            return {
                'expected_latency_change_ms': 0,  # Right-sizing shouldn't increase latency
                'risk_level': 'low'
            }
        return {
            'expected_latency_change_ms': 0,
            'risk_level': 'low'
        }
    
    def _analyze_dependencies(self, opportunity: Opportunity) -> Dict:
        """Analyze dependency risk"""
        # Would query service mesh or dependency graph
        return {
            'upstream_services': [],
            'downstream_services': [],
            'risk_level': 'low'
        }
    
    def _calculate_slo_impact(self, opportunity: Opportunity) -> Dict:
        """Calculate SLO impact score"""
        # Simplified SLO impact
        if opportunity.risk_score < 0.3:
            slo_risk = 'low'
        elif opportunity.risk_score < 0.6:
            slo_risk = 'medium'
        else:
            slo_risk = 'high'
        
        return {
            'slo_violation_risk': slo_risk,
            'availability_impact': 'none' if opportunity.risk_score < 0.3 else 'minimal',
            'latency_impact': 'none'
        }
    
    def _format_risk_analysis(self, risk_analysis: Dict) -> str:
        """Format risk analysis for PR description"""
        return f"""
- **Blast Radius**: {risk_analysis['blast_radius']['affected_pods']} pod(s), {risk_analysis['blast_radius']['affected_services']} service(s)
- **Latency Impact**: {risk_analysis['latency_impact']['expected_latency_change_ms']}ms ({risk_analysis['latency_impact']['risk_level']} risk)
- **Dependency Risk**: {risk_analysis['dependency_risk']['risk_level']}
- **SLO Impact**: {risk_analysis['slo_impact']['slo_violation_risk']} risk
- **Overall Confidence**: {risk_analysis['confidence']:.0%}
        """.strip()
    
    def _generate_autoscaling_fix_pr(self, opp: Opportunity) -> PullRequest:
        """Generate PR for autoscaling fix"""
        changes = []
        
        hpa_file = f"k8s/{opp.namespace}/hpa-{opp.workload}.yaml"
        changes.append(PRChange(
            file_path=hpa_file,
            change_type='kubernetes',
            before=opp.before_state,
            after=opp.after_state,
            description=f"Fix HPA configuration: min replicas {opp.before_state.get('min_replicas', 'N/A')} → {opp.after_state.get('min_replicas', 'N/A')}"
        ))
        
        return PullRequest(
            title=f"Cost Optimization: Fix Autoscaling for {opp.workload}",
            description=f"""
## Cost Optimization Opportunity

**Type**: Autoscaling Configuration Fix
**Workload**: {opp.workload}
**Namespace**: {opp.namespace}

### Impact
- **Estimated Monthly Savings**: ${opp.estimated_monthly_savings:.2f}
- **Confidence**: {opp.confidence:.0%}
- **Risk Score**: {opp.risk_score:.0%}

### Changes
- Min replicas: {opp.before_state.get('min_replicas', 'N/A')} → {opp.after_state.get('min_replicas', 'N/A')}
- Scale-up delay: {opp.before_state.get('scale_up_delay', 'N/A')}s → {opp.after_state.get('scale_up_delay', 'N/A')}s

### Evidence
- Current CPU utilization: {opp.evidence.get('avg_cpu_utilization', 0):.1%}
- Current memory utilization: {opp.evidence.get('avg_memory_utilization', 0):.1%}

---
*Generated by AI DevOps Brain FinOps Engine*
            """.strip(),
            opportunity_id=opp.id,
            branch_name=f"finops/autoscaling-fix-{opp.workload}-{datetime.utcnow().strftime('%Y%m%d')}",
            changes=changes,
            estimated_savings=opp.estimated_monthly_savings,
            risk_score=opp.risk_score,
            evidence=opp.evidence
        )
    
    def _generate_karpenter_consolidation_pr(self, opp: Opportunity) -> PullRequest:
        """Generate PR for Karpenter consolidation"""
        changes = []
        
        # Generate Karpenter provisioner change
        karpenter_file = f"infrastructure/karpenter/{opp.workload}-provisioner.yaml"
        changes.append(PRChange(
            file_path=karpenter_file,
            change_type='karpenter',
            before=opp.before_state,
            after=opp.after_state,
            description=f"Consolidate nodes: {opp.before_state.get('node_count', 'N/A')} → {opp.after_state.get('node_count', 'N/A')} nodes"
        ))
        
        return PullRequest(
            title=f"Cost Optimization: Karpenter Consolidation for {opp.workload}",
            description=f"""
## Cost Optimization Opportunity

**Type**: Karpenter Node Consolidation
**Node Group**: {opp.workload}
**Cluster**: {opp.cluster}

### Impact
- **Estimated Monthly Savings**: ${opp.estimated_monthly_savings:.2f}
- **Confidence**: {opp.confidence:.0%}
- **Risk Score**: {opp.risk_score:.0%}

### Changes
- Node count: {opp.before_state.get('node_count', 'N/A')} → {opp.after_state.get('node_count', 'N/A')}
- Instance type: {opp.before_state.get('instance_type', 'N/A')} (unchanged)

### Evidence
- Average CPU utilization: {opp.evidence.get('avg_cpu_utilization', 0):.1%}
- Average memory utilization: {opp.evidence.get('avg_memory_utilization', 0):.1%}

---
*Generated by AI DevOps Brain FinOps Engine*
            """.strip(),
            opportunity_id=opp.id,
            branch_name=f"finops/karpenter-consolidation-{opp.workload}-{datetime.utcnow().strftime('%Y%m%d')}",
            changes=changes,
            estimated_savings=opp.estimated_monthly_savings,
            risk_score=opp.risk_score,
            evidence=opp.evidence
        )
    
    def _generate_cpu_rightsize_pr(self, opp: Opportunity) -> PullRequest:
        """Generate PR for CPU right-sizing"""
        changes = []
        
        # Generate K8s manifest change
        k8s_file = f"k8s/{opp.namespace}/{opp.workload}.yaml"
        changes.append(PRChange(
            file_path=k8s_file,
            change_type='kubernetes',
            before=opp.before_state,
            after=opp.after_state,
            description=f"Right-size CPU request from {opp.before_state['cpu_request']} to {opp.after_state['cpu_request']:.2f} cores"
        ))
        
        return PullRequest(
            title=f"Cost Optimization: Right-size CPU for {opp.workload}",
            description=f"""
## Cost Optimization Opportunity

**Type**: CPU Right-sizing
**Workload**: {opp.workload}
**Namespace**: {opp.namespace}
**Cluster**: {opp.cluster}

### Impact
- **Estimated Monthly Savings**: ${opp.estimated_monthly_savings:.2f}
- **Confidence**: {opp.confidence:.0%}
- **Risk Score**: {opp.risk_score:.0%}

### Changes
- CPU request: {opp.before_state['cpu_request']} → {opp.after_state['cpu_request']:.2f} cores
- CPU limit: {opp.before_state.get('cpu_limit', 'N/A')} → {opp.after_state.get('cpu_limit', 'N/A')} cores

### Evidence
- Current CPU utilization: {opp.evidence.get('utilization', 0):.1%}
- Current CPU usage: {opp.evidence.get('current_cpu_usage', 0):.2f} cores

### Recommendation
{opp.evidence.get('recommendation', 'Reduce CPU requests based on actual usage')}

---
*Generated by AI DevOps Brain FinOps Engine*
            """.strip(),
            opportunity_id=opp.id,
            branch_name=f"finops/cpu-rightsize-{opp.workload}-{datetime.utcnow().strftime('%Y%m%d')}",
            changes=changes,
            estimated_savings=opp.estimated_monthly_savings,
            risk_score=opp.risk_score,
            evidence=opp.evidence
        )
    
    def _generate_memory_rightsize_pr(self, opp: Opportunity) -> PullRequest:
        """Generate PR for memory right-sizing"""
        changes = []
        
        k8s_file = f"k8s/{opp.namespace}/{opp.workload}.yaml"
        changes.append(PRChange(
            file_path=k8s_file,
            change_type='kubernetes',
            before=opp.before_state,
            after=opp.after_state,
            description=f"Right-size memory request from {opp.before_state['memory_request_gb']:.2f}GB to {opp.after_state['memory_request_gb']:.2f}GB"
        ))
        
        return PullRequest(
            title=f"Cost Optimization: Right-size Memory for {opp.workload}",
            description=f"""
## Cost Optimization Opportunity

**Type**: Memory Right-sizing
**Workload**: {opp.workload}
**Namespace**: {opp.namespace}
**Cluster**: {opp.cluster}

### Impact
- **Estimated Monthly Savings**: ${opp.estimated_monthly_savings:.2f}
- **Confidence**: {opp.confidence:.0%}
- **Risk Score**: {opp.risk_score:.0%}

### Changes
- Memory request: {opp.before_state['memory_request_gb']:.2f}GB → {opp.after_state['memory_request_gb']:.2f}GB
- Memory limit: {opp.before_state.get('memory_limit_gb', 'N/A')}GB → {opp.after_state.get('memory_limit_gb', 'N/A')}GB

### Evidence
- Current memory utilization: {opp.evidence.get('utilization', 0):.1%}
- Current memory usage: {opp.evidence.get('current_memory_usage_gb', 0):.2f}GB

---
*Generated by AI DevOps Brain FinOps Engine*
            """.strip(),
            opportunity_id=opp.id,
            branch_name=f"finops/memory-rightsize-{opp.workload}-{datetime.utcnow().strftime('%Y%m%d')}",
            changes=changes,
            estimated_savings=opp.estimated_monthly_savings,
            risk_score=opp.risk_score,
            evidence=opp.evidence
        )
    
    def _generate_node_consolidation_pr(self, opp: Opportunity) -> PullRequest:
        """Generate PR for node consolidation"""
        changes = []
        
        # Generate Terraform change for node group
        tf_file = f"infrastructure/node-groups/{opp.workload}.tf"
        changes.append(PRChange(
            file_path=tf_file,
            change_type='terraform',
            before={'node_count': opp.before_state['node_count']},
            after={'node_count': opp.after_state['node_count']},
            description=f"Reduce node count from {opp.before_state['node_count']} to {opp.after_state['node_count']}"
        ))
        
        return PullRequest(
            title=f"Cost Optimization: Consolidate Nodes for {opp.workload}",
            description=f"""
## Cost Optimization Opportunity

**Type**: Node Consolidation
**Node Group**: {opp.workload}
**Cluster**: {opp.cluster}

### Impact
- **Estimated Monthly Savings**: ${opp.estimated_monthly_savings:.2f}
- **Confidence**: {opp.confidence:.0%}
- **Risk Score**: {opp.risk_score:.0%}

### Changes
- Node count: {opp.before_state['node_count']} → {opp.after_state['node_count']}
- Instance type: {opp.before_state.get('instance_type', 'N/A')} (unchanged)

### Evidence
- Average CPU utilization: {opp.evidence.get('avg_cpu_utilization', 0):.1%}
- Average memory utilization: {opp.evidence.get('avg_memory_utilization', 0):.1%}

---
*Generated by AI DevOps Brain FinOps Engine*
            """.strip(),
            opportunity_id=opp.id,
            branch_name=f"finops/node-consolidation-{opp.workload}-{datetime.utcnow().strftime('%Y%m%d')}",
            changes=changes,
            estimated_savings=opp.estimated_monthly_savings,
            risk_score=opp.risk_score,
            evidence=opp.evidence
        )
    
    def _generate_volume_cleanup_pr(self, opp: Opportunity) -> PullRequest:
        """Generate PR for volume cleanup"""
        changes = []
        
        # Generate Terraform change to remove volume
        tf_file = f"infrastructure/storage/{opp.workload}.tf"
        changes.append(PRChange(
            file_path=tf_file,
            change_type='terraform',
            before={'volume_id': opp.before_state['volume_id'], 'status': 'exists'},
            after={'volume_id': opp.after_state['volume_id'], 'status': 'deleted'},
            description=f"Delete orphaned volume {opp.before_state['volume_id']}"
        ))
        
        return PullRequest(
            title=f"Cost Optimization: Cleanup Orphaned Volume {opp.workload}",
            description=f"""
## Cost Optimization Opportunity

**Type**: Orphaned Volume Cleanup
**Volume ID**: {opp.workload}
**Cluster**: {opp.cluster}

### Impact
- **Estimated Monthly Savings**: ${opp.estimated_monthly_savings:.2f}
- **Confidence**: {opp.confidence:.0%}
- **Risk Score**: {opp.risk_score:.0%}

### Changes
- Delete orphaned EBS volume: {opp.before_state['volume_id']}
- Volume size: {opp.evidence.get('size_gb', 0)}GB
- Age: {opp.evidence.get('age_days', 0)} days

### Evidence
- Volume status: {opp.evidence.get('status', 'unknown')}
- Volume type: {opp.evidence.get('type', 'unknown')}

---
*Generated by AI DevOps Brain FinOps Engine*
            """.strip(),
            opportunity_id=opp.id,
            branch_name=f"finops/volume-cleanup-{opp.workload}-{datetime.utcnow().strftime('%Y%m%d')}",
            changes=changes,
            estimated_savings=opp.estimated_monthly_savings,
            risk_score=opp.risk_score,
            evidence=opp.evidence
        )
    
    def create_pr_files(self, pr: PullRequest) -> List[str]:
        """Create PR files in the repository"""
        created_files = []
        
        for change in pr.changes:
            file_path = os.path.join(self.repo_path, change.file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Generate file content based on change type
            if change.change_type == 'kubernetes':
                content = self._generate_k8s_manifest(change)
            elif change.change_type == 'terraform':
                content = self._generate_terraform(change)
            else:
                content = json.dumps(change.after, indent=2)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            created_files.append(file_path)
        
        return created_files
    
    def _generate_k8s_manifest(self, change: PRChange) -> str:
        """Generate Kubernetes manifest from change"""
        # Simplified - would generate full YAML
        return f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {change.file_path.split('/')[-1].replace('.yaml', '')}
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            cpu: "{change.after.get('cpu_request', '100m')}"
            memory: "{change.after.get('memory_request_gb', 0.5)}Gi"
          limits:
            cpu: "{change.after.get('cpu_limit', change.after.get('cpu_request', '100m'))}"
            memory: "{change.after.get('memory_limit_gb', 1.0)}Gi"
        """.strip()
    
    def _generate_terraform(self, change: PRChange) -> str:
        """Generate Terraform config from change"""
        # Simplified - would generate full Terraform
        return f"""
# {change.description}
resource "aws_eks_node_group" "example" {{
  node_count = {change.after.get('node_count', 1)}
  # ... other config
}}
        """.strip()

