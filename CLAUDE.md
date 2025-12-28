# CLAUDE.md

Project-specific guidance for Claude when working on this codebase.

## Bash Commands

```bash
uv run tally --help              # Show all commands
uv run tally run /path/to/config # Run analysis
uv run tally diag /path/to/config # Debug config issues
uv run tally discover /path/to/config # Find unknown merchants
uv run tally inspect file.csv    # Analyze CSV structure
uv run pytest tests/             # Run all tests
uv run pytest tests/test_analyzer.py -v # Run analyzer tests
```

## Core Files

- `src/tally/analyzer.py` - Core analysis, HTML report generation, currency formatting
- `src/tally/cli.py` - CLI commands, AGENTS.md template (update for new features)
- `src/tally/config_loader.py` - Settings loading, migration logic
- `src/tally/format_parser.py` - CSV format string parsing
- `src/tally/merchant_utils.py` - Merchant normalization, rule matching
- `tests/test_analyzer.py` - Main test file for new features

## IMPORTANT: Requirements

**Testing:**
- YOU MUST add tests for new analyzer features in `tests/test_analyzer.py`
- YOU MUST use Playwright MCP to verify HTML report changes before committing

**Development:**
- YOU MUST use `uv run` to run tally (not `python -m tally`)
- YOU MUST reference issues with `Fixes #N` or `Closes #N` in commits

**Releases:**
- YOU MUST use GitHub workflow for releases (never manual)

**Configuration:**
- YOU MUST maintain backwards compatibility for `settings.yaml`
- YOU MUST document new options in `config/settings.yaml.example`
- YOU MUST update AGENTS.md in `cli.py` for new user-facing features

## Code Style

- Error messages MUST be self-descriptive with actionable suggestions
- The tool MUST be usable without external documentation
