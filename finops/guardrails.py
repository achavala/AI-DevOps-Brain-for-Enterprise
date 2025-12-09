#!/usr/bin/env python3
"""
Guardrails - Policy enforcement for safe automation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, time
from enum import Enum

class PolicyAction(Enum):
    """Policy action result"""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"

@dataclass
class PolicyCheck:
    """Result of a policy check"""
    policy_name: str
    action: PolicyAction
    reason: str
    details: Dict

class GuardrailEngine:
    """Guardrail engine for safe automation"""
    
    def __init__(self):
        self.policies = {
            'max_daily_change': 1000.0,  # Max $ change per day
            'max_single_change': 500.0,   # Max $ for single change
            'protected_tags': ['production', 'critical'],
            'change_window_start': time(2, 0),  # 2 AM
            'change_window_end': time(6, 0),    # 6 AM
            'min_confidence': 0.7,
            'max_risk_score': 0.5,
            'blast_radius_limit': 3,  # Max namespaces affected
        }
    
    def check_opportunity(self, opportunity: Dict, daily_changes: List[Dict]) -> PolicyCheck:
        """Check if an opportunity passes guardrails"""
        
        # Check confidence threshold
        if opportunity.get('confidence', 0) < self.policies['min_confidence']:
            return PolicyCheck(
                policy_name='min_confidence',
                action=PolicyAction.DENY,
                reason=f"Confidence {opportunity.get('confidence', 0):.2f} below threshold {self.policies['min_confidence']}",
                details={'confidence': opportunity.get('confidence', 0)}
            )
        
        # Check risk score
        if opportunity.get('risk_score', 1.0) > self.policies['max_risk_score']:
            return PolicyCheck(
                policy_name='max_risk_score',
                action=PolicyAction.REQUIRE_APPROVAL,
                reason=f"Risk score {opportunity.get('risk_score', 0):.2f} above threshold {self.policies['max_risk_score']}",
                details={'risk_score': opportunity.get('risk_score', 0)}
            )
        
        # Check single change limit
        savings = opportunity.get('estimated_monthly_savings', 0)
        if savings > self.policies['max_single_change']:
            return PolicyCheck(
                policy_name='max_single_change',
                action=PolicyAction.REQUIRE_APPROVAL,
                reason=f"Change amount ${savings:.2f} exceeds single change limit ${self.policies['max_single_change']}",
                details={'savings': savings}
            )
        
        # Check daily change limit
        daily_total = sum(d.get('estimated_monthly_savings', 0) for d in daily_changes)
        if daily_total + savings > self.policies['max_daily_change']:
            return PolicyCheck(
                policy_name='max_daily_change',
                action=PolicyAction.REQUIRE_APPROVAL,
                reason=f"Daily change limit would be exceeded (${daily_total + savings:.2f} > ${self.policies['max_daily_change']})",
                details={'daily_total': daily_total, 'new_change': savings}
            )
        
        # Check protected tags
        tags = opportunity.get('tags', [])
        if any(tag in self.policies['protected_tags'] for tag in tags):
            return PolicyCheck(
                policy_name='protected_tags',
                action=PolicyAction.REQUIRE_APPROVAL,
                reason=f"Resource has protected tags: {[t for t in tags if t in self.policies['protected_tags']]}",
                details={'tags': tags}
            )
        
        # Check change window
        current_time = datetime.now().time()
        if not (self.policies['change_window_start'] <= current_time <= self.policies['change_window_end']):
            return PolicyCheck(
                policy_name='change_window',
                action=PolicyAction.REQUIRE_APPROVAL,
                reason=f"Outside change window ({self.policies['change_window_start']} - {self.policies['change_window_end']})",
                details={'current_time': current_time}
            )
        
        # Check blast radius
        affected_namespaces = len(set(d.get('namespace') for d in daily_changes + [opportunity]))
        if affected_namespaces > self.policies['blast_radius_limit']:
            return PolicyCheck(
                policy_name='blast_radius',
                action=PolicyAction.REQUIRE_APPROVAL,
                reason=f"Blast radius ({affected_namespaces} namespaces) exceeds limit ({self.policies['blast_radius_limit']})",
                details={'affected_namespaces': affected_namespaces}
            )
        
        # All checks passed
        return PolicyCheck(
            policy_name='all_checks',
            action=PolicyAction.ALLOW,
            reason="All guardrail checks passed",
            details={}
        )
    
    def update_policy(self, policy_name: str, value):
        """Update a policy value"""
        if policy_name in self.policies:
            self.policies[policy_name] = value
        else:
            raise ValueError(f"Unknown policy: {policy_name}")

