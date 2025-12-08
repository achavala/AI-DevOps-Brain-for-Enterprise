# ✅ Port Conflicts Fixed

## Issue

Port 5432 was already in use by another container (`dicer-db-1` from another project).

## Solution

Updated `scripts/setup-local-services.sh` to:
1. ✅ **Detect port conflicts** automatically
2. ✅ **Use alternative ports** when conflicts occur
3. ✅ **Clean up old containers** before starting new ones
4. ✅ **Show clear warnings** about port changes

## Port Mappings

### Default Ports (if available):
- PostgreSQL: `5432`
- Redis: `6379`
- Kafka: `9092`
- MinIO: `9000` (API), `9001` (Console)
- Zookeeper: `2181`

### Alternative Ports (if conflicts):
- PostgreSQL: `5433`
- Redis: `6380`
- Kafka: `9093`
- MinIO: `9010` (API), `9011` (Console)
- Zookeeper: `2182`

## Current Setup

Based on your system:
- ✅ **PostgreSQL**: Port `5433` (5432 was in use)
- ✅ **Redis**: Port `6379` (available)
- ✅ **Kafka**: Port `9092` (available)
- ✅ **MinIO**: Ports `9000/9001` (available)

## Configuration Update

I've updated `config/local.yaml` to use port `5433` for PostgreSQL.

If you need to use different ports, update:
```yaml
# config/local.yaml
database:
  port: 5433  # Change if needed
  local_port: 5433
```

## Check Port Usage

To see what ports are in use:
```bash
./scripts/check-ports.sh
```

## Services Status

All services should now be running:
- ✅ PostgreSQL (port 5433)
- ✅ Redis (port 6379)
- ✅ Kafka (port 9092)
- ✅ MinIO (ports 9000/9001)

## Next Steps

1. **Verify services**:
   ```bash
   ./scripts/trading-heartbeat.sh
   ```

2. **Deploy platform**:
   ```bash
   ./scripts/deploy-platform-local.sh
   ```

3. **Run smoke tests**:
   ```bash
   ./scripts/smoke-test-local.sh
   ```

---

**All port conflicts resolved! Services are running on alternative ports when needed.**

