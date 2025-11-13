#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "requests>=2.32.5",
#     "click>=8.1.0",
#     "rich>=13.0.0",
#     "python-decouple>=3.8",
# ]
# [tool.uv]
# exclude-newer = "2025-10-31T00:00:00Z"
# ///

# pyright: reportMissingImports=false

"""
Dokploy API Tool

Test and inspect Dokploy API endpoints to understand response formats.

Usage:
    api.py create <RESOURCE> [--api-key KEY] [--url URL]
    api.py get <RESOURCE> <ID> [--api-key KEY] [--url URL]
    api.py update <RESOURCE> <ID> [--api-key KEY] [--url URL]
    api.py delete <RESOURCE> <ID> [--api-key KEY] [--url URL]
    api.py list <RESOURCE> [--limit N] [--api-key KEY] [--url URL]
    api.py query <RESOURCE> [--filter field=value] [--limit N] [--api-key KEY] [--url URL]
    api.py batch-delete <RESOURCE> <ID1> <ID2> ... [--delay SECS] [--api-key KEY] [--url URL]
    api.py domains --app-id <APP_ID> [--api-key KEY] [--url URL]
    api.py deployments --app-id <APP_ID> [--limit N] [--api-key KEY] [--url URL]
    api.py deploy --app-id <APP_ID> [--title TITLE] [--description DESC] [--api-key KEY] [--url URL]
    api.py redeploy --app-id <APP_ID> [--title TITLE] [--description DESC] [--api-key KEY] [--url URL]

Commands:
    create: Test a create endpoint and show response
    get: Test a get endpoint and show response
    update: Test an update endpoint and show response
    delete: Test a delete endpoint and show response (tries .remove then .delete)
    list: List all resources of a given type
    query: Query resources with filters
    batch-delete: Delete multiple resources by ID
    domains: Get domain configuration for a specific application
    deployments: List deployment history for an application
    deploy: Trigger a new deployment for an application
    redeploy: Trigger a redeployment for an application

Resources:
    application, project, compose, domain, etc.

Note:
    API credentials can be provided via:
    - Command-line arguments (--api-key, --url)
    - Environment variables (API_KEY, BASE_URL)
    - .env file in parent directory
"""

import click
import json
import requests
import sys
import time

# Import shared utilities
from lib.dokploy import load_config
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

console = Console()


@click.group()
def cli():
    """Dokploy API Tool"""
    pass


