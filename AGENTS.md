# Household Economy Analysis - Agent Guide

This repository contains the HEA Warehouse, a Django/Django REST Framework application for managing global Household Economy Analysis baseline data.

This file is the canonical repository policy for coding agents working in this repository. Agent-specific files should reference this document instead of duplicating it.

## Scope

- This file describes repository conventions and safe command patterns.
- It does not grant shell or filesystem permissions by itself.
- Actual approval and trust behavior is enforced by each client tool and local workspace settings.

## Working Directory

- Run commands from the repository root.
- Prefer the direct project commands the team already uses.
- Activate the virtual environment before Python or Django commands.

## Preferred Commands

- `source .venv/bin/activate && ./manage.py check`
- `source .venv/bin/activate && ./manage.py test --settings hea.settings.ci --keepdb --noinput`
- `source .venv/bin/activate && ./manage.py test --settings hea.settings.ci --noinput`
- `source .venv/bin/activate && black --check .`
- `source .venv/bin/activate && ruff check .`
- `source .venv/bin/activate && isort --check-only .`

If local tool settings support command allowlists, trust `./manage.py` and the small set of lint/test commands above directly instead of introducing a wrapper layer.

## Safe Commands

These commands are expected during normal development and usually do not require extra confirmation when the workspace is already trusted:

- Read-only inspection: `git status`, `git diff`, `git diff --cached`, `git show`, `rg`, `ls`, `pwd`, `cat`, `sed`, `find`
- Python environment setup inside the repo: `source .venv/bin/activate`
- Django commands: `./manage.py ...`
- Test commands: `./manage.py test --settings hea.settings.ci --keepdb --noinput ...`
- Formatting and lint checks: `black --check .`, `ruff check .`, `isort --check-only .`

## Commands That Still Need Explicit Confirmation

- Dependency installation or upgrades
- Destructive git operations such as `git reset --hard` or force pushes
- Database-destructive commands where data loss is plausible
- Editing large fixtures, locale bundles, or generated assets unless the task explicitly requires it
- Authentication flows, browser sign-in, or writing machine-local config outside the repository

## Filesystem Expectations

- Reading files inside this repository is expected.
- Repository-local configuration files are preferred over editor-user files.
- Access to files outside the repository, including VS Code user storage and home-directory config, depends on the client tool and local trust settings.
- If repository instructions are needed by multiple agents, keep them under version control here instead of relying on editor-specific user files.

## Environment

- Always activate the virtual environment before running any commands: `source .venv/bin/activate`.
- The application is a Django project (`manage.py` in the repo root) with DRF APIs and supporting tooling configured through `pyproject.toml`.
- The `apps` directory is included in the `PYTHONPATH`, so use `from baseline.models import XXX` instead of `from apps.baseline import XXX`
- Prefer the direct project commands the team already uses, especially `./manage.py`, `black`, `ruff`, and `isort`.

## Development Workflow

- Make code changes inside the repository root.
- Install additional packages by updating `requirements/base.txt` and then running `uv pip install -r requirements/base.txt`
- Keep data fixtures, locale files, and other large assets untouched unless explicitly requested.
- Generate ER diagrams via the command sequence documented in `README.md` if schema updates need diagrams.
- Authentication flows, editor-user files, and other machine-local configuration are outside normal repository changes. Only touch them when the task explicitly requires it.
- Work is tracked in Jira tickets at https://fewsnet.atlassian.net/jira/software/c/projects/HEA/ and accessible via the https://mcp.atlassian.com/v1/mcp/authv2.
- All work for this repository should be in tickets in the HEA space in the fewsnet.atlassian.net Jira instance.
- Jira tickets should be moved to In Progress status once work on them begins.
- Work should be carried out in feature branches with a branch name that begins with the ticket, for example `HEA-999/Improved_admin_screens`.
- Commit messages should end with `- see <Jira ticket reference>`, e.g. `Better KPI stat for home page - see HEA-999`.

## Coding Standards

- Code should use modern best practices for the Python version specified in docker/app/Dockerfile.
- All Classes and Functions require multiline docstrings.
- Format Python code using `black` with the settings from `pyproject.toml`.
- Sort imports with `isort` with the settings from `pyproject.toml`.
- Lint and static-check using `ruff` with the settings from `pyproject.toml`.
- Run the formatters before committing.
- Create and use modern type hints.
- Use imports from the `apps` PYTHONPATH root, for example `from baseline.models import ExampleModel`.
- Keep changes inside the repository root.
- Avoid touching fixtures, locale files, and other large assets unless the task requires it.
- Use `import datetime`: For consistency the project will import the datetime library directly, rather then performing absolute imports of the underlying components. This avoids confusion when some developers use `from datetime import datetime` and some use `import datetime`.
- Use standard library functions or common libraries rather than writing your own:
    - F-Strings
    - defaultdict
    - functools (for partial , reduce , lru_cache etc.)
    - logging rather than print
    - operator.and , operator.or
    - pandas
    - requests
- Prefer timezone-aware DateTime objects: `datetime.datetime.now(datetime.timezone.utc)`

## Testing

- Run the default test suite with the CI settings module and persistent database for speed: `source .venv/bin/activate && ./manage.py test --settings hea.settings.ci --keepdb --noinput`
- If tests fail because of a stale database or migration issues, then rerun the tests without the --keepdb before doing any further diagnosis, using --noinput so that the test database is created without further prompting: `source .venv/bin/activate && ./manage.py test --settings hea.settings.ci --noinput`
- When iterating quickly, run tests for a single module, test case or test method by appending the dot-notation path to the test(s). For example: `source .venv/bin/activate && ./manage.py test --settings hea.settings.ci --noinput --keepdb pipelines_tests.test_assets.test_livelihood_activity_assets.GetActivityLabelAttributesTestCase`
- Always run tests from the repository root. Tests rely on the local Postgres instance listening on `$DATABASE_URL`, so ensure that service is running before invoking the suite.
- When writing new TestCase classes use the `setUpTestData` class method to create reusable test data.
- Use the existing FactoryBoy factories to create test data. Prefer simple factory calls that let the factories create parent objects, rather than creating each object in the hierarchy and then setting the foreign keys on child objects directly.
- Prefer creating actual test data using FactoryBoy factories to using `unittest.mock`.

## Review Conventions

- For docs-only or prompt-only changes, skip Python formatting, lint, and test commands as not applicable.
- For Python or migration changes, run targeted checks first and widen only when the task requires it.

## Additional Notes
- Sensitive production data is not stored here; fixtures such as `example_fixture.json` are safe to load for local development.
- Docker compose files exist for services like Dagster; prefer local Django commands unless container-specific behavior must be validated.
- Always document non-trivial migrations, data loads, or management commands in `README.md` or `docs/` to keep the knowledge base current.
