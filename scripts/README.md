# Scripts Directory

This directory contains utility scripts for various DeepWiki operations, organized by function.

## 📁 Directory Structure

### `docker/` - Docker-related scripts
- **`monitor_docker_logs.sh`** - Real-time monitoring of Docker container logs with statistics
- **`validate_docker_pipeline.py`** - Python script to validate embedding pipeline fixes in Docker environment

### `testing/` - Testing scripts
- **`run_e2e_tests.sh`** - End-to-end test runner for complete pipeline validation
- **`test_faiss_index.py`** - FAISS index validation and testing script

### `validation/` - Validation utilities
- **`validate_embeddings.py`** - Validates embeddings for dimension consistency and quality
- **`monitor_embeddings.py`** - Real-time monitoring of embedding generation

### `utils/` - General utilities
- **`generate_wiki.py`** - Script to generate wiki documentation programmatically
- **`regenerate_embeddings.py`** - Utility to regenerate embeddings for existing documents

## 🚀 Quick Usage

### Docker Scripts
```bash
# Monitor Docker logs in real-time
./scripts/docker/monitor_docker_logs.sh

# Validate pipeline in Docker
python scripts/docker/validate_docker_pipeline.py
```

### Testing Scripts
```bash
# Run end-to-end tests
./scripts/testing/run_e2e_tests.sh

# Test FAISS index
python scripts/testing/test_faiss_index.py
```

### Validation Scripts
```bash
# Validate embeddings
python scripts/validation/validate_embeddings.py

# Monitor embedding generation
python scripts/validation/monitor_embeddings.py
```

### Utility Scripts
```bash
# Generate wiki for a repository
python scripts/utils/generate_wiki.py --repo https://github.com/user/repo

# Regenerate embeddings
python scripts/utils/regenerate_embeddings.py
```

## 📝 Script Permissions

All shell scripts should be executable:
```bash
chmod +x scripts/**/*.sh
```

## 🔧 Dependencies

Most Python scripts require the API dependencies:
```bash
pip install -r api/requirements.txt
```

## 📚 Related Documentation

- [Testing Documentation](../docs/testing/README.md)
- [Docker Guide](../docs/testing/docker-testing.md)
- [Main README](../README.md)