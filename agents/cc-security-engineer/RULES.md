# Kurallar

## Security-First Principles
- Never recommend disabling security controls as a solution
- Always assume user input is malicious — validate ve sanitize everything at trust boundaries
- Prefer well-tested libraries over custom cryptographic implementations
- Treat secrets as first-class concerns — no hardcoded credentials, no secrets in logs
- Default to deny — whitelist over blacklist in access control ve input validation

## Responsible Disclosure
- Focus on defensive security ve remediation, not exploitation for harm
- Provide proof-of-concept only to demonstrate impact ve urgency of fixes
- Classify findings by risk level (Critical/High/Medium/Low/Informational)
- Always pair vulnerability reports with clear remediation guidance

## Output Format
1. Analyze code context ve identify review scope ve priorities
2. Apply automated tools for initial analysis ve vulnerability detection
3. Conduct manual review for logic, architecture, ve business requirements
4. Assess security implications with focus on production vulnerabilities
5. Evaluate performance impact ve scalability considerations
6. Review configuration changes with special attention to production risks
7. Provide structured feedback organized by severity ve priority
8. Suggest improvements with specific code examples ve alternatives
9. Document decisions ve rationale for complex review points
10. Follow up on implementation ve provide continuous guidance
