#!/usr/bin/env python3
"""
AI DevOps Brain - Web UI
Streamlit-based dashboard for monitoring incidents, RCA, and remediations
"""

import streamlit as st
import psycopg2
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Page config
st.set_page_config(
    page_title="AI DevOps Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .incident-card {
        border-left: 4px solid;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .severity-high {
        border-color: #dc3545;
        background-color: #fff5f5;
    }
    .severity-medium {
        border-color: #ffc107;
        background-color: #fffbf0;
    }
    .severity-low {
        border-color: #28a745;
        background-color: #f0fff4;
    }
</style>
""", unsafe_allow_html=True)

# Create engine once per process (singleton pattern)
@st.cache_resource
def get_db_engine():
    """Get SQLAlchemy database engine (cached per Streamlit session)"""
    try:
        # Use DB_URL if set, otherwise construct from individual env vars
        db_url = os.getenv('DB_URL')
        if not db_url:
            db_url = (
                f"postgresql+psycopg2://{os.getenv('POSTGRES_USER', 'postgres')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'finance123')}@"
                f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
                f"{os.getenv('POSTGRES_PORT', '5433')}/"
                f"{os.getenv('POSTGRES_DB', 'devops_brain')}"
            )
        
        # Use NullPool to avoid connection reuse issues
        # future=True for SQLAlchemy 2.0 style
        engine = create_engine(
            db_url,
            poolclass=NullPool,
            connect_args={"connect_timeout": 5},
            future=True
        )
        return engine
    except Exception as e:
        return None

def get_recent_incidents(limit: int = 50, namespace: Optional[str] = None) -> pd.DataFrame:
    """Get recent incidents from database"""
    engine = None
    try:
        engine = get_db_engine()
        if not engine:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'id', 'namespace', 'service', 'severity', 'anomaly_type',
                'detected_at', 'status', 'root_cause', 'remediation', 'structured_data'
            ])
        
        query = """
            SELECT 
                id,
                namespace,
                service,
                severity,
                anomaly_type,
                detected_at,
                status,
                root_cause,
                remediation,
                structured_data
            FROM incidents
        """
        
        conditions = []
        params = {}
        
        if namespace:
            conditions.append("namespace = :namespace")
            params['namespace'] = namespace
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY detected_at DESC LIMIT :limit"
        params['limit'] = limit
        
        # Use engine.connect() for proper connection lifecycle
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        
        # Parse structured data
        if 'structured_data' in df.columns and not df.empty:
            df['confidence'] = df['structured_data'].apply(
                lambda x: x.get('confidence', 0.0) if isinstance(x, dict) else (json.loads(x).get('confidence', 0.0) if isinstance(x, str) else 0.0)
            )
            df['signals'] = df['structured_data'].apply(
                lambda x: ', '.join(x.get('signals', [])) if isinstance(x, dict) else (', '.join(json.loads(x).get('signals', [])) if isinstance(x, str) else 'N/A')
            )
            df['pattern'] = df['structured_data'].apply(
                lambda x: x.get('pattern', 'N/A') if isinstance(x, dict) else (json.loads(x).get('pattern', 'N/A') if isinstance(x, str) else 'N/A')
            )
            df['industry'] = df['structured_data'].apply(
                lambda x: x.get('industry', df['namespace']) if isinstance(x, dict) else (json.loads(x).get('industry', df['namespace']) if isinstance(x, str) else df['namespace'])
            )
            df['suggested_actions'] = df['structured_data'].apply(
                lambda x: x.get('suggested_actions', []) if isinstance(x, dict) else (json.loads(x).get('suggested_actions', []) if isinstance(x, str) else [])
            )
        
        return df
    except Exception as e:
        st.error(f"Error fetching incidents: {e}")
        return pd.DataFrame(columns=[
            'id', 'namespace', 'service', 'severity', 'anomaly_type',
            'detected_at', 'status', 'root_cause', 'remediation', 'structured_data'
        ])
    # No need to dispose engine - it's cached and reused

def get_incident_stats() -> Dict:
    """Get incident statistics"""
    engine = None
    try:
        engine = get_db_engine()
        if not engine:
            return {
                'total': 0,
                'by_severity': {},
                'by_namespace': {},
                'by_status': {},
                'recent_24h': 0,
                'avg_confidence': 0.0
            }
        
        with engine.connect() as conn:
            # Total incidents
            result = conn.execute(text("SELECT COUNT(*) FROM incidents"))
            total = result.scalar() or 0
            
            # By severity
            result = conn.execute(text("""
                SELECT severity, COUNT(*) 
                FROM incidents 
                GROUP BY severity
            """))
            by_severity = dict(result.fetchall())
            
            # By namespace
            result = conn.execute(text("""
                SELECT namespace, COUNT(*) 
                FROM incidents 
                GROUP BY namespace
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """))
            by_namespace = dict(result.fetchall())
            
            # By status
            result = conn.execute(text("""
                SELECT status, COUNT(*) 
                FROM incidents 
                GROUP BY status
            """))
            by_status = dict(result.fetchall())
            
            # Recent (last 24 hours)
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM incidents 
                WHERE detected_at > NOW() - INTERVAL '24 hours'
            """))
            recent_24h = result.scalar() or 0
            
            # Average confidence
            result = conn.execute(text("""
                SELECT AVG((structured_data->>'confidence')::float)
                FROM incidents
                WHERE structured_data->>'confidence' IS NOT NULL
            """))
            avg_confidence = result.scalar() or 0.0
        
        return {
            'total': total,
            'by_severity': by_severity,
            'by_namespace': by_namespace,
            'by_status': by_status,
            'recent_24h': recent_24h,
            'avg_confidence': float(avg_confidence)
        }
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {
            'total': 0,
            'by_severity': {},
            'by_namespace': {},
            'by_status': {},
            'recent_24h': 0,
            'avg_confidence': 0.0
        }
    # No need to dispose engine - it's cached and reused

