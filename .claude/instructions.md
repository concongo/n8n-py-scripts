# Project Instructions for Claude Code

## Changelog Management

This project maintains a `CHANGELOG.md` file at the root of the repository to track all notable changes.

### When to Update the Changelog

Update the CHANGELOG.md file whenever you:
- Add new features or modules
- Make significant refactoring changes
- Fix bugs
- Change or remove existing functionality
- Update dependencies in a meaningful way

### How to Update the Changelog

1. Add entries under the `[Unreleased]` section
2. Use the following categories:
   - **Added** - for new features
   - **Changed** - for changes in existing functionality
   - **Deprecated** - for soon-to-be removed features
   - **Removed** - for now removed features
   - **Fixed** - for any bug fixes
   - **Security** - in case of vulnerabilities

3. When making commits, move unreleased changes to a dated section using the format `[YYYY-MM-DD]`

### Example Entry

```markdown
## [Unreleased]

### Added
- New utility function for data processing with comprehensive documentation

### Changed
- Refactored authentication module to improve maintainability
```

## Commit Message Format

Follow the conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for code refactoring
- `docs:` for documentation changes
- `test:` for test additions or changes
- `chore:` for maintenance tasks

## Python Code Standards

- Follow Python best practices and PEP 8
- Keep functions under 50 lines when possible
- Add comprehensive docstrings with Args, Returns, and Raises sections
- Use type hints consistently
- Write tests for new functionality
