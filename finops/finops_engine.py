#!/usr/bin/env python3
"""
FinOps Engine - Main orchestration engine
Combines waste detection, PR generation, guardrails, and reporting
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from finops.savings_ledger import SavingsLedger, Opportunity, OpportunityStatus
from finops.waste_detectors import WasteDetectionEngine, DetectorResult
from finops.pr_generator import PRGenerator, PullRequest
from finops.guardrails import GuardrailEngine, PolicyCheck, PolicyAction
from finops.report_generator import ReportGenerator
from finops.aws_cost_integration import AWSCostExplorer, CostAllocator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinOpsEngine:
    """Main FinOps engine orchestrating all components"""
    
    def __init__(self, db_conn=None, github_token: Optional[str] = None):
        self.ledger = SavingsLedger()
        self.detector = WasteDetectionEngine()
        self.pr_generator = PRGenerator(
            repo_path=os.getenv('REPO_PATH', '.'),
            github_token=github_token
        )
        self.guardrails = GuardrailEngine()
        self.reporter = ReportGenerator(self.ledger)
        self.db_conn = db_conn
        
        # AWS integration (optional)
        self.aws_cost_explorer = None
        if os.getenv('AWS_ACCESS_KEY_ID'):
            try:
                self.aws_cost_explorer = AWSCostExplorer()
            except Exception as e:
                logger.warning(f"AWS Cost Explorer not available: {e}")
    
    def run_detection_cycle(self, cluster_data: Dict) -> List[Opportunity]:
        """Run a complete detection cycle"""
        logger.info("Starting waste detection cycle...")
        
        # Detect opportunities
        detector_results = self.detector.detect_all(cluster_data)
        logger.info(f"Detected {len(detector_results)} opportunities")
        
        # Convert to opportunities
        opportunities = []
        daily_changes = []  # Track for guardrail checks
        
        for result in detector_results:
            # Check guardrails
            opp_dict = {
                'confidence': result.confidence,
                'risk_score': result.risk_score,
                'estimated_monthly_savings': result.estimated_monthly_savings,
                'tags': cluster_data.get('tags', []),
                'namespace': result.namespace,
            }
            
            policy_check = self.guardrails.check_opportunity(opp_dict, daily_changes)
            
            if policy_check.action == PolicyAction.DENY:
                logger.info(f"Opportunity {result.opportunity_id} denied: {policy_check.reason}")
                continue
            
            # Create opportunity
            opportunity = Opportunity(
                id=result.opportunity_id,
                type=result.type,
                status=OpportunityStatus.REQUIRE_APPROVAL if policy_check.action == PolicyAction.REQUIRE_APPROVAL else OpportunityStatus.DETECTED,
                detected_at=result.detected_at,
                cluster=result.cluster,
                namespace=result.namespace,
                workload=result.workload,
                team=result.team,
                estimated_monthly_savings=result.estimated_monthly_savings,
                confidence=result.confidence,
                risk_score=result.risk_score,
                evidence=result.evidence,
                before_state=result.before_state,
                after_state=result.after_state
            )
            
            opportunities.append(opportunity)
            daily_changes.append(opp_dict)
            
            # Add to ledger
            self.ledger.add_opportunity(opportunity)
            
            # Store in database if available
            if self.db_conn:
                self._store_opportunity(opportunity)
        
        logger.info(f"Created {len(opportunities)} opportunities")
        return opportunities
    
    def generate_prs(self, opportunities: List[Opportunity]) -> List[PullRequest]:
        """Generate PRs for approved opportunities"""
        prs = []
        
        for opp in opportunities:
            if opp.status == OpportunityStatus.DETECTED or opp.status == OpportunityStatus.APPROVED:
                try:
                    pr = self.pr_generator.generate_pr(opp)
                    prs.append(pr)
                    
                    # Update opportunity with PR info
                    opp.pr_url = f"https://github.com/.../pull/{pr.branch_name}"  # Would be real URL
                    opp.status = OpportunityStatus.APPROVED
                    
                except Exception as e:
                    logger.error(f"Error generating PR for {opp.id}: {e}")
        
        return prs
    
    def generate_weekly_report(self) -> Dict:
        """Generate weekly CFO/CTO report"""
        week_start = datetime.utcnow() - timedelta(days=7)
        return self.reporter.generate_weekly_report(week_start)
    
    def generate_monthly_report(self) -> Dict:
        """Generate monthly CFO/CTO report"""
        month_start = datetime.utcnow() - timedelta(days=30)
        return self.reporter.generate_monthly_report(month_start)
    
    def _store_opportunity(self, opportunity: Opportunity):
        """Store opportunity in database"""
        # Implementation would use SQLAlchemy or direct SQL
        pass

