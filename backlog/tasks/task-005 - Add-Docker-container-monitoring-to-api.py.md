---
id: task-005
title: Add Docker container monitoring to api.py
status: To Do
assignee: []
created_date: '2025-11-13 17:12'
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
- [ ] #1 Command to list containers by application name pattern
- [ ] #2 Display container ID, name, and state
- [ ] #3 Command to get detailed container information
- [ ] #4 Support for filtering by container state (running, exited, etc.)
<!-- AC:END -->
