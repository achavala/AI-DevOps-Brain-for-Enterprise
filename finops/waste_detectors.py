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

class WasteDetectionEngine:
    """Main waste detection engine"""
    
    def __init__(self):
        self.detectors = [
            OverRequestedCPUDetector(),
            OverRequestedMemoryDetector(),
            IdleNodeDetector(),
            OrphanVolumeDetector(),
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

