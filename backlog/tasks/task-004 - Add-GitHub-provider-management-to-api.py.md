---
id: task-004
title: Add GitHub provider management to api.py
status: Done
assignee: []
created_date: '2025-11-13 17:10'
updated_date: '2025-11-13 18:16'
labels:
  - enhancement
  - api
  - endpoints
  - github
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add support for GitHub provider operations including listing providers (github.githubProviders), connecting applications to providers (application.saveGithubProvider), and testing connections. These operations are critical for fixing deployment failures caused by disconnected providers.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Command to list all GitHub providers
- [x] #2 Command to connect application to GitHub provider with required fields
- [x] #3 Command to test GitHub provider connection
- [x] #4 Display provider details including ID, name, and creation date
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Added three new CLI commands for GitHub provider management:

### Commands Added
1. **github-providers** (lines 937-1014)
   - Lists all GitHub providers
   - GET `/api/github.githubProviders`
   - Displays table with: Provider ID, Name, Account ID, Created At
   - Shows full JSON details for first provider

2. **connect-github** (lines 1017-1094)
   - Connects application to GitHub provider
   - POST `/api/application.saveGithubProvider`
   - Required: `--app-id`, `--github-id`, `--owner`
   - Optional: `--repository`, `--branch` (default: main), `--build-path` (default: /), `--enable-submodules`, `--trigger-type` (push|tag)
   - Critical for fixing deployment failures caused by disconnected providers

3. **test-github** (lines 1097-1153)
   - Tests GitHub provider connection
   - POST `/api/github.testConnection`
   - Required: `--github-id`

### Testing
- Added 8 unit tests in tests/test_api.py (lines 369-561)
- All tests passing with proper mocking
- Coverage includes: success cases, error handling, optional parameters, missing required parameters

### Documentation
- Updated api.py docstring with usage examples
- Commands visible in `uv run api.py --help` output
- Addresses deployment failure scenario documented in CLAUDE.md troubleshooting section
<!-- SECTION:NOTES:END -->
