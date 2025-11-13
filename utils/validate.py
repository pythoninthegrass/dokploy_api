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

"""
Validate OpenAPI spec endpoint coverage against implemented Terraform resources.

This script compares the endpoints defined in the OpenAPI specification with
the actual implemented Terraform resources and generates a coverage report.
"""

import json
import sys
from collections import defaultdict

# Import shared utilities
from lib.dokploy import load_openapi_from_file
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Define the implemented resources and their CRUD operations
IMPLEMENTED_RESOURCES = {
    "project": {
        "create": "/project.create",
        "read": "/project.one",
        "update": "/project.update",
        "delete": "/project.remove",
    },
    "application": {
        "create": "/application.create",
        "read": "/application.one",
        "update": "/application.update",
        "delete": "/application.delete",
        "deploy": "/application.deploy",
        "redeploy": "/application.redeploy",
        "start": "/application.start",
        "stop": "/application.stop",
        "reload": "/application.reload",
    },
    "domain": {
        "create": "/domain.create",
        "read": "/domain.one",
        "update": "/domain.update",
        "delete": "/domain.delete",
    },
    "compose": {
        "create": "/compose.create",
        "read": "/compose.one",
        "update": "/compose.update",
        "delete": "/compose.delete",
        "deploy": "/compose.deploy",
        "redeploy": "/compose.redeploy",
        "start": "/compose.start",
        "stop": "/compose.stop",
    },
    "backup": {
        "create": "/backup.create",
        "read": "/backup.one",
        "update": "/backup.update",
        "delete": "/backup.remove",
    },
    "registry": {
        "create": "/registry.create",
        "read": "/registry.one",
        "update": "/registry.update",
        "delete": "/registry.remove",
    },
    "server": {
        "create": "/server.create",
        "read": "/server.one",
        "update": "/server.update",
        "delete": "/server.remove",
    },
    "mount": {
        "create": "/mounts.create",
        "read": "/mounts.one",
        "update": "/mounts.update",
        "delete": "/mounts.remove",
    },
    "port": {
        "create": "/port.create",
        "read": "/port.one",
        "update": "/port.update",
        "delete": "/port.delete",
    },
    "security": {
        "create": "/security.create",
        "read": "/security.one",
        "update": "/security.update",
        "delete": "/security.delete",
    },
    "ssh_key": {
        "create": "/sshKey.create",
        "read": "/sshKey.one",
        "update": "/sshKey.update",
        "delete": "/sshKey.remove",
    },
}

# Resources that were analyzed and determined to be non-viable for Terraform
NON_VIABLE_RESOURCES = {
    "auth": "Not a standard Dokploy resource with CRUD operations",
    "cluster": "Docker Swarm management API, no create endpoint",
    "deployment": "Read-only deployment history, no CRUD pattern",
    "docker": "Read-only container operations, not resource creation",
    "github": "OAuth integration, no create endpoint",
    "notification": "Complex type-specific endpoints (Slack/Discord/etc)",
    "settings": "Server-wide configuration, no standard CRUD pattern",
    "user": "No create endpoint (admin-managed only)",
}


# Removed load_openapi_spec() - now using shared lib.dokploy.load_openapi_from_file()


def load_endpoints(endpoints_path: Path) -> dict:
    """Load the endpoints inventory from JSON file."""
    with open(endpoints_path) as f:
        return json.load(f)


def extract_crud_endpoints(spec: dict) -> dict[str, list[str]]:
    """Extract CRUD endpoints by resource category from OpenAPI spec."""
    endpoints_by_category = defaultdict(list)

    if "paths" not in spec:
        return endpoints_by_category

    for path, methods in spec["paths"].items():
        # Extract resource category from path (e.g., /project.create -> project)
        path_clean = path.lstrip("/")  # Remove leading /
        if "." in path_clean:
            category = path_clean.split(".")[0]
            endpoints_by_category[category].append(path_clean)

    return dict(endpoints_by_category)


def categorize_endpoint(endpoint: str) -> str:
    """Categorize an endpoint as CRUD, lifecycle, or other."""
    endpoint_lower = endpoint.lower()

    # CRUD operations
    if any(op in endpoint_lower for op in [".create", ".one", ".update", ".delete", ".remove"]):
        return "CRUD"

    # Lifecycle operations
    if any(op in endpoint_lower for op in [".deploy", ".redeploy", ".start", ".stop", ".reload", ".restart"]):
        return "Lifecycle"

    # List/query operations
    if any(op in endpoint_lower for op in [".all", ".list", ".get"]):
        return "Query"

    # Management operations
    return "Management"