def render_incident_card(incident: pd.Series):
    """Render a single incident card"""
    severity = incident.get('severity', 'low').lower()
    severity_class = f"severity-{severity}"
    
    confidence = incident.get('confidence', 0.0)
    confidence_color = 'green' if confidence > 0.7 else 'orange' if confidence > 0.4 else 'red'
    
    st.markdown(f"""
    <div class="incident-card {severity_class}">
        <h4>{incident.get('service', 'Unknown')} - {incident.get('namespace', 'Unknown')}</h4>
        <p><strong>Type:</strong> {incident.get('anomaly_type', 'N/A')} | 
           <strong>Severity:</strong> {incident.get('severity', 'N/A')} | 
           <strong>Confidence:</strong> <span style="color: {confidence_color}">{confidence:.2f}</span></p>
        <p><strong>Detected:</strong> {incident.get('detected_at', 'N/A')}</p>
        <p><strong>Root Cause:</strong> {incident.get('root_cause', 'N/A')[:200]}...</p>
        <p><strong>Remediation:</strong> {incident.get('remediation', 'N/A')[:200]}...</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">🧠 AI DevOps Brain - Enterprise Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Namespace filter
        namespaces = ['All'] + [
            'finance', 'healthcare', 'automotive', 'retail', 'logistics',
            'energy', 'telecom', 'banking', 'insurance', 'manufacturing',
            'gov', 'education', 'cloud', 'media', 'aiplatform',
            'semiconductor', 'aicloud', 'gpucloud', 'socialmedia'
        ]
        selected_namespace = st.selectbox("Namespace", namespaces)
        
        # Severity filter
        severities = ['All', 'high', 'medium', 'low']
        selected_severity = st.selectbox("Severity", severities)
        
        # Status filter
        statuses = ['All', 'open', 'resolved', 'investigating']
        selected_status = st.selectbox("Status", statuses)
        
        # Limit
        limit = st.slider("Number of incidents", 10, 100, 50)
        
        st.divider()
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        # Links
        st.markdown("### 🔗 Quick Links")
        st.markdown("- [Grafana](http://localhost:3000)")
        st.markdown("- [Minikube Dashboard](http://localhost:8001)")
        st.markdown("- [Kubernetes API](http://localhost:8080)")
    
    # Get data
    namespace_filter = None if selected_namespace == 'All' else selected_namespace
    incidents_df = get_recent_incidents(limit=limit, namespace=namespace_filter)
    
    # Apply filters
    if not incidents_df.empty:
        if selected_severity != 'All':
            incidents_df = incidents_df[incidents_df['severity'].str.lower() == selected_severity.lower()]
        if selected_status != 'All':
            incidents_df = incidents_df[incidents_df['status'].str.lower() == selected_status.lower()]
    
    # Statistics
    stats = get_incident_stats()
    
    # Top metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Incidents", stats.get('total', 0))
    
    with col2:
        st.metric("Last 24h", stats.get('recent_24h', 0))
    
    with col3:
        high_count = stats.get('by_severity', {}).get('high', 0)
        st.metric("High Severity", high_count, delta=None)
    
    with col4:
        open_count = stats.get('by_status', {}).get('open', 0)
        st.metric("Open", open_count)
    
    with col5:
        avg_conf = stats.get('avg_confidence', 0.0)
        st.metric("Avg Confidence", f"{avg_conf:.2f}")
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Incidents by Severity")
        if stats.get('by_severity'):
            severity_df = pd.DataFrame(list(stats['by_severity'].items()), columns=['Severity', 'Count'])
            fig = px.pie(severity_df, values='Count', names='Severity', 
                        color_discrete_map={'high': '#dc3545', 'medium': '#ffc107', 'low': '#28a745'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("📈 Incidents by Namespace")
        if stats.get('by_namespace'):
            namespace_df = pd.DataFrame(list(stats['by_namespace'].items()), columns=['Namespace', 'Count'])
            fig = px.bar(namespace_df, x='Namespace', y='Count', 
                        color='Count', color_continuous_scale='Reds')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    st.divider()
    
    # Incidents table
    st.subheader("📋 Recent Incidents")
    
    if not incidents_df.empty:
        # Display options
        view_mode = st.radio("View Mode", ["Table", "Cards"], horizontal=True)
        
        if view_mode == "Table":
            # Prepare table data
            display_df = incidents_df[[
                'namespace', 'service', 'severity', 'anomaly_type', 
                'detected_at', 'status', 'confidence'
            ]].copy()
            
            # Format confidence
            display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            # Card view
            for idx, incident in incidents_df.iterrows():
                render_incident_card(incident)
        
            # Detailed view
            st.divider()
            st.subheader("🔍 Incident Details")
            
            if not incidents_df.empty:
                try:
                    selected_idx = st.selectbox(
                        "Select incident to view details",
                        range(len(incidents_df)),
                        format_func=lambda x: f"{incidents_df.iloc[x]['namespace']} - {incidents_df.iloc[x]['service']} - {str(incidents_df.iloc[x]['detected_at'])[:19]}"
                    )
                    
                    selected_incident = incidents_df.iloc[selected_idx]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Basic Information")
                        st.json({
                            "ID": str(selected_incident.get('id', 'N/A')),
                            "Namespace": str(selected_incident.get('namespace', 'N/A')),
                            "Service": str(selected_incident.get('service', 'N/A')),
                            "Severity": str(selected_incident.get('severity', 'N/A')),
                            "Type": str(selected_incident.get('anomaly_type', 'N/A')),
                            "Status": str(selected_incident.get('status', 'N/A')),
                            "Detected At": str(selected_incident.get('detected_at', 'N/A'))
                        })
                    
                    with col2:
                        st.markdown("### Structured Data")
                        structured = selected_incident.get('structured_data', {})
                        if isinstance(structured, str):
                            try:
                                structured = json.loads(structured)
                            except:
                                structured = {}
                        elif structured is None:
                            structured = {}
                        
                        st.json(structured)
                    
                    st.markdown("### Root Cause Analysis")
                    root_cause = selected_incident.get('root_cause', 'N/A')
                    if root_cause and root_cause != 'N/A':
                        st.info(str(root_cause))
                    else:
                        st.info("No root cause analysis available")
                    
                    st.markdown("### Remediation")
                    remediation = selected_incident.get('remediation', 'N/A')
                    if remediation and remediation != 'N/A':
                        st.success(str(remediation))
                    else:
                        st.info("No remediation suggestion available")
                    
                    # Suggested actions
                    suggested_actions = selected_incident.get('suggested_actions', [])
                    if suggested_actions and len(suggested_actions) > 0:
                        st.markdown("### Suggested Actions")
                        for i, action in enumerate(suggested_actions, 1):
                            if isinstance(action, dict):
                                with st.expander(f"Action {i}: {action.get('type', 'unknown')}"):
                                    st.json(action)
                except Exception as e:
                    st.warning(f"Error displaying incident details: {e}")
    else:
        st.info("No incidents found. Run the demo scenario to generate incidents:")
        st.code("./scripts/run-demo-scenario.sh")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        AI DevOps Brain for Enterprise | Built with Streamlit
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