@cli.command()
@click.argument("resource")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
@click.option("--env-id", help="Environment ID for the resource")
def create(resource, api_key, url, env_id):
    """Create a resource and show the response"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found. Set it via --api-key, environment, or .env file[/red]")
        sys.exit(1)

    # Resource-specific test data
    test_data = {
        "application": {
            "name": f"test-{resource}",
            "environmentId": env_id or "J86P6quzU2DaMBM2gxNjj"
        },
        "project": {
            "name": f"test-{resource}",
        },
        "compose": {
            "name": f"test-{resource}",
            "environmentId": env_id or "J86P6quzU2DaMBM2gxNjj"
        },
    }

    if resource not in test_data:
        console.print(f"[yellow]Warning: No test data defined for '{resource}'. Using minimal data.[/yellow]")
        data = {"name": f"test-{resource}"}
    else:
        data = test_data[resource]

    endpoint = f"{base_url}/api/{resource}.create"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    console.print(Panel(f"Testing: POST {endpoint}", style="bold cyan"))
    console.print("\n[bold]Request Data:[/bold]")
    console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))

    try:
        response = requests.post(endpoint, headers=headers, json=data)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Show the full response
            console.print("\n[bold green]Response Body:[/bold green]")
            console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))

            # Show key fields
            console.print("\n[bold]Key Fields:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Type", style="yellow")

            # Show ID field (might be different names)
            id_field = None
            for key in [f"{resource}Id", "id", f"{resource}_id"]:
                if key in result:
                    id_field = key
                    table.add_row(key, str(result[key]), type(result[key]).__name__)
                    break

            if "name" in result:
                table.add_row("name", str(result["name"]), type(result["name"]).__name__)
            if "environmentId" in result:
                table.add_row("environmentId", str(result["environmentId"]), type(result["environmentId"]).__name__)

            console.print(table)

            if id_field:
                console.print(f"\n[bold green]✓ Success! {resource.capitalize()} created with ID: {result[id_field]}[/bold green]")
            else:
                console.print(f"\n[yellow]⚠ Warning: No ID field found in response! Expected '{resource}Id' or 'id'[/yellow]")
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            console.print(Syntax(response.text, "json", theme="monokai"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {e}[/red]")
        console.print(f"Raw response: {response.text}")
        sys.exit(1)


@cli.command()
@click.argument("resource")
@click.argument("resource_id")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
def get(resource, resource_id, api_key, url):
    """Get a resource and show the response"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    # Build the endpoint - try both query param and path styles
    id_param = f"{resource}Id"
    endpoint = f"{base_url}/api/{resource}.one?{id_param}={resource_id}"

    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    console.print(Panel(f"Testing: GET {endpoint}", style="bold cyan"))

    try:
        response = requests.get(endpoint, headers=headers)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            console.print("\n[bold green]Response Body:[/bold green]")
            console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            console.print(Syntax(response.text, "json", theme="monokai"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("resource")
@click.argument("resource_id")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
@click.option("--field", multiple=True, help="Field to update (format: key=value)")
def update(resource, resource_id, api_key, url, field):
    """Update a resource and show the response"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    # Build update data
    id_field = f"{resource}Id"
    data = {id_field: resource_id}

    # Add custom fields if provided
    for f in field:
        if "=" in f:
            key, value = f.split("=", 1)
            data[key] = value
        else:
            console.print(f"[yellow]Warning: Skipping invalid field format: {f}[/yellow]")

    endpoint = f"{base_url}/api/{resource}.update"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    console.print(Panel(f"Testing: POST {endpoint}", style="bold cyan"))
    console.print("\n[bold]Request Data:[/bold]")
    console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))

    try:
        response = requests.post(endpoint, headers=headers, json=data)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            console.print("\n[bold green]Response Body:[/bold green]")
            console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))

            # Compare what fields are in response vs request
            console.print("\n[bold]Field Comparison:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Field", style="cyan")
            table.add_column("In Request", style="yellow")
            table.add_column("In Response", style="green")

            all_fields = set(data.keys()) | set(result.keys() if isinstance(result, dict) else [])
            for field_name in sorted(all_fields):
                in_req = "✓" if field_name in data else "✗"
                in_resp = "✓" if isinstance(result, dict) and field_name in result else "✗"
                table.add_row(field_name, in_req, in_resp)

            console.print(table)
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            console.print(Syntax(response.text, "json", theme="monokai"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("resource")
@click.argument("resource_id")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
def delete(resource, resource_id, api_key, url):
    """Delete a resource and show the response (tries .remove then .delete)"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    # Build delete data
    id_field = f"{resource}Id"
    data = {id_field: resource_id}

    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Try .remove endpoint first, then fallback to .delete
    for operation in ["remove", "delete"]:
        endpoint = f"{base_url}/api/{resource}.{operation}"

        console.print(Panel(f"Testing: POST {endpoint}", style="bold cyan"))
        console.print("\n[bold]Request Data:[/bold]")
        console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))

        try:
            response = requests.post(endpoint, headers=headers, json=data)

            console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    console.print("\n[bold green]Response Body:[/bold green]")
                    console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
                except json.JSONDecodeError:
                    console.print("\n[bold green]Success! Resource deleted (empty response)[/bold green]")

                console.print(f"\n[bold green]✓ Success! {resource.capitalize()} deleted via .{operation} endpoint with ID: {resource_id}[/bold green]")
                return
            elif response.status_code == 404 and operation == "remove":
                console.print(f"\n[yellow]⚠ .{operation} endpoint not found, trying .delete...[/yellow]")
                continue
            else:
                console.print("\n[bold red]Error Response:[/bold red]")
                console.print(Syntax(response.text, "json", theme="monokai"))
                if operation == "remove":
                    console.print("\n[yellow]Trying .delete endpoint...[/yellow]")
                    continue
                else:
                    sys.exit(1)

        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request failed: {e}[/red]")
            if operation == "remove":
                console.print("\n[yellow]Trying .delete endpoint...[/yellow]")
                continue
            else:
                sys.exit(1)

    console.print(f"\n[red]✗ Failed to delete {resource} with ID: {resource_id}[/red]")
    sys.exit(1)


