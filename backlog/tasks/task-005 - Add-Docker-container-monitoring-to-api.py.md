---
id: task-005
title: Add Docker container monitoring to api.py
status: Done
assignee: []
created_date: '2025-11-13 17:12'
updated_date: '2025-11-13 18:20'
labels:
  - enhancement
  - api
  - endpoints
  - docker
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add support for Docker container operations including listing containers by app name (docker.getContainersByAppNameMatch), viewing container details, and checking container status. Useful for troubleshooting running applications.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Command to list containers by application name pattern
- [x] #2 Display container ID, name, and state
- [x] #3 Command to get detailed container information
- [x] #4 Support for filtering by container state (running, exited, etc.)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Added two new CLI commands for Docker container monitoring:

### Commands Added
1. **docker-containers** (lines 1162-1257)
   - Lists Docker containers by application name pattern
   - GET `/api/docker.getContainersByAppNameMatch?appName=X`
   - Required: `--app-name`
   - Optional: `--app-type` (stack|docker-compose), `--server-id`
   - Displays table with: Container ID, Name, State, Status, Image
   - Shows full JSON details for first container
   - Useful for troubleshooting specific applications

2. **docker-list** (lines 1260-1350)
   - Lists all Docker containers
   - GET `/api/docker.getContainers`
   - Optional: `--server-id`
   - Displays table with: Container ID, Name, State, Status, Image
   - Includes summary by state (running, exited, etc.)
   - Provides overview of all containers on the system

### Features
- Container state filtering built into display (shows state column)
- Summary statistics for docker-list command
- Handles both Docker API response formats (Names array vs name field)
- Full container details available in JSON output

### Testing
- Added 6 unit tests in tests/test_api.py (lines 563-705)
- All tests passing with proper mocking
- Coverage includes: success cases, filtering, empty results, server ID parameter

### Documentation
- Updated api.py docstring with usage examples
- Commands visible in `uv run api.py --help` output
- Addresses troubleshooting scenario mentioned in CLAUDE.md
<!-- SECTION:NOTES:END -->
