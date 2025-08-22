# @checkpoint Command System Prompt

## Trigger Words
When I say these words:
- checkpoint-options

## Command Purpose
This means your context is getting full, and you need to create a structured checkpoint before switching development phases.
OR
The user has provided a checkpoint file with a next-phase prompt to follow, read and follow the instructions.

## Checkpoint Workflow
1. **Determine specification name for the checkpoint output <date-feature-name.md>**
- 1.a If continuing the conversation with a checkpoint provided take from current context 
- 1.b If no checkpoint file was attached, create a new checkpoint file/scratchpad with the instructions below

2. Update/Generate checkpoint specification file/scratchpad output
   - Summarize the goals and outcomes of this chat (The "what")
   - To each goal and outcome, identify if too vague, if too vague add a section `JUSTIFICATION` - Explain the "why"/"how" behind the "what"
   - At the end of the checkpoint for this section add `ACTION-PLAN` section with a clear set of high level instructions and TODO's for a developer or researcher to continue based on your agent mode.
   - At the top, create a system prompt based on your agent mode adapted to the next step/phase (pm.txt / qa.txt)

## Key Principles
- **Create specification-specific documentation** that captures current specification/task phase
- **Preserve key context** across sessions for complex development workflows
- **Enable phase transitions** by creating actionable next-phase prompts

## Next Phase Determination
Choose next phase based on current specification state
- If the user agrees all goals of this phase are met with no unresolved issues or unknowns, propose we are ready for the next phase of work

Phases are usually defined as

Development:
- High level specs (PRD) > Specs by domain > System architecture design > System design task breakdown > Task implementation (Coding) 

Research Tasks:
- High level specs (PRD) > Specs by domain > Task implementation (Research) 

Product Management:
- High level specs (PRD) > Specs by domain > System architecture design > System design task breakdown > Task implementation (Dev/Research) 

## Checkpoint Options functionality
- Identify current solution approaches as a crossing point where a path must be taken.
- Summarize into a list; the user can choose these options.

### SPLIT ${NAME}
- Split all currently available solution spaces in the text into `checkpoint/name/{Approach Name}`.

### {Approach Name} examples
`IV. - Approach 4 Modification of X subsystem`
