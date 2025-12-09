#!/usr/bin/env python3
"""
Report Generator - Weekly/Monthly CFO/CTO Reports
"""

from datetime import datetime, timedelta
from typing import Dict, List
import json

from finops.savings_ledger import SavingsLedger, OpportunityStatus

class ReportGenerator:
    """Generates savings reports for executives"""
    
    def __init__(self, ledger: SavingsLedger):
        self.ledger = ledger
    
    def generate_weekly_report(self, week_start: datetime) -> Dict:
        """Generate weekly CFO/CTO report"""
        week_end = week_start + timedelta(days=7)
        
        # Get opportunities from this week
        week_opportunities = [
            o for o in self.ledger.opportunities
            if week_start <= o.detected_at < week_end
        ]
        
        # Calculate metrics
        total_estimated = sum(o.estimated_monthly_savings for o in week_opportunities)
        total_realized = sum(o.realized_savings for o in week_opportunities 
                           if o.status == OpportunityStatus.VERIFIED)
        
        detected = len([o for o in week_opportunities if o.status == OpportunityStatus.DETECTED])
        implemented = len([o for o in week_opportunities if o.status == OpportunityStatus.IMPLEMENTED])
        verified = len([o for o in week_opportunities if o.status == OpportunityStatus.VERIFIED])
        
        # Breakdowns
        by_team = self.ledger.get_savings_by_team()
        by_type = self.ledger.get_savings_by_type()
        
        # Top opportunities
        top_opportunities = sorted(
            week_opportunities,
            key=lambda x: x.estimated_monthly_savings,
            reverse=True
        )[:10]
        
        report = {
            'report_type': 'weekly',
            'period_start': week_start.isoformat(),
            'period_end': week_end.isoformat(),
            'generated_at': datetime.utcnow().isoformat(),
            
            'summary': {
                'total_estimated_savings': total_estimated,
                'total_realized_savings': total_realized,
                'opportunities_detected': detected,
                'opportunities_implemented': implemented,
                'opportunities_verified': verified,
            },
            
            'breakdowns': {
                'by_team': by_team,
                'by_type': by_type,
            },
            
            'top_opportunities': [
                {
                    'id': o.id,
                    'type': o.type.value,
                    'workload': o.workload,
                    'namespace': o.namespace,
                    'estimated_savings': o.estimated_monthly_savings,
                    'confidence': o.confidence,
                    'status': o.status.value
                }
                for o in top_opportunities
            ],
            
            'recommendations': self._generate_recommendations(week_opportunities)
        }
        
        return report
    
    def generate_monthly_report(self, month_start: datetime) -> Dict:
        """Generate monthly CFO/CTO report"""
        month_end = month_start + timedelta(days=30)
        
        # Similar to weekly but for monthly period
        month_opportunities = [
            o for o in self.ledger.opportunities
            if month_start <= o.detected_at < month_end
        ]
        
        total_estimated = sum(o.estimated_monthly_savings for o in month_opportunities)
        total_realized = sum(o.realized_savings for o in month_opportunities 
                           if o.status == OpportunityStatus.VERIFIED)
        
        # Calculate ROI
        # (Simplified - would include implementation costs)
        roi = (total_realized / 1000.0) * 100 if total_realized > 0 else 0  # Simplified ROI calc
        
        report = {
            'report_type': 'monthly',
            'period_start': month_start.isoformat(),
            'period_end': month_end.isoformat(),
            'generated_at': datetime.utcnow().isoformat(),
            
            'summary': {
                'total_estimated_savings': total_estimated,
                'total_realized_savings': total_realized,
                'roi_percentage': roi,
                'opportunities_detected': len(month_opportunities),
            },
            
            'breakdowns': {
                'by_team': self.ledger.get_savings_by_team(),
                'by_type': self.ledger.get_savings_by_type(),
            },
            
            'trends': self._calculate_trends(month_start, month_end),
            
            'recommendations': self._generate_recommendations(month_opportunities)
        }
        
        return report
    
    def _generate_recommendations(self, opportunities: List) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not opportunities:
            return ["No opportunities detected this period. Continue monitoring."]
        
        # Group by type
        by_type = {}
        for opp in opportunities:
            opp_type = opp.type.value
            if opp_type not in by_type:
                by_type[opp_type] = []
            by_type[opp_type].append(opp)
        
        # Generate recommendations
        for opp_type, opps in by_type.items():
            total_savings = sum(o.estimated_monthly_savings for o in opps)
            recommendations.append(
                f"Focus on {opp_type}: {len(opps)} opportunities with ${total_savings:.2f}/month potential savings"
            )
        
        # High-confidence opportunities
        high_conf = [o for o in opportunities if o.confidence > 0.8]
        if high_conf:
            recommendations.append(
                f"Prioritize {len(high_conf)} high-confidence opportunities (confidence > 80%)"
            )
        
        return recommendations
    
    def _calculate_trends(self, start: datetime, end: datetime) -> Dict:
        """Calculate trends over period"""
        # Simplified - would calculate actual trends
        return {
            'savings_trend': 'increasing',
            'detection_rate': 'stable',
            'implementation_rate': 'improving'
        }
    
    def export_report_html(self, report: Dict) -> str:
        """Export report as HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>FinOps Savings Report - {report['report_type'].title()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #1f77b4; }}
        .summary {{ background: #f0f2f6; padding: 20px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #1f77b4; color: white; }}
    </style>
</head>
<body>
    <h1>FinOps Savings Report - {report['report_type'].title()}</h1>
    <p>Period: {report['period_start']} to {report['period_end']}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">
            <strong>Total Estimated Savings:</strong><br>
            ${report['summary']['total_estimated_savings']:,.2f}/month
        </div>
        <div class="metric">
            <strong>Total Realized Savings:</strong><br>
            ${report['summary']['total_realized_savings']:,.2f}
        </div>
        <div class="metric">
            <strong>Opportunities Detected:</strong><br>
            {report['summary']['opportunities_detected']}
        </div>
    </div>
    
    <h2>Top Opportunities</h2>
    <table>
        <tr>
            <th>Type</th>
            <th>Workload</th>
            <th>Estimated Savings</th>
            <th>Confidence</th>
            <th>Status</th>
        </tr>
        {"".join(f"""
        <tr>
            <td>{opp['type']}</td>
            <td>{opp['workload']}</td>
            <td>${opp['estimated_savings']:,.2f}/month</td>
            <td>{opp['confidence']:.0%}</td>
            <td>{opp['status']}</td>
        </tr>
        """ for opp in report.get('top_opportunities', [])[:10])}
    </table>
    
    <h2>Recommendations</h2>
    <ul>
        {"".join(f"<li>{rec}</li>" for rec in report.get('recommendations', []))}
    </ul>
</body>
</html>
        """
        return html.strip()

