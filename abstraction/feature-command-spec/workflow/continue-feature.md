### Continue Feature

**Trigger**: `continue feature` or `continue feature {name}`

1. **Feature Discovery**
   - `continue feature` → Use `tree -d .ai/feature/` to list available features
   - `continue feature {name}` → Auto-load that feature's IMPLEMENTATION.prompt.md as system context

2. **Context Loading**
   - Read existing `LLM-ACTION-PLAN.md` and `ACTION-PLAN-JUSTIFICATION.md`
   - Adopt `IMPLEMENTATION.prompt.md` role and mission
   - Continue from last documented state
