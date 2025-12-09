#!/usr/bin/env python3
"""
AWS Cost Integration
Integrates with AWS Cost Explorer API and Cost & Usage Reports (CUR)
"""

import os
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CostDataPoint:
    """Single cost data point"""
    date: datetime
    service: str
    cluster: Optional[str]
    namespace: Optional[str]
    workload: Optional[str]
    team: Optional[str]
    amount: float
    unit: str = "USD"

class AWSCostExplorer:
    """AWS Cost Explorer API integration"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.ce_client = boto3.client('ce', region_name=region)
    
    def get_cluster_costs(self, cluster_name: str, start_date: datetime, end_date: datetime) -> List[CostDataPoint]:
        """Get costs for a specific EKS cluster"""
        # Use Cost Explorer API with tags
        # Assumes cluster is tagged with 'kubernetes.io/cluster/<cluster-name>' = 'owned'
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Tags': {
                        'Key': f'kubernetes.io/cluster/{cluster_name}',
                        'Values': ['owned']
                    }
                },
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'TAG', 'Key': 'kubernetes.io/namespace'},
                ]
            )
            
            results = []
            for result in response.get('ResultsByTime', []):
                date = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d')
                
                for group in result.get('Groups', []):
                    service = group['Keys'][0] if len(group['Keys']) > 0 else 'Unknown'
                    namespace = group['Keys'][1].split(':')[-1] if len(group['Keys']) > 1 else None
                    
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    results.append(CostDataPoint(
                        date=date,
                        service=service,
                        cluster=cluster_name,
                        namespace=namespace,
                        workload=None,
                        team=None,
                        amount=amount
                    ))
            
            return results
            
        except Exception as e:
            print(f"Error fetching cost data: {e}")
            return []
    
    def get_eks_costs(self, start_date: datetime, end_date: datetime) -> List[CostDataPoint]:
        """Get all EKS-related costs"""
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Elastic Compute Cloud - Compute', 'AmazonEC2']
                    }
                },
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                ]
            )
            
            results = []
            for result in response.get('ResultsByTime', []):
                date = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d')
                
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    results.append(CostDataPoint(
                        date=date,
                        service=service,
                        cluster=None,
                        namespace=None,
                        workload=None,
                        team=None,
                        amount=amount
                    ))
            
            return results
            
        except Exception as e:
            print(f"Error fetching EKS costs: {e}")
            return []

class CostAllocator:
    """Allocates costs to workloads using K8s metadata"""
    
    def __init__(self, k8s_client, cost_data: List[CostDataPoint]):
        self.k8s_client = k8s_client
        self.cost_data = cost_data
    
    def allocate_costs(self, cluster: str) -> Dict:
        """Allocate costs to namespaces and workloads"""
        # This would:
        # 1. Get K8s resource usage (CPU, memory, storage)
        # 2. Map AWS costs to K8s resources
        # 3. Allocate based on usage ratios
        
        allocation = {
            'cluster': cluster,
            'namespaces': {},
            'total_cost': 0.0
        }
        
        # Simplified allocation - would use real resource usage
        for cost_point in self.cost_data:
            if cost_point.cluster == cluster:
                namespace = cost_point.namespace or 'default'
                if namespace not in allocation['namespaces']:
                    allocation['namespaces'][namespace] = {
                        'total_cost': 0.0,
                        'workloads': {}
                    }
                
                allocation['namespaces'][namespace]['total_cost'] += cost_point.amount
                allocation['total_cost'] += cost_point.amount
        
        return allocation

