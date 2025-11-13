#!/usr/bin/env python

"""
End-to-end tests for api.py CLI workflows

Tests verify complete user workflows from start to finish, simulating real-world
usage patterns with multiple command sequences and state management.
"""

import json
import pytest
import requests
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path to import api module
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import cli
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Create a Click test runner"""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock load_config to return test credentials"""
    return {"api_key": "test-api-key", "base_url": "https://test.dokploy.com"}


@pytest.fixture
def mock_api():
    """Mock API responses for complete workflows"""

    class MockAPI:
        def __init__(self):
            self.resources = {}
            self.call_count = 0

        def reset(self):
            self.resources = {}
            self.call_count = 0

        def create_response(self, resource_type, resource_id, data):
            """Simulate creating a resource"""
            self.resources[resource_id] = {**data, f"{resource_type}Id": resource_id}
            return Mock(status_code=200, json=lambda: self.resources[resource_id])

        def get_response(self, resource_id):
            """Simulate getting a resource"""
            if resource_id in self.resources:
                return Mock(status_code=200, json=lambda: self.resources[resource_id])
            return Mock(status_code=404, json=lambda: {"error": "Not found"})

        def update_response(self, resource_id, data):
            """Simulate updating a resource"""
            if resource_id in self.resources:
                self.resources[resource_id].update(data)
                return Mock(status_code=200, json=lambda: self.resources[resource_id])
            return Mock(status_code=404, json=lambda: {"error": "Not found"})

        def delete_response(self, resource_id):
            """Simulate deleting a resource"""
            if resource_id in self.resources:
                del self.resources[resource_id]
                return Mock(status_code=200, json=lambda: {"success": True})
            return Mock(status_code=404, json=lambda: {"error": "Not found"})

        def list_response(self):
            """Simulate listing resources"""
            return Mock(status_code=200, json=lambda: list(self.resources.values()))

    return MockAPI()


class TestCRUDWorkflow:
    """Test complete CRUD workflow: create → get → update → delete"""

    def test_complete_project_crud_workflow(self, runner, mock_config, mock_api):
        """Test full project lifecycle: create, get, list, delete"""
        project_id = "test-project-123"

        with patch("api.load_config", return_value=mock_config):
            # Step 1: Create project (uses built-in test data)
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = mock_api.create_response("project", project_id, {"name": "test-project"})
                result = runner.invoke(cli, ["create", "project"])
                assert result.exit_code == 0
                assert "200" in result.output

            # Step 2: Get project
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = mock_api.get_response(project_id)
                result = runner.invoke(cli, ["get", "project", project_id])
                assert result.exit_code == 0
                assert "test-project" in result.output

            # Step 3: List projects
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = mock_api.list_response()
                result = runner.invoke(cli, ["list", "project"])
                assert result.exit_code == 0
                assert "Found" in result.output

            # Step 4: Delete project
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = mock_api.delete_response(project_id)
                result = runner.invoke(cli, ["delete", "project", project_id])
                assert result.exit_code == 0

            # Step 5: Verify deletion (get returns 404)
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = mock_api.get_response(project_id)
                result = runner.invoke(cli, ["get", "project", project_id])
                assert result.exit_code == 1
                assert "404" in result.output or "not found" in result.output.lower()

    def test_list_and_query_workflow(self, runner, mock_config):
        """Test listing and querying resources"""
        with patch("api.load_config", return_value=mock_config):
            # List all projects
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {"projectId": "proj-1", "name": "Project 1"},
                        {"projectId": "proj-2", "name": "Project 2"},
                    ],
                )
                result = runner.invoke(cli, ["list", "project"])
                assert result.exit_code == 0
                assert "Found 2 project(s)" in result.output

            # Query with filter
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: [{"projectId": "proj-1", "name": "Project 1"}])
                result = runner.invoke(cli, ["query", "project", "--filter", "name=Project 1"])
                assert result.exit_code == 0
                assert "Found 1" in result.output


