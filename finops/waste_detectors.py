#!/usr/bin/env python3
"""
Waste Detection Engine
Rules-based detectors for EKS cost optimization opportunities
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import uuid

from finops.savings_ledger import Opportunity, OpportunityType, OpportunityStatus

@dataclass
class DetectorResult:
    """Result from a waste detector"""
    opportunity_id: str
    type: OpportunityType
    detected_at: datetime
    cluster: str
    namespace: str
    workload: str
    team: str
    estimated_monthly_savings: float
    confidence: float
    risk_score: float
    evidence: Dict
    before_state: Dict
    after_state: Dict
    recommendation: str

class WasteDetector:
    """Base class for waste detectors"""
    
    def detect(self, cluster_data: Dict) -> List[DetectorResult]:
        """Detect waste opportunities in cluster data"""
        raise NotImplementedError
    
    def get_type(self) -> OpportunityType:
        """Get the opportunity type this detector finds"""
        raise NotImplementedError

class OverRequestedCPUDetector(WasteDetector):
    """Detects over-requested CPU resources"""
    
    def __init__(self, utilization_threshold: float = 0.3, savings_threshold: float = 10.0):
        self.utilization_threshold = utilization_threshold
        self.savings_threshold = savings_threshold
    
    def get_type(self) -> OpportunityType:
        return OpportunityType.OVER_REQUESTED_CPU
    
    def detect(self, cluster_data: Dict) -> List[DetectorResult]:
        """Detect pods with over-requested CPU"""
        results = []
        
        for namespace, workloads in cluster_data.get('workloads', {}).items():
            for workload in workloads:
                # Get current requests and usage
                cpu_request = workload.get('cpu_request', 0)
                cpu_usage = workload.get('cpu_usage', 0)
                cpu_limit = workload.get('cpu_limit', cpu_request)
                
                if cpu_request == 0:
                    continue
                
                utilization = cpu_usage / cpu_request if cpu_request > 0 else 0
                
                # If utilization is low, suggest reducing requests
                if utilization < self.utilization_threshold:
                    # Calculate savings (assume $0.10 per vCPU-hour)
                    current_cost = cpu_request * 730 * 0.10  # Monthly
                    suggested_request = max(cpu_usage * 1.5, 0.1)  # 50% headroom
                    new_cost = suggested_request * 730 * 0.10
                    savings = current_cost - new_cost
                    
                    if savings >= self.savings_threshold:
                        results.append(DetectorResult(
                            opportunity_id=str(uuid.uuid4()),
                            type=self.get_type(),
                            detected_at=datetime.utcnow(),
                            cluster=cluster_data.get('cluster', 'unknown'),
                            namespace=namespace,
                            workload=workload.get('name', 'unknown'),
                            team=workload.get('team', 'unknown'),
                            estimated_monthly_savings=savings,
                            confidence=0.85 if utilization < 0.2 else 0.65,
                            risk_score=0.2,  # Low risk - just reducing requests
                            evidence={
                                'current_cpu_request': cpu_request,
                                'current_cpu_usage': cpu_usage,
                                'utilization': utilization,
                                'cpu_limit': cpu_limit
                            },
                            before_state={
                                'cpu_request': cpu_request,
                                'cpu_limit': cpu_limit
                            },
                            after_state={
                                'cpu_request': suggested_request,
                                'cpu_limit': suggested_request * 2  # Keep limit at 2x request
                            },
                            recommendation=f"Reduce CPU request from {cpu_request} to {suggested_request:.2f} cores. Current utilization: {utilization:.1%}"
                        ))
        
        return results

class OverRequestedMemoryDetector(WasteDetector):
    """Detects over-requested memory resources"""
    
    def __init__(self, utilization_threshold: float = 0.3, savings_threshold: float = 10.0):
        self.utilization_threshold = utilization_threshold
        self.savings_threshold = savings_threshold
    
    def get_type(self) -> OpportunityType:
        return OpportunityType.OVER_REQUESTED_MEMORY
    
    def detect(self, cluster_data: Dict) -> List[DetectorResult]:
        """Detect pods with over-requested memory"""
        results = []
        
        for namespace, workloads in cluster_data.get('workloads', {}).items():
            for workload in workloads:
                mem_request_gb = workload.get('memory_request_gb', 0)
                mem_usage_gb = workload.get('memory_usage_gb', 0)
                mem_limit_gb = workload.get('memory_limit_gb', mem_request_gb)
                
                if mem_request_gb == 0:
                    continue
                
                utilization = mem_usage_gb / mem_request_gb if mem_request_gb > 0 else 0
                
                if utilization < self.utilization_threshold:
                    # Calculate savings (assume $0.01 per GB-hour)
                    current_cost = mem_request_gb * 730 * 0.01  # Monthly
                    suggested_request = max(mem_usage_gb * 1.5, 0.5)  # 50% headroom
                    new_cost = suggested_request * 730 * 0.01
                    savings = current_cost - new_cost
                    
                    if savings >= self.savings_threshold:
                        results.append(DetectorResult(
                            opportunity_id=str(uuid.uuid4()),
                            type=self.get_type(),
                            detected_at=datetime.utcnow(),
                            cluster=cluster_data.get('cluster', 'unknown'),
                            namespace=namespace,
                            workload=workload.get('name', 'unknown'),
                            team=workload.get('team', 'unknown'),
                            estimated_monthly_savings=savings,
                            confidence=0.85 if utilization < 0.2 else 0.65,
                            risk_score=0.2,
                            evidence={
                                'current_memory_request_gb': mem_request_gb,
                                'current_memory_usage_gb': mem_usage_gb,
                                'utilization': utilization,
                                'memory_limit_gb': mem_limit_gb
                            },
                            before_state={
                                'memory_request_gb': mem_request_gb,
                                'memory_limit_gb': mem_limit_gb
                            },
                            after_state={
                                'memory_request_gb': suggested_request,
                                'memory_limit_gb': suggested_request * 2
                            },
                            recommendation=f"Reduce memory request from {mem_request_gb:.2f}GB to {suggested_request:.2f}GB. Current utilization: {utilization:.1%}"
                        ))
        
        return results

class IdleNodeDetector(WasteDetector):
    """Detects idle or underutilized node groups"""
    
    def __init__(self, utilization_threshold: float = 0.2, min_node_count: int = 2):
        self.utilization_threshold = utilization_threshold
        self.min_node_count = min_node_count
    
    def get_type(self) -> OpportunityType:
        return OpportunityType.IDLE_NODES
    
    def detect(self, cluster_data: Dict) -> List[DetectorResult]:
        """Detect idle nodes"""
        results = []
        
        node_groups = cluster_data.get('node_groups', [])
        
        for ng in node_groups:
            node_count = ng.get('node_count', 0)
            avg_cpu_util = ng.get('avg_cpu_utilization', 0)
            avg_mem_util = ng.get('avg_memory_utilization', 0)
            instance_type = ng.get('instance_type', 'unknown')
            
            # Estimate node cost (simplified - would use real pricing)
            node_cost_per_month = self._estimate_node_cost(instance_type)
            
            if node_count >= self.min_node_count and (avg_cpu_util < self.utilization_threshold or avg_mem_util < self.utilization_threshold):
                # Can we consolidate?
                total_util = (avg_cpu_util + avg_mem_util) / 2
                suggested_nodes = max(1, int(node_count * total_util * 1.2))  # 20% headroom
                
                if suggested_nodes < node_count:
                    savings = (node_count - suggested_nodes) * node_cost_per_month
                    
                    results.append(DetectorResult(
                        opportunity_id=str(uuid.uuid4()),
                        type=self.get_type(),
                        detected_at=datetime.utcnow(),
                        cluster=cluster_data.get('cluster', 'unknown'),
                        namespace='cluster',
                        workload=ng.get('name', 'unknown'),
                        team='infrastructure',
                        estimated_monthly_savings=savings,
                        confidence=0.75,
                        risk_score=0.3,  # Medium risk - node changes
                        evidence={
                            'current_node_count': node_count,
                            'avg_cpu_utilization': avg_cpu_util,
                            'avg_memory_utilization': avg_mem_util,
                            'instance_type': instance_type
                        },
                        before_state={
                            'node_count': node_count,
                            'instance_type': instance_type
                        },
                        after_state={
                            'node_count': suggested_nodes,
                            'instance_type': instance_type
                        },
                        recommendation=f"Reduce node group from {node_count} to {suggested_nodes} nodes. Current utilization: CPU {avg_cpu_util:.1%}, Memory {avg_mem_util:.1%}"
                    ))
        
        return results
    
    def _estimate_node_cost(self, instance_type: str) -> float:
        """Estimate monthly cost for instance type (simplified)"""
        # Simplified pricing - would use AWS Pricing API
        pricing = {
            't3.medium': 30.0,
            't3.large': 60.0,
            'm5.large': 70.0,
            'm5.xlarge': 140.0,
            'c5.xlarge': 150.0,
        }
        return pricing.get(instance_type, 100.0)  # Default $100/month

class OrphanVolumeDetector(WasteDetector):
    """Detects orphaned EBS volumes"""
    
    def get_type(self) -> OpportunityType:
        return OpportunityType.ORPHAN_VOLUMES
    
    def detect(self, cluster_data: Dict) -> List[DetectorResult]:
        """Detect orphaned volumes"""
        results = []
        
        volumes = cluster_data.get('volumes', [])
        
        for vol in volumes:
            if vol.get('status') == 'available' and not vol.get('attached'):
                # Orphaned volume
                size_gb = vol.get('size_gb', 0)
                volume_type = vol.get('type', 'gp3')
                age_days = vol.get('age_days', 0)
                
                # Only flag volumes older than 7 days
                if age_days > 7:
                    # Estimate cost (gp3: $0.08/GB-month)
                    monthly_cost = size_gb * 0.08
                    
                    results.append(DetectorResult(
                        opportunity_id=str(uuid.uuid4()),
                        type=self.get_type(),
                        detected_at=datetime.utcnow(),
                        cluster=cluster_data.get('cluster', 'unknown'),
                        namespace='storage',
                        workload=vol.get('volume_id', 'unknown'),
                        team='infrastructure',
                        estimated_monthly_savings=monthly_cost,
                        confidence=0.95,  # High confidence - clearly orphaned
                        risk_score=0.1,  # Very low risk - just deleting unused volume
                        evidence={
                            'volume_id': vol.get('volume_id'),
                            'size_gb': size_gb,
                            'type': volume_type,
                            'age_days': age_days,
                            'status': vol.get('status')
                        },
                        before_state={
                            'volume_id': vol.get('volume_id'),
                            'status': 'exists'
                        },
                        after_state={
                            'volume_id': vol.get('volume_id'),
                            'status': 'deleted'
                        },
                        recommendation=f"Delete orphaned volume {vol.get('volume_id')} ({size_gb}GB, {age_days} days old). Monthly savings: ${monthly_cost:.2f}"
                    ))
        
        return results

class MisconfiguredAutoscalingDetector(WasteDetector):
    """Detects misconfigured HPA/KEDA autoscaling"""
    
    def __init__(self, min_utilization_threshold: float = 0.3, max_utilization_threshold: float = 0.8):
        self.min_utilization_threshold = min_utilization_threshold
        self.max_utilization_threshold = max_utilization_threshold
    
    def get_type(self) -> OpportunityType:
        return OpportunityType.MISCONFIGURED_AUTOSCALING
    
    def detect(self, cluster_data: Dict) -> List[DetectorResult]:
        """Detect misconfigured autoscaling"""
        results = []
        
        hpa_configs = cluster_data.get('hpa_configs', [])
        keda_configs = cluster_data.get('keda_configs', [])
        
        # Check HPA configurations
        for hpa in hpa_configs:
            namespace = hpa.get('namespace', 'default')
            workload = hpa.get('workload', 'unknown')
            min_replicas = hpa.get('min_replicas', 1)
            max_replicas = hpa.get('max_replicas', 10)
            current_replicas = hpa.get('current_replicas', min_replicas)
            avg_cpu_util = hpa.get('avg_cpu_utilization', 0)
            avg_mem_util = hpa.get('avg_memory_utilization', 0)
            
            # Check if min replicas too high
            if min_replicas > 1 and avg_cpu_util < self.min_utilization_threshold:
                # Can reduce min replicas
                suggested_min = max(1, int(min_replicas * avg_cpu_util * 1.2))
                if suggested_min < min_replicas:
                    # Estimate savings (simplified)
                    savings = (min_replicas - suggested_min) * 50.0  # $50/month per pod
                    
                    results.append(DetectorResult(
                        opportunity_id=str(uuid.uuid4()),
                        type=self.get_type(),
                        detected_at=datetime.utcnow(),
                        cluster=cluster_data.get('cluster', 'unknown'),
                        namespace=namespace,
                        workload=workload,
                        team=hpa.get('team', 'unknown'),
                        estimated_monthly_savings=savings,
                        confidence=0.75,
                        risk_score=0.3,
                        evidence={
                            'current_min_replicas': min_replicas,
                            'suggested_min_replicas': suggested_min,
                            'avg_cpu_utilization': avg_cpu_util,
                            'avg_memory_utilization': avg_mem_util
                        },
                        before_state={
                            'min_replicas': min_replicas,
                            'max_replicas': max_replicas
                        },
                        after_state={
                            'min_replicas': suggested_min,
                            'max_replicas': max_replicas
                        },
                        recommendation=f"Reduce HPA min replicas from {min_replicas} to {suggested_min} for {workload}. Current CPU utilization: {avg_cpu_util:.1%}"
                    ))
            
            # Check if scaling is too slow
            if hpa.get('scale_up_delay', 0) > 300:  # More than 5 minutes
                savings = 20.0  # Estimated savings from faster scaling
                results.append(DetectorResult(
                    opportunity_id=str(uuid.uuid4()),
                    type=self.get_type(),
                    detected_at=datetime.utcnow(),
                    cluster=cluster_data.get('cluster', 'unknown'),
                    namespace=namespace,
                    workload=workload,
                    team=hpa.get('team', 'unknown'),
                    estimated_monthly_savings=savings,
                    confidence=0.65,
                    risk_score=0.2,
                    evidence={
                        'scale_up_delay': hpa.get('scale_up_delay', 0),
                        'recommended_delay': 60  # 1 minute
                    },
                    before_state={'scale_up_delay': hpa.get('scale_up_delay', 0)},
                    after_state={'scale_up_delay': 60},
                    recommendation=f"Reduce HPA scale-up delay from {hpa.get('scale_up_delay', 0)}s to 60s for faster scaling"
                ))
        
        # Check KEDA configurations (similar logic)
        for keda in keda_configs:
            # Similar detection logic for KEDA
            pass
        
        return results

class KarpenterConsolidationDetector(WasteDetector):
    """Detects Karpenter node consolidation opportunities"""
    
    def __init__(self, utilization_threshold: float = 0.5):
        self.utilization_threshold = utilization_threshold
    
    def get_type(self) -> OpportunityType:
        return OpportunityType.KARPENTER_CONSOLIDATION
    
    def detect(self, cluster_data: Dict) -> List[DetectorResult]:
        """Detect Karpenter consolidation opportunities"""
        results = []
        
        nodes = cluster_data.get('nodes', [])
        node_groups = {}
        
        # Group nodes by instance type
        for node in nodes:
            instance_type = node.get('instance_type', 'unknown')
            if instance_type not in node_groups:
                node_groups[instance_type] = []
            node_groups[instance_type].append(node)
        
        # Find underpacked nodes
        for instance_type, node_list in node_groups.items():
            if len(node_list) < 2:
                continue  # Need at least 2 nodes to consolidate
            
            total_cpu_util = sum(n.get('cpu_utilization', 0) for n in node_list) / len(node_list)
            total_mem_util = sum(n.get('memory_utilization', 0) for n in node_list) / len(node_list)
            avg_util = (total_cpu_util + total_mem_util) / 2
            
            if avg_util < self.utilization_threshold:
                # Can consolidate
                node_cost = self._estimate_node_cost(instance_type)
                suggested_nodes = max(1, int(len(node_list) * avg_util * 1.3))  # 30% headroom
                
                if suggested_nodes < len(node_list):
                    savings = (len(node_list) - suggested_nodes) * node_cost
                    
                    results.append(DetectorResult(
                        opportunity_id=str(uuid.uuid4()),
                        type=self.get_type(),
                        detected_at=datetime.utcnow(),
                        cluster=cluster_data.get('cluster', 'unknown'),
                        namespace='cluster',
                        workload=f"{instance_type}-nodes",
                        team='infrastructure',
                        estimated_monthly_savings=savings,
                        confidence=0.7,
                        risk_score=0.4,  # Medium risk - node changes
                        evidence={
                            'current_node_count': len(node_list),
                            'suggested_node_count': suggested_nodes,
                            'avg_cpu_utilization': total_cpu_util,
                            'avg_memory_utilization': total_mem_util,
                            'instance_type': instance_type
                        },
                        before_state={
                            'node_count': len(node_list),
                            'instance_type': instance_type
                        },
                        after_state={
                            'node_count': suggested_nodes,
                            'instance_type': instance_type
                        },
                        recommendation=f"Consolidate {instance_type} nodes from {len(node_list)} to {suggested_nodes}. Current utilization: {avg_util:.1%}"
                    ))
        
        return results
    
    def _estimate_node_cost(self, instance_type: str) -> float:
        """Estimate monthly cost for instance type"""
        pricing = {
            't3.medium': 30.0,
            't3.large': 60.0,
            'm5.large': 70.0,
            'm5.xlarge': 140.0,
            'c5.xlarge': 150.0,
        }
        return pricing.get(instance_type, 100.0)

class WasteDetectionEngine:
    """Main waste detection engine"""
    
    def __init__(self):
        self.detectors = [
            OverRequestedCPUDetector(),
            OverRequestedMemoryDetector(),
            IdleNodeDetector(),
            OrphanVolumeDetector(),
            MisconfiguredAutoscalingDetector(),  # NEW
            KarpenterConsolidationDetector(),  # NEW
        ]
    
    def detect_all(self, cluster_data: Dict) -> List[DetectorResult]:
        """Run all detectors and return all opportunities"""
        all_results = []
        
        for detector in self.detectors:
            try:
                results = detector.detect(cluster_data)
                all_results.extend(results)
            except Exception as e:
                print(f"Error in detector {detector.__class__.__name__}: {e}")
        
        # Sort by estimated savings (descending)
        all_results.sort(key=lambda x: x.estimated_monthly_savings, reverse=True)
        
        return all_results
    
    def add_detector(self, detector: WasteDetector):
        """Add a custom detector"""
        self.detectors.append(detector)

