---
id: task-003
title: Add deployment operations support to api.py
status: Done
assignee: []
created_date: '2025-11-13 17:10'
updated_date: '2025-11-13 18:05'
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
