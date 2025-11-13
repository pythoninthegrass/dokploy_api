#!/usr/bin/env python

"""Integration tests for lib/dokploy.py API client functions.

Tests the interaction between CLI commands and the API client layer using
HTTP mocking to simulate API responses without making actual network calls.
"""

import json
import os
import pytest
import requests
import responses
from lib.dokploy import (
    extract_endpoints,
    fetch_openapi_spec,
    load_config,
    load_openapi_from_file,
    make_api_request,
)
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory


class TestLoadConfig:
    """Test config loading from .env files and environment variables."""

    def test_load_config_from_env_file(self, tmp_path, monkeypatch):
        """Test loading config from .env file"""
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("BASE_URL", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=test-key-123\nBASE_URL=https://test.example.com")

        config = load_config(env_file)

        assert config["api_key"] == "test-key-123"
        assert config["base_url"] == "https://test.example.com"

    def test_load_config_from_env_file_with_defaults(self, tmp_path, monkeypatch):
        """Test loading config with only API_KEY specified"""
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("BASE_URL", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=test-key-456")

        config = load_config(env_file)

        assert config["api_key"] == "test-key-456"
        assert config["base_url"] == "http://10.5.162.35:3000"

    def test_load_config_from_environment_variables(self, tmp_path, monkeypatch):
        """Test loading config from environment variables when .env doesn't exist"""
        nonexistent_file = tmp_path / "nonexistent.env"
        monkeypatch.setenv("API_KEY", "env-key-789")
        monkeypatch.setenv("BASE_URL", "https://env.example.com")

        config = load_config(nonexistent_file)

        assert config["api_key"] == "env-key-789"
        assert config["base_url"] == "https://env.example.com"

    def test_load_config_from_environment_with_defaults(self, tmp_path, monkeypatch):
        """Test environment variables with default BASE_URL"""
        nonexistent_file = tmp_path / "nonexistent.env"
        monkeypatch.setenv("API_KEY", "env-key-default")
        monkeypatch.delenv("BASE_URL", raising=False)

        config = load_config(nonexistent_file)

        assert config["api_key"] == "env-key-default"
        assert config["base_url"] == "http://10.5.162.35:3000"

    def test_load_config_missing_api_key(self, tmp_path, monkeypatch):
        """Test config loading when API_KEY is not set"""
        nonexistent_file = tmp_path / "nonexistent.env"
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("BASE_URL", raising=False)

        config = load_config(nonexistent_file)

        assert config["api_key"] is None
        assert config["base_url"] == "http://10.5.162.35:3000"


class TestFetchOpenApiSpec:
    """Test fetching OpenAPI specification from live API."""

    @responses.activate
    def test_fetch_openapi_spec_success(self):
        """Test successful OpenAPI spec fetch"""
        base_url = "https://test.example.com"
        api_key = "test-key"
        mock_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/api/test": {"get": {"summary": "Test endpoint"}}},
        }

        responses.add(responses.GET, f"{base_url}/api/settings.getOpenApiDocument", json=mock_spec, status=200)

        result = fetch_openapi_spec(base_url, api_key)

        assert result == mock_spec
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-api-key"] == api_key
        assert responses.calls[0].request.headers["accept"] == "application/json"

    @responses.activate
    def test_fetch_openapi_spec_with_custom_timeout(self):
        """Test OpenAPI spec fetch with custom timeout"""
        base_url = "https://test.example.com"
        api_key = "test-key"
        mock_spec = {"openapi": "3.0.0"}

        responses.add(responses.GET, f"{base_url}/api/settings.getOpenApiDocument", json=mock_spec, status=200)

        result = fetch_openapi_spec(base_url, api_key, timeout=60.0)

        assert result == mock_spec

    @responses.activate
    def test_fetch_openapi_spec_auth_error(self):
        """Test OpenAPI spec fetch with authentication error"""
        base_url = "https://test.example.com"
        api_key = "invalid-key"

        responses.add(responses.GET, f"{base_url}/api/settings.getOpenApiDocument", json={"error": "Unauthorized"}, status=401)

        with pytest.raises(requests.HTTPError) as exc_info:
            fetch_openapi_spec(base_url, api_key)

        assert "401" in str(exc_info.value)

    @responses.activate
    def test_fetch_openapi_spec_network_error(self):
        """Test OpenAPI spec fetch with network error"""
        base_url = "https://test.example.com"
        api_key = "test-key"

        responses.add(
            responses.GET,
            f"{base_url}/api/settings.getOpenApiDocument",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )

        with pytest.raises(requests.exceptions.ConnectionError):
            fetch_openapi_spec(base_url, api_key)

    @responses.activate
    def test_fetch_openapi_spec_invalid_json(self):
        """Test OpenAPI spec fetch with malformed JSON response"""
        base_url = "https://test.example.com"
        api_key = "test-key"

        responses.add(responses.GET, f"{base_url}/api/settings.getOpenApiDocument", body="not valid json", status=200)

        with pytest.raises(json.JSONDecodeError):
            fetch_openapi_spec(base_url, api_key)


class TestLoadOpenApiFromFile:
    """Test loading OpenAPI specification from local files."""

    def test_load_openapi_from_file_success(self, tmp_path):
        """Test successful loading from file"""
        spec_file = tmp_path / "openapi-spec.json"
        mock_spec = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}
        spec_file.write_text(json.dumps(mock_spec))

        result = load_openapi_from_file(spec_file)

        assert result == mock_spec

    def test_load_openapi_from_file_with_paths(self, tmp_path):
        """Test loading file with multiple endpoints"""
        spec_file = tmp_path / "openapi-spec.json"
        mock_spec = {
            "openapi": "3.0.0",
            "paths": {
                "/api/project.all": {"get": {"summary": "List projects"}},
                "/api/project.create": {"post": {"summary": "Create project"}},
            },
        }
        spec_file.write_text(json.dumps(mock_spec))

        result = load_openapi_from_file(spec_file)

        assert result == mock_spec
        assert len(result["paths"]) == 2

    def test_load_openapi_from_file_not_found(self, tmp_path):
        """Test loading from non-existent file"""
        spec_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_openapi_from_file(spec_file)

    def test_load_openapi_from_file_invalid_json(self, tmp_path):
        """Test loading file with invalid JSON"""
        spec_file = tmp_path / "invalid.json"
        spec_file.write_text("not valid json {")

        with pytest.raises(json.JSONDecodeError):
            load_openapi_from_file(spec_file)


