# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-01-09

### Changed
- Updated commit-and-push skill to use version-based CHANGELOG entries
  - Step 7 now specifies format as `[X.Y.Z] - YYYY-MM-DD` instead of `[YYYY-MM-DD]`
  - Version number is primary identifier, date is secondary reference
  - Instructions updated in `.claude/instructions.md` to reflect new format
- Restructured CHANGELOG.md to use semantic version numbers
  - Converted from date-based to version-based section headers
  - Previous entries retroactively assigned version 0.1.0
  - Pre-versioning entries moved to legacy section for historical reference

## [0.2.0] - 2026-01-09

### Added
- Semantic versioning with automatic version management to commit-and-push skill
  - `.version` file tracks current version following MAJOR.MINOR.PATCH format
  - Auto-increments version based on commit type: feat→minor, fix→patch, breaking→major
  - Creates annotated git tags for each release (e.g., v0.2.0)
  - Pushes tags along with commits using --follow-tags
  - Version starts at 0.1.0 if file doesn't exist

### Changed
- CHANGELOG.md format now uses version numbers as primary identifiers
  - Format changed from `[YYYY-MM-DD]` to `[X.Y.Z] - YYYY-MM-DD`
  - Version numbers align with semantic versioning in `.version` file
  - Dates remain as secondary reference

## [0.1.0] - 2026-01-09

### Added
- `.claude/skills/commit-and-push/` custom skill for automated git workflow
  - Runs ruff linting with auto-fix capability before committing
  - Executes full test suite as quality gate
  - Generates conventional commit messages automatically
  - Updates CHANGELOG.md systematically with version-based entries
  - Creates commits with proper attribution
  - Requires explicit confirmation before pushing to remote
  - Invocable via `/commit-and-push` or `/cap` alias
- `calculate_security_type_aggregation_by_sector.py` module for sector-based equity portfolio analysis
  - Filters equity positions using asset_key prefix matching
  - Aggregates market values and allocation percentages by sector
  - Configurable option to exclude unknown sectors
  - Produces wide-format output with sector breakdowns
  - Includes slugified column names for downstream processing
  - Provides both equity-total and account-total denominators
- `calculate_security_type_aggregation.py` module for aggregating portfolio positions by security type
  - Computes market values and allocation percentages in wide format
  - Includes helper functions: `prepare_dataframe()`, `aggregate_by_security_type()`, `calculate_allocations()`, and `pivot_to_wide_format()`
  - Comprehensive docstrings and type hints throughout
- `test/conftest.py` for centralized test fixture management
  - Organized by project and workflow following fixtures directory structure
  - Automatic fixture discovery for all test files
  - Clear sections with template for adding new workflows
- `.claude/instructions.md` with project guidelines for changelog maintenance and coding standards

### Changed
- Refactored `calculate_security_type_aggregation.py` to follow Python best practices
  - Split monolithic `main()` function (112 lines) into focused, single-responsibility functions
  - Each function now under 50 lines for better maintainability
  - Enhanced documentation with detailed Args, Returns, and Raises sections
- Reorganized test fixtures for better scalability
  - Extracted all fixtures from `test_upload_position_file_workflow.py` to `conftest.py`
  - Test file reduced from 181 to 92 lines (49% reduction)
  - Clean separation between test setup and test logic
  - Fixtures organized by workflow matching `test/fixtures/` hierarchy

## Previous Releases

For releases prior to version 0.1.0, please refer to the git commit history.

---

## Legacy Date-Based Entries (Pre-Versioning)

The following entries used date-based identifiers before semantic versioning was implemented:

### 2026-01-08

### Added
- `load_module()` utility function in `test/utils.py` for dynamic module loading
  - Supports both absolute paths and src-relative paths
  - Reusable across different workflows and test files
  - Includes comprehensive docstrings with usage examples

### Changed
- Refactored test fixture module loading to eliminate duplication
  - Removed ~28 lines of duplicated code from `test_upload_position_file_workflow.py`
  - Simplified module loading fixtures to use centralized utility

### Previous Changes

For changes prior to 2026-01-08, please refer to the git commit history.
