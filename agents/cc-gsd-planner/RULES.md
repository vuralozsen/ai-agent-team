# Kurallar

## Solo Developer + Claude Workflow
Planning for ONE person (the user) ve ONE implementer (Claude)
- No teams, stakeholders, ceremonies, coordination overhead
- User = visionary/product owner, Claude = builder
- Estimate effort in Claude execution time, not human dev time

## Plans Are Prompts
PLAN.md IS the prompt (not a document that becomes one). Contains:
- Objective (what and why)
- Context (@file references)
- Tasks (with verification criteria)
- Success criteria (measurable)

## Quality Degradation Curve
| Context Usage | Quality | Claude's State |
|---------------|---------|----------------|
| 0-30% | PEAK | Thorough, comprehensive |
| 30-50% | GOOD | Confident, solid work |
| 50-70% | DEGRADING | Efficiency mode begins |
| 70%+ | POOR | Rushed, minimal |

**Rule**: Plans should complete within ~50% context. Each plan: 2-3 tasks max.

## Discovery Levels
**Level 0 - Skip**: ALL work follows established codebase patterns (grep confirms)
**Level 1 - Quick Verification**: Single known library, confirm syntax/version
**Level 2 - Standard Research**: Choosing between 2-3 options, new external integration
**Level 3 - Deep Dive**: Architectural decision with long-term impact, novel problem

For niche domains (3D, games, audio, shaders, ML), suggest `/gsd:research-phase` before plan-phase.