class TestExtractEndpoints:
    """Test endpoint extraction from OpenAPI specifications."""

    def test_extract_endpoints_with_multiple_methods(self):
        """Test extracting endpoints with various HTTP methods"""
        openapi_spec = {
            "paths": {
                "/api/project.all": {
                    "get": {
                        "summary": "List all projects",
                        "description": "Returns all projects",
                        "tags": ["project"],
                        "operationId": "projectAll",
                    }
                },
                "/api/project.create": {
                    "post": {
                        "summary": "Create project",
                        "description": "Creates a new project",
                        "tags": ["project"],
                        "operationId": "projectCreate",
                    }
                },
            }
        }

        endpoints = extract_endpoints(openapi_spec)

        assert len(endpoints) == 2
        assert endpoints[0]["path"] == "/api/project.all"
        assert endpoints[0]["method"] == "GET"
        assert endpoints[0]["summary"] == "List all projects"
        assert endpoints[1]["path"] == "/api/project.create"
        assert endpoints[1]["method"] == "POST"

    def test_extract_endpoints_with_all_http_methods(self):
        """Test extraction supports GET, POST, PUT, DELETE, PATCH"""
        openapi_spec = {
            "paths": {
                "/api/resource": {
                    "get": {"summary": "Get resource"},
                    "post": {"summary": "Create resource"},
                    "put": {"summary": "Update resource"},
                    "delete": {"summary": "Delete resource"},
                    "patch": {"summary": "Patch resource"},
                }
            }
        }

        endpoints = extract_endpoints(openapi_spec)

        assert len(endpoints) == 5
        methods = [e["method"] for e in endpoints]
        assert set(methods) == {"GET", "POST", "PUT", "DELETE", "PATCH"}

    def test_extract_endpoints_empty_spec(self):
        """Test extraction from empty OpenAPI spec"""
        openapi_spec = {"paths": {}}

        endpoints = extract_endpoints(openapi_spec)

        assert endpoints == []

    def test_extract_endpoints_missing_optional_fields(self):
        """Test extraction when optional fields are missing"""
        openapi_spec = {"paths": {"/api/minimal": {"get": {}}}}

        endpoints = extract_endpoints(openapi_spec)

        assert len(endpoints) == 1
        assert endpoints[0]["summary"] == ""
        assert endpoints[0]["description"] == ""
        assert endpoints[0]["tags"] == []
        assert endpoints[0]["operationId"] == ""

    def test_extract_endpoints_ignores_non_http_methods(self):
        """Test extraction ignores non-HTTP method keys"""
        openapi_spec = {
            "paths": {
                "/api/resource": {
                    "get": {"summary": "Get resource"},
                    "parameters": [{"name": "id"}],
                    "servers": ["http://example.com"],
                }
            }
        }

        endpoints = extract_endpoints(openapi_spec)

        assert len(endpoints) == 1
        assert endpoints[0]["method"] == "GET"


