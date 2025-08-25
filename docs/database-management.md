# Database Management Guide

This guide covers how to manage, rebuild, and maintain the DeepWiki embedding database, especially when dealing with empty or corrupted embeddings.

## Overview

DeepWiki stores document embeddings in a local database located at:
```
~/.adalflow/databases/{repo_name}.pkl
```

When the system detects this database exists, it loads the cached embeddings instead of regenerating them. This speeds up subsequent runs but can cause issues if the embeddings are corrupted or empty.

## Common Issues

### Empty Embeddings
After the recent fixes, the system now properly validates embeddings and prevents empty vectors from being created. However, if you have an older database with empty embeddings (from before the fix), you'll need to rebuild it.

### Symptoms of Corrupted Embeddings
- Search results return no matches despite relevant content
- Error messages about dimension mismatches
- Log messages showing "Loaded 923 documents from existing database" but searches fail
- Empty or zero-dimensional embedding vectors in the database

## Database Rebuild Options

### Option 1: Complete Database Rebuild (Recommended)

Use the simple rebuild script to delete the existing database and force complete regeneration:

```bash
# List all existing databases
python scripts/utils/rebuild_database.py --list

# Rebuild the default database (with backup)
python scripts/utils/rebuild_database.py

# Rebuild a specific repository database
python scripts/utils/rebuild_database.py --repo-name AsyncFuncAI_deepwiki-open

# Force rebuild without confirmation prompts
python scripts/utils/rebuild_database.py --force

# Skip backup creation (not recommended)
python scripts/utils/rebuild_database.py --force --no-backup
```

**What happens:**
1. Creates a backup of the existing database (unless --no-backup is used)
2. Deletes the corrupted database file
3. On next application run, automatically regenerates all embeddings with proper validation
4. Ensures no empty vectors persist in the new database

### Option 2: Selective Embedding Regeneration

Use the advanced regeneration script to fix only corrupted embeddings while preserving valid ones:

```bash
# Validate existing embeddings without making changes
python scripts/utils/regenerate_embeddings.py --validate-only

# Dry run to see what would be regenerated
python scripts/utils/regenerate_embeddings.py --dry-run

# Regenerate corrupted embeddings with custom batch size
python scripts/utils/regenerate_embeddings.py --batch-size 10

# Resume regeneration from a specific index (useful for interruptions)
python scripts/utils/regenerate_embeddings.py --resume-from 50

# Process specific embedding file
python scripts/utils/regenerate_embeddings.py \
    --input-file embeddings.json \
    --output-file fixed_embeddings.json
```

**Features:**
- Validates all embeddings for corruption
- Only regenerates invalid embeddings
- Supports batch processing with retry logic
- Can resume from interruptions
- Creates backups before modification
- Provides detailed progress reporting

### Option 3: Manual Database Deletion

For quick manual deletion:

```bash
# Remove the database file directly
rm ~/.adalflow/databases/AsyncFuncAI_deepwiki-open.pkl

# Or remove all databases
rm -rf ~/.adalflow/databases/*.pkl
```

## Best Practices

### 1. Regular Validation
Periodically validate your embeddings to catch issues early:
```bash
python scripts/utils/regenerate_embeddings.py --validate-only
```

### 2. Backup Before Rebuild
Always create backups before modifying the database:
```bash
# The rebuild script creates automatic backups to:
~/.adalflow/database_backups/{repo_name}_{timestamp}.pkl
```

### 3. Monitor Embedding Generation
Watch for these log messages during generation:
- ✅ Good: "Generated embeddings for N documents"
- ⚠️  Warning: "Empty embedding vector detected"
- ❌ Error: "Failed to generate embedding for document"

### 4. Verify After Rebuild
After rebuilding, verify the new embeddings:
```bash
# Check the database was recreated
ls -la ~/.adalflow/databases/

# Run validation
python scripts/utils/regenerate_embeddings.py --validate-only

# Test search functionality
# (Run your application and perform test searches)
```

## How the Fix Works

The recent pipeline fixes ensure:

1. **Validation at Generation** (`google_embedding_client.py:227`)
   - Raises `EmbeddingGenerationError` for empty vectors
   - Validates dimension consistency (768 dimensions)

2. **Defensive Type Checking** (`google_embedding_client.py:472`)
   - Prevents Mock object iteration errors in tests
   - Handles corrupted data gracefully

3. **Pipeline Validation** (`data_pipeline.py:414`)
   - `validate_embeddings()` filters out invalid embeddings
   - `validate_dimension_consistency()` ensures uniform dimensions

## Troubleshooting

### Q: How do I know if my database has empty embeddings?
Run validation to check:
```bash
python scripts/utils/regenerate_embeddings.py --validate-only
```

### Q: The rebuild is taking too long, can I speed it up?
Increase the batch size (be mindful of API rate limits):
```bash
python scripts/utils/regenerate_embeddings.py --batch-size 100
```

### Q: What if regeneration fails partway through?
The script saves progress and can resume:
```bash
# Resume from where it left off
python scripts/utils/regenerate_embeddings.py --resume-from <last_index>
```

### Q: How do I rebuild for a different repository?
Specify the repository name:
```bash
python scripts/utils/rebuild_database.py --repo-name YourOrg_YourRepo
```

## Environment Variables

Ensure your `.env` file contains valid API keys:
```env
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Related Files

- **Database location**: `~/.adalflow/databases/*.pkl`
- **Backup location**: `~/.adalflow/database_backups/`
- **Rebuild script**: `scripts/utils/rebuild_database.py`
- **Regeneration script**: `scripts/utils/regenerate_embeddings.py`
- **Validation script**: `scripts/validation/validate_embeddings.py`
- **Pipeline code**: `api/data_pipeline.py`
- **Embedding client**: `api/google_embedding_client.py`

## Summary

For most users experiencing issues with empty embeddings from the default website example:

1. **Quick fix**: Run `python scripts/utils/rebuild_database.py --force`
2. **Safe approach**: Run without `--force` to review and confirm
3. **Advanced users**: Use `regenerate_embeddings.py` for selective fixes

The database will automatically rebuild with proper embeddings on the next application run, ensuring all 923 documents have valid 768-dimensional vectors with no empty embeddings.