#!/usr/bin/env python3
"""
Savings Ledger - Core FinOps component
Tracks cost optimization opportunities, changes, and realized savings
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import json

class OpportunityStatus(Enum):
    """Status of a cost optimization opportunity"""
    DETECTED = "detected"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    ROLLED_BACK = "rolled_back"
    EXPIRED = "expired"

class OpportunityType(Enum):
    """Type of cost optimization opportunity"""
    OVER_REQUESTED_CPU = "over_requested_cpu"
    OVER_REQUESTED_MEMORY = "over_requested_memory"
    IDLE_NODES = "idle_nodes"
    ORPHAN_VOLUMES = "orphan_volumes"
    MISCONFIGURED_AUTOSCALING = "misconfigured_autoscaling"
    KARPENTER_CONSOLIDATION = "karpenter_consolidation"
    ZOMBIE_WORKLOADS = "zombie_workloads"
    UNUSED_RESOURCES = "unused_resources"

@dataclass
class CostBaseline:
    """Baseline cost for attribution"""
    workload_id: str
    namespace: str
    cluster: str
    team: str
    monthly_cost: float
    cpu_cost: float
    memory_cost: float
    storage_cost: float
    network_cost: float
    period_start: datetime
    period_end: datetime

@dataclass
class Opportunity:
    """Cost optimization opportunity"""
    id: str
    type: OpportunityType
    status: OpportunityStatus
    detected_at: datetime
    
    # Attribution
    cluster: str
    namespace: str
    workload: str
    team: str
    
    # Impact
    estimated_monthly_savings: float
    confidence: float  # 0.0-1.0
    risk_score: float  # 0.0-1.0
    
    # Evidence
    evidence: Dict  # Metrics, logs, config snapshots
    before_state: Dict  # Current resource state
    after_state: Dict  # Proposed resource state
    
    # Action
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    implemented_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    
    # Tracking
    realized_savings: float = 0.0
    rollback_reason: Optional[str] = None

@dataclass
class SavingsLedger:
    """Main savings ledger"""
    opportunities: List[Opportunity] = field(default_factory=list)
    baselines: List[CostBaseline] = field(default_factory=list)
    
    def add_opportunity(self, opportunity: Opportunity):
        """Add a new opportunity"""
        self.opportunities.append(opportunity)
    
    def get_opportunities_by_status(self, status: OpportunityStatus) -> List[Opportunity]:
        """Get opportunities by status"""
        return [o for o in self.opportunities if o.status == status]
    
    def get_total_estimated_savings(self) -> float:
        """Get total estimated monthly savings"""
        return sum(o.estimated_monthly_savings for o in self.opportunities 
                  if o.status in [OpportunityStatus.DETECTED, OpportunityStatus.APPROVED, 
                                 OpportunityStatus.IMPLEMENTED, OpportunityStatus.VERIFIED])
    
    def get_total_realized_savings(self) -> float:
        """Get total realized savings"""
        return sum(o.realized_savings for o in self.opportunities 
                  if o.status == OpportunityStatus.VERIFIED)
    
    def get_savings_by_team(self) -> Dict[str, float]:
        """Get savings breakdown by team"""
        team_savings = {}
        for opp in self.opportunities:
            if opp.status == OpportunityStatus.VERIFIED:
                team_savings[opp.team] = team_savings.get(opp.team, 0.0) + opp.realized_savings
        return team_savings
    
    def get_savings_by_type(self) -> Dict[str, float]:
        """Get savings breakdown by opportunity type"""
        type_savings = {}
        for opp in self.opportunities:
            if opp.status == OpportunityStatus.VERIFIED:
                type_key = opp.type.value
                type_savings[type_key] = type_savings.get(type_key, 0.0) + opp.realized_savings
        return type_savings

