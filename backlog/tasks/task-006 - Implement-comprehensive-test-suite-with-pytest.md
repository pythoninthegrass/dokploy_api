---
id: task-006
title: Implement comprehensive test suite with pytest
status: To Do
assignee: []
created_date: '2025-11-13 17:40'
labels:
  - testing
  - pytest
  - quality
  - coverage
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create a comprehensive testing strategy covering unit tests, integration tests, and end-to-end (e2e) tests for all Python modules in the project. Currently only tests/test_api.py exists with limited coverage of the domains command.

## Current Test Coverage (35% overall)
- **api.py**: 25% coverage (428 statements, 322 missing)
  - Missing: create, get, update, delete, list, query, batch-delete commands
  - Partial: domains command (only 3/6 tests passing due to mocking issues)
- **lib/dokploy.py**: 20% coverage (44 statements, 35 missing)
  - Missing: load_config, fetch_openapi_spec, load_openapi_from_file, extract_endpoints, make_api_request
- **utils/extract.py**: No tests (needs coverage analysis)
- **utils/schema.py**: No tests (needs coverage analysis)
- **utils/validate.py**: No tests (needs coverage analysis)
- **tests/test_api.py**: 95% coverage (existing test file)

## Required Test Types

### Unit Tests
Test individual functions and methods in isolation with mocked dependencies:
- lib/dokploy.py functions (load_config, fetch_openapi_spec, etc.)
- Individual CLI command logic
- Data validation and transformation functions
- Error handling paths

### Integration Tests
Test interaction between components:
- API client (lib/dokploy.py) with CLI commands (api.py)
- OpenAPI spec loading and parsing
- Configuration loading from different sources (.env, environment, CLI args)
- Mock HTTP responses to test complete request/response cycles

### End-to-End Tests
Test complete workflows with real or realistic data:
- Full CRUD operations (create, get, update, delete)
- Batch operations
- Query and filtering
- Error scenarios (network failures, invalid data, authentication failures)
- Output formatting verification
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Achieve minimum 80% overall test coverage
- [ ] #2 All CLI commands in api.py have unit tests
- [ ] #3 All functions in lib/dokploy.py have unit tests
- [ ] #4 Integration tests cover API client and command interaction
- [ ] #5 End-to-end tests verify complete CRUD workflows
- [ ] #6 All tests pass consistently without flakiness
- [ ] #7 Test suite runs in under 10 seconds
- [ ] #8 Mocking infrastructure works correctly (fix current issues in test_api.py)
<!-- AC:END -->
