---
id: task-003
title: Add deployment operations support to api.py
status: Done
assignee: []
created_date: '2025-11-13 17:10'
updated_date: '2025-11-13 18:09'
labels:
  - enhancement
  - api
  - endpoints
  - deployment
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add support for deployment-related endpoints including deployment.all (with applicationId filter), application.deploy, and application.redeploy. These are specialized endpoints that trigger and monitor application deployments.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Command to list deployments for an application with filtering
- [x] #2 Command to trigger new deployment
- [x] #3 Command to trigger redeployment
- [x] #4 Display deployment status, timestamps, and log paths
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Added three new CLI commands for deployment operations:

### Commands Added
1. **deployments** (lines 712-796)
   - Lists deployment history for an application
   - GET `/api/deployment.all?applicationId=X`
   - Displays table with: Deployment ID, Status, Created At, Title, Log Path
   - Supports `--limit` parameter for filtering results

2. **deploy** (lines 799-862)
   - Triggers new application deployment
   - POST `/api/application.deploy`
   - Required: `--app-id`
   - Optional: `--title`, `--description`

3. **redeploy** (lines 865-928)
   - Triggers application redeployment
   - POST `/api/application.redeploy`
   - Required: `--app-id`
   - Optional: `--title`, `--description`

### Testing
- Added 8 unit tests in tests/test_api.py (lines 198-367)
- All tests passing with proper mocking
- Coverage includes: success cases, error handling, optional parameters

### Documentation
- Updated api.py docstring with usage examples
- Commands visible in `uv run api.py --help` output
<!-- SECTION:NOTES:END -->
