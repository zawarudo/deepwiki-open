# Docker Testing Guide - Frontend & Backend

## 🚀 Quick Start

The DeepWiki Docker container runs **BOTH** the frontend and backend services:
- **Backend API**: Python FastAPI server on port `8001`
- **Frontend UI**: Next.js application on port `9001` (mapped from internal port 3000)

### Running the Complete Test Suite

```bash
# This will test both frontend and backend
./test-pipeline-docker.sh
```

## 📦 What's Running in the Container

When you start the Docker container, it automatically launches:

1. **Backend API Server** (`python -m api.main --port 8001`)
   - Embedding pipeline
   - WebSocket endpoints
   - Health checks
   - All the fixes from the epic

2. **Frontend Next.js Server** (`node server.js` on port 3000)
   - Web UI for DeepWiki
   - Repository input interface
   - Real-time progress updates
   - Wiki visualization

## 🌐 Accessing the Services

### After running `docker-compose up -d`:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend UI | http://localhost:9001 | Main web interface |
| Backend API | http://localhost:8001 | API endpoints |
| API Health | http://localhost:8001/health | Health check |
| API Docs | http://localhost:8001/docs | Swagger UI |

## 🧪 Testing Both Services

### 1. Automated Testing
```bash
# Run the complete test suite (includes frontend checks)
./test-pipeline-docker.sh
```

### 2. Manual Testing

#### Test Frontend is Running:
```bash
# Check if frontend is accessible
curl http://localhost:9001

# Or open in browser
open http://localhost:9001  # macOS
xdg-open http://localhost:9001  # Linux
```

#### Test Backend API:
```bash
# Health check
curl http://localhost:8001/health

# API documentation
open http://localhost:8001/docs
```

#### Test Frontend-Backend Integration:
```bash
# Through the UI:
1. Open http://localhost:9001
2. Enter a GitHub repository URL
3. Click "Generate Wiki"
4. Watch the real-time progress

# Through API:
curl -X POST http://localhost:8001/api/generate_wiki \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/example/repo"}'
```

## 🐳 Docker Commands

### Build and Run with Both Services:
```bash
# Stop any existing containers
docker-compose down

# Rebuild with latest changes (no cache)
docker-compose build --no-cache

# Start both services
docker-compose up -d

# Check logs for both services
docker-compose logs -f
```

### Using Test Environment:
```bash
# Use the test-specific compose file
docker-compose -f docker-compose.test.yml up -d

# This runs on different ports to avoid conflicts:
# - Frontend: http://localhost:3001
# - Backend: http://localhost:8001
```

### Monitor Both Services:
```bash
# Watch logs in real-time
docker-compose logs -f

# Check if both processes are running
docker exec deepwiki-open_deepwiki_1 ps aux | grep -E "python|node"

# Monitor with our custom script
./scripts/monitor_docker_logs.sh
```

## 🔍 Verifying Services are Running

### Check Running Processes:
```bash
# See both Python and Node processes
docker exec deepwiki-open_deepwiki_1 ps aux
```

Expected output:
```
PID   USER     COMMAND
1     root     /bin/bash /app/start.sh
7     root     python -m api.main --port 8001
8     root     node server.js
```

### Check Port Bindings:
```bash
# Verify ports are exposed
docker-compose ps
```

Expected output:
```
Name                    Command               State           Ports
deepwiki_deepwiki_1     /app/start.sh           Up      0.0.0.0:8001->8001/tcp
                                                        0.0.0.0:9001->3000/tcp
```

## 🛠️ Troubleshooting

### Frontend Not Loading?

1. **Check if Node.js server is running:**
   ```bash
   docker exec deepwiki-open_deepwiki_1 ps aux | grep node
   ```

2. **Check frontend logs:**
   ```bash
   docker-compose logs | grep -E "node|Next.js|PORT=3000"
   ```

3. **Verify port mapping:**
   ```bash
   docker port deepwiki-open_deepwiki_1 3000
   # Should show: 0.0.0.0:9001
   ```

### Backend API Not Responding?

1. **Check Python server:**
   ```bash
   docker exec deepwiki-open_deepwiki_1 ps aux | grep python
   ```

2. **Check API logs:**
   ```bash
   docker-compose logs | grep -E "api.main|FastAPI|Uvicorn"
   ```

3. **Test health endpoint:**
   ```bash
   curl -v http://localhost:8001/health
   ```

### Connection Between Frontend and Backend?

1. **Check environment variables:**
   ```bash
   docker exec deepwiki-open_deepwiki_1 env | grep SERVER_BASE_URL
   # Should show: SERVER_BASE_URL=http://localhost:8001
   ```

2. **Monitor WebSocket connections:**
   ```bash
   docker-compose logs | grep -E "WebSocket|ws:|connected"
   ```

## 🔧 Environment Variables

Make sure your `.env` file includes:

```env
# Required for embeddings
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Optional - for testing without real APIs
USE_MOCK_EMBEDDINGS=false  # Set to true for testing without API keys

# Ports (defaults)
PORT=8001  # Backend API port
# Frontend always uses 3000 internally, mapped to 9001 externally
```

## 📊 Full System Test

To verify everything is working together:

```bash
# 1. Run our comprehensive test script
./test-pipeline-docker.sh

# 2. When prompted, keep container running
# 3. Open browser to http://localhost:9001
# 4. Try generating a wiki for a small repository
# 5. Monitor logs in another terminal:
./scripts/monitor_docker_logs.sh
```

## ✅ Success Indicators

You know both services are working when:

1. ✅ Frontend loads at http://localhost:9001
2. ✅ API responds at http://localhost:8001/health
3. ✅ Can submit a repository URL in the UI
4. ✅ WebSocket connects and shows progress
5. ✅ No empty vector errors in logs
6. ✅ All embeddings are 768-dimensional
7. ✅ Retry logic activates on transient failures
8. ✅ Enhanced error messages appear when needed

## 🎯 Testing the Complete Pipeline

### Through the UI (Recommended):
1. Navigate to http://localhost:9001
2. Enter: `https://github.com/simple-icons/simple-icons` (or another small repo)
3. Click "Generate Wiki"
4. Watch the real-time progress
5. Verify the wiki generates successfully

### Through the API:
```bash
# Generate wiki via API
curl -X POST http://localhost:8001/api/generate_wiki \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/simple-icons/simple-icons", "model": "gpt-4o-mini"}'

# Monitor progress via WebSocket (in browser console at http://localhost:9001):
# The UI automatically connects to ws://localhost:8001/ws/{task_id}
```

## 📈 Performance Monitoring

While testing, monitor resource usage:

```bash
# Real-time stats
docker stats deepwiki-open_deepwiki_1

# Check memory usage
docker exec deepwiki-open_deepwiki_1 free -h

# Check disk usage
docker exec deepwiki-open_deepwiki_1 df -h
```

---

Remember: The Docker container runs **both** frontend and backend together. You don't need to run them separately! 🚀