# Docker Build Troubleshooting Guide

## 🚨 Problem: Slow Docker Build (800+ seconds)

The main bottleneck is the `npm ci --legacy-peer-deps` step taking 817 seconds.

## 🚀 Quick Fixes

### Option 1: Use the Optimized Dockerfile
```bash
# Use the optimized Dockerfile with better caching
./docker-build-fast.sh --optimized
```

### Option 2: Use BuildKit for Better Caching
```bash
# Enable BuildKit for improved build performance
DOCKER_BUILDKIT=1 docker-compose build
```

### Option 3: Skip npm ci if Dependencies Haven't Changed
```bash
# Quick build that uses cached node_modules
./docker-build-fast.sh --quick
```

## 🔧 Permanent Solutions

### 1. **Use .dockerignore Properly**
Create/update `.dockerignore` to exclude unnecessary files:

```bash
cat > .dockerignore << 'EOF'
# Node
node_modules
npm-debug.log
.npm
.next
out
dist

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv
env
pip-log.txt
pip-delete-this-directory.txt

# Git
.git
.gitignore

# IDE
.vscode
.idea
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
test-results
test-reports
coverage
.pytest_cache

# Logs
*.log
logs

# Documentation
*.md
docs
EOF
```

### 2. **Use Multi-Stage Build Caching**

The `Dockerfile.optimized` I created uses better caching strategies:
- Separates dependency installation from code copying
- Uses `--no-audit --no-fund` flags to speed up npm
- Implements retry logic for network issues

### 3. **Pre-build Base Image**

Create a base image with dependencies pre-installed:

```bash
# Build a base image with dependencies
docker build -t deepwiki-base:latest -f - . << 'EOF'
FROM node:20-alpine3.22
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps --no-audit --no-fund
EOF

# Use it in your Dockerfile
# FROM deepwiki-base:latest AS node_deps
```

### 4. **Use Docker Build Cache Mount**

With BuildKit, use cache mounts for package managers:

```dockerfile
# In Dockerfile
RUN --mount=type=cache,target=/root/.npm \
    npm ci --legacy-peer-deps
```

## 📊 Build Time Comparison

| Method | Time | Command |
|--------|------|---------|
| No cache | 800+ seconds | `docker-compose build --no-cache` |
| With cache | 200-300 seconds | `docker-compose build` |
| BuildKit | 100-200 seconds | `DOCKER_BUILDKIT=1 docker-compose build` |
| Optimized | 50-150 seconds | `./docker-build-fast.sh --optimized` |
| Quick build | 30-60 seconds | `./docker-build-fast.sh --quick` |

## 🔍 Debugging Slow Builds

### Check What's Taking Time
```bash
# Build with detailed timing
DOCKER_BUILDKIT=1 docker build --progress=plain -t test .
```

### Monitor Network Speed
```bash
# Check if npm registry is slow
time npm ping
time curl -o /dev/null https://registry.npmjs.org
```

### Use Alternative Registry
```bash
# Use a faster npm mirror
npm config set registry https://registry.npmmirror.com
```

### Clear Docker Cache
```bash
# If builds are still slow, clear everything
docker system prune -a --volumes
docker builder prune -a
```

## 🏃 Fastest Build for Testing

If you need to test the fixes quickly without waiting for a full build:

### Option A: Use Development Mode
```bash
# This mounts code directly without building
docker-compose -f docker-compose.dev.yml up
```

### Option B: Quick Test Build
```bash
# 1. Stop everything
docker-compose down

# 2. Use the fast build script
./docker-build-fast.sh --quick

# 3. Or if that's still slow, try:
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build

# 4. Start container
docker-compose up -d

# 5. Run tests
./scripts/validate_docker_pipeline.py
```

## 🎯 Recommended Approach

For testing the embedding pipeline fixes:

```bash
# 1. First time - use optimized build
./docker-build-fast.sh --optimized

# 2. Subsequent builds - use quick mode
./docker-build-fast.sh --quick

# 3. Run tests
./test-pipeline-docker.sh

# 4. Monitor
./scripts/monitor_docker_logs.sh
```

## 💡 Pro Tips

1. **Keep node_modules cached**: Don't use `--no-cache` unless package.json changed
2. **Use BuildKit**: Always set `DOCKER_BUILDKIT=1`
3. **Layer order matters**: Put least-changing files first
4. **Parallel builds**: BuildKit can build stages in parallel
5. **Local registry**: Consider running a local npm registry cache

## 🔧 Emergency: Skip Docker for Quick Testing

If Docker build is too slow and you need to test immediately:

```bash
# Run locally without Docker
# Backend
cd api
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python -m api.main --port 8001 &

# Frontend (in new terminal)
npm install
npm run dev

# Run tests
pytest test/
```

## 📈 Monitoring Build Performance

```bash
# Time the build
time docker-compose build

# Watch CPU/Memory during build
docker stats

# Check Docker daemon logs
journalctl -u docker.service -f
```

## 🆘 If Nothing Works

The build might be slow due to:
1. **Network issues**: Try a different network or VPN
2. **Docker Desktop resources**: Increase CPU/Memory in Docker Desktop settings
3. **Disk space**: Clear space with `docker system prune -a`
4. **Registry issues**: npm registry might be slow, try later
5. **Corporate proxy**: Configure Docker to use proxy settings

As a last resort, you can test with the already-built image:
```bash
# Pull a pre-built image if available
docker pull deepwiki-open_deepwiki:latest

# Or use development mode which doesn't require building
docker-compose -f docker-compose.dev.yml up
```