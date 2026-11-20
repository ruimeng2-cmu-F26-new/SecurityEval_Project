# Static rule-test fixtures (hand-written)

These files are **hand-written rule tests for Member 2's AST rules**. They are not
SecurityEval samples and not LLM generations; never report findings on them as
experiment results. They are parsed by the scanners only and are never imported or run.

A line ending in `# expect: <RULE_ID>` (or several IDs separated by spaces) must be reported by those AST rules; every other
line must not be. `*_unsafe.py` files contain known-unsafe patterns, `*_safe.py` files
contain known-safe or out-of-scope patterns (expected: zero AST findings).
`no_findings.py` and `syntax_error.py` exercise Bandit's no-finding and error paths.
