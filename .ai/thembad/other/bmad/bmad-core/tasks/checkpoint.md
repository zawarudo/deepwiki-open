# Checkpoint Task

## Purpose

Save the current work state into AI-friendly files that enable seamless continuation of work later. This creates a comprehensive snapshot of progress, context, and next steps organized for optimal AI resumption.

## Primary Goals

1. **Capture Current State**: Document what has been accomplished, decisions made, and current working context
2. **Organize for AI Continuation**: Structure information in a way that allows AI agents to quickly understand and continue work
3. **Create Resume Point**: Generate a main continue-task.prompt.md file that serves as the primary entry point for resuming work
4. **Preserve Context**: Maintain all relevant context, decisions, and working assumptions

## Process

### 1. Identify Current Feature/Project

Ask the user to identify:
- Current feature or project name (will be used as `{our-feature}` in file paths)
- Brief description of what they're working on
- Current stage/phase of work

### 2. Context Gathering

Collect information about:

**Current Status:**
- What has been completed so far
- What is currently in progress
- What decisions have been made
- What assumptions are being used

**Working Context:**
- Current documents and files being worked on
- Key stakeholders and their requirements
- Technical constraints and preferences
- Any blockers or challenges encountered

**Next Steps:**
- What needs to be done next
- Priority order of upcoming tasks
- Dependencies that need to be resolved
- Success criteria for completion

### 3. Create Directory Structure

Create the following directory structure:
```
.ai/feature/{our-feature}/
├── continue-task.prompt.md           # Main resume point
├── context/
│   ├── current-state.md             # Current progress and status
│   ├── decisions-made.md            # Key decisions and rationale
│   ├── working-assumptions.md       # Current assumptions and constraints
│   └── stakeholder-requirements.md  # Requirements and expectations
├── artifacts/
│   ├── documents/                   # Copies of current working documents
│   ├── notes/                       # Meeting notes, brainstorming, etc.
│   └── research/                    # Research findings and insights
└── next-steps/
    ├── immediate-tasks.md           # Next 1-3 tasks to complete
    ├── backlog.md                   # Upcoming tasks and considerations
    └── success-criteria.md          # How to know when done
```

### 4. Generate Core Files

#### A. continue-task.prompt.md (Primary Resume File)

This is the main entry point for resuming work. Structure it as:

```markdown
# Continue Task: {Feature Name}

## Context Summary
Brief overview of what we're working on and current state.

## Current Status
What's been completed, what's in progress, where we left off.

## Immediate Next Steps
The next 1-3 specific tasks that need to be completed.

## Key Context Files
- [Current State Details](./context/current-state.md)
- [Decisions Made](./context/decisions-made.md)
- [Working Assumptions](./context/working-assumptions.md)
- [Stakeholder Requirements](./context/stakeholder-requirements.md)

## Working Files
List of current documents and files being worked on.

## Success Criteria
How to know when this feature/project is complete.

## Agent Instructions
Specific instructions for the AI agent on how to continue this work:
- What persona/role to adopt
- What tools and resources to use
- What communication style to maintain
- What constraints to respect

## Quick Start Commands
Specific commands or actions to take immediately upon resuming.
```

#### B. Context Files

**current-state.md:**
- Detailed status of all work streams
- Progress percentages and completion status
- Current working documents and their status
- Recent accomplishments and milestones

**decisions-made.md:**
- Key decisions made during this work session
- Rationale behind each decision
- Alternative options considered
- Impact and implications of decisions

**working-assumptions.md:**
- Current assumptions about requirements
- Technical constraints and preferences
- User needs and market conditions
- Resource availability and timelines

**stakeholder-requirements.md:**
- Requirements from each stakeholder
- Priority levels and must-haves
- Communication preferences
- Approval processes and checkpoints

#### C. Artifacts

Copy or reference current working documents:
- Current PRD versions
- Design documents
- Technical specifications
- Research findings
- Meeting notes
- Brainstorming outputs

#### D. Next Steps Files

**immediate-tasks.md:**
- Next 1-3 specific tasks with clear descriptions
- Dependencies and prerequisites
- Estimated effort and timeline
- Success criteria for each task

**backlog.md:**
- Upcoming tasks and considerations
- Future features and enhancements
- Technical debt and improvements
- Long-term strategic items

**success-criteria.md:**
- Definition of done for the overall feature
- Acceptance criteria and testing requirements
- Stakeholder approval requirements
- Launch criteria and success metrics

### 5. Optimization for AI Continuation

Ensure each file:
- **Starts with context**: Brief summary of what this file contains
- **Uses clear headers**: Structured for easy scanning
- **Includes timestamps**: When information was captured
- **References connections**: Links to related files and decisions
- **Provides specifics**: Concrete details rather than vague descriptions

### 6. Validation and Summary

After creating all files:

1. **Review completeness**: Ensure all important context is captured
2. **Check AI-readability**: Verify files are structured for AI consumption
3. **Test resume flow**: Ensure the continue-task.prompt.md provides clear next steps
4. **Create summary**: Provide brief overview of what was checkpointed

## Output Format

Present the user with:

```text
Checkpoint created successfully for: {Feature Name}

Primary resume file: .ai/feature/{our-feature}/continue-task.prompt.md

Files created:
- continue-task.prompt.md (Main resume point)
- context/current-state.md
- context/decisions-made.md  
- context/working-assumptions.md
- context/stakeholder-requirements.md
- artifacts/[copied working files]
- next-steps/immediate-tasks.md
- next-steps/backlog.md
- next-steps/success-criteria.md

Next time you want to continue this work, simply reference the continue-task.prompt.md file to get back up to speed quickly.
```

## Usage Notes

- **Feature naming**: Use descriptive names that clearly identify the work
- **Regular checkpoints**: Recommend creating checkpoints at natural stopping points
- **Context updates**: Update checkpoint files as work progresses
- **AI instructions**: Tailor the agent instructions based on what type of work will continue
- **File organization**: Keep artifacts organized and properly referenced

This checkpoint system enables seamless work continuation by providing comprehensive context in an AI-optimized format. 