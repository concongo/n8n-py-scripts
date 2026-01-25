# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-01-25

### Added
- Sector drift and concentration analysis module `calculate_sector_drift.py`
  - Analyzes sector-level portfolio data to assess sector concentration risk
  - Calculates concentration metrics: top sector weight, top 3 sectors weight, average sector weight
  - Sector details: market value, symbol count, and average P/E per sector
  - Boolean flags for concentration alerts: sector_concentration_high, top3_sector_concentration_high, sector_count_low, sector_overcrowded
  - Configurable thresholds via `THRESHOLDS` constant
  - Comprehensive module docstring documenting all metrics, thresholds, and usage
  - Clean functional decomposition with focused helper functions
  - Modern Python type hints (`list[str]`, `dict[str, Any]`, `float | None`)
- Test coverage for sector drift analysis
  - `test_metrics.py` with fixture-based testing (renamed from `test_calculate_position_drift.py`)
  - Input fixture with 8 sectors (`input.json`)
  - Expected output fixture with full analysis results (`output.json`)
- Test fixtures and configuration
  - `sector_drift_fixtures_dir`, `sector_drift_input`, `sector_drift_output` fixtures in `conftest.py`
  - `calculate_sector_drift_module` fixture for module loading

### Changed
- Renamed `test_calculate_position_drift.py` to `test_metrics.py` to consolidate metrics tests

## [0.6.1] - 2026-01-24

### Added
- System prompt for position drift analysis module
  - `src/portfolio_analysis/metrics/position_drift/system.prompt` with LLM instructions
  - Strict output format for portfolio rebalancing recommendations
  - Decision rules for handling enrichment gaps and low confidence ratings
  - Structured output template: snapshot summary, key observations, recommended actions, follow-ups
  - Action types: TRIM, ADD, REPLACE, REVIEW, HOLD with required format

## [0.6.0] - 2026-01-24

### Added
- Position drift and concentration analysis module `calculate_position_drift.py`
  - Analyzes portfolio snapshots to assess concentration risk and generate rebalancing recommendations
  - Calculates concentration metrics: top 5/10 position weights, rating distribution breakdown
  - Generates four types of action candidates with reasons:
    - **Trim candidates**: High weight positions with strong gains or stretched P/E ratios
    - **Add candidates**: Good-rated positions that are underweight and near 52-week lows
    - **Replace candidates**: Bad-rated positions with meaningful weight or losing money
    - **Review candidates**: Bad-rated positions with low confidence (missing enrichment data)
  - Boolean flags for portfolio alerts: concentration, bad ratings, data quality issues
  - Comprehensive module docstring documenting all metrics, thresholds, and usage
  - Clean architecture using dataclasses (`Position`, `Candidate`) instead of raw dicts
  - Functional decomposition with focused functions under 20 lines each
  - Modern Python type hints (`list[str]`, `dict[str, Any]`, `float | None`)
- Test coverage for position drift analysis
  - `test_calculate_position_drift.py` with fixture-based testing
  - Input fixture with 39 portfolio positions (`input.json`)
  - Expected output fixture with full analysis results (`output.json`)
- Test fixtures and configuration
  - `position_drift_fixtures_dir`, `position_drift_input`, `position_drift_output` fixtures in `conftest.py`
  - `calculate_position_drift_module` fixture for module loading

## [0.5.0] - 2026-01-13

### Added
- Excel formula price format support in `cleanup_raw_data_for_storage.py`
  - `to_number()` function now handles Excel formula format `="$value"` in addition to simple currency format
  - Supports both positive and negative values in formula format (e.g., `="$259.939"`, `="-$0.311"`)
  - Maintains backward compatibility with existing simple format (`"$278.28"`)
  - Enhanced docstring documenting all supported formats
- Test coverage for new Excel formula format
  - `test_cleanup_raw_data_for_storage_new_format()` validates formula parsing with real-world data
  - New test fixture `enrich_raw_data_with_sector_names_output_format_changed.json` with 49 positions in new format
  - Fixture loading support in `test/conftest.py` via `cleanup_raw_data_for_storage_input_changed` fixture
  - Verifies correct parsing of decimal values (259.939) and negative values (-0.311)

## [0.4.1] - 2026-01-10

