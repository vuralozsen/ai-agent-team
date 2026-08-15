# Kurallar

## Quality Gate Enforcement
- **No shortcuts**: Every task must pass QA validation
- **Evidence required**: All decisions based on actual agent outputs ve evidence
- **Retry limits**: Maximum 3 attempts per task before escalation
- **Clear handoffs**: Each agent gets complete context ve specific instructions

## Pipeline State Management
- **Track progress**: Maintain state of current task, phase, ve completion status
- **Context preservation**: Pass relevant information between agents
- **Error recovery**: Handle agent failures gracefully with retry logic
- **Documentation**: Record decisions ve pipeline progression
