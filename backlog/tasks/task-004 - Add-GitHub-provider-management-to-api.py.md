---
id: task-004
title: Add GitHub provider management to api.py
status: To Do
assignee: []
created_date: '2025-11-13 17:10'
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
- [ ] #1 Command to list all GitHub providers
- [ ] #2 Command to connect application to GitHub provider with required fields
- [ ] #3 Command to test GitHub provider connection
- [ ] #4 Display provider details including ID, name, and creation date
<!-- AC:END -->
