### New Feature Setup

**Trigger**: `@feature` or `new feature`

REQUIRED: Confirm each step is correctly complete before moving to the next. Confirm correct directories and files are created. Do not skip the Planning Phase Initiation step; check in early before writing out the final IMPLEMENTATION.prompt.md.

1. **Feature Identification**
   - If no feature name provided, ask one question at a time to identify feature name
   - Create feature directory: `.ai/feature/{feature-name}/`

2. **Directory Structure Creation**
   ```
   .ai/feature/{feature-name}/
   ├── LLM-ACTION-PLAN.md           # Main planning document
   ├── ACTION-PLAN-JUSTIFICATION.md # Benefits/negatives analysis  
   ├── IMPLEMENTATION.prompt.md     # Next phase system prompt
   └── scratchpad/                  # Open-ended workspace
       ├── research/                # Research notes and findings
       ├── notes/                   # Meeting notes, performance notes
       └── ideas/                   # Random thoughts, brainstorming
   ```

3. **Planning Phase Initiation**
   - Begin collaborative vision and architecture discussion
   - Use one question at a time approach
   - Build thorough step-by-step specification
