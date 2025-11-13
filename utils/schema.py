#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "requests>=2.32.5",
#     "python-decouple>=3.8",
# ]
# [tool.uv]
# exclude-newer = "2025-10-31T00:00:00Z"
# ///

import json

# Import shared utilities
from lib.dokploy import load_openapi_from_file
from pathlib import Path
from typing import Any

# Priority resources to extract
PRIORITY_RESOURCES = [
    "project",
    "application",
    "auth",
    "backup",
    "cluster",
    "compose",
    "deployment",
    "docker",
    "domain",
    "github",
    "mounts",
    "notification",
    "port",
    "registry",
    "security",
    "server",
    "settings",
    "sshKey",
    "user",
]

# Removed load_openapi_spec() - now using shared lib.dokploy.load_openapi_from_file()


def extract_schema_for_resource(openapi_spec: dict[str, Any], resource: str) -> dict[str, Any]:
    """Extract schema information for a specific resource."""
    result = {"resource": resource, "endpoints": [], "schemas": {}}

    # Extract endpoints for this resource
    paths = openapi_spec.get("paths", {})
    for path, methods in paths.items():
        # Check if path belongs to this resource
        if f"/{resource}." in path.lower():
            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    endpoint_info = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "operationId": details.get("operationId", ""),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody", {}),
                        "responses": details.get("responses", {}),
                    }
                    result["endpoints"].append(endpoint_info)

    # Extract component schemas related to this resource
    components = openapi_spec.get("components", {})
    schemas = components.get("schemas", {})

    for schema_name, schema_def in schemas.items():
        # Check if schema name contains the resource name
        if resource.lower() in schema_name.lower():
            result["schemas"][schema_name] = schema_def

    return result


def write_schema_markdown(resource: str, schema_data: dict[str, Any]) -> None:
    """Write schema information as markdown."""
    output_path = Path(f"docs/schemas/{resource}.md")

    lines = [f"# {resource.capitalize()} Resource Schema", "", "## Endpoints", ""]

    # Document endpoints
    if schema_data["endpoints"]:
        for ep in schema_data["endpoints"]:
            lines.append(f"### `{ep['method']}` {ep['path']}")
            lines.append("")
            if ep["summary"]:
                lines.append(f"**Summary**: {ep['summary']}")
                lines.append("")
            if ep["description"]:
                lines.append(f"**Description**: {ep['description']}")
                lines.append("")

            # Parameters
            if ep["parameters"]:
                lines.append("**Parameters**:")
                lines.append("")
                for param in ep["parameters"]:
                    param_name = param.get("name", "")
                    param_in = param.get("in", "")
                    param_required = " (required)" if param.get("required") else ""
                    param_desc = param.get("description", "")
                    lines.append(f"- `{param_name}` ({param_in}){param_required}: {param_desc}")
                lines.append("")

            # Request body
            if ep["requestBody"]:
                lines.append("**Request Body**:")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(ep["requestBody"], indent=2))
                lines.append("```")
                lines.append("")

            # Responses
            if ep["responses"]:
                lines.append("**Responses**:")
                lines.append("")
                for status, response_data in ep["responses"].items():
                    response_desc = response_data.get("description", "")
                    lines.append(f"- `{status}`: {response_desc}")
                lines.append("")
    else:
        lines.append("No endpoints found for this resource.")
        lines.append("")

    # Document schemas
    lines.append("## Schemas")
    lines.append("")

    if schema_data["schemas"]:
        for schema_name, schema_def in schema_data["schemas"].items():
            lines.append(f"### {schema_name}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(schema_def, indent=2))
            lines.append("```")
            lines.append("")
    else:
        lines.append("No schemas found for this resource in components.")
        lines.append("")

    output_path.write_text("\n".join(lines))
    print(f"Created {output_path}")


def main():
    """Main function."""
    print("Loading OpenAPI specification...")
    openapi_spec = load_openapi_from_file()

    print(f"Extracting schemas for {len(PRIORITY_RESOURCES)} priority resources...")

    for resource in PRIORITY_RESOURCES:
        print(f"Processing {resource}...")
        schema_data = extract_schema_for_resource(openapi_spec, resource)
        write_schema_markdown(resource, schema_data)

    print("\nCompleted!")
    print("Generated schema documentation in docs/schemas/")


if __name__ == "__main__":
    main()
