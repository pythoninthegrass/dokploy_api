# dokploy_api

Programmatically interact with a [Dokploy](https://dokploy.com/) instance via the official [OpenAPI REST commands](https://docs.dokploy.com/docs/api).

## Minimum Requirements

* [uv](https://docs.astral.sh/uv/)

## Recommended Requirements

* [mise](https://mise.jdx.dev/getting-started.html)

## Quickstart

```bash
# install via uv
uv tool install git+https://github.com/pythoninthegrass/dokploy_api

# Configure via environment variables
export API_KEY="your-api-key"
export BASE_URL="https://your-dokploy-instance.com"

# Add to shell profile for persistence (~/.bashrc, ~/.zshrc, etc.)
echo 'export API_KEY="your-api-key"' >> ~/.bashrc
echo 'export BASE_URL="https://your-dokploy-instance.com"' >> ~/.bashrc

# Set variables per-command:
API_KEY="key" BASE_URL="https://your-dokploy-instance.com" dokploy list project
```
