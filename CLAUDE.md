# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

n8n-mcp-server is an MCP (Model Context Protocol) server providing 9 tools to interact with the n8n workflow automation platform at n8n.homelab.com. Built with FastMCP and Python 3.11+, it enables Claude Code to manage workflows (CRUD operations), execute workflows, and monitor execution history.

## **CRITICAL: Development vs Staging**

**THIS IS THE DEVELOPMENT DIRECTORY** - `/home/kviscount.adm@homelab.com/projects/n8n-mcp-server/`

**ALWAYS create/modify source files HERE**, including:
- Source code in `src/`
- Skills in `skills/`
- Commands in `commands/` (if created)
- Tests in `tests/`
- Documentation files

**NEVER create files directly in the staging directory:**
- Staging location: `/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api/`
- Files are COPIED to staging during build/deploy
- Staging is read-only from development perspective

**Workflow:**
1. Create/modify files in THIS directory (development)
2. Test and validate changes here
3. Copy to staging directory for deployment (manual or via build process)

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=n8n_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_server.py -v
```

### Code Quality (run before committing)
```bash
# Format code (line-length: 100)
black src tests

# Lint code
ruff check src tests

# Type check (strict mode)
mypy src
```

### Development Setup
```bash
# Create virtual environment and install
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your N8N_API_KEY
```

### Running the Server
```bash
# Direct execution
python -m n8n_mcp.server

# Register with Claude Code
claude mcp add n8n-api \
  --env N8N_BASE_URL=https://n8n.homelab.com \
  --env N8N_API_KEY=your_key_here \
  --scope user -- \
  python -m n8n_mcp.server
```

## Architecture

### Core Components

**src/n8n_mcp/server.py** - FastMCP server entry point
- Defines 9 MCP tools decorated with `@mcp.tool()` and `@handle_errors`
- Loads `.env` from plugin directory (not cwd) to support installed plugin usage
- Module-level `N8nClient` instance for efficiency
- Tools: list_workflows, get_workflow, create_workflow, update_workflow, delete_workflow, activate_workflow, execute_workflow, get_executions, get_execution

**src/n8n_mcp/client.py** - N8nClient class
- Async context manager (`async with`) wrapping httpx for n8n REST API
- Methods mirror the 9 MCP tools
- SSL verification disabled (`verify_ssl=False`) for homelab environments
- Proper cleanup in `__aexit__` and `close()`

**Architecture Pattern**: FastMCP tools → N8nClient methods → httpx HTTP calls → n8n API

### Environment Variables
- `N8N_BASE_URL`: n8n instance URL (default: https://n8n.homelab.com)
- `N8N_API_KEY`: Required user API token from n8n

**CRITICAL**: Environment is loaded from plugin directory (`_plugin_dir = Path(__file__).resolve().parent.parent.parent`), not current working directory, to support installed plugin usage.

## Code Style

### Type Hints (Strict Mode)
```python
# All functions must have complete type hints
async def list_workflows() -> dict[str, Any]:
    """List all workflows from n8n.

    Returns:
        Dictionary containing workflows data from n8n API
    """
```

### Formatting Standards
- **Line length**: 100 characters (black + ruff)
- **Target**: Python 3.11
- **Imports**: Sorted by ruff
- **Naming**: snake_case (functions), PascalCase (classes), UPPER_SNAKE_CASE (constants)

### Special Rules
- `src/n8n_mcp/models.py`: mixedCase allowed for n8n API field names (ruff ignore N815)
- All MCP tools use `@handle_errors` decorator for consistent error handling
- Async/await required for all API operations

## Testing Requirements

- New features require tests in `tests/test_server.py`
- Use pytest with async support (`asyncio_mode = "auto"`)
- Maintain or improve coverage (currently comprehensive)
- Mock n8n API responses using pytest fixtures

## Common Patterns

### Adding a New MCP Tool
1. Add method to `N8nClient` class in `client.py`
2. Add tool function in `server.py` with `@mcp.tool()` and `@handle_errors`
3. Add comprehensive tests in `tests/test_server.py`
4. Update README.md tool list
5. Run: `black src tests && ruff check src tests && mypy src && pytest`

### Environment Loading
The `.env` file is loaded from the plugin directory, not cwd:
```python
_plugin_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_plugin_dir / ".env")
```
This ensures the server works when installed as a Claude Code plugin.

### Error Handling
Use the `@handle_errors` decorator on all MCP tools:
```python
@mcp.tool()
@handle_errors
async def my_tool() -> dict[str, Any]:
    """Tool description."""
    return await client.my_method()
```

## Plugin Staging Directory

**Location**: `/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api/`

**IMPORTANT**: This is the DEPLOYMENT/STAGING directory. Files are copied here from the development directory.

The staging directory contains:
- `.claude-plugin/plugin.json` - Plugin metadata
- `.mcp.json` - MCP server configuration
- `src/` - Source code (copied from development)
- `skills/` - Skills (copied from development)
- `commands/` - Commands (copied from development)

**To update staging:**
1. Make changes in THIS development directory first
2. Copy updated files to staging directory
3. Test the plugin from staging

**NEVER:**
- Create new files directly in staging
- Edit files in staging without updating development first
- Use staging as the source of truth

## Git Workflow

**CRITICAL**: Per user's global CLAUDE.md:
- Use `git switch` (NOT `git checkout`) for branch operations
- NEVER `git push` to main
- Source control must be maintained in project directory

## n8n API Integration

Compatible with n8n REST API v1. Supported endpoints:
- GET/POST/PUT/DELETE/PATCH `/api/v1/workflows`
- POST `/api/v1/workflows/{id}/execute`
- GET `/api/v1/executions`

See `N8N_API_WORKFLOW_CREATION_REPORT.md` for detailed API research.
