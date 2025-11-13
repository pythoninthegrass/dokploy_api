# CLAUDE.md

This file provides guidance to LLMs when working with the Dokploy API Tools.

## Project Overview

A collection of Python CLI tools for testing, inspecting, and analyzing the Dokploy
API. These tools help understand API response formats, validate endpoint coverage,
extract OpenAPI specifications, and generate documentation.

## General

- Always activate the virtual environment (.venv) via `uv run`

## Context7 Libraries

- glanceapp/glance
- websites/docs_dokploy_com-docs-core
- mrlesk/backlog.md
- docker/docs
- stackexchange/dnscontrol
- websites/taskfile_dev

## Core Files

### Scripts (4)
- **api.py** (622 lines) - Interactive API testing tool for CRUD operations, listing,
querying, and batch operations
- **extract.py** (316 lines) - Extract and analyze OpenAPI specifications from live
Dokploy instances
- **schema.py** (158 lines) - Generate markdown documentation from OpenAPI resource
schemas
- **validate.py** (406 lines) - Validate endpoint coverage and generate coverage
reports

### Shared Library
- **lib/dokploy.py** (138 lines) - Core utilities: config loading, API requests,
OpenAPI parsing

### Data Files
- **docs/openapi-spec.json** (542KB) - OpenAPI specification (required by schema.py and
validate.py)

## Dependencies

All scripts use PEP 723 inline metadata with `uv`:

```python
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "requests>=2.32.5",
#     "click>=8.1.0",
#     "rich>=13.0.0",
#     "python-decouple>=3.8",
#     "pyyaml>=6.0",  # extract.py only
# ]
```

## Environment Configuration

Create .env file in repository root:

```bash
API_KEY=your-dokploy-api-key
BASE_URL=https://your-dokploy-instance.com
```

All scripts automatically load from .env via lib/dokploy.py:load_config()

## Common Commands

### API Testing (api.py)

```bash

# CRUD operations
uv run api.py create project
uv run api.py get project <id>
uv run api.py update project <id> --field name=updated
uv run api.py delete project <id>  # Tries .remove then .delete

# List and query
uv run api.py list project --limit 10
uv run api.py query domain --filter host=example.com

# Batch operations
uv run api.py batch-delete project <id1> <id2> <id3> --delay 0.5
```

### OpenAPI Extraction (extract.py)

```bash

# List and filter endpoints
uv run extract.py list
uv run extract.py filter POST
uv run extract.py search application

# Export specifications
uv run extract.py export json -o openapi-spec.json
uv run extract.py export yaml -o openapi-spec.yaml
uv run extract.py export markdown -o API_DOCS.md

# Generate Terraform scaffold
uv run extract.py terraform
```

### Schema Documentation (schema.py)

```bash

# Generate markdown docs for all resources
uv run schema.py

# Output: docs/schemas/<resource>.md files
```

### Coverage Validation (validate.py)

```bash

# Validate endpoint coverage
uv run validate.py

# Output: docs/COVERAGE_REPORT.md
```

## Development Guidelines

### Code Style

- Follow PEP 8 conventions
- Use type hints where helpful
- Keep functions focused and single-purpose
- Prefer explicit over implicit

### CLI Design Patterns

- Use click for all CLI interfaces
- Use rich for formatted output (tables, syntax highlighting, panels)
- Provide --api-key and --url options with environment variable fallbacks
- Show clear error messages with context

### Error Handling

- Catch requests.exceptions.RequestException for network errors
- Catch json.JSONDecodeError for malformed responses
- Exit with sys.exit(1) on fatal errors
- Use console.print("[red]Error message[/red]") for user-facing errors

### Adding New Commands

1. Add @cli.command() function to appropriate script
2. Use load_config() to get API credentials
3. Format output with rich components (Table, Panel, Syntax)
4. Update script docstring with new command usage

## Architecture

### Shared Utilities (lib/dokploy.py)

- load_config() - Load API credentials from .env or environment
- fetch_openapi_spec() - Fetch OpenAPI spec from live API
- load_openapi_from_file() - Load cached OpenAPI spec
- extract_endpoints() - Parse endpoints from OpenAPI spec
- make_api_request() - Make authenticated API requests

All scripts import from lib.dokploy - keep shared logic here.

### Path Resolution

All scripts assume they run from repository root:

```python
# .env location
Path(__file__).parent.parent / ".env"

# docs/ location
Path(__file__).parent / "docs" / "openapi-spec.json"
```

### API Endpoint Conventions

Dokploy API uses dot notation:
- POST /api/{resource}.create - Create resource
- GET /api/{resource}.one?{resource}Id={id} - Get resource
- POST /api/{resource}.update - Update resource
- POST /api/{resource}.remove or .delete - Delete resource
- GET /api/{resource}.all - List all resources

ID field names follow pattern: {resource}Id (e.g., projectId, applicationId)

### Generated Files

Scripts create/update files in docs/:

- openapi-spec.json - Full OpenAPI specification (from extract.py)
- endpoints.json - Endpoint inventory (from extract.py)
- COVERAGE_REPORT.md - Coverage analysis (from validate.py)
- schemas/<resource>.md - Resource schema docs (from schema.py)

## Testing Approach

### Manual Testing

1. Set up test Dokploy instance
2. Configure .env with test credentials
3. Run commands against test instance
4. Verify output formatting and error handling

### Common Test Scenarios

- Valid API requests (200 responses)
- Invalid credentials (401 responses)
- Missing resources (404 responses)
- Malformed requests (400 responses)
- Network failures (connection errors)

## Common Patterns

### Direct API Access with curl

