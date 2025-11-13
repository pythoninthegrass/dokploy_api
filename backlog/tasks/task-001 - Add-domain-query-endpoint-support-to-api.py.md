---
id: task-001
title: Add domain query endpoint support to api.py
status: To Do
assignee: []
created_date: '2025-11-13 17:09'
labels:
  - enhancement
  - api
  - endpoints
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add support for domain.byApplicationId endpoint which uses non-standard query parameters. This endpoint retrieves domain configuration for a specific application.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Command 'uv run api.py domains --app-id APP_ID' returns domain configuration
- [ ] #2 Output displays domain details in a formatted table
- [ ] #3 Error handling for missing or invalid application IDs
<!-- AC:END -->
