# Repository Structure Migration Guide

This guide documents the recent reorganization of scripts and test files for better maintainability.

## 📁 File Relocations

### Docker Files
| Old Location | New Location |
|--------------|--------------|
| `Dockerfile-ollama-local` | `docker/Dockerfile.ollama-local` |
| `Dockerfile.optimized` | `docker/Dockerfile.optimized` |
| `docker-compose.dev.yml` | `docker/compose/dev.yml` |
| `docker-compose.test.yml` | `docker/compose/test.yml` |
| `docker-build-fast.sh` | `docker/scripts/build-fast.sh` |
| `test-pipeline-docker.sh` | `docker/scripts/test-pipeline.sh` |

### Scripts
| Old Location | New Location |
|--------------|--------------|
| `scripts/monitor_docker_logs.sh` | `scripts/docker/monitor_docker_logs.sh` |
| `scripts/validate_docker_pipeline.py` | `scripts/docker/validate_docker_pipeline.py` |
| `scripts/run_e2e_tests.sh` | `scripts/testing/run_e2e_tests.sh` |
| `scripts/test_faiss_index.py` | `scripts/testing/test_faiss_index.py` |
| `scripts/validate_embeddings.py` | `scripts/validation/validate_embeddings.py` |
| `scripts/monitor_embeddings.py` | `scripts/validation/monitor_embeddings.py` |
| `scripts/generate_wiki.py` | `scripts/utils/generate_wiki.py` |
| `scripts/regenerate_embeddings.py` | `scripts/utils/regenerate_embeddings.py` |

### Test Files
| Old Location | New Location |
|--------------|--------------|
| `test/test_empty_embedding_validation.py` | `test/embeddings/test_empty_embedding_validation.py` |
| `test/test_dimension_consistency.py` | `test/embeddings/test_dimension_consistency.py` |
| `test/test_batch_retry_logic.py` | `test/embeddings/test_batch_retry_logic.py` |
| `test/test_emergency_fix.py` | `test/embeddings/test_emergency_fix.py` |
| `test/test_error_reporting.py` | `test/embeddings/test_error_reporting.py` |
| `test/test_e2e_embedding_pipeline.py` | `test/integration/test_e2e_embedding_pipeline.py` |
| `test/test_generate_wiki_flow.py` | `test/integration/test_generate_wiki_flow.py` |
| `test/test_extract_repo_name.py` | `test/unit/test_extract_repo_name.py` |
| `test/test_lang_config.py` | `test/unit/test_lang_config.py` |

### Documentation
| Old Location | New Location |
|--------------|--------------|
| `DOCKER_TESTING_GUIDE.md` | `docs/testing/docker-testing.md` |
| `DOCKER_BUILD_TROUBLESHOOTING.md` | `docs/testing/troubleshooting.md` |

## 🔄 Updating Your Scripts

### If you have custom scripts referencing old paths:

1. **Docker Compose Commands**
   ```bash
   # Old
   docker-compose -f docker-compose.dev.yml up
   
   # New
   docker-compose -f docker/compose/dev.yml up
   ```

2. **Test Scripts**
   ```bash
   # Old
   ./test-pipeline-docker.sh
   
   # New
   ./docker/scripts/test-pipeline.sh
   ```

3. **Python Imports**
   ```python
   # If you import test utilities, update paths
   # Old: from test.test_utils import helper
   # New: from test.fixtures.test_utils import helper
   ```

## 🚀 New Convenience Scripts

### Main Test Runner
A new unified test runner is available:
```bash
# Run all tests
./run-tests.sh all

# Run specific categories
./run-tests.sh unit
./run-tests.sh integration
./run-tests.sh embeddings

# Run in Docker
./run-tests.sh docker

# Generate coverage
./run-tests.sh coverage
```

## 📚 Documentation Updates

### New Documentation Structure
- `TESTING.md` - Main testing guide in root
- `docs/testing/README.md` - Comprehensive testing documentation
- `docs/testing/docker-testing.md` - Docker testing guide
- `docs/testing/embedding-tests.md` - Embedding pipeline tests
- `test/README.md` - Test organization guide
- `scripts/README.md` - Scripts directory guide
- `docker/README.md` - Docker configuration guide

## 🔧 Configuration Updates

### Docker Compose Context
The docker-compose files now use relative context paths:
```yaml
# docker/compose/dev.yml
build:
  context: ../..  # Points to repository root
  dockerfile: Dockerfile
```

### Test Paths
Test discovery still works from root:
```bash
# These all still work
pytest test/
pytest test/unit/
pytest test/embeddings/
```

## ⚠️ Breaking Changes

1. **Direct script execution** - Update any CI/CD pipelines or scripts that directly reference the old paths
2. **Docker build context** - The compose files in `docker/compose/` use `../..` as context
3. **Import paths** - No changes needed for Python imports as the structure within categories is preserved

## 💡 Benefits of New Structure

1. **Better Organization** - Related files are grouped together
2. **Easier Discovery** - Clear categorization of scripts and tests
3. **Improved Documentation** - Centralized docs with clear navigation
4. **Standard Practice** - Follows common repository structure conventions
5. **Scalability** - Easy to add new categories without cluttering root

## 🆘 Need Help?

If you encounter issues:
1. Check the new paths in this guide
2. Use the convenience script: `./run-tests.sh`
3. Refer to the updated documentation in `docs/testing/`
4. Check README files in each directory for guidance