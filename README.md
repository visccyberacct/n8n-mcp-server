# n8n MCP Server

MCP server providing tools to interact with the n8n workflow automation platform at n8n-backend.homelab.com.

## Features

- 6+ n8n API tools for workflow automation
- Async/await support for all operations
- Secure API key authentication
- Complete type hints and documentation
- Production-ready error handling
- Comprehensive test suite

## Tools

- `list_workflows` - Get all workflows from n8n
- `get_workflow` - Get specific workflow by ID
- `execute_workflow` - Trigger workflow execution
- `get_executions` - List workflow execution history
- `get_execution` - Get specific execution details by ID
- `activate_workflow` - Activate or deactivate a workflow

## Installation

### Prerequisites

- Python 3.11 or higher
- n8n instance with API access (n8n-backend.homelab.com)
- Claude CLI installed (`curl -sSL https://claude.ai/install | bash`)

### Setup

```bash
cd ~/scripts/n8n-mcp-server

# Install dependencies using Poetry
poetry install

# Or using uv
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your n8n API key
# N8N_API_KEY=your_actual_api_key_here
```

## Usage with Claude Code

### Register MCP Server

```bash
claude mcp add n8n-api \
  --env N8N_BASE_URL=https://n8n-backend.homelab.com \
  --env N8N_API_KEY=your_key_here \
  --scope user -- \
  python -m n8n_mcp.server
```

### Example Usage

Once registered, ask Claude Code:

- "List all my n8n workflows"
- "Execute workflow ID abc123"
- "Show me the last 10 workflow executions"
- "Activate workflow xyz789"
- "Get details for execution exec-456"

## Development

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=n8n_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_server.py -v
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type check
mypy src
```

## API Compatibility

Compatible with n8n REST API v1. Tested against n8n version 1.x.

The following n8n API endpoints are supported:

- `GET /api/v1/workflows` - List all workflows
- `GET /api/v1/workflows/{id}` - Get workflow details
- `POST /api/v1/workflows/{id}/execute` - Execute workflow
- `GET /api/v1/executions` - List executions
- `GET /api/v1/executions/{id}` - Get execution details
- `PATCH /api/v1/workflows/{id}` - Update workflow (activate/deactivate)

## Troubleshooting

### Authentication Errors

**Issue**: Getting "Not authorized" or "401 Unauthorized" errors

**Solution**:
- Verify N8N_API_KEY is correct
- Ensure you're using a USER token (not project token)
- Check the API key has proper permissions in n8n

### Connection Errors

**Issue**: Cannot connect to n8n instance

**Solution**:
- Verify N8N_BASE_URL is correct (https://n8n-backend.homelab.com)
- Check network access to n8n instance
- Verify n8n instance is running
- Check firewall rules if applicable

### Tool Not Found

**Issue**: Claude Code says n8n tools are not available

**Solution**:
- Ensure MCP server is registered correctly: `claude mcp list`
- Verify environment variables are set in registration command
- Restart Claude Code after registration
- Check MCP server logs for errors

### Import Errors

**Issue**: Module import errors when running the server

**Solution**:
- Ensure virtual environment is activated
- Run `poetry install` or `uv pip install -e .`
- Verify Python version is 3.11+

## Project Structure

```
n8n-mcp-server/
├── src/n8n_mcp/
│   ├── __init__.py       # Package initialization
│   ├── server.py         # FastMCP server with 6 tools
│   └── client.py         # n8n API client wrapper
├── tests/
│   ├── __init__.py
│   └── test_server.py    # Comprehensive test suite
├── pyproject.toml        # Project dependencies
├── README.md             # This file
└── .env.example          # Example configuration
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please ensure:

- All tests pass (`pytest`)
- Code is formatted (`black src tests`)
- Code is linted (`ruff check src tests`)
- Type hints are provided (`mypy src`)
- Documentation is updated

## Support

For issues, questions, or contributions, please contact the maintainer or open an issue in the project repository.