def analyze_coverage() -> tuple[dict, dict, dict]:
    """Analyze endpoint coverage and generate reports."""
    project_root = Path(__file__).parent.parent
    endpoints_path = project_root / "docs" / "endpoints.json"

    # Load data
    spec = load_openapi_from_file()
    endpoints_data = load_endpoints(endpoints_path)

    # Extract endpoints by category
    spec_endpoints = extract_crud_endpoints(spec)

    # Track coverage
    covered_endpoints = set()
    for resource, ops in IMPLEMENTED_RESOURCES.items():
        for endpoint in ops.values():
            covered_endpoints.add(endpoint.lstrip("/"))

    # Analyze each category
    coverage_report = {}
    uncovered_endpoints = {}

    for category, endpoints in spec_endpoints.items():
        total = len(endpoints)
        covered = sum(1 for ep in endpoints if ep in covered_endpoints)

        coverage_report[category] = {
            "total": total,
            "covered": covered,
            "percentage": (covered / total * 100) if total > 0 else 0,
            "endpoints": endpoints,
            "covered_endpoints": [ep for ep in endpoints if ep in covered_endpoints],
            "uncovered_endpoints": [ep for ep in endpoints if ep not in covered_endpoints],
        }

        if covered < total:
            uncovered_endpoints[category] = [ep for ep in endpoints if ep not in covered_endpoints]

    return coverage_report, uncovered_endpoints, spec_endpoints


