# Prosedürler

## Execution Flow

### Step 1: load_project_state
Load planning context:
- Read STATE.md for position, decisions, blockers
- Check codebase map for relevant documents

### Step 2: identify_phase
Read existing PLAN.md or DISCOVERY.md in phase directory
**If `--gaps` flag**: Switch to gap_closure_mode

### Step 3: mandatory_discovery
Apply discovery level protocol (Level 0-3)

### Step 4: read_project_history
Generate digest index, select relevant phases, read full SUMMARYs

### Step 5: gather_phase_context
Read CONTEXT.md, RESEARCH.md, DISCOVERY.md

### Step 6: break_into_tasks
Decompose phase into tasks
Think dependencies first, not sequence

### Step 7: build_dependency_graph
Map dependencies explicitly before grouping
Identify parallelization: No deps = Wave 1, depends only on Wave 1 = Wave 2

### Step 8: assign_waves
Calculate wave numbers based on dependencies

### Step 9: group_into_plans
Same-wave tasks with no file conflicts → parallel plans

### Step 10: derive_must_haves
Apply goal-backward methodology

### Step 11: estimate_scope
Verify each plan fits context budget: 2-3 tasks, ~50% target

### Step 12: confirm_breakdown
Present breakdown with wave structure

### Step 13: write_phase_prompt
Create PLAN.md files with all frontmatter fields

### Step 14: validate_plan
Validate each PLAN.md using gsd-tools

### Step 15: update_roadmap
Update ROADMAP.md to finalize phase placeholders

### Step 16: git_commit
Commit all PLAN.md files

## Plan Format
```markdown
---
phase: XX-name
plan: NN
type: execute
wave: N
depends_on: []
files_modified: []
autonomous: true
requirements: []
user_setup: []

must_haves:
  truths: []
  artifacts: []
  key_links: []
---

<objective>
[What this plan accomplishes]
Purpose: [Why this matters]
Output: [Artifacts created]
</objective>

<context>
@templates/execute-plan.md
@templates/summary.md
</context>

<tasks>
<task type="auto">
<name>Task 1: [Action-oriented name]</name>
<files>path/to/file.ext</files>
<action>[Specific implementation]</action>
<verify>[Command or check]</verify>
<done>[Acceptance criteria]</done>
</task>
</tasks>
```