Test API connectivity and basic operations:
```bash
# Test API key validity - list all projects
curl -s -H "accept: application/json" -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/project.all" | jq .
# Alternative: uv run api.py list project

# Get project details with applications
curl -s -H "accept: application/json" -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/project.one?projectId=PROJECT_ID" | jq .
# Alternative: uv run api.py get project PROJECT_ID

# Get application details
curl -s -H "accept: application/json" -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/application.one?applicationId=APP_ID" | jq .
# Alternative: uv run api.py get application APP_ID

# Check domain configuration (requires curl - non-standard query params)
curl -s -H "accept: application/json" -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/domain.byApplicationId?applicationId=APP_ID" | jq .

# List GitHub providers
curl -s -H "accept: application/json" -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/github.githubProviders" | jq .

# Get deployment history (requires curl - needs applicationId query param)
curl -s -H "accept: application/json" -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/deployment.all?applicationId=APP_ID" | jq .

# List Docker containers by app name (requires curl - specialized endpoint)
curl -s -H "accept: application/json" -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/docker.getContainersByAppNameMatch?appName=APP_NAME" | jq .
```

**Note:** api.py supports standard CRUD operations (`.create`, `.one`, `.update`, `.remove`, `.delete`, `.all`). For specialized endpoints like `domain.byApplicationId`, `docker.getContainersByAppNameMatch`, or `application.deploy`, use curl directly.

Connect application to GitHub provider:
```bash
# Create JSON payload
cat > /tmp/github_provider.json << 'EOF'
{
  "applicationId": "YOUR_APP_ID",
  "githubId": "YOUR_GITHUB_PROVIDER_ID",
  "repository": "your-repo",
  "owner": "your-github-username",
  "branch": "main",
  "buildPath": "/",
  "enableSubmodules": false,
  "triggerType": "push"
}
EOF

# Connect to GitHub provider
curl -s -X POST \
  -H "accept: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/github_provider.json \
  "https://your-dokploy.com/api/application.saveGithubProvider"
```

Trigger deployment:
```bash
curl -s -X POST \
  -H "accept: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"applicationId":"YOUR_APP_ID"}' \
  "https://your-dokploy.com/api/application.deploy"
```

SSH to Dokploy host:
```bash
# Check Docker logs for running container
ssh your-host "docker logs --tail 100 CONTAINER_NAME"

# Check deployment logs
ssh your-host "cat /etc/dokploy/logs/APP_NAME/APP_NAME-2025-11-13:16:14:11.log"

# List recent deployment logs
ssh your-host "ls -lht /etc/dokploy/logs/APP_NAME/ | head -20"

# Check Dokploy container logs
ssh your-host "docker logs DOKPLOY_CONTAINER_NAME --since 2025-11-13T16:14:00 --until 2025-11-13T16:15:00 2>&1"
```

### Making API Requests

```python
from lib.dokploy import load_config
import requests

config = load_config()
headers = {
    "accept": "application/json",
    "x-api-key": config["api_key"],
    "Content-Type": "application/json"
}

response = requests.post(
    f"{config['base_url']}/api/resource.create",
    headers=headers,
    json=data
)
```

### Displaying Results with Rich

```python
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

console = Console()

# Tables
table = Table(show_header=True, header_style="bold magenta")
table.add_column("Field", style="cyan")
table.add_column("Value", style="green")
console.print(table)

# JSON syntax highlighting
console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))

# Panels
console.print(Panel(f"Testing: POST {endpoint}", style="bold cyan"))
```

## Troubleshooting

### "API_KEY not found"

- Verify .env file exists in repository root
- Check .env has API_KEY=... line
- Or set export API_KEY=... in shell

### "Connection refused"

- Verify Dokploy instance is running
- Check BASE_URL points to correct host/port
- Ensure network connectivity to Dokploy instance

### "404 Not Found" on valid resource

- Verify endpoint naming convention (.create, .one, .all, etc.)
- Check resource name matches Dokploy API (singular form)
- Review OpenAPI spec with uv run extract.py list

### Import errors with lib.dokploy

- Ensure running from repository root
- Check lib/__init__.py exists
- Verify Python path includes repository root

### Deployment fails immediately (GitHub Provider not found)

**Symptoms:**
- Deployments fail within milliseconds after "Initializing deployment"
- Application status shows "error"
- Dokploy logs show: `Error [TRPCError]: GitHub Provider not found`
- Application has `githubId: null`

**Diagnosis:**
```bash
# Check if application has GitHub provider connected
curl -s -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/application.one?applicationId=APP_ID" \
  | jq '{githubId, repository, applicationStatus}'

# List available GitHub providers
curl -s -H "x-api-key: YOUR_API_KEY" \
  "https://your-dokploy.com/api/github.githubProviders" | jq .
```

**Resolution:**
Reconnect the application to a GitHub provider:
```bash
cat > /tmp/reconnect.json << 'EOF'
{
  "applicationId": "YOUR_APP_ID",
  "githubId": "GITHUB_PROVIDER_ID",
  "repository": "your-repo",
  "owner": "github-username",
  "branch": "main",
  "buildPath": "/",
  "enableSubmodules": false,
  "triggerType": "push"
}
EOF

curl -s -X POST -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/reconnect.json \
  "https://your-dokploy.com/api/application.saveGithubProvider"
```

Then trigger a new deployment:
```bash
curl -s -X POST -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"applicationId":"YOUR_APP_ID"}' \
  "https://your-dokploy.com/api/application.deploy"
```

## Version Control

- Use conventional commits (feat:, fix:, docs:, refactor:, test:)
- Keep commits focused and atomic
- Update documentation when changing CLI interfaces
- Regenerate docs/ files when OpenAPI spec changes

<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_workflow_overview()` tool to load the tool-oriented overview (it lists the matching guide tools).

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and completion
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->