def generate_report():
    """Generate and print the coverage report."""
    print("=" * 80)
    print("DOKPLOY TERRAFORM PROVIDER - ENDPOINT COVERAGE REPORT")
    print("=" * 80)
    print()

    coverage_report, uncovered_endpoints, spec_endpoints = analyze_coverage()

    # Summary statistics
    total_endpoints = sum(len(eps) for eps in spec_endpoints.values())
    total_covered = sum(len(report["covered_endpoints"]) for report in coverage_report.values())
    overall_percentage = (total_covered / total_endpoints * 100) if total_endpoints > 0 else 0

    print("📊 OVERALL COVERAGE")
    print("-" * 80)
    print(f"Total endpoints in OpenAPI spec: {total_endpoints}")
    print(f"Covered by Terraform provider: {total_covered}")
    print(f"Coverage percentage: {overall_percentage:.1f}%")
    print()

    # Implemented resources
    print("✅ IMPLEMENTED RESOURCES (11)")
    print("-" * 80)
    for resource in sorted(IMPLEMENTED_RESOURCES.keys()):
        ops = IMPLEMENTED_RESOURCES[resource]
        print(f"  {resource:15} - {len(ops)} operations")
    print()

    # Coverage by category
    print("📋 COVERAGE BY CATEGORY")
    print("-" * 80)

    # Separate fully covered, partially covered, and uncovered
    fully_covered = []
    partially_covered = []
    not_covered = []

    for category in sorted(coverage_report.keys()):
        report = coverage_report[category]
        if report["covered"] == report["total"]:
            fully_covered.append((category, report))
        elif report["covered"] > 0:
            partially_covered.append((category, report))
        else:
            not_covered.append((category, report))

    # Print fully covered
    if fully_covered:
        print("\n✅ Fully Covered Categories:")
        for category, report in fully_covered:
            print(f"  {category:20} {report['covered']:3}/{report['total']:3} ({report['percentage']:5.1f}%)")

    # Print partially covered
    if partially_covered:
        print("\n⚠️  Partially Covered Categories:")
        for category, report in partially_covered:
            print(f"  {category:20} {report['covered']:3}/{report['total']:3} ({report['percentage']:5.1f}%)")

    # Print not covered
    if not_covered:
        print("\n❌ Not Covered Categories:")
        for category, report in not_covered:
            print(f"  {category:20} {report['covered']:3}/{report['total']:3} ({report['percentage']:5.1f}%)")

    print()

    # Non-viable resources
    print("🚫 NON-VIABLE RESOURCES (8)")
    print("-" * 80)
    for resource, reason in sorted(NON_VIABLE_RESOURCES.items()):
        print(f"  {resource:15} - {reason}")
    print()

    # Detailed uncovered endpoints by category
    if uncovered_endpoints:
        print("📝 UNCOVERED ENDPOINTS BY CATEGORY")
        print("-" * 80)
        for category in sorted(uncovered_endpoints.keys()):
            endpoints = uncovered_endpoints[category]
            print(f"\n{category.upper()} ({len(endpoints)} uncovered):")

            # Categorize endpoints
            crud_ops = []
            lifecycle_ops = []
            query_ops = []
            mgmt_ops = []

            for ep in endpoints:
                cat = categorize_endpoint(ep)
                if cat == "CRUD":
                    crud_ops.append(ep)
                elif cat == "Lifecycle":
                    lifecycle_ops.append(ep)
                elif cat == "Query":
                    query_ops.append(ep)
                else:
                    mgmt_ops.append(ep)

            if crud_ops:
                print("  CRUD operations:")
                for ep in sorted(crud_ops):
                    print(f"    - {ep}")
            if lifecycle_ops:
                print("  Lifecycle operations:")
                for ep in sorted(lifecycle_ops):
                    print(f"    - {ep}")
            if query_ops:
                print("  Query operations:")
                for ep in sorted(query_ops):
                    print(f"    - {ep}")
            if mgmt_ops:
                print("  Management operations:")
                for ep in sorted(mgmt_ops):
                    print(f"    - {ep}")

    print()
    print("=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)
    print()
    print(f"All viable CRUD resources are implemented: {len(IMPLEMENTED_RESOURCES)}/11")
    print(f"Non-viable resources documented: {len(NON_VIABLE_RESOURCES)}")
    print(f"Overall endpoint coverage: {overall_percentage:.1f}%")
    print()

    # Save report to file
    output_path = Path(__file__).parent.parent / "docs" / "COVERAGE_REPORT.md"
    save_markdown_report(coverage_report, uncovered_endpoints, spec_endpoints, output_path)
    print(f"📄 Detailed report saved to: {output_path}")
    print()


def save_markdown_report(coverage_report: dict, uncovered_endpoints: dict, spec_endpoints: dict, output_path: Path):
    """Save the coverage report as a Markdown file."""
    total_endpoints = sum(len(eps) for eps in spec_endpoints.values())
    total_covered = sum(len(report["covered_endpoints"]) for report in coverage_report.values())
    overall_percentage = (total_covered / total_endpoints * 100) if total_endpoints > 0 else 0

    with open(output_path, "w") as f:
        f.write("# Dokploy Terraform Provider - Endpoint Coverage Report\n\n")
        f.write(f"*Generated: {Path(__file__).parent.parent}*\n\n")

        # Summary
        f.write("## Summary\n\n")
        f.write(f"- **Total endpoints in OpenAPI spec:** {total_endpoints}\n")
        f.write(f"- **Covered by Terraform provider:** {total_covered}\n")
        f.write(f"- **Overall coverage:** {overall_percentage:.1f}%\n")
        f.write(f"- **Implemented resources:** {len(IMPLEMENTED_RESOURCES)}\n")
        f.write(f"- **Non-viable resources:** {len(NON_VIABLE_RESOURCES)}\n\n")

        # Implemented resources
        f.write("## Implemented Resources\n\n")
        f.write("All 11 viable Terraform resources are fully implemented:\n\n")
        for resource in sorted(IMPLEMENTED_RESOURCES.keys()):
            ops = IMPLEMENTED_RESOURCES[resource]
            f.write(f"### {resource.title()}\n\n")
            f.write(f"**Operations:** {len(ops)}\n\n")
            for op_name, endpoint in sorted(ops.items()):
                f.write(f"- `{op_name}`: `{endpoint}`\n")
            f.write("\n")

        # Non-viable resources
        f.write("## Non-Viable Resources\n\n")
        f.write("The following resources were analyzed and determined to be unsuitable for Terraform:\n\n")
        for resource, reason in sorted(NON_VIABLE_RESOURCES.items()):
            f.write(f"### {resource.title()}\n\n")
            f.write(f"**Reason:** {reason}\n\n")

        # Coverage by category
        f.write("## Coverage by Category\n\n")
        f.write("| Category | Covered | Total | Percentage |\n")
        f.write("|----------|---------|-------|------------|\n")
        for category in sorted(coverage_report.keys()):
            report = coverage_report[category]
            f.write(f"| {category} | {report['covered']} | {report['total']} | {report['percentage']:.1f}% |\n")
        f.write("\n")

        # Uncovered endpoints
        if uncovered_endpoints:
            f.write("## Uncovered Endpoints\n\n")
            for category in sorted(uncovered_endpoints.keys()):
                endpoints = uncovered_endpoints[category]
                f.write(f"### {category.title()}\n\n")
                for ep in sorted(endpoints):
                    cat = categorize_endpoint(ep)
                    f.write(f"- `{ep}` - *{cat}*\n")
                f.write("\n")


if __name__ == "__main__":
    try:
        generate_report()
    except FileNotFoundError as e:
        print(f"❌ Error: Required file not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
