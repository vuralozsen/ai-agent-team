# Prosedürler

## Workflow Phases

### Phase 1: Project Analysis & Planning
```bash
# Verify project specification exists
ls -la project-specs/*-setup.md

# Spawn project-manager-senior to create task list
"Please spawn a project-manager-senior agent to read the specification file at project-specs/[project]-setup.md and create a comprehensive task list."

# Wait for completion, verify task list created
```

### Phase 2: Technical Architecture
```bash
# Verify task list exists from Phase 1
cat project-tasks/*-tasklist.md

# Spawn ArchitectUX to create foundation
"Please spawn an ArchitectUX agent to create technical architecture and UX foundation from project-specs/[project]-setup.md and task list."
```

### Phase 3: Development-QA Continuous Loop
```bash
# For each task, run Dev-QA loop until PASS
# Task 1 implementation
"Please spawn appropriate developer agent to implement TASK 1 ONLY from the task list using ArchitectUX foundation."

# Task 1 QA validation
"Please spawn an EvidenceQA agent to test TASK 1 implementation only. Provide PASS/FAIL decision with specific feedback."

# Decision logic:
# IF QA = PASS: Move to Task 2
# IF QA = FAIL: Loop back to developer with QA feedback
# Repeat until all tasks PASS QA validation
```

### Phase 4: Final Integration & Validation
```bash
# Only when ALL tasks pass individual QA
# Spawn final integration testing
"Please spawn a testing-reality-checker agent to perform final integration testing on the completed system."
```

## Decision Logic

### Task-by-Task Quality Loop
**IF QA Result = PASS:**
- Mark current task as validated
- Move to next task in list
- Reset retry counter

**IF QA Result = FAIL:**
- Increment retry counter
- If retries < 3: Loop back to dev with QA feedback
- If retries >= 3: Escalate with detailed failure report
- Keep current task focus

### Error Handling & Recovery
- Agent Spawn Failures: Retry up to 2 times, document if persistent
- Task Implementation Failures: Maximum 3 retry attempts, escalate after
- Quality Validation Failures: Retry QA spawn, request manual evidence if needed
