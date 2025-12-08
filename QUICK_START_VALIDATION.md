# ✅ Quick Start - Validation Phase

## 🎯 Goal: Validate End-to-End Platform

Run these 3 commands in order to validate your entire platform.

---

## Step 1: Test Database Health

```bash
./scripts/test-ui-db.sh
```

**Expected Output:**
```
✅ PostgreSQL container is running
✅ Database connection successful
✅ incidents table exists
   📊 Total incidents: X
✅ All database checks passed!
```

**If errors:** Check PostgreSQL is running: `docker ps | grep postgres`

---

## Step 2: Start Web UI

```bash
./scripts/start-ui.sh
```

**Expected:**
- No SQLAlchemy warnings
- No DB connection errors
- UI starts on http://localhost:8504
- Incidents page loads (may be empty)

**Verify:**
- Open http://localhost:8504
- Check sidebar filters work
- Verify no error messages

---

## Step 3: Run Demo Scenario

```bash
./scripts/run-demo-scenario.sh
```

**This will:**
1. Deploy all 19 industries (if not already)
2. Start observability pipeline
3. Deploy AI Operator
4. Generate traffic
5. Trigger chaos events
6. Display results

**Expected Output:**
- Incidents created in database
- AI Operator detects issues
- RCA analysis performed
- Suggested actions generated

**Verify in UI:**
- Refresh http://localhost:8504
- Should see incidents in table
- Check confidence scores
- View structured data

---

## ✅ Validation Checklist

After running all 3 steps:

- [ ] Database connection works
- [ ] UI loads without errors
- [ ] No SQLAlchemy warnings
- [ ] Incidents appear in UI
- [ ] Filters work correctly
- [ ] Incident details display
- [ ] Charts render
- [ ] Structured data visible

**If all checked:** ✅ **PLATFORM VALIDATED**

---

## 🔧 Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL
docker ps | grep postgres

# Restart if needed
./scripts/setup-local-services.sh
./scripts/setup-db-for-ui.sh
```

### UI Not Loading
```bash
# Check port
lsof -i :8504

# Restart UI
./scripts/start-ui.sh
```

### No Incidents Generated
```bash
# Manually trigger chaos
./scripts/chaos-advanced.sh finance cpu

# Check operator logs
kubectl logs -l app=ai-operator --tail=50
```

---

## 🚀 Next Steps After Validation

Once validated:
1. Generate more incidents
2. Test all UI paths
3. Integrate AI models
4. Deploy observability stack

See `REFINED_ROADMAP.md` for full roadmap.