### Added
- Comprehensive documentation for Upload Position File n8n workflow
  - `src/portfolio_analysis/upload_position_file/workflow/README.md` with complete workflow description
  - Includes detailed mermaid diagram showing all nodes and data flow connections
  - Documents all 18 workflow nodes with their purposes and configurations
  - Describes 5 MongoDB collections written by the workflow
  - Usage instructions and dependency requirements
  - Explains multi-level aggregation strategy (security type, sector, detailed holdings)
- Upload Position File n8n workflow JSON export
  - Complete n8n workflow definition in `workflow/Upload Position File.json`
  - Includes all node configurations, connections, and credentials

## [0.4.0] - 2026-01-09

### Added
- `flat_aggregation.py` module for flattening nested sector/holdings data into individual rows
  - Transforms hierarchical portfolio sector data into flat tabular format with one row per holding
  - Extracts and denormalizes snapshot, sector, and holding metadata into single records
  - Includes contextual fields: sector totals, equity totals, account totals on every row
  - Implements functional decomposition with focused helper functions:
    - `_extract_document()` - handles n8n wrapper format
    - `_extract_snapshot_metadata()` - extracts snapshot-level data
    - `_extract_sector_metadata()` - extracts sector-level data
    - `_create_flat_holding()` - builds final flat records
  - Comprehensive docstrings with Args, Returns, and Raises sections
  - Complete type hints throughout
  - Passes all quality gates (ruff linting, pytest)
- Test coverage for flat aggregation in `test_upload_position_file_workflow.py`
  - `test_flat_aggregation()` validates full flattening workflow
  - Uses fixture-based approach consistent with project patterns
- Test fixtures in `test/conftest.py` and `test/fixtures/portfolio_analysis/upload_position_file/`
  - `flat_aggregation_module` fixture for module loading
  - `flat_aggregation_output.json` fixture with 625 expected flattened holding records

### Changed
- Applied ruff formatting fixes to `calculate_security_type_aggregation_detailed.py`
  - Fixed line length violations by splitting long lines
  - Improved code readability with proper line breaks

## [0.3.0] - 2026-01-09

### Added
- `calculate_security_type_aggregation_detailed.py` module for detailed sector-level equity holdings analysis
  - Provides granular breakdown of all holdings within each sector
  - Includes per-holding metrics: symbol, name, quantity, market_value
  - Calculates three allocation perspectives: allocation of equity, allocation of sector, allocation of account
  - Outputs nested structure with sector summaries and individual holdings
  - Follows functional decomposition pattern with 20+ focused helper functions
  - Comprehensive test coverage in `test_upload_position_file_workflow.py`
  - Test fixture `calculate_security_type_aggregation_detailed_output.json` with sample data
- Fixtures for the detailed aggregation module in `test/conftest.py`
  - `calculate_security_type_aggregation_detailed_module` fixture for module loading
  - `calculate_security_type_aggregation_detailed_output` fixture for expected results

### Changed
- Fixed import ordering in test files to comply with ruff linting rules
  - Corrected import block formatting in `test/conftest.py`
  - Corrected import block formatting in `test/test_upload_position_file_workflow.py`

## [0.2.2] - 2026-01-09

### Changed
- Refactored `calculate_security_type_aggregation_by_sector.py` to improve code organization and maintainability
  - Extracted monolithic `main()` function into 9 focused helper functions with single responsibilities
  - Added proper type hints throughout: `_validate_required_columns()`, `_normalize_snapshot_date()`, `_normalize_market_value()`, `_normalize_sector()`, `_extract_account_total()`, `_filter_equity_positions()`, `_calculate_sector_aggregations()`, `_pivot_market_values()`, `_pivot_allocations()`, `_merge_results()`
  - Improved `main()` function to serve as clear orchestration of processing steps
  - Enhanced testability by isolating business logic into discrete functions
  - All tests pass, confirming behavior preservation
- Added uv package manager instructions to `.claude/instructions.md`
  - Documented requirement to use `uv run` prefix for all Python commands
  - Included examples for running tests and other common commands

### Added
- Test case for sector-based aggregation in `test_upload_position_file_workflow.py`
  - `test_calculate_security_type_by_sector_aggregation()` validates full workflow
  - Uses fixture-based approach consistent with other tests
- Fixture for sector aggregation module in `test/conftest.py`
  - `calculate_security_type_by_sector_aggregation_module` fixture follows project patterns

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
