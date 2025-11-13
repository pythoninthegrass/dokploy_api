# dokploy_api

Programmatically interact with a [Dokploy](https://dokploy.com/) instance via the official [OpenAPI REST commands](https://docs.dokploy.com/docs/api).

## Minimum Requirements

* [uv](https://docs.astral.sh/uv/)

## Recommended Requirements

* [mise](https://mise.jdx.dev/getting-started.html)

## Installation

```bash
uv tool install git+https://github.com/pythoninthegrass/dokploy_api
```

## Configuration

The `dokploy` command needs your Dokploy API credentials. Configure using one of these methods:

### Option 1: Environment Variables (Recommended)

Set persistent environment variables in your shell profile:

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export API_KEY="your-dokploy-api-key"
export BASE_URL="https://your-dokploy-instance.com"
```

Reload your shell or run:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### Option 2: Per-Command Environment Variables

Set variables for a single command:

```bash
API_KEY="your-key" BASE_URL="https://dokploy.example.com" dokploy list project
```

### Option 3: `.env` File (Project-Specific)

Create a `.env` file in your working directory:

```bash
cat > .env << 'EOF'
API_KEY=your-dokploy-api-key
BASE_URL=https://your-dokploy-instance.com
EOF
```

Then run `dokploy` from that directory:
```bash
cd /path/to/your/project
dokploy list project
```

### Configuration Priority

Settings are loaded in this order (first found wins):

1. `.env` file in current working directory
2. Environment variables
3. Command-line flags (`--api-key`, `--url`) - override all others

## Usage

List all projects:
```bash
dokploy list project
```

Get application details:
```bash
dokploy get application <app-id>
```

Trigger deployment:
```bash
dokploy deploy --app-id <app-id>
```

View all available commands:
```bash
dokploy --help
```

## Tool Management

### Update to Latest Version

```bash
uv tool upgrade dokploy-api
```

### Uninstall

```bash
uv tool uninstall dokploy-api
```

### Check Installation

```bash
uv tool list
```
