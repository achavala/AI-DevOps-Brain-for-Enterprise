#!/usr/bin/env python3
"""
Print recent incidents from the database in a formatted way
"""

import os
import sys
import psycopg2
from datetime import datetime
from tabulate import tabulate

def get_incidents(limit=10):
    """Get recent incidents from database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5433'),
            database=os.getenv('POSTGRES_DB', 'devops_brain'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres')
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                namespace,
                service,
                severity,
                anomaly_type,
                detected_at,
                status,
                root_cause,
                remediation
            FROM incidents
            ORDER BY detected_at DESC
            LIMIT %s
        """, (limit,))
        
        incidents = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return incidents
    except Exception as e:
        print(f"❌ Error connecting to database: {e}", file=sys.stderr)
        return None

def format_incidents(incidents):
    """Format incidents for display"""
    if not incidents:
        return []
    
    formatted = []
    for inc in incidents:
        id_short = inc[0][:20] + "..." if len(inc[0]) > 20 else inc[0]
        detected = inc[5].strftime("%Y-%m-%d %H:%M:%S") if inc[5] else "N/A"
        root_cause = (inc[7][:50] + "...") if inc[7] and len(inc[7]) > 50 else (inc[7] or "N/A")
        remediation = (inc[8][:50] + "...") if inc[8] and len(inc[8]) > 50 else (inc[8] or "N/A")
        
        formatted.append([
            id_short,
            inc[1],  # namespace
            inc[2],   # service
            inc[3],   # severity
            inc[4],   # anomaly_type
            detected,
            inc[6],   # status
            root_cause,
            remediation
        ])
    
    return formatted

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print("📋 Recent Incidents")
    print("=" * 100)
    print()
    
    incidents = get_incidents(limit)
    
    if incidents is None:
        print("❌ Could not retrieve incidents. Check database connection.")
        sys.exit(1)
    
    if not incidents:
        print("✅ No incidents found in database.")
        print()
        print("To generate incidents:")
        print("  1. Run: ./scripts/run-demo-scenario.sh")
        print("  2. Or: ./scripts/chaos-advanced.sh <namespace> <experiment>")
        sys.exit(0)
    
    formatted = format_incidents(incidents)
    
    headers = [
        "ID",
        "Namespace",
        "Service",
        "Severity",
        "Type",
        "Detected At",
        "Status",
        "Root Cause",
        "Remediation"
    ]
    
    print(tabulate(formatted, headers=headers, tablefmt="grid"))
    print()
    print(f"Total incidents shown: {len(incidents)}")
    print()

if __name__ == "__main__":
    main()

