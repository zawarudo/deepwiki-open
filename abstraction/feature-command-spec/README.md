# Feature Command Spec

This abstraction modularizes the feature planning command into focused documents for reuse and maintenance. It is derived from `.ai/thembad/feature/start-feature.md` and split by function: command triggers and purpose, workflows, methodology, templates, quality gates, and governance.

## Structure

- command/
  - triggers.md
  - purpose.md
  - interaction-protocol.md
  - role-persona.md
- workflow/
  - new-feature.md
  - continue-feature.md
- templates/
  - directory-structure.md
  - checklist-template.md
- methodology/
  - phases.md
  - granularity-guidelines.md
- quality/
  - success-criteria.md
  - critical-assessment-rules.md
- governance/
  - modification-rule.md

## How to use

- Start here to understand responsibilities and navigate to the relevant module.
- Combine `workflow/*` with `templates/*` to run a new feature or continue an existing one.
- Apply `methodology/*` to guide planning and implementation.
- Enforce `quality/*` before declaring work complete.
- Follow `governance/modification-rule.md` when evolving the system.

## Origin

Source: `.ai/thembad/feature/start-feature.md` split into cohesive modules to enable clarity, reuse, and future automation (schema/CLI).

## Diagrams

### System Flow

```mermaid
graph TD;
A["User triggers command<br/>(@feature | new feature | continue feature)"] --> B{"Mode selected?"};
B -->|"New Feature"| N1["Identify feature name (ask one question at a time)"];
N1 --> N2["Create directory structure<br/>.ai/feature/{feature-name}/..."];
N2 --> N3["Initiate Planning Phase"];
B -->|"Continue Feature"| C1["Discover/select feature (tree -d .ai/feature/)"];
C1 --> C2["Load context<br/>(LLM-ACTION-PLAN.md, ACTION-PLAN-JUSTIFICATION.md)"];
C2 --> C3["Adopt IMPLEMENTATION.prompt.md role & mission"];
N3 --> P1["Phase 1: Planning & Architecture"];
C3 --> P1;
P1 --> P2["Phase 2: Implementation Planning"];
P2 --> T["Use checklist template (Architecture/Implementation/Validation)"];
T --> Q["Apply quality gates (success criteria & critical assessment)"];
Q --> D["Developer-ready specification produced"];
```

### Module Interactions

```mermaid
graph LR;
Command["command/*\\n(triggers, purpose, interaction, role)"] --> Workflow["workflow/*\\n(new-feature, continue-feature)"];
Command --> Methodology["methodology/*\\n(phases, granularity-guidelines)"];
Workflow --> Templates["templates/*\\n(directory-structure, checklist-template)"];
Methodology --> Templates;
Templates --> Quality["quality/*\\n(success-criteria, critical-assessment-rules)"];
Workflow --> Quality;
Quality --> Governance["governance/*\\n(modification-rule)"];
Governance -.-> Command;
```
