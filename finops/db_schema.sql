-- FinOps Savings Ledger Database Schema

CREATE DATABASE IF NOT EXISTS finops_brain;

\c finops_brain;

-- Cost Baselines Table
CREATE TABLE IF NOT EXISTS cost_baselines (
    id SERIAL PRIMARY KEY,
    workload_id VARCHAR(255) NOT NULL,
    namespace VARCHAR(100) NOT NULL,
    cluster VARCHAR(100) NOT NULL,
    team VARCHAR(100) NOT NULL,
    monthly_cost DECIMAL(12, 2) NOT NULL,
    cpu_cost DECIMAL(12, 2) DEFAULT 0.0,
    memory_cost DECIMAL(12, 2) DEFAULT 0.0,
    storage_cost DECIMAL(12, 2) DEFAULT 0.0,
    network_cost DECIMAL(12, 2) DEFAULT 0.0,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workload_id, period_start, period_end)
);

CREATE INDEX idx_baselines_cluster ON cost_baselines(cluster);
CREATE INDEX idx_baselines_namespace ON cost_baselines(namespace);
CREATE INDEX idx_baselines_team ON cost_baselines(team);
CREATE INDEX idx_baselines_period ON cost_baselines(period_start, period_end);

-- Opportunities Table
CREATE TABLE IF NOT EXISTS opportunities (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'detected',
    detected_at TIMESTAMP NOT NULL,
    
    -- Attribution
    cluster VARCHAR(100) NOT NULL,
    namespace VARCHAR(100) NOT NULL,
    workload VARCHAR(255) NOT NULL,
    team VARCHAR(100) NOT NULL,
    
    -- Impact
    estimated_monthly_savings DECIMAL(12, 2) NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    risk_score DECIMAL(3, 2) NOT NULL CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    
    -- Evidence
    evidence JSONB NOT NULL,
    before_state JSONB NOT NULL,
    after_state JSONB NOT NULL,
    
    -- Action
    pr_url VARCHAR(500),
    pr_number INTEGER,
    implemented_at TIMESTAMP,
    verified_at TIMESTAMP,
    
    -- Tracking
    realized_savings DECIMAL(12, 2) DEFAULT 0.0,
    rollback_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_opp_status ON opportunities(status);
CREATE INDEX idx_opp_cluster ON opportunities(cluster);
CREATE INDEX idx_opp_team ON opportunities(team);
CREATE INDEX idx_opp_type ON opportunities(type);
CREATE INDEX idx_opp_detected ON opportunities(detected_at);

-- Cost Allocation Table
CREATE TABLE IF NOT EXISTS cost_allocation (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    cluster VARCHAR(100) NOT NULL,
    namespace VARCHAR(100) NOT NULL,
    workload VARCHAR(255) NOT NULL,
    team VARCHAR(100) NOT NULL,
    
    -- Cost breakdown
    total_cost DECIMAL(12, 2) NOT NULL,
    compute_cost DECIMAL(12, 2) DEFAULT 0.0,
    storage_cost DECIMAL(12, 2) DEFAULT 0.0,
    network_cost DECIMAL(12, 2) DEFAULT 0.0,
    other_cost DECIMAL(12, 2) DEFAULT 0.0,
    
    -- Resource usage
    cpu_hours DECIMAL(12, 2),
    memory_gb_hours DECIMAL(12, 2),
    storage_gb DECIMAL(12, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, cluster, namespace, workload)
);

CREATE INDEX idx_allocation_date ON cost_allocation(date);
CREATE INDEX idx_allocation_cluster ON cost_allocation(cluster);
CREATE INDEX idx_allocation_team ON cost_allocation(team);

-- Savings Reports Table
CREATE TABLE IF NOT EXISTS savings_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    report_type VARCHAR(20) NOT NULL, -- 'weekly', 'monthly', 'quarterly'
    
    -- Summary
    total_estimated_savings DECIMAL(12, 2) NOT NULL,
    total_realized_savings DECIMAL(12, 2) NOT NULL,
    opportunities_detected INTEGER NOT NULL,
    opportunities_implemented INTEGER NOT NULL,
    opportunities_verified INTEGER NOT NULL,
    
    -- Breakdowns
    savings_by_team JSONB,
    savings_by_type JSONB,
    savings_by_cluster JSONB,
    
    -- Report data
    report_data JSONB NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(report_date, report_type)
);

CREATE INDEX idx_reports_date ON savings_reports(report_date);
CREATE INDEX idx_reports_type ON savings_reports(report_type);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45)
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_user ON audit_log(user);
CREATE INDEX idx_audit_action ON audit_log(action);

