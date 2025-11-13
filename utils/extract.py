#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "requests>=2.32.5",
#     "click>=8.1.0",
#     "pyyaml>=6.0",
#     "rich>=13.0.0",
#     "python-decouple>=3.8",
# ]
# [tool.uv]
# exclude-newer = "2025-10-31T00:00:00Z"
# ///

# pyright: reportMissingImports=false

"""
Dokploy OpenAPI Endpoint Extractor

Usage:
    extract.py list [--api-key KEY] [--url URL]
    extract.py filter <METHOD> [--api-key KEY] [--url URL]
    extract.py search <TERM> [--api-key KEY] [--url URL]
    extract.py export <json|yaml|markdown> [--output FILE] [--api-key KEY] [--url URL]
    extract.py terraform [--output FILE] [--api-key KEY] [--url URL]

Commands:
    list: List all available API endpoints
    filter: Filter endpoints by HTTP method (GET, POST, etc.)
    search: Search endpoints by path or description
    export: Export endpoints to JSON, YAML, or Markdown format
    terraform: Generate Terraform provider scaffolding structure

Note:
    API credentials can be provided via:
    - Command-line arguments (--api-key, --url)
    - Environment variables (API_KEY, BASE_URL)
    - .env file in current working directory
"""

import builtins
import click
import json
import requests
import sys
import yaml

# Import shared utilities
from lib.dokploy import extract_endpoints, fetch_openapi_spec, load_config
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from typing import Any, Dict, List, Optional

console = Console()


def filter_by_method(endpoints: list[dict[str, Any]], method: str) -> list[dict[str, Any]]:
    """Filter endpoints by HTTP method."""
    return [ep for ep in endpoints if ep["method"] == method.upper()]


def search_endpoints(endpoints: list[dict[str, Any]], term: str) -> list[dict[str, Any]]:
    """Search endpoints by path, summary, or description."""
    term_lower = term.lower()
    return [
        ep
        for ep in endpoints
        if term_lower in ep["path"].lower() or term_lower in ep["summary"].lower() or term_lower in ep["description"].lower()
    ]


