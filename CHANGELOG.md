# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `calculate_security_type_aggregation.py` module for aggregating portfolio positions by security type
  - Computes market values and allocation percentages in wide format
  - Includes helper functions: `prepare_dataframe()`, `aggregate_by_security_type()`, `calculate_allocations()`, and `pivot_to_wide_format()`
  - Comprehensive docstrings and type hints throughout

### Changed
- Refactored `calculate_security_type_aggregation.py` to follow Python best practices
  - Split monolithic `main()` function into focused, single-responsibility functions
  - Each function now under 50 lines for better maintainability
  - Enhanced documentation with detailed Args, Returns, and Raises sections

## [2026-01-08]

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
