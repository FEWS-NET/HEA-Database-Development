---
description: "Review currently staged git changes and report concrete risks before commit"
name: "Review Staged Changes"
argument-hint: "Optional focus area, risk tolerance, or files to prioritize"
agent: "agent"
---
Review the currently staged changes in this repository.

Inputs:
- Primary input is the staged diff from `git diff --cached --unified=0`.
- Also inspect staged file content when needed for context.
- If there are no staged changes, say so and stop.

Task:
- Perform a code-review pass focused on defects, regressions, and missing tests.
- Prioritize behavior changes, data integrity, migrations, API compatibility, and performance risks.
- Verify migration ordering/dependencies if migration files are staged.
- Decide whether the staged files are code-affecting or docs-only/prompt-only/agent-metadata-only changes before running validation commands.
- For Python, migrations, or other executable code changes, run the validation commands from "Standard execution sequence" and include the outcome.
- For docs-only, prompt-only, or agent-metadata-only changes, explicitly report that Python formatting, lint, and test commands were not applicable.
- Use repository conventions when judging correctness.

Standard execution sequence:
1. Run from repository root.
2. Activate environment:
	- `source .venv/bin/activate`
3. Run formatting/lint checks in this order:
	- `black --check .`
	- `ruff check .`
	- `isort --check-only .`
4. Run tests with CI settings:
	- `./manage.py test --settings hea.settings.ci --keepdb --noinput`
5. If tests fail specifically due to stale test DB/migration mismatch, rerun once with:
	- `./manage.py test --settings hea.settings.ci --noinput`

Execution rules:
- Do not silently skip any step.
- If the staged diff is docs-only, prompt-only, or agent-metadata-only, skip the Python validation steps and report them as not applicable.
- Continue through all check commands and report each result, even if one fails.
- For tests, stop after the first successful command or after both test commands fail.
- If a command cannot run, report the exact blocker.

Output format:
1. Findings (ordered by severity)
- For each finding include: severity, why it matters, and a concrete fix suggestion.
- Include file and line references for each finding.
2. Open questions / assumptions
- Call out uncertain intent or missing context.
3. Suggested tests
- List high-value tests to add or run for confidence.
4. Test run result
- Report exact test command(s), pass/fail status, whether fallback rerun was used, or that tests were not applicable.
5. Formatting/lint check result
- Report exact commands for `black`, `ruff`, and `isort`, pass/fail for each, or that they were not applicable.
6. Brief summary
- One short paragraph with overall risk level.

Rules:
- Do not rewrite code unless explicitly asked.
- Be specific and actionable; avoid generic style-only comments.
- If no material issues are found, state "No findings" and still list residual risks/testing gaps.

If the user includes additional arguments, treat them as review constraints and apply them.
