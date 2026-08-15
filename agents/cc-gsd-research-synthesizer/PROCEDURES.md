# Prosedürler

## Execution Flow

### Step 1: Read Research Files
```bash
cat .planning/research/STACK.md
cat .planning/research/FEATURES.md
cat .planning/research/ARCHITECTURE.md
cat .planning/research/PITFALLS.md
```

### Step 2: Synthesize Executive Summary
Answer:
- What type of product is this and how do experts build it?
- What's the recommended approach based on research?
- What are the key risks and how to mitigate them?

### Step 3: Extract Key Findings
- **From STACK.md**: Core technologies with rationale
- **From FEATURES.md**: Must-have features, should-have features, anti-features
- **From ARCHITECTURE.md**: Major components, key patterns
- **From PITFALLS.md**: Top pitfalls with prevention strategies

### Step 4: Derive Roadmap Implications
**Suggest phase structure**:
- What should come first based on dependencies?
- What groupings make sense based on architecture?
- Which features belong together?

**Add research flags**:
- Which phases need `/gsd:research-phase` during planning?
- Which phases have well-documented patterns (skip research)?

### Step 5: Assess Confidence
| Area | Confidence | Notes |
|------|------------|-------|
| Stack | [level] | Based on source quality from STACK.md |
| Features | [level] | Based on source quality from FEATURES.md |
| Architecture | [level] | Based on source quality from ARCHITECTURE.md |
| Pitfalls | [level] | Based on source quality from PITFALLS.md |

### Step 6: Write SUMMARY.md
Use template with all required sections

### Step 7: Commit All Research
```bash
node gsd-tools.cjs commit "docs: complete project research" --files .planning/research/
```

## Structured Returns
```markdown
## SYNTHESIS COMPLETE

**Files synthesized**:
- .planning/research/STACK.md
- .planning/research/FEATURES.md
- .planning/research/ARCHITECTURE.md
- .planning/research/PITFALLS.md

**Output**: .planning/research/SUMMARY.md

### Executive Summary
[2-3 sentence distillation]

### Roadmap Implications
Suggested phases: [N]

1. **[Phase name]** — [one-liner rationale]
2. **[Phase name]** — [one-liner rationale]

### Research Flags
Needs research: Phase [X], Phase [Y]
Standard patterns: Phase [Z]

### Confidence
Overall: [HIGH/MEDIUM/LOW]
Gaps: [list any]

### Ready for Requirements
SUMMARY.md committed. Orchestrator can proceed to requirements definition.
```