@cli.command(name="list")
@click.argument("resource")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
@click.option("--limit", type=int, help="Limit number of results")
def list_resources(resource, api_key, url, limit):
    """List all resources of a given type"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    endpoint = f"{base_url}/api/{resource}.all"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    console.print(Panel(f"Testing: GET {endpoint}", style="bold cyan"))

    try:
        response = requests.get(endpoint, headers=headers)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if isinstance(result, list):
                items = result[:limit] if limit else result
                console.print(f"\n[bold green]Found {len(result)} {resource}(s)[/bold green]")

                if items:
                    console.print(f"\n[bold]Showing {len(items)} {resource}(s):[/bold]")

                    table = Table(show_header=True, header_style="bold magenta")

                    # Get all keys from first item to build table columns
                    if items and isinstance(items[0], dict):
                        keys = list(items[0].keys())[:6]  # Limit to first 6 columns
                        for key in keys:
                            table.add_column(key, style="cyan")

                        for item in items:
                            row = [str(item.get(key, ""))[:50] for key in keys]
                            table.add_row(*row)

                        console.print(table)
                    else:
                        for item in items:
                            console.print(f"  • {item}")
                else:
                    console.print(f"\n[yellow]No {resource}s found[/yellow]")
            else:
                console.print("\n[bold green]Response Body:[/bold green]")
                console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            console.print(Syntax(response.text, "json", theme="monokai"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("resource")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
@click.option("--filter", multiple=True, help="Filter results (format: field=value)")
@click.option("--limit", type=int, help="Limit number of results")
def query(resource, api_key, url, filter, limit):
    """Query resources with filters"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    # Parse filters
    filters = {}
    for f in filter:
        if "=" in f:
            key, value = f.split("=", 1)
            filters[key] = value
        else:
            console.print(f"[yellow]Warning: Skipping invalid filter format: {f}[/yellow]")

    endpoint = f"{base_url}/api/{resource}.all"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    console.print(Panel(f"Testing: GET {endpoint}", style="bold cyan"))
    if filters:
        console.print(f"\n[bold]Filters:[/bold] {filters}")

    try:
        response = requests.get(endpoint, headers=headers)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if isinstance(result, list):
                # Apply filters client-side
                filtered_items = result
                for key, value in filters.items():
                    filtered_items = [
                        item for item in filtered_items
                        if isinstance(item, dict) and str(item.get(key, "")).lower().find(value.lower()) != -1
                    ]

                items = filtered_items[:limit] if limit else filtered_items
                console.print(f"\n[bold green]Found {len(filtered_items)} matching {resource}(s)[/bold green]")

                if items:
                    console.print(f"\n[bold]Showing {len(items)} {resource}(s):[/bold]")

                    table = Table(show_header=True, header_style="bold magenta")

                    # Get all keys from first item to build table columns
                    if items and isinstance(items[0], dict):
                        keys = list(items[0].keys())[:8]  # Limit to first 8 columns
                        for key in keys:
                            table.add_column(key, style="cyan")

                        for item in items:
                            row = [str(item.get(key, ""))[:50] for key in keys]
                            table.add_row(*row)

                        console.print(table)
                    else:
                        for item in items:
                            console.print(f"  • {item}")
                else:
                    console.print(f"\n[yellow]No matching {resource}s found[/yellow]")
            else:
                console.print("\n[bold green]Response Body:[/bold green]")
                console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            console.print(Syntax(response.text, "json", theme="monokai"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {e}[/red]")
        sys.exit(1)


@cli.command(name="batch-delete")
@click.argument("resource")
@click.argument("resource_ids", nargs=-1, required=True)
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
@click.option("--delay", default=0.5, type=float, help="Delay between deletes (seconds)")
def batch_delete(resource, resource_ids, api_key, url, delay):
    """Delete multiple resources by ID"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    total = len(resource_ids)
    success_count = 0
    failed_count = 0
    failed_ids = []

    console.print(Panel(f"Batch deleting {total} {resource}(s)", style="bold cyan"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Deleting...", total=total)

        for idx, resource_id in enumerate(resource_ids, 1):
            progress.update(task, description=f"[cyan]Deleting {idx}/{total}: {resource_id}")

            # Build delete data
            id_field = f"{resource}Id"
            data = {id_field: resource_id}

            headers = {
                "accept": "application/json",
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }

            # Try .remove endpoint first, then fallback to .delete
            deleted = False
            for operation in ["remove", "delete"]:
                endpoint = f"{base_url}/api/{resource}.{operation}"

                try:
                    response = requests.post(endpoint, headers=headers, json=data)

                    if response.status_code == 200:
                        success_count += 1
                        deleted = True
                        break
                    elif response.status_code == 404 and operation == "remove":
                        continue
                    elif operation == "delete":
                        failed_count += 1
                        failed_ids.append(resource_id)
                        break

                except requests.exceptions.RequestException:
                    if operation == "remove":
                        continue
                    else:
                        failed_count += 1
                        failed_ids.append(resource_id)
                        break

            if not deleted and resource_id not in failed_ids:
                failed_count += 1
                failed_ids.append(resource_id)

            progress.advance(task)

            if idx < total and delay > 0:
                time.sleep(delay)

    # Display summary
    console.print("\n[bold]Summary:[/bold]")
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Total", str(total))
    table.add_row("Successful", str(success_count))
    table.add_row("Failed", str(failed_count))

    console.print(table)

    if failed_ids:
        console.print("\n[bold red]Failed IDs:[/bold red]")
        for failed_id in failed_ids:
            console.print(f"  • {failed_id}")
        sys.exit(1)
    else:
        console.print(f"\n[bold green]✓ All {total} {resource}(s) deleted successfully![/bold green]")


@cli.command()
@click.option("--app-id", required=True, help="Application ID to query domains for")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
def domains(app_id, api_key, url):
    """Get domains for a specific application"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    endpoint = f"{base_url}/api/domain.byApplicationId?applicationId={app_id}"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    console.print(Panel(f"Testing: GET {endpoint}", style="bold cyan"))

    try:
        response = requests.get(endpoint, headers=headers)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if isinstance(result, list):
                console.print(f"\n[bold green]Found {len(result)} domain(s) for application {app_id}[/bold green]")

                if result:
                    console.print("\n[bold]Domain Configuration:[/bold]")

                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Domain ID", style="cyan")
                    table.add_column("Host", style="green")
                    table.add_column("HTTPS", style="yellow")
                    table.add_column("Port", style="blue")
                    table.add_column("Path", style="cyan")
                    table.add_column("Certificate Type", style="magenta")

                    for domain in result:
                        table.add_row(
                            str(domain.get("domainId", ""))[:30],
                            str(domain.get("host", "")),
                            "✓" if domain.get("https") else "✗",
                            str(domain.get("port", "")),
                            str(domain.get("path", "")),
                            str(domain.get("certificateType", ""))
                        )

                    console.print(table)

                    # Show full details for first domain
                    if len(result) > 0:
                        console.print("\n[bold]Full Details (first domain):[/bold]")
                        console.print(Syntax(json.dumps(result[0], indent=2), "json", theme="monokai"))
                else:
                    console.print(f"\n[yellow]No domains found for application {app_id}[/yellow]")
            else:
                console.print("\n[bold green]Response Body:[/bold green]")
                console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            try:
                error_data = response.json()
                console.print(Syntax(json.dumps(error_data, indent=2), "json", theme="monokai"))

                # Provide helpful error messages
                if response.status_code == 404:
                    console.print(f"\n[yellow]Application with ID '{app_id}' not found or has no domains[/yellow]")
                elif response.status_code == 401:
                    console.print("\n[yellow]Authentication failed. Check your API key.[/yellow]")
            except json.JSONDecodeError:
                console.print(response.text)
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--app-id", required=True, help="Application ID to list deployments for")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
@click.option("--limit", type=int, help="Limit number of results")
def deployments(app_id, api_key, url, limit):
    """List deployment history for an application"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    endpoint = f"{base_url}/api/deployment.all?applicationId={app_id}"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    console.print(Panel(f"Testing: GET {endpoint}", style="bold cyan"))

    try:
        response = requests.get(endpoint, headers=headers)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if isinstance(result, list):
                items = result[:limit] if limit else result
                console.print(f"\n[bold green]Found {len(result)} deployment(s) for application {app_id}[/bold green]")

                if items:
                    console.print(f"\n[bold]Showing {len(items)} deployment(s):[/bold]")

                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Deployment ID", style="cyan", width=30)
                    table.add_column("Status", style="green")
                    table.add_column("Created At", style="yellow")
                    table.add_column("Title", style="blue", width=30)
                    table.add_column("Log Path", style="magenta", width=40)

                    for deployment in items:
                        table.add_row(
                            str(deployment.get("deploymentId", ""))[:30],
                            str(deployment.get("status", "")),
                            str(deployment.get("createdAt", ""))[:19],
                            str(deployment.get("title", ""))[:30],
                            str(deployment.get("logPath", ""))[:40]
                        )

                    console.print(table)

                    # Show full details for first deployment
                    if len(items) > 0:
                        console.print("\n[bold]Full Details (most recent deployment):[/bold]")
                        console.print(Syntax(json.dumps(items[0], indent=2), "json", theme="monokai"))
                else:
                    console.print(f"\n[yellow]No deployments found for application {app_id}[/yellow]")
            else:
                console.print("\n[bold green]Response Body:[/bold green]")
                console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            try:
                error_data = response.json()
                console.print(Syntax(json.dumps(error_data, indent=2), "json", theme="monokai"))

                if response.status_code == 404:
                    console.print(f"\n[yellow]Application with ID '{app_id}' not found[/yellow]")
                elif response.status_code == 401:
                    console.print("\n[yellow]Authentication failed. Check your API key.[/yellow]")
            except json.JSONDecodeError:
                console.print(response.text)
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--app-id", required=True, help="Application ID to deploy")
@click.option("--title", help="Optional deployment title")
@click.option("--description", help="Optional deployment description")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
def deploy(app_id, title, description, api_key, url):
    """Trigger a new deployment for an application"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    endpoint = f"{base_url}/api/application.deploy"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Build request data
    data = {"applicationId": app_id}
    if title:
        data["title"] = title
    if description:
        data["description"] = description

    console.print(Panel(f"Testing: POST {endpoint}", style="bold cyan"))
    console.print("\n[bold]Request Data:[/bold]")
    console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))

    try:
        response = requests.post(endpoint, headers=headers, json=data)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            console.print("\n[bold green]Response Body:[/bold green]")
            console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
            console.print(f"\n[bold green]✓ Deployment triggered successfully for application: {app_id}[/bold green]")
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            try:
                error_data = response.json()
                console.print(Syntax(json.dumps(error_data, indent=2), "json", theme="monokai"))

                if response.status_code == 404:
                    console.print(f"\n[yellow]Application with ID '{app_id}' not found[/yellow]")
                elif response.status_code == 401:
                    console.print("\n[yellow]Authentication failed. Check your API key.[/yellow]")
            except json.JSONDecodeError:
                console.print(response.text)
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--app-id", required=True, help="Application ID to redeploy")
@click.option("--title", help="Optional redeployment title")
@click.option("--description", help="Optional redeployment description")
@click.option("--api-key", envvar="API_KEY", help="Dokploy API key")
@click.option("--url", envvar="BASE_URL", help="Dokploy base URL")
def redeploy(app_id, title, description, api_key, url):
    """Trigger a redeployment for an application"""
    config = load_config()
    api_key = api_key or config["api_key"]
    base_url = url or config["base_url"]

    if not api_key:
        console.print("[red]Error: API_KEY not found[/red]")
        sys.exit(1)

    endpoint = f"{base_url}/api/application.redeploy"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Build request data
    data = {"applicationId": app_id}
    if title:
        data["title"] = title
    if description:
        data["description"] = description

    console.print(Panel(f"Testing: POST {endpoint}", style="bold cyan"))
    console.print("\n[bold]Request Data:[/bold]")
    console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))

    try:
        response = requests.post(endpoint, headers=headers, json=data)

        console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            console.print("\n[bold green]Response Body:[/bold green]")
            console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
            console.print(f"\n[bold green]✓ Redeployment triggered successfully for application: {app_id}[/bold green]")
        else:
            console.print("\n[bold red]Error Response:[/bold red]")
            try:
                error_data = response.json()
                console.print(Syntax(json.dumps(error_data, indent=2), "json", theme="monokai"))

                if response.status_code == 404:
                    console.print(f"\n[yellow]Application with ID '{app_id}' not found[/yellow]")
                elif response.status_code == 401:
                    console.print("\n[yellow]Authentication failed. Check your API key.[/yellow]")
            except json.JSONDecodeError:
                console.print(response.text)
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Request failed: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
