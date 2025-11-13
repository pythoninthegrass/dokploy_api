#!/usr/bin/env python

"""
Unit tests for api.py CLI commands

Tests use mocking to verify command behavior without making real API calls.
Tests verify:
- Command parameter handling and validation
- Successful response formatting and display
- Error handling for invalid inputs and API errors
- Network error handling
"""

import json
import pytest
import requests
import sys
from pathlib import Path

# Add parent directory to path to import api module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the CLI from api.py
from api import cli
from click.testing import CliRunner
from unittest.mock import Mock, patch


class TestDomainsCommand:
    """Test suite for domains command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Mock load_config to return test credentials"""
        return {"api_key": "test-api-key", "base_url": "https://test.dokploy.com"}

    @pytest.fixture
    def valid_domain_response(self):
        """Sample valid domain response"""
        return [
            {
                "domainId": "test-domain-id-1",
                "host": "example.com",
                "https": True,
                "port": 443,
                "path": "/",
                "certificateType": "letsencrypt",
            },
            {
                "domainId": "test-domain-id-2",
                "host": "api.example.com",
                "https": True,
                "port": 443,
                "path": "/api",
                "certificateType": "letsencrypt",
            },
        ]

    def test_domains_command_with_valid_app_id(self, runner, mock_config, valid_domain_response):
        """Test domains command with valid application ID returns domain configuration"""
        app_id = "test-app-123"

        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_domain_response
            mock_get.return_value = mock_response

            # Run command
            result = runner.invoke(cli, ["domains", "--app-id", app_id])

            # Verify command succeeded
            assert result.exit_code == 0, f"Command failed with output: {result.output}"

            # Verify API was called correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert f"domain.byApplicationId?applicationId={app_id}" in call_args[0][0]

            # Verify output contains domain information
            assert "Found 2 domain(s)" in result.output
            assert "Domain Configuration" in result.output
            assert "example.com" in result.output
            assert "api.example.com" in result.output

    def test_domains_command_with_invalid_app_id(self, runner, mock_config):
        """Test domains command with invalid application ID handles error gracefully"""
        app_id = "invalid-app-id"

        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            # Setup mock 404 response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Application not found"}
            mock_get.return_value = mock_response

            # Run command
            result = runner.invoke(cli, ["domains", "--app-id", app_id])

            # Verify command reports error
            assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

            # Verify error message is displayed
            assert "Error Response" in result.output
            assert "404" in result.output or "not found" in result.output.lower()

    def test_domains_command_with_no_domains(self, runner, mock_config):
        """Test domains command when application has no domains"""
        app_id = "app-with-no-domains"

        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            # Setup mock response with empty list
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            # Run command
            result = runner.invoke(cli, ["domains", "--app-id", app_id])

            # Verify command succeeded
            assert result.exit_code == 0

            # Verify output indicates no domains
            assert "Found 0 domain(s)" in result.output
            assert "No domains found" in result.output

    def test_domains_command_missing_app_id(self, runner):
        """Test domains command fails without required app-id parameter"""
        result = runner.invoke(cli, ["domains"])

        # Verify command fails with appropriate error
        assert result.exit_code != 0
        assert "Missing option" in result.output or "--app-id" in result.output

    def test_domains_command_network_error(self, runner, mock_config):
        """Test domains command handles network errors"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            # Simulate network error - use requests.exceptions.RequestException
            mock_get.side_effect = requests.exceptions.RequestException("Connection refused")

            result = runner.invoke(cli, ["domains", "--app-id", "test-app"])

            # Verify error is reported
            assert result.exit_code == 1
            assert "Request failed" in result.output

    def test_domains_command_displays_table_format(self, runner, mock_config, valid_domain_response):
        """Test domains command displays results in formatted table"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_domain_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["domains", "--app-id", "test-app"])

            # Verify table headers are present
            assert "Domain ID" in result.output
            assert "Host" in result.output
            assert "HTTPS" in result.output
            assert "Port" in result.output
            assert "Certificate Type" in result.output

            # Verify table values are present
            assert "example.com" in result.output
            assert "letsencrypt" in result.output


