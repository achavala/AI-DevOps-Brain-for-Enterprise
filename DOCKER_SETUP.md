# 🐳 Docker Setup Guide

Quick guide to get Docker running for local development.

---

## ✅ Check Docker Status

```bash
./scripts/check-docker.sh
```

Or manually:
```bash
docker info
```

---

## 🚀 Start Docker Desktop

### macOS

1. **Open Docker Desktop**
   - Look in Applications folder
   - Or search "Docker" in Spotlight (Cmd+Space)
   - Or run: `open -a Docker`

2. **Wait for Docker to Start**
   - Look for whale icon in menu bar (top right)
   - Icon should be steady (not animated)
   - Can take 30-60 seconds on first start

3. **Verify It's Running**
   ```bash
   docker info
   ```
   Should show Docker system information (no errors)

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Solution**: Docker Desktop is not running
1. Open Docker Desktop application
2. Wait for it to fully start
3. Check menu bar icon is steady

### Issue: Docker Desktop won't start

**Solutions**:
1. **Restart Docker Desktop**:
   ```bash
   # Quit Docker Desktop
   osascript -e 'quit app "Docker"'
   
   # Wait a few seconds
   sleep 5
   
   # Start again
   open -a Docker
   ```

2. **Check system requirements**:
   - macOS 10.15 or later
   - At least 4GB RAM available
   - Virtualization enabled (usually automatic)

3. **Reset Docker Desktop** (if needed):
   - Docker Desktop → Settings → Troubleshoot → Reset to factory defaults
   - ⚠️ This will remove all containers and images

### Issue: Docker is slow

**Solutions**:
1. **Increase resources**:
   - Docker Desktop → Settings → Resources
   - Increase CPU (4+ cores)
   - Increase Memory (8GB+)

2. **Clean up**:
   ```bash
   docker system prune -a
   ```

---

## ✅ Verify Docker is Ready

After starting Docker Desktop, verify:

```bash
# Check Docker is running
docker info

# Should show system information, no errors

# Check Docker version
docker --version

# Test with a simple command
docker run hello-world
```

---

## 🎯 Quick Start After Docker is Running

Once Docker is running:

```bash
# 1. Check status
./scripts/check-docker.sh

# 2. Start local environment
./scripts/start-local.sh

# 3. Check heartbeat
./scripts/trading-heartbeat.sh
```

---

## 📋 Common Commands

```bash
# Check Docker status
docker info

# List running containers
docker ps

# List all containers
docker ps -a

# Stop all containers
docker stop $(docker ps -q)

# Remove all containers
docker rm $(docker ps -aq)

# View Docker logs
docker logs <container-name>

# Docker system info
docker system df
```

---

## 💡 Pro Tips

1. **Keep Docker Desktop running** while working
2. **Start Docker first** before running scripts
3. **Check menu bar icon** - steady = ready, animated = starting
4. **Use lightweight mode** if Docker is slow: `./scripts/setup-lightweight-local.sh`

---

## 🆘 Still Having Issues?

1. **Check Docker Desktop logs**:
   - Docker Desktop → Troubleshoot → View logs

2. **Restart Docker Desktop**:
   - Quit completely and restart

3. **Check system resources**:
   - Activity Monitor → Check CPU/Memory usage

4. **Reinstall Docker Desktop** (last resort):
   - Download from: https://www.docker.com/products/docker-desktop

---

**Once Docker is running, you're ready to use the local environment! 🚀**

