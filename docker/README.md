# Docker Directory

This directory contains Docker configurations and scripts for building and running DeepWiki in containers.

## 📁 Directory Structure

### Root Files (kept in project root for standard practice)
- **`Dockerfile`** - Main production Dockerfile
- **`docker-compose.yml`** - Main docker-compose configuration

### `docker/` - Additional Docker Files

#### Dockerfiles
- **`Dockerfile.optimized`** - Optimized Dockerfile with better caching and faster builds
- **`Dockerfile.ollama-local`** - Dockerfile for running with local Ollama models

#### `compose/` - Docker Compose Configurations
- **`dev.yml`** - Development environment with hot reload
- **`test.yml`** - Test environment configuration

#### `scripts/` - Docker Management Scripts
- **`build-fast.sh`** - Fast Docker build script with multiple strategies
- **`test-pipeline.sh`** - Comprehensive test suite runner in Docker

## 🚀 Quick Start

### Building Images

```bash
# Standard build
docker-compose build

# Fast build with optimization
./docker/scripts/build-fast.sh --optimized

# Development build
docker-compose -f docker-compose.yml -f docker/compose/dev.yml build
```

### Running Containers

```bash
# Production mode
docker-compose up -d

# Development mode with hot reload
docker-compose -f docker-compose.yml -f docker/compose/dev.yml up

# Test mode
docker-compose -f docker/compose/test.yml up
```

## 🛠️ Build Options

### Using build-fast.sh

```bash
# Standard build with cache
./docker/scripts/build-fast.sh

# Optimized build (faster)
./docker/scripts/build-fast.sh --optimized

# Clean build (no cache)
./docker/scripts/build-fast.sh --clean

# Quick build for development
./docker/scripts/build-fast.sh --quick

# Use BuildKit for better caching
./docker/scripts/build-fast.sh --buildkit
```

### Build Time Optimization

| Method | Time | Command |
|--------|------|---------|
| No cache | 800+ sec | `docker-compose build --no-cache` |
| With cache | 200-300 sec | `docker-compose build` |
| Optimized | 50-150 sec | `./docker/scripts/build-fast.sh --optimized` |
| Quick | 30-60 sec | `./docker/scripts/build-fast.sh --quick` |

## 🧪 Testing with Docker

### Run Test Suite
```bash
# Run complete test suite
./docker/scripts/test-pipeline.sh

# Run specific tests in container
docker-compose exec deepwiki pytest test/embeddings/ -v

# Use test compose file
docker-compose -f docker/compose/test.yml up
```

### Test Environment Features
- Isolated test container
- Mock embedding support
- Test result persistence
- HTML report generation

## 🔧 Docker Configurations

### Production (docker-compose.yml)
- Ports: 8001 (API), 9001 (Frontend)
- Memory: 6GB limit, 2GB reserved
- Health checks enabled
- Volume persistence for data

### Development (compose/dev.yml)
- Hot reload enabled
- Source code mounted
- Separate API and web services
- Development environment variables

### Test (compose/test.yml)
- Test-specific ports (8001, 3001)
- Debug logging enabled
- Test result volumes
- Optional test-runner service

## 📊 Container Management

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs api -f

# With monitoring script
./scripts/docker/monitor_docker_logs.sh
```

### Container Stats
```bash
# Resource usage
docker stats

# Process list
docker-compose ps

# Health status
docker-compose ps | grep healthy
```

### Cleanup
```bash
# Stop containers
docker-compose down

# Remove volumes
docker-compose down -v

# Full cleanup
docker system prune -a
```

## 🌐 Service URLs

After starting containers:

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8001 | Backend API |
| API Docs | http://localhost:8001/docs | Swagger UI |
| Frontend | http://localhost:9001 | Web interface |
| Health | http://localhost:8001/health | Health check |

## 🔑 Environment Variables

Required in `.env` file:
```env
# API Keys
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key

# Optional
USE_MOCK_EMBEDDINGS=false
PORT=8001
LOG_LEVEL=INFO
```

## 🐛 Troubleshooting

### Slow Builds
- Use optimized Dockerfile: `./docker/scripts/build-fast.sh --optimized`
- Enable BuildKit: `DOCKER_BUILDKIT=1 docker-compose build`
- Check [Troubleshooting Guide](../docs/testing/troubleshooting.md)

### Container Won't Start
- Check logs: `docker-compose logs`
- Verify ports available: `lsof -i :8001`
- Check .env file exists with API keys

### Permission Issues
- Ensure proper file permissions
- Use appropriate user in Dockerfile
- Check volume mount permissions

## 📚 Related Documentation

- [Docker Testing Guide](../docs/testing/docker-testing.md)
- [Troubleshooting Guide](../docs/testing/troubleshooting.md)
- [Main README](../README.md)