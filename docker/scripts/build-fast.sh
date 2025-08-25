#!/bin/bash

# =============================================================================
# Fast Docker Build Script for DeepWiki
# =============================================================================
# This script builds the Docker image with optimizations for speed
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}                    Fast Docker Build for DeepWiki                           ${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Function to print status
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we should use the optimized Dockerfile
USE_OPTIMIZED=false
if [ "$1" == "--optimized" ] || [ "$1" == "-o" ]; then
    USE_OPTIMIZED=true
    print_status "Using optimized Dockerfile"
fi

# Stop any running containers
print_status "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Prune build cache if requested
if [ "$1" == "--clean" ]; then
    print_status "Cleaning Docker build cache..."
    docker builder prune -f
fi

# Build strategy based on what changed
build_docker() {
    local dockerfile="Dockerfile"
    if [ "$USE_OPTIMIZED" = true ] && [ -f "Dockerfile.optimized" ]; then
        dockerfile="Dockerfile.optimized"
    fi
    
    print_status "Building with $dockerfile..."
    
    # Check if package files changed
    PACKAGE_CHANGED=$(git diff HEAD~1 --name-only | grep -E "package.*json|requirements.txt" || echo "")
    
    if [ -z "$PACKAGE_CHANGED" ]; then
        print_status "Dependencies unchanged - using cache"
        # Build with cache
        docker-compose build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --progress=plain
    else
        print_status "Dependencies changed - rebuilding"
        # Build without cache for dependency layers
        docker-compose build \
            --no-cache \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --progress=plain
    fi
}

# Alternative: Use docker build directly with BuildKit
build_with_buildkit() {
    print_status "Building with Docker BuildKit for better caching..."
    
    # Enable BuildKit
    export DOCKER_BUILDKIT=1
    export BUILDKIT_PROGRESS=plain
    
    # Build the image
    docker build \
        --cache-from deepwiki-open_deepwiki:latest \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        -t deepwiki-open_deepwiki:latest \
        -f ${USE_OPTIMIZED:+Dockerfile.optimized} \
        --target production \
        .
}

# Quick build for development (skips some optimizations)
quick_build() {
    print_status "Quick build for development..."
    
    # Create a temporary docker-compose override
    cat > docker-compose.build.yml << 'EOF'
version: '3.8'
services:
  deepwiki:
    build:
      context: .
      dockerfile: Dockerfile
      cache_from:
        - deepwiki-open_deepwiki:latest
      args:
        - BUILDKIT_INLINE_CACHE=1
    image: deepwiki-open_deepwiki:latest
EOF
    
    # Build with the override
    COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
        docker-compose -f docker-compose.yml -f docker-compose.build.yml build
    
    # Clean up
    rm -f docker-compose.build.yml
}

# Main build process
main() {
    START_TIME=$(date +%s)
    
    # Parse arguments
    case "$1" in
        --clean)
            print_status "Full rebuild with cache cleanup"
            docker builder prune -f
            build_docker
            ;;
        --optimized|-o)
            print_status "Using optimized Dockerfile"
            USE_OPTIMIZED=true
            build_docker
            ;;
        --buildkit|-b)
            build_with_buildkit
            ;;
        --quick|-q)
            quick_build
            ;;
        *)
            print_status "Standard build"
            build_docker
            ;;
    esac
    
    # Calculate build time
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    MINUTES=$((BUILD_TIME / 60))
    SECONDS=$((BUILD_TIME % 60))
    
    print_success "Build completed in ${MINUTES}m ${SECONDS}s"
    
    # Ask if user wants to start the container
    echo ""
    read -p "Start the container now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting container..."
        docker-compose up -d
        
        # Wait for services
        print_status "Waiting for services to start..."
        sleep 10
        
        # Check services
        if curl -f http://localhost:8001/health >/dev/null 2>&1; then
            print_success "Backend API is running at http://localhost:8001"
        fi
        
        if curl -f http://localhost:9001 >/dev/null 2>&1; then
            print_success "Frontend is running at http://localhost:9001"
        fi
        
        print_success "Services are ready!"
        echo ""
        echo "Run tests with: ./test-pipeline-docker.sh"
        echo "Monitor logs with: ./scripts/monitor_docker_logs.sh"
    fi
}

# Show usage
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean       Clean build cache and rebuild from scratch"
    echo "  --optimized   Use optimized Dockerfile (Dockerfile.optimized)"
    echo "  --buildkit    Use Docker BuildKit for better caching"
    echo "  --quick       Quick build for development"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Standard build with cache"
    echo "  $0 --optimized        # Use optimized Dockerfile"
    echo "  $0 --clean            # Full rebuild"
    echo "  $0 --quick            # Fast development build"
    exit 0
fi

# Run main function
main "$@"