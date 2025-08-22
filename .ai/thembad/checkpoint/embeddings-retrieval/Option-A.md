# Option A: Fail-fast + guidance only (minimal)

## Summary
Minimal changes to surface clear operator guidance when embeddings are all empty, without automatic retries.

## Pros
- Quick to implement
- Clear operator feedback
- Low risk

## Cons
- Does not auto-recover
- Requires manual reruns or config changes

## Good when
- Failures are rare and due to environment/API quotas

## Scope of Change
- `api/rag.py`: fail-fast with actionable error message

## Acceptance Criteria
- Zero-valid vectors case surfaces explicit guidance and exits cleanly


