# Agent Guide for raiffeisen_to_zenmoney

This file is a compact, repo-specific guide for agentic coding tools.
Keep changes small, follow existing patterns, and avoid touching secrets.

## Project Snapshot
- Language: Python 3.13+
- Package manager: uv
- Entry point: src/main.py
- Config: config.yaml (local only, never commit)
- Services: email -> XML -> operations -> ZenMoney API

## Quick Start
```bash
uv sync
cp config.sample.yaml config.yaml
python src/main.py
```

## Build / Lint / Test
Note: no explicit build step; run via python or package as needed.

### Lint
```bash
ruff check src/
```

### Format
```bash
black src/
```

### Tests
```bash
pytest
```

### Run a single test
Use one of these, prefer the most precise selector available:
```bash
pytest tests/test_file.py::test_name
pytest -k "keyword" tests/
```

## Repo Docs for Context
Start here for fast onboarding:
- .ai/QUICKSTART.md
- .ai/project-map.md
- .ai/codebase-context.md
- .ai/development-guide.md

## Configuration and Secrets
- Never commit config.yaml (contains credentials)
- Use config.sample.yaml as template
- API keys and passwords must stay out of source
- Safe overrides via environment variables are acceptable

## Code Style and Conventions

### General
- Follow PEP 8 and keep functions small and focused
- Prefer explicit, readable logic over cleverness
- Use type hints on all new functions and public methods
- Use docstrings for non-obvious behavior or public APIs

### Imports
- Group imports: stdlib, third-party, local
- Prefer absolute imports within the src/ package
- Keep imports sorted and minimal

### Types and Models
- Pydantic models are used for API payloads and parsing
- Dataclasses are used for internal operation types
- RawOperation and Statement are Pydantic models
- Operation types (Simple/Transition/Deel/CashWithdrawal) are dataclasses

### Naming
- snake_case for functions, variables, and modules
- PascalCase for classes
- Constants in ALL_CAPS for module-level config
- Avoid abbreviations unless already established (e.g., op, cfg)

### Formatting
- Use black formatting (default settings)
- Keep lines reasonably short; avoid deep nesting
- Prefer f-strings for string formatting

### Error Handling
- Current pattern: let exceptions propagate
- Raise descriptive exceptions at integration boundaries
- Avoid swallowing errors unless you also log context

### Logging / Output
- Current behavior prints status messages to stdout
- If adding logs, keep them concise and actionable

## Domain-Specific Patterns

### Configuration Access
- New code should use config.get(...)
- Legacy code may use envs.py constants for compatibility

### Operation Pipeline
- get_statements() -> prepare_operations() -> filter_operations()
  -> prepare_new_state() -> update_state()
- Link exchanges by reference number and exchange keywords
- Deel transfers and cash withdrawals are detected by keyword rules

### ZenMoney API Models
- Field names match API camelCase
- Optional fields default to None
- Use NewZenMoneyState for updates

## Testing Guidance
- Prefer unit tests around linking, detection, and mapping
- Keep tests deterministic; mock IMAP and API calls
- Validate date formats in duplicate detection logic

## Files to Know
- src/main.py: entry point and orchestration
- src/config.py: YAML config loader
- src/envs.py: legacy constants bridge
- src/services/emails_statements/: IMAP + XML parsing
- src/services/operations/: operation detection and dedupe
- src/services/zen_money/: API models and sync

## Notes for Agents
- Do not modify config.yaml or add secrets
- Update config.sample.yaml if config shape changes
- Keep behavior stable; this tool syncs real financial data
- Test with small date ranges (DAYS=1) when verifying

## Auto-Cleanup of Duplicates
The system automatically detects and removes duplicate transactions during each sync:

### What Gets Auto-Cleaned
- **SMS Duplicates**: Operations added twice with/without "Stanje: ***" suffix
- **Import Duplicates**: Same date, amount, currency with matching import comments

### How It Works
1. During `main()` execution, `auto_cleanup_duplicates()` runs first
2. Scans ZenMoney for duplicate transactions
3. Keeps newest version (by created timestamp), removes older ones
4. No manual intervention required

### Code Location
- `src/services/zen_money/auto_cleanup.py`: Auto-cleanup module
- `src/main.py`: Integrated at the start of sync process

### Important
- Auto-cleanup runs automatically on every sync
- No user action required
- Never delete `src/services/zen_money/auto_cleanup.py`
- Documentation about duplicates: `.ai/SMS_DUPLICATES_GUIDE.md`

## Cursor / Copilot Rules
- No .cursor/rules/, .cursorrules, or .github/copilot-instructions.md found
- Duplicate cleanup is automatic - no manual cleanup scripts needed
