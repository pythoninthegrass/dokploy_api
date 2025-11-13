import json
import requests
from pathlib import Path
from typing import Any, Optional


def load_config(env_file: Path | None = None) -> dict[str, str | None]:
    """Load configuration from .env file or environment.

    Search order for .env file:
    1. Current working directory (.env)
    2. Parent directory of this module (for local development)
    3. Fall back to environment variables

    Args:
        env_file: Path to .env file. If None, searches automatically.

    Returns:
        Dict with 'api_key' and 'base_url' keys.
    """
    import os
    from decouple import Config, RepositoryEnv

    if env_file is None:
        # Check current working directory first (for tool installations)
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            env_file = cwd_env
        else:
            # Fall back to parent directory (for local development)
            env_file = Path(__file__).parent.parent / ".env"

    if env_file.exists():
        config = Config(RepositoryEnv(str(env_file)))
        return {
            "api_key": config.get("API_KEY", default=None),
            "base_url": config.get("BASE_URL", default="http://10.5.162.35:3000"),
        }
    else:
        # Fall back to environment variables
        return {
            "api_key": os.environ.get("API_KEY"),
            "base_url": os.environ.get("BASE_URL", "http://10.5.162.35:3000"),
        }


def fetch_openapi_spec(base_url: str, api_key: str, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch OpenAPI specification from Dokploy instance.

    Args:
        base_url: Dokploy base URL
        api_key: API authentication key
        timeout: Request timeout in seconds

    Returns:
        OpenAPI specification as dict

    Raises:
        requests.HTTPError: If API request fails
        requests.RequestException: If network error occurs
        json.JSONDecodeError: If response is not valid JSON
    """
    url = f"{base_url}/api/settings.getOpenApiDocument"
    headers = {"accept": "application/json", "x-api-key": api_key}

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def load_openapi_from_file(spec_path: Path | None = None) -> dict[str, Any]:
    """Load OpenAPI specification from local JSON file.

    Args:
        spec_path: Path to openapi-spec.json. If None, uses docs/openapi-spec.json

    Returns:
        OpenAPI specification as dict
    """
    if spec_path is None:
        spec_path = Path(__file__).parent.parent / "docs" / "openapi-spec.json"

    with open(spec_path) as f:
        return json.load(f)


def extract_endpoints(openapi_spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract endpoints from OpenAPI specification.

    Args:
        openapi_spec: OpenAPI specification dict

    Returns:
        List of endpoint dicts with path, method, summary, etc.
    """
    endpoints = []
    paths = openapi_spec.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "tags": details.get("tags", []),
                    "operationId": details.get("operationId", ""),
                }
                endpoints.append(endpoint)

    return endpoints


def make_api_request(
    endpoint: str, method: str, api_key: str, data: dict | None = None, params: dict | None = None
) -> requests.Response:
    """Make authenticated API request to Dokploy.

    Args:
        endpoint: Full endpoint URL
        method: HTTP method (GET, POST, etc.)
        api_key: API authentication key
        data: JSON body for POST/PUT requests
        params: Query parameters for GET requests

    Returns:
        Response object
    """
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    if data is not None:
        headers["Content-Type"] = "application/json"

    if method.upper() == "GET":
        return requests.get(endpoint, headers=headers, params=params)
    elif method.upper() in ["POST", "PUT", "PATCH"]:
        return requests.post(endpoint, headers=headers, json=data)
    elif method.upper() == "DELETE":
        return requests.delete(endpoint, headers=headers, json=data)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