def display_endpoints_table(endpoints: list[dict[str, Any]]) -> None:
    """Display endpoints in a rich table."""
    table = Table(title="Dokploy API Endpoints", show_lines=True)
    table.add_column("Method", style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta")
    table.add_column("Summary", style="green")
    table.add_column("Tags", style="yellow")

    for ep in endpoints:
        table.add_row(ep["method"], ep["path"], ep["summary"], ", ".join(ep["tags"]))

    console.print(table)
    console.print(f"\n[bold]Total endpoints: {len(endpoints)}[/bold]")


def export_to_json(endpoints: list[dict[str, Any]], output: str | None = None) -> None:
    """Export endpoints to JSON format."""
    data = json.dumps(endpoints, indent=2)

    if output:
        Path(output).write_text(data)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        console.print(Syntax(data, "json", theme="monokai", line_numbers=True))


def export_to_yaml(endpoints: list[dict[str, Any]], output: str | None = None) -> None:
    """Export endpoints to YAML format."""
    data = yaml.dump(endpoints, default_flow_style=False, sort_keys=False)

    if output:
        Path(output).write_text(data)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        console.print(Syntax(data, "yaml", theme="monokai", line_numbers=True))


def export_to_markdown(endpoints: list[dict[str, Any]], output: str | None = None) -> None:
    """Export endpoints to Markdown format."""
    lines = ["# Dokploy API Endpoints\n"]

    # Group by tags
    by_tags: dict[str, builtins.list[dict[str, Any]]] = {}
    for ep in endpoints:
        tags = ep["tags"] if ep["tags"] else ["Uncategorized"]
        for tag in tags:
            if tag not in by_tags:
                by_tags[tag] = []
            by_tags[tag].append(ep)

    for tag, eps in sorted(by_tags.items()):
        lines.append(f"\n## {tag}\n")
        for ep in eps:
            lines.append(f"### `{ep['method']}` {ep['path']}\n")
            if ep["summary"]:
                lines.append(f"{ep['summary']}\n")
            if ep["description"]:
                lines.append(f"{ep['description']}\n")
            lines.append("")

    data = "\n".join(lines)

    if output:
        Path(output).write_text(data)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        console.print(Panel(data, title="Markdown Output", border_style="blue"))


def generate_terraform_scaffold(endpoints: list[dict[str, Any]], output: str | None = None) -> None:
    """Generate Terraform provider scaffolding structure."""
    resources: dict[str, dict[str, str]] = {}

    # Group endpoints by resource type (extracted from path)
    for ep in endpoints:
        # Extract resource name from path like /api/project.create -> project
        parts = ep["path"].strip("/").split(".")
        if len(parts) >= 2:
            resource_name = parts[0].replace("api/", "")
            operation = parts[1] if len(parts) > 1 else "unknown"

            if resource_name not in resources:
                resources[resource_name] = {}

            # Map operations to CRUD
            if "create" in operation.lower():
                resources[resource_name]["create"] = f"{ep['method']} {ep['path']}"
            elif "one" in operation.lower() or "get" in operation.lower():
                resources[resource_name]["read"] = f"{ep['method']} {ep['path']}"
            elif "update" in operation.lower():
                resources[resource_name]["update"] = f"{ep['method']} {ep['path']}"
            elif "delete" in operation.lower() or "remove" in operation.lower():
                resources[resource_name]["delete"] = f"{ep['method']} {ep['path']}"
            elif "all" in operation.lower() or "list" in operation.lower():
                resources[resource_name]["list"] = f"{ep['method']} {ep['path']}"
            else:
                resources[resource_name][operation] = f"{ep['method']} {ep['path']}"

    scaffold = {
        "provider": "dokploy",
        "resources": resources,
        "metadata": {"total_resources": len(resources), "total_endpoints": len(endpoints)},
    }

    data = json.dumps(scaffold, indent=2)

    if output:
        Path(output).write_text(data)
        console.print(f"[green]Terraform scaffold exported to {output}[/green]")
    else:
        console.print(Syntax(data, "json", theme="monokai", line_numbers=True))

    console.print(f"\n[bold]Found {len(resources)} potential Terraform resources[/bold]")


@click.group()
def cli():
    """Dokploy OpenAPI Endpoint Extractor"""
    pass


@cli.command()
@click.option("--api-key", help="Dokploy API key")
@click.option("--url", help="Dokploy base URL")
def list(api_key: str | None, url: str | None) -> None:
    """List all available API endpoints."""
    config = load_config()
    api_key = api_key or config["api_key"]
    url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API key is required.[/red]")
        console.print("[yellow]Provide via --api-key, API_KEY env var, or .env file.[/yellow]")
        sys.exit(1)

    console.print(f"[cyan]Fetching OpenAPI spec from {url}...[/cyan]")
    openapi_spec = fetch_openapi_spec(url, api_key)
    endpoints = extract_endpoints(openapi_spec)
    display_endpoints_table(endpoints)


@cli.command()
@click.argument("method")
@click.option("--api-key", help="Dokploy API key")
@click.option("--url", help="Dokploy base URL")
def filter(method: str, api_key: str | None, url: str | None) -> None:
    """Filter endpoints by HTTP method (GET, POST, etc.)."""
    config = load_config()
    api_key = api_key or config["api_key"]
    url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API key is required.[/red]")
        sys.exit(1)

    console.print(f"[cyan]Fetching OpenAPI spec from {url}...[/cyan]")
    openapi_spec = fetch_openapi_spec(url, api_key)
    endpoints = extract_endpoints(openapi_spec)
    filtered = filter_by_method(endpoints, method)
    display_endpoints_table(filtered)


@cli.command()
@click.argument("term")
@click.option("--api-key", help="Dokploy API key")
@click.option("--url", help="Dokploy base URL")
def search(term: str, api_key: str | None, url: str | None) -> None:
    """Search endpoints by path or description."""
    config = load_config()
    api_key = api_key or config["api_key"]
    url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API key is required.[/red]")
        sys.exit(1)

    console.print(f"[cyan]Fetching OpenAPI spec from {url}...[/cyan]")
    openapi_spec = fetch_openapi_spec(url, api_key)
    endpoints = extract_endpoints(openapi_spec)
    results = search_endpoints(endpoints, term)
    display_endpoints_table(results)


@cli.command()
@click.argument("format", type=click.Choice(["json", "yaml", "markdown"]))
@click.option("--output", "-o", help="Output file path")
@click.option("--api-key", help="Dokploy API key")
@click.option("--url", help="Dokploy base URL")
def export(format: str, output: str | None, api_key: str | None, url: str | None) -> None:
    """Export endpoints to JSON, YAML, or Markdown format."""
    config = load_config()
    api_key = api_key or config["api_key"]
    url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API key is required.[/red]")
        sys.exit(1)

    console.print(f"[cyan]Fetching OpenAPI spec from {url}...[/cyan]")
    openapi_spec = fetch_openapi_spec(url, api_key)
    endpoints = extract_endpoints(openapi_spec)

    if format == "json":
        export_to_json(endpoints, output)
    elif format == "yaml":
        export_to_yaml(endpoints, output)
    elif format == "markdown":
        export_to_markdown(endpoints, output)


@cli.command()
@click.option("--output", "-o", help="Output file path")
@click.option("--api-key", help="Dokploy API key")
@click.option("--url", help="Dokploy base URL")
def terraform(output: str | None, api_key: str | None, url: str | None) -> None:
    """Generate Terraform provider scaffolding structure."""
    config = load_config()
    api_key = api_key or config["api_key"]
    url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API key is required.[/red]")
        sys.exit(1)

    console.print(f"[cyan]Fetching OpenAPI spec from {url}...[/cyan]")
    openapi_spec = fetch_openapi_spec(url, api_key)
    endpoints = extract_endpoints(openapi_spec)
    generate_terraform_scaffold(endpoints, output)


if __name__ == "__main__":
    cli()
