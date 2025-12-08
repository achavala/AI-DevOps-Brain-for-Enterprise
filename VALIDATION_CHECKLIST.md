# ✅ Validation Checklist - Production-Ready Demo

## Overview

This checklist validates that your AI DevOps Brain platform works end-to-end and is ready for demos and production use.

## ✅ Checklist Items

### A. AI Operator Receives Live Data

#### A1. Database Setup
```bash
# Create schema
psql -h localhost -p 5433 -U postgres -f ai-operator/k8s/db-schema.sql

# Verify tables exist
psql -h localhost -p 5433 -U postgres -d devops_brain -c "\dt"
```

**Expected**: Tables `incidents`, `anomalies`, `remediations` exist

#### A2. Deploy AI Operator
```bash
kubectl apply -f ai-operator/k8s/deployment.yaml

# Check pod status
kubectl get pods -l app=ai-operator

# Check logs
kubectl logs -l app=ai-operator --tail=50
```

**Expected Logs**:
- ✅ "Connected to Postgres" (or warning if DB unavailable)
- ✅ "Subscribed to Kafka topics" (or warning if Kafka unavailable)
- ✅ "Watching namespaces: [...]" (list of 19 namespaces)
- ✅ "AI DevOps Brain Operator starting..."

**If missing**: Check environment variables, service connectivity

---

### B. Full Chaos → Incident → RCA Flow

#### B1. Start Observability Pipeline
```bash
# Run in background
python3 observability/pipeline.py > /tmp/observability.log 2>&1 &

# Check it's running
ps aux | grep observability/pipeline.py
```

**Expected**: Process running, no errors in log

#### B2. Generate Baseline Traffic
```bash
# All industries (5 minutes, 2 req/s each)
./scripts/load-traffic-all.sh 300 2

# Or single industry
./scripts/load-traffic.sh finance 60 5
```

**Expected**: Traffic logs show successful requests

#### B3. Trigger Controlled Chaos
```bash
# CPU stress in finance
./scripts/chaos-advanced.sh finance cpu

# Wait 30 seconds, then check
kubectl get pods -n finance
```

**Expected**: 
- Pods show CPU stress
- Operator logs show detection

#### B4. Verify Detection Chain
```bash
# Watch operator logs
kubectl logs -l app=ai-operator -f | grep -i finance
```

**Expected Chain**:
1. ✅ "Anomaly detected: finance / cpu_saturation / deployment=finance-sim"
2. ✅ "RCA: suspected root cause = finance-sim, node=X"
3. ✅ "Remediation suggestion: scale up / restart / throttle load"
4. ✅ "Incident stored: finance-..."

#### B5. Verify Database Storage
```bash
# Query incidents
psql -h localhost -p 5433 -U postgres -d devops_brain -c "
    SELECT 
        id, namespace, severity, anomaly_type, 
        detected_at, status, confidence
    FROM incidents 
    ORDER BY detected_at DESC 
    LIMIT 5;
"
```

**Expected**:
- ✅ Incident records present
- ✅ Namespace = "finance"
- ✅ Anomaly type = "cpu_saturation" or similar
- ✅ Structured data includes confidence, signals, suggested_actions

**If missing**: Check operator logs for errors, verify DB connection

---

### C. Guardrails for Auto-Remediation

#### C1. Verify Suggestions Are Manual
```bash
# Check incident remediation field
psql -h localhost -p 5433 -U postgres -d devops_brain -c "
    SELECT remediation, structured_data->'suggested_actions' as actions
    FROM incidents 
    ORDER BY detected_at DESC 
    LIMIT 1;
"
```

**Expected**:
- ✅ Remediation is a suggestion, not an action
- ✅ Suggested actions have confidence scores
- ✅ No automatic scaling/restarting happened

