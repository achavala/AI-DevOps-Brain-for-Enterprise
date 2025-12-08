-- AI DevOps Brain Database Schema

CREATE DATABASE IF NOT EXISTS devops_brain;

\c devops_brain;

-- Incidents table with structured data support
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(255) PRIMARY KEY,
    namespace VARCHAR(100) NOT NULL,
    service VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    detected_at TIMESTAMP NOT NULL,
    description TEXT,
    root_cause TEXT,
    remediation TEXT,
    status VARCHAR(20) DEFAULT 'open',
    structured_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_incidents_namespace ON incidents(namespace);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_detected_at ON incidents(detected_at);

-- Anomalies table
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    namespace VARCHAR(100) NOT NULL,
    metric VARCHAR(100) NOT NULL,
    value FLOAT NOT NULL,
    threshold FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    severity VARCHAR(20) NOT NULL,
    incident_id VARCHAR(255) REFERENCES incidents(id)
);

CREATE INDEX idx_anomalies_namespace ON anomalies(namespace);
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp);

-- Remediations table
CREATE TABLE IF NOT EXISTS remediations (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(255) REFERENCES incidents(id),
    action_type VARCHAR(100) NOT NULL,
    action_details JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    executed_at TIMESTAMP,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_remediations_incident ON remediations(incident_id);
CREATE INDEX idx_remediations_status ON remediations(status);

