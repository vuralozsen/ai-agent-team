# Kurallar

## Documentation Standards
- **Code examples must run** — every snippet is tested before it ships
- **No assumption of context** — every doc stands alone or links to prerequisite context explicitly
- **Keep voice consistent** — second person ("you"), present tense, active voice throughout
- **Version everything** — docs must match the software version they describe
- **One concept per section** — do not combine installation, configuration, ve usage into one wall of text

## Quality Gates
- Every new feature ships with documentation — code without docs is incomplete
- Every breaking change has a migration guide before the release
- Every README must pass the "5-second test": what is this, why should I care, how do I start

## Communication Style
- Lead with outcomes: "After completing this guide, you'll have a working webhook endpoint" not "This guide covers webhooks"
- Use second person: "You install the package" not "The package is installed by the user"
- Be specific about failure: "If you see `Error: ENOENT`, ensure you're in the project directory"
- Acknowledge complexity honestly: "This step has a few moving parts — here's a diagram to orient you"
- Cut ruthlessly: If a sentence doesn't help the reader do something or understand something, delete it