#### C2. Test Dry-Run Mode (Future)
When implementing auto-actions:
- ✅ Add `DRY_RUN=true` environment variable
- ✅ Log actions instead of executing
- ✅ Rate limiting (max X changes per hour)
- ✅ Safety checks (don't scale failing services)

---

### D. Demo Scenario Validation

#### D1. Run Complete Demo
```bash
./scripts/run-demo-scenario.sh
```

**Expected Output**:
- ✅ All 19 industries deployed
- ✅ AI Operator running
- ✅ Observability pipeline active
- ✅ Traffic generated
- ✅ Chaos events triggered
- ✅ Incidents detected and stored
- ✅ Results displayed

#### D2. Verify Results
```bash
# View recent incidents
python3 ai-operator/tools/print_recent_incidents.py

# Check operator logs
kubectl logs -l app=ai-operator --tail=50

# Check database
psql -h localhost -p 5433 -U postgres -d devops_brain -c "
    SELECT COUNT(*) as total_incidents FROM incidents;
"
```

**Expected**:
- ✅ Multiple incidents from different namespaces
- ✅ Structured data with confidence scores
- ✅ Industry-specific patterns detected
- ✅ Suggested actions present

---

### E. Industry-Specific Patterns

#### E1. Test Semiconductor Pattern
```bash
./scripts/chaos-advanced.sh semiconductor memory

# Check incident
python3 ai-operator/tools/print_recent_incidents.py | grep semiconductor
```

**Expected**:
- ✅ Pattern = "wafer_yield_drop_like" or similar
- ✅ Pattern source = "semiconductor_ruleset_v1"
- ✅ Industry = "semiconductor"

#### E2. Test AI Cloud Pattern
```bash
./scripts/chaos-advanced.sh aicloud pod-kill

# Check incident
python3 ai-operator/tools/print_recent_incidents.py | grep aicloud
```

**Expected**:
- ✅ Pattern = "gpu_allocation_failure" or "model_overload"
- ✅ Pattern source = "aicloud_ruleset_v1"
- ✅ Suggested actions include scaling

---

### F. Structured Output Validation

#### F1. Check Incident Structure
```bash
psql -h localhost -p 5433 -U postgres -d devops_brain -c "
    SELECT 
        id,
        namespace,
        structured_data->'confidence' as confidence,
        structured_data->'signals' as signals,
        structured_data->'pattern' as pattern,
        structured_data->'suggested_actions' as actions
    FROM incidents 
    ORDER BY detected_at DESC 
    LIMIT 1;
"
```

**Expected JSON Structure**:
```json
{
  "confidence": 0.75,
  "signals": ["pod_failed", "container_crashed"],
  "pattern": "wafer_yield_drop_like",
  "suggested_actions": [
    {
      "type": "scale_up",
      "target": "semiconductor-sim",
      "params": {"replicas": 3},
      "confidence": 0.675
    }
  ]
}
```

---

## 🎯 Success Criteria

### Minimum (Demo-Ready)
- ✅ AI Operator deploys and connects to services
- ✅ At least 1 chaos event → incident → RCA flow works
- ✅ Incidents stored in database with structured data
- ✅ Industry-specific patterns detected
- ✅ Demo scenario script runs end-to-end

### Production-Ready
- ✅ All 19 industries monitored
- ✅ Multiple chaos types trigger incidents
- ✅ Confidence scores and "needs_human_review" status
- ✅ Structured outputs queryable from database
- ✅ Guardrails prevent automatic actions
- ✅ Dashboard shows incidents in real-time

---

## 🚀 Quick Validation Command

Run this single command to validate everything:

```bash
./scripts/run-demo-scenario.sh && \
python3 ai-operator/tools/print_recent_incidents.py && \
echo "✅ Validation complete!"
```

---

## 📊 Expected Metrics

After running demo scenario:

- **Incidents**: 5-10 incidents from chaos events
- **Namespaces**: At least 3-5 different namespaces
- **Patterns**: Industry-specific patterns detected
- **Confidence**: Scores between 0.3-0.95
- **Actions**: Suggested actions for each incident

---

## 🔧 Troubleshooting

### Operator Not Detecting Incidents
1. Check operator logs: `kubectl logs -l app=ai-operator`
2. Verify pod events: `kubectl get events --sort-by='.lastTimestamp'`
3. Check namespace labels: `kubectl get pods -n finance --show-labels`

### Database Connection Issues
1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check connection: `psql -h localhost -p 5433 -U postgres -c "SELECT 1"`
3. Review operator env vars: `kubectl get deployment ai-operator -o yaml | grep -A 10 env`

### No Structured Data
1. Verify schema: `psql -h localhost -p 5433 -U postgres -d devops_brain -c "\d incidents"`
2. Check operator version (should have structured fields)
3. Review incident creation code

---

## ✅ Checklist Status

- [ ] A1. Database schema created
- [ ] A2. AI Operator deployed and logging
- [ ] B1. Observability pipeline running
- [ ] B2. Traffic generation working
- [ ] B3. Chaos events trigger incidents
- [ ] B4. Detection chain verified
- [ ] B5. Database storage confirmed
- [ ] C1. Manual suggestions verified
- [ ] D1. Demo scenario runs successfully
- [ ] D2. Results validated
- [ ] E1. Semiconductor pattern detected
- [ ] E2. AI Cloud pattern detected
- [ ] F1. Structured output validated

**Status**: Run `./scripts/run-demo-scenario.sh` to validate all items!