class TestDeploymentWorkflow:
    """Test deployment workflow: connect GitHub → deploy → monitor"""

    def test_complete_deployment_workflow(self, runner, mock_config):
        """Test full deployment cycle from GitHub connection to deployment monitoring"""
        app_id = "deploy-app-123"
        github_id = "github-provider-1"
        deployment_id = "deploy-001"

        with patch("api.load_config", return_value=mock_config):
            # Step 1: List available GitHub providers
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [{"githubId": github_id, "githubAppName": "Test Provider", "accountId": "acc-123"}],
                )
                result = runner.invoke(cli, ["github-providers"])
                assert result.exit_code == 0
                assert github_id in result.output

            # Step 2: Connect application to GitHub provider
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = Mock(status_code=200, json=lambda: {"success": True})
                result = runner.invoke(
                    cli,
                    [
                        "connect-github",
                        "--app-id",
                        app_id,
                        "--github-id",
                        github_id,
                        "--owner",
                        "testuser",
                        "--repository",
                        "test-repo",
                        "--branch",
                        "main",
                    ],
                )
                assert result.exit_code == 0
                assert "Successfully connected" in result.output

            # Step 3: Trigger deployment
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = Mock(status_code=200, json=lambda: {"deploymentId": deployment_id, "status": "pending"})
                result = runner.invoke(cli, ["deploy", "--app-id", app_id, "--title", "Initial deployment"])
                assert result.exit_code == 0
                assert "triggered successfully" in result.output

            # Step 4: Monitor deployment status
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {
                            "deploymentId": deployment_id,
                            "status": "done",
                            "title": "Initial deployment",
                            "createdAt": "2025-11-13T10:00:00Z",
                        }
                    ],
                )
                result = runner.invoke(cli, ["deployments", "--app-id", app_id])
                assert result.exit_code == 0
                assert deployment_id in result.output
                assert "done" in result.output

    def test_failed_deployment_retry_workflow(self, runner, mock_config):
        """Test deployment failure and retry logic"""
        app_id = "retry-app-123"

        with patch("api.load_config", return_value=mock_config):
            # Step 1: First deployment fails
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = Mock(status_code=500, json=lambda: {"error": "Internal server error"})
                result = runner.invoke(cli, ["deploy", "--app-id", app_id])
                assert result.exit_code == 1
                assert "Error Response" in result.output

            # Step 2: Check deployment history shows failure
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {
                            "deploymentId": "deploy-failed",
                            "status": "error",
                            "title": "Failed deployment",
                            "createdAt": "2025-11-13T10:00:00Z",
                        }
                    ],
                )
                result = runner.invoke(cli, ["deployments", "--app-id", app_id])
                assert result.exit_code == 0
                assert "error" in result.output

            # Step 3: Retry deployment (redeploy)
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = Mock(status_code=200, json=lambda: {"deploymentId": "deploy-retry", "status": "pending"})
                result = runner.invoke(cli, ["redeploy", "--app-id", app_id, "--title", "Retry deployment"])
                assert result.exit_code == 0
                assert "triggered successfully" in result.output


class TestDomainManagementWorkflow:
    """Test domain management workflow"""

    def test_domain_query_workflow(self, runner, mock_config):
        """Test querying and listing domains for applications"""
        app_id = "domain-app-123"
        domain_id = "domain-001"

        with patch("api.load_config", return_value=mock_config):
            # Query domains for application
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {
                            "domainId": domain_id,
                            "host": "example.com",
                            "https": True,
                            "port": 443,
                            "certificateType": "letsencrypt",
                        }
                    ],
                )
                result = runner.invoke(cli, ["domains", "--app-id", app_id])
                assert result.exit_code == 0
                assert "example.com" in result.output
                assert domain_id in result.output
                assert "Found 1 domain(s)" in result.output

            # Query domains - no results
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: [])
                result = runner.invoke(cli, ["domains", "--app-id", "app-no-domains"])
                assert result.exit_code == 0
                assert "Found 0 domain(s)" in result.output

    def test_multiple_domains_query_workflow(self, runner, mock_config):
        """Test querying multiple domains for single application"""
        app_id = "multi-domain-app"
        domains = ["example.com", "www.example.com", "api.example.com"]

        with patch("api.load_config", return_value=mock_config):
            # Query all domains for application
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {"domainId": f"domain-{i}", "host": host, "https": True, "port": 443} for i, host in enumerate(domains)
                    ],
                )
                result = runner.invoke(cli, ["domains", "--app-id", app_id])
                assert result.exit_code == 0
                assert f"Found {len(domains)} domain(s)" in result.output
                for host in domains:
                    assert host in result.output


class TestBatchOperations:
    """Test batch operations across multiple resources"""

    def test_batch_delete_workflow(self, runner, mock_config):
        """Test batch deleting multiple resources"""
        project_ids = ["proj-001", "proj-002", "proj-003"]

        with patch("api.load_config", return_value=mock_config):
            # List projects first
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [{"projectId": pid, "name": f"Project {pid}"} for pid in project_ids],
                )
                result = runner.invoke(cli, ["list", "project"])
                assert result.exit_code == 0
                assert f"Found {len(project_ids)} project(s)" in result.output

            # Batch delete projects
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = Mock(status_code=200, json=lambda: {"success": True})
                result = runner.invoke(cli, ["batch-delete", "project"] + project_ids + ["--delay", "0"])
                assert result.exit_code == 0
                assert "Successful" in result.output
                assert "3" in result.output
                assert "deleted successfully" in result.output

    def test_batch_operations_with_partial_failure(self, runner, mock_config):
        """Test batch delete with some failures"""
        project_ids = ["valid-1", "invalid", "valid-2"]

        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:

            def delete_with_failure(*args, **kwargs):
                data = kwargs.get("json", {})
                project_id = data.get("projectId")
                if project_id == "invalid":
                    return Mock(status_code=404, json=lambda: {"error": "Not found"})
                return Mock(status_code=200, json=lambda: {"success": True})

            mock_post.side_effect = delete_with_failure

            result = runner.invoke(cli, ["batch-delete", "project"] + project_ids + ["--delay", "0"])
            # Exit code 1 because some deletes failed
            assert result.exit_code == 1
            assert "Successful" in result.output
            assert "Failed" in result.output
            assert "invalid" in result.output


