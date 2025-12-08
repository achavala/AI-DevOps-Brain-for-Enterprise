# 🔧 Quick Fix - UI Database Connection

## Issue
The UI was failing to connect to PostgreSQL because the password was incorrect.

## Solution

The PostgreSQL container uses password `finance123` (from docker-compose), not `postgres`.

## Fixed Files

1. **`ai-operator/ui/run.sh`** - Updated default password to `finance123`
2. **`ai-operator/ui/app.py`** - Updated default password to `finance123`
3. **`scripts/setup-db-for-ui.sh`** - Created helper script to setup database

## Quick Start

```bash
# 1. Setup database (if not already done)
./scripts/setup-db-for-ui.sh

# 2. Start UI
./scripts/start-ui.sh

# 3. Open browser
# http://localhost:8504
```

## Environment Variables

You can override the password if needed:

```bash
export POSTGRES_PASSWORD=finance123
./scripts/start-ui.sh
```

## Verification

Check database connection:

```bash
export PGPASSWORD=finance123
psql -h localhost -p 5433 -U postgres -d devops_brain -c "SELECT COUNT(*) FROM incidents;"
```

## Status

✅ Database setup script created
✅ UI password configuration fixed
✅ Connection handling improved

The UI should now start successfully!

