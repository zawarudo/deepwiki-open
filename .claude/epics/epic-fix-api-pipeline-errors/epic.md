# Epic: Fix API Pipeline Errors

## Overview
Critical failures in embedding dimension validation tests are causing pipeline errors. These tests are failing due to exception type mismatches and incomplete validation logic in the Google Embedding Client.

## Test Failures Summary
- `test_clear_dimension_error_messages` ❌
- `test_wrong_model_dimensions` ❌  
- `test_zero_dimension_vectors_rejected` ❌
- `test_extreme_dimension_values_rejected` ❌

---

## Task 000: Document Discovery Glob Pattern Bug 🔴 EMERGENCY

### Problem
The pipeline finds 0 documents because glob patterns skip root-level files entirely.

### Root Cause
- Glob pattern `/**/*{ext}` only matches files in subdirectories
- Files in the repository root (like README.md, main.py) are completely ignored
- This affects ALL repositories processed by the pipeline

### Solution
Fix glob patterns in `data_pipeline.py`:
```python
# Line 281 - Fix for all file extensions
files = glob.glob(f"{path}/**{ext}", recursive=True)

# Line 322 - Fix for specific extensions
files = glob.glob(f"{path}/**{ext}", recursive=True)
```

### Files to Modify
- `api/data_pipeline.py:281`
- `api/data_pipeline.py:322`

### Impact
- **CRITICAL**: No root-level files are being processed in ANY repository
- **Affects**: All embedding tests, all production document processing
- **Symptom**: "Found 0 documents" even when files exist

---

## Task 001: Exception Type Mismatch in Dimension Validation 🔴 CRITICAL

### Problem
The `_validate_embedding` method in `google_embedding_client.py:228` raises `ValueError` but tests expect `EmbeddingGenerationError`.

### Root Cause
- Method raises generic `ValueError` for dimension mismatches
- Tests are checking for domain-specific `EmbeddingGenerationError`
- This breaks the error handling contract expected by consumers

### Solution
Modify `_validate_embedding` to raise `EmbeddingGenerationError`:
```python
def _validate_embedding(self, embedding: List[float], expected_dim: int = 768) -> bool:
    if embedding is None:
        raise EmbeddingGenerationError("Null embedding vector")
    if not embedding or len(embedding) == 0:
        raise EmbeddingGenerationError("Empty embedding vector (zero dimensions)")
    if len(embedding) != expected_dim:
        raise EmbeddingGenerationError(
            f"Invalid embedding dimension: {len(embedding)}, expected {expected_dim}"
        )
    return True
```

### Files to Modify
- `api/google_embedding_client.py:228-233`

---

## Task 002: Missing Validation in Error Recovery Path 🟡 HIGH

### Problem
Dimension validation is missing when appending embeddings in the error recovery path at line 429.

### Root Cause
- When retrying failed embeddings, vectors are appended without validation
- This allows invalid dimensions to slip through to FAISS
- Can cause downstream crashes in vector storage

### Solution
Add validation before appending recovered embeddings:
```python
# Line 429 - Add validation
self._validate_embedding(vec)
successful_embeddings.append(vec)
```

### Files to Modify
- `api/google_embedding_client.py:429`

---

## Task 003: Incomplete Empty Vector Detection 🟡 HIGH

### Problem
Zero-dimension vectors (empty arrays `[]`) are not properly detected in null checking logic.

### Root Cause
- Current null check only looks for explicit `None` values
- Empty arrays `[]` pass through undetected
- FAISS crashes when receiving zero-dimension vectors

### Solution
Enhance null detection at lines 345-353:
```python
if embedding_values is None or not embedding_values or len(embedding_values) == 0:
    logger.warning(f"Null or empty embedding detected for text: {texts[idx][:50]}...")
    successful_embeddings.append(None)
```

### Files to Modify
- `api/google_embedding_client.py:345-353`

---

## Task 004: Improve Error Messages for Dimension Mismatches 🟢 MEDIUM

### Problem
Generic error messages don't include model context, making debugging difficult.

### Root Cause
- Error message doesn't specify which model had the dimension mismatch
- Tests expect specific error message formats
- Hard to trace issues in multi-model scenarios

### Solution
Include model name in error messages:
```python
raise EmbeddingGenerationError(
    f"Invalid embedding dimension for {self.model_name}: {len(embedding)}, expected {expected_dim}"
)
```

### Files to Modify
- `api/google_embedding_client.py:229`

---

## Task 005: Add Batch-Level Dimension Consistency Check 🔵 LOW

### Problem
No validation that all embeddings in a batch have consistent dimensions.

### Root Cause
- Individual validation exists but no batch-level consistency check
- Mixed dimensions within batch could cause subtle bugs
- Late detection of dimension inconsistencies

### Solution
Add batch consistency validation after collecting all embeddings:
```python
# After collecting all embeddings
dimensions = [len(e) for e in successful_embeddings if e is not None]
if len(set(dimensions)) > 1:
    raise EmbeddingGenerationError(
        f"Inconsistent dimensions in batch: {set(dimensions)}"
    )
```

### Files to Modify
- `api/google_embedding_client.py` (after embedding collection loop)

---

## Success Criteria
✅ All 4 failing tests pass  
✅ No regression in passing tests  
✅ Clear error messages for dimension issues  
✅ Consistent exception types throughout  
✅ No invalid dimensions reach FAISS  

## Priority Order
1. Task 000 - Fix glob pattern bug (EMERGENCY - blocks all processing)
2. Task 001 - Fix exception types (CRITICAL)
3. Task 002 - Add validation in recovery path (HIGH)
4. Task 003 - Fix empty vector detection (HIGH)
5. Task 004 - Improve error messages (MEDIUM)
6. Task 005 - Add batch consistency check (LOW)

## Testing Command
```bash
pytest test/embeddings/test_dimension_consistency.py -v
```

## Notes
- All changes are localized to `google_embedding_client.py`
- No API contract changes required
- Backwards compatible with existing code