class TestErrorRecovery:
    """Test error handling and recovery workflows"""

    def test_network_failure_recovery(self, runner, mock_config):
        """Test handling network failures and retry"""
        project_id = "network-test-project"

        with patch("api.load_config", return_value=mock_config):
            # First attempt fails with network error
            with patch("api.requests.get") as mock_get:
                mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
                result = runner.invoke(cli, ["get", "project", project_id])
                assert result.exit_code == 1
                assert "Request failed" in result.output

            # Second attempt succeeds
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"projectId": project_id, "name": "Recovered Project"})
                result = runner.invoke(cli, ["get", "project", project_id])
                assert result.exit_code == 0
                assert "Recovered Project" in result.output

    def test_authentication_failure_workflow(self, runner):
        """Test handling authentication failures"""
        with patch("api.load_config", return_value={"api_key": "invalid-key", "base_url": "https://test.com"}):
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(status_code=401, json=lambda: {"error": "Unauthorized"})
                result = runner.invoke(cli, ["list", "project"])
                assert result.exit_code == 1
                assert "401" in result.output or "Unauthorized" in result.output

    def test_resource_not_found_workflow(self, runner, mock_config):
        """Test handling missing resources gracefully"""
        with patch("api.load_config", return_value=mock_config):
            # Try to get non-existent resource
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(status_code=404, json=lambda: {"error": "Resource not found"})
                result = runner.invoke(cli, ["get", "project", "nonexistent-id"])
                assert result.exit_code == 1
                assert "404" in result.output or "not found" in result.output.lower()

            # Try to update non-existent resource
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = Mock(status_code=404, json=lambda: {"error": "Resource not found"})
                result = runner.invoke(cli, ["update", "project", "nonexistent-id", "--field", "name=test"])
                assert result.exit_code == 1

            # Try to delete non-existent resource
            with patch("api.requests.post") as mock_post:
                mock_post.return_value = Mock(status_code=404, json=lambda: {"error": "Resource not found"})
                result = runner.invoke(cli, ["delete", "project", "nonexistent-id"])
                assert result.exit_code == 1


class TestMultiResourceWorkflow:
    """Test workflows involving multiple related resources"""

    def test_list_and_filter_applications_workflow(self, runner, mock_config):
        """Test listing and filtering applications across projects"""
        project_id = "multi-app-project"
        app_ids = ["app-001", "app-002"]

        with patch("api.load_config", return_value=mock_config):
            # List all applications
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {"applicationId": app_id, "name": f"App {i + 1}", "projectId": project_id}
                        for i, app_id in enumerate(app_ids)
                    ],
                )
                result = runner.invoke(cli, ["list", "application"])
                assert result.exit_code == 0
                assert f"Found {len(app_ids)}" in result.output

            # Query applications filtered by project
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {"applicationId": app_id, "name": f"App {i + 1}", "projectId": project_id}
                        for i, app_id in enumerate(app_ids)
                    ],
                )
                result = runner.invoke(cli, ["query", "application", "--filter", f"projectId={project_id}"])
                assert result.exit_code == 0
                assert f"Found {len(app_ids)}" in result.output
                assert "App 1" in result.output
                assert "App 2" in result.output

    def test_docker_monitoring_workflow(self, runner, mock_config):
        """Test Docker container monitoring workflow"""
        app_name = "my-app"

        with patch("api.load_config", return_value=mock_config):
            # Step 1: List all containers
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {"Id": "abc123", "Names": ["/my-app-web"], "State": "running", "Status": "Up 2 hours"},
                        {"Id": "def456", "Names": ["/my-app-db"], "State": "running", "Status": "Up 2 hours"},
                        {"Id": "ghi789", "Names": ["/other-app"], "State": "running", "Status": "Up 1 hour"},
                    ],
                )
                result = runner.invoke(cli, ["docker-list"])
                assert result.exit_code == 0
                assert "Found 3 container(s)" in result.output

            # Step 2: Filter containers by app name
            with patch("api.requests.get") as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    json=lambda: [
                        {"Id": "abc123", "Names": ["/my-app-web"], "State": "running", "Status": "Up 2 hours"},
                        {"Id": "def456", "Names": ["/my-app-db"], "State": "running", "Status": "Up 2 hours"},
                    ],
                )
                result = runner.invoke(cli, ["docker-containers", "--app-name", app_name])
                assert result.exit_code == 0
                assert "Found 2 container(s)" in result.output
                assert "my-app-web" in result.output
                assert "my-app-db" in result.output