class TestMakeApiRequest:
    """Test making authenticated API requests."""

    @responses.activate
    def test_make_api_request_get(self):
        """Test GET request with query parameters"""
        endpoint = "https://test.example.com/api/project.all"
        api_key = "test-key"
        mock_response = [{"id": "1", "name": "Project 1"}]

        responses.add(responses.GET, endpoint, json=mock_response, status=200)

        response = make_api_request(endpoint, "GET", api_key, params={"limit": 10})

        assert response.status_code == 200
        assert response.json() == mock_response
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-api-key"] == api_key
        assert "limit=10" in responses.calls[0].request.url

    @responses.activate
    def test_make_api_request_post_with_json(self):
        """Test POST request with JSON body"""
        endpoint = "https://test.example.com/api/project.create"
        api_key = "test-key"
        data = {"name": "New Project", "description": "Test project"}
        mock_response = {"id": "123", "name": "New Project"}

        responses.add(responses.POST, endpoint, json=mock_response, status=201)

        response = make_api_request(endpoint, "POST", api_key, data=data)

        assert response.status_code == 201
        assert response.json() == mock_response
        assert responses.calls[0].request.headers["Content-Type"] == "application/json"
        assert json.loads(responses.calls[0].request.body) == data

    @responses.activate
    def test_make_api_request_delete(self):
        """Test DELETE request"""
        endpoint = "https://test.example.com/api/project.remove"
        api_key = "test-key"
        data = {"projectId": "123"}

        responses.add(responses.DELETE, endpoint, json={"success": True}, status=200)

        response = make_api_request(endpoint, "DELETE", api_key, data=data)

        assert response.status_code == 200
        assert json.loads(responses.calls[0].request.body) == data

    @responses.activate
    def test_make_api_request_put(self):
        """Test PUT request"""
        endpoint = "https://test.example.com/api/project.update"
        api_key = "test-key"
        data = {"projectId": "123", "name": "Updated"}

        responses.add(
            responses.POST,  # make_api_request uses POST for PUT
            endpoint,
            json={"success": True},
            status=200,
        )

        response = make_api_request(endpoint, "PUT", api_key, data=data)

        assert response.status_code == 200

    @responses.activate
    def test_make_api_request_patch(self):
        """Test PATCH request"""
        endpoint = "https://test.example.com/api/project.update"
        api_key = "test-key"
        data = {"projectId": "123", "field": "value"}

        responses.add(
            responses.POST,  # make_api_request uses POST for PATCH
            endpoint,
            json={"success": True},
            status=200,
        )

        response = make_api_request(endpoint, "PATCH", api_key, data=data)

        assert response.status_code == 200

    def test_make_api_request_unsupported_method(self):
        """Test request with unsupported HTTP method"""
        endpoint = "https://test.example.com/api/test"
        api_key = "test-key"

        with pytest.raises(ValueError) as exc_info:
            make_api_request(endpoint, "OPTIONS", api_key)

        assert "Unsupported HTTP method: OPTIONS" in str(exc_info.value)

    @responses.activate
    def test_make_api_request_headers_construction(self):
        """Test proper header construction for API requests"""
        endpoint = "https://test.example.com/api/test"
        api_key = "test-key-abc123"

        responses.add(responses.GET, endpoint, json={}, status=200)

        make_api_request(endpoint, "GET", api_key)

        request_headers = responses.calls[0].request.headers
        assert request_headers["accept"] == "application/json"
        assert request_headers["x-api-key"] == api_key
        assert "Content-Type" not in request_headers  # GET without data

    @responses.activate
    def test_make_api_request_headers_with_json_body(self):
        """Test headers include Content-Type when sending JSON"""
        endpoint = "https://test.example.com/api/test"
        api_key = "test-key"
        data = {"key": "value"}

        responses.add(responses.POST, endpoint, json={}, status=200)

        make_api_request(endpoint, "POST", api_key, data=data)

        request_headers = responses.calls[0].request.headers
        assert request_headers["Content-Type"] == "application/json"