class TestDeploymentCommands:
    """Test suite for deployment commands"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Mock load_config to return test credentials"""
        return {"api_key": "test-api-key", "base_url": "https://test.dokploy.com"}

    @pytest.fixture
    def valid_deployments_response(self):
        """Sample valid deployments response"""
        return [
            {
                "deploymentId": "deploy-1",
                "status": "done",
                "createdAt": "2025-11-13T10:00:00Z",
                "title": "Deploy v1.0.0",
                "logPath": "/etc/dokploy/logs/app/deploy-1.log",
            },
            {
                "deploymentId": "deploy-2",
                "status": "running",
                "createdAt": "2025-11-13T11:00:00Z",
                "title": "Deploy v1.0.1",
                "logPath": "/etc/dokploy/logs/app/deploy-2.log",
            },
        ]

    def test_deployments_command_with_valid_app_id(self, runner, mock_config, valid_deployments_response):
        """Test deployments command lists deployment history"""
        app_id = "test-app-123"

        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_deployments_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["deployments", "--app-id", app_id])

            assert result.exit_code == 0
            assert "Found 2 deployment(s)" in result.output
            assert "deploy-1" in result.output
            assert "done" in result.output

    def test_deployments_command_with_limit(self, runner, mock_config, valid_deployments_response):
        """Test deployments command respects limit parameter"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_deployments_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["deployments", "--app-id", "test-app", "--limit", "1"])

            assert result.exit_code == 0
            assert "Showing 1 deployment(s)" in result.output

    def test_deployments_command_with_no_deployments(self, runner, mock_config):
        """Test deployments command when no deployments exist"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["deployments", "--app-id", "test-app"])

            assert result.exit_code == 0
            assert "No deployments found" in result.output

    def test_deploy_command_success(self, runner, mock_config):
        """Test deploy command triggers deployment successfully"""
        app_id = "test-app-123"

        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"deploymentId": "new-deploy-1"}
            mock_post.return_value = mock_response

            result = runner.invoke(cli, ["deploy", "--app-id", app_id])

            assert result.exit_code == 0
            assert "Deployment triggered successfully" in result.output

            # Verify POST was called with correct data
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["applicationId"] == app_id

    def test_deploy_command_with_title_and_description(self, runner, mock_config):
        """Test deploy command with optional title and description"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"deploymentId": "new-deploy-1"}
            mock_post.return_value = mock_response

            result = runner.invoke(cli, ["deploy", "--app-id", "test-app", "--title", "v2.0.0", "--description", "Major release"])

            assert result.exit_code == 0

            # Verify title and description were included
            call_args = mock_post.call_args
            assert call_args[1]["json"]["title"] == "v2.0.0"
            assert call_args[1]["json"]["description"] == "Major release"

    def test_deploy_command_with_invalid_app_id(self, runner, mock_config):
        """Test deploy command handles invalid application ID"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Application not found"}
            mock_post.return_value = mock_response

            result = runner.invoke(cli, ["deploy", "--app-id", "invalid-app"])

            assert result.exit_code == 1
            assert "Error Response" in result.output

    def test_redeploy_command_success(self, runner, mock_config):
        """Test redeploy command triggers redeployment successfully"""
        app_id = "test-app-123"

        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"deploymentId": "redeploy-1"}
            mock_post.return_value = mock_response

            result = runner.invoke(cli, ["redeploy", "--app-id", app_id])

            assert result.exit_code == 0
            assert "Redeployment triggered successfully" in result.output

    def test_redeploy_command_with_title(self, runner, mock_config):
        """Test redeploy command with optional title"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"deploymentId": "redeploy-1"}
            mock_post.return_value = mock_response

            result = runner.invoke(cli, ["redeploy", "--app-id", "test-app", "--title", "Hotfix"])

            assert result.exit_code == 0

            # Verify title was included
            call_args = mock_post.call_args
            assert call_args[1]["json"]["title"] == "Hotfix"


class TestGitHubProviderCommands:
    """Test suite for GitHub provider commands"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Mock load_config to return test credentials"""
        return {"api_key": "test-api-key", "base_url": "https://test.dokploy.com"}

    @pytest.fixture
    def valid_providers_response(self):
        """Sample valid GitHub providers response"""
        return [
            {
                "githubId": "github-provider-1",
                "githubAppName": "Dokploy GitHub App",
                "accountId": "account-123",
                "createdAt": "2025-11-01T10:00:00Z",
            },
            {
                "githubId": "github-provider-2",
                "githubAppName": "Production App",
                "accountId": "account-456",
                "createdAt": "2025-11-02T15:30:00Z",
            },
        ]

    def test_github_providers_command_success(self, runner, mock_config, valid_providers_response):
        """Test github-providers command lists providers"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_providers_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["github-providers"])

            assert result.exit_code == 0
            assert "Found 2 GitHub provider(s)" in result.output
            assert "github-provider-1" in result.output
            assert "Dokploy GitHub App" in result.output

    def test_github_providers_command_empty(self, runner, mock_config):
        """Test github-providers command with no providers"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["github-providers"])

            assert result.exit_code == 0
            assert "No GitHub providers found" in result.output

    def test_connect_github_command_success(self, runner, mock_config):
        """Test connect-github command connects app to provider"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_post.return_value = mock_response

            result = runner.invoke(
                cli,
                [
                    "connect-github",
                    "--app-id",
                    "test-app-123",
                    "--github-id",
                    "github-provider-1",
                    "--owner",
                    "testuser",
                    "--repository",
                    "test-repo",
                ],
            )

            assert result.exit_code == 0
            assert "Successfully connected" in result.output

            # Verify POST was called with correct data
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            data = call_args[1]["json"]
            assert data["applicationId"] == "test-app-123"
            assert data["githubId"] == "github-provider-1"
            assert data["owner"] == "testuser"
            assert data["repository"] == "test-repo"

    def test_connect_github_command_with_optional_params(self, runner, mock_config):
        """Test connect-github command with all optional parameters"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_post.return_value = mock_response

            result = runner.invoke(
                cli,
                [
                    "connect-github",
                    "--app-id",
                    "test-app",
                    "--github-id",
                    "github-provider",
                    "--owner",
                    "testuser",
                    "--repository",
                    "repo",
                    "--branch",
                    "develop",
                    "--build-path",
                    "/app",
                    "--enable-submodules",
                    "--trigger-type",
                    "tag",
                ],
            )

            assert result.exit_code == 0

            # Verify optional parameters were included
            call_args = mock_post.call_args
            data = call_args[1]["json"]
            assert data["branch"] == "develop"
            assert data["buildPath"] == "/app"
            assert data["enableSubmodules"] is True
            assert data["triggerType"] == "tag"

    def test_connect_github_command_missing_required_params(self, runner):
        """Test connect-github command fails without required parameters"""
        result = runner.invoke(cli, ["connect-github"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_connect_github_command_with_404_error(self, runner, mock_config):
        """Test connect-github command handles 404 error"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Application not found"}
            mock_post.return_value = mock_response

            result = runner.invoke(
                cli, ["connect-github", "--app-id", "invalid-app", "--github-id", "github-provider", "--owner", "testuser"]
            )

            assert result.exit_code == 1
            assert "Error Response" in result.output

    def test_test_github_command_success(self, runner, mock_config):
        """Test test-github command tests connection successfully"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"connected": True, "status": "ok"}
            mock_post.return_value = mock_response

            result = runner.invoke(cli, ["test-github", "--github-id", "github-provider-1"])

            assert result.exit_code == 0
            assert "connection test successful" in result.output

            # Verify POST was called with correct data
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["githubId"] == "github-provider-1"

    def test_test_github_command_with_404_error(self, runner, mock_config):
        """Test test-github command handles provider not found"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Provider not found"}
            mock_post.return_value = mock_response

            result = runner.invoke(cli, ["test-github", "--github-id", "invalid-provider"])

            assert result.exit_code == 1
            assert "not found" in result.output


class TestDockerCommands:
    """Test suite for Docker commands"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Mock load_config to return test credentials"""
        return {"api_key": "test-api-key", "base_url": "https://test.dokploy.com"}

    @pytest.fixture
    def valid_containers_response(self):
        """Sample valid Docker containers response"""
        return [
            {"Id": "abc123def456", "Names": ["/my-app-web"], "State": "running", "Status": "Up 2 hours", "Image": "nginx:latest"},
            {"Id": "def456ghi789", "Names": ["/my-app-db"], "State": "running", "Status": "Up 2 hours", "Image": "postgres:14"},
            {
                "Id": "ghi789jkl012",
                "Names": ["/my-app-cache"],
                "State": "exited",
                "Status": "Exited (0) 1 hour ago",
                "Image": "redis:alpine",
            },
        ]

    def test_docker_containers_command_success(self, runner, mock_config, valid_containers_response):
        """Test docker-containers command lists matching containers"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_containers_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["docker-containers", "--app-name", "my-app"])

            assert result.exit_code == 0
            assert "Found 3 container(s)" in result.output
            assert "my-app-web" in result.output
            assert "running" in result.output

    def test_docker_containers_command_with_filters(self, runner, mock_config, valid_containers_response):
        """Test docker-containers command with app-type filter"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_containers_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["docker-containers", "--app-name", "my-app", "--app-type", "stack"])

            assert result.exit_code == 0

            # Verify query parameters were included
            call_args = mock_get.call_args
            assert "appType=stack" in call_args[0][0]

    def test_docker_containers_command_no_matches(self, runner, mock_config):
        """Test docker-containers command with no matching containers"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["docker-containers", "--app-name", "nonexistent"])

            assert result.exit_code == 0
            assert "No containers found" in result.output

    def test_docker_list_command_success(self, runner, mock_config, valid_containers_response):
        """Test docker-list command lists all containers"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_containers_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["docker-list"])

            assert result.exit_code == 0
            assert "Found 3 container(s)" in result.output
            assert "Summary by State" in result.output
            assert "running: 2" in result.output
            assert "exited: 1" in result.output

    def test_docker_list_command_with_server_id(self, runner, mock_config, valid_containers_response):
        """Test docker-list command with server ID filter"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = valid_containers_response
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["docker-list", "--server-id", "server-123"])

            assert result.exit_code == 0

            # Verify query parameter was included
            call_args = mock_get.call_args
            assert "serverId=server-123" in call_args[0][0]

    def test_docker_list_command_empty(self, runner, mock_config):
        """Test docker-list command with no containers"""
        with patch("api.load_config", return_value=mock_config), patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["docker-list"])

            assert result.exit_code == 0
            assert "No containers found" in result.output
