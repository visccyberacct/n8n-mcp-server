# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

n8n-mcp-server is an MCP (Model Context Protocol) server providing **30 tools** to interact with the n8n workflow automation platform. Built with FastMCP and Python 3.11+, it enables Claude Code to manage workflows (CRUD, execute, clone, validate), credentials, tags, and executions.

**Key Capabilities:**
- Workflow CRUD + filtering, cloning, health analysis
- Credential and tag management
- Execution history and retry
- Pre-submission workflow validation

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
3. Deploy to staging: Use `/deploy-plugin` command to sync files and version to marketplace

## Development Commands

### Plugin Deployment
```bash
# Deploy to marketplace (syncs files + version)
/deploy-plugin
```
This command:
- Reads current version from pyproject.toml (managed by git hook)
- Copies `src/`, `skills/`, `pyproject.toml`, `README.md`, `.env.example` to marketplace
- Updates marketplace plugin.json with version from development
- Validates deployment
- **Commits and pushes** marketplace changes
- **Creates PR and auto-merges** to marketplace main
- Reports what changed

**Version Management:**
Versions are managed by global git pre-push hook based on Conventional Commits:
- `feat:` → MINOR bump (0.1.2 → 0.2.0)
- `fix:` / `chore:` → PATCH bump (0.1.2 → 0.1.3)
- `BREAKING CHANGE:` → MAJOR bump (0.1.2 → 1.0.0)

**Workflow:**
1. Make changes and commit with Conventional Commits
2. Run `git push` (hook auto-bumps version)
3. Run `/deploy-plugin` (syncs to marketplace)

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=n8n_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_server.py -v

# Run tests with XML coverage (for SonarCloud)
pytest --cov=n8n_mcp --cov-report=xml
```

### Code Quality (run before committing)
```bash
# Format and lint code (line-length: 100)
ruff format src tests
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

### Configuration Command
```bash
# Configure n8n MCP server credentials (after plugin is installed)
/n8n-setup
```
This interactive command:
- Prompts for N8N_BASE_URL and N8N_API_KEY
- Creates/updates `.env` file in the plugin directory
- Validates the credentials by testing connection to n8n
- Provides clear error messages if validation fails

## Architecture

### Core Components

**src/n8n_mcp/server.py** - FastMCP server entry point
- Defines 30 MCP tools decorated with `@mcp.tool()` and `@handle_errors`
- Loads `.env` from plugin directory (not cwd) to support installed plugin usage
- Module-level `N8nClient` instance for efficiency (shared across all tool calls)
- Tool categories: workflows (13), executions (5), credentials (6), tags (5), health (1)

**src/n8n_mcp/client.py** - N8nClient class
- Async context manager (`async with`) wrapping httpx for n8n REST API
- Methods mirror the 30 MCP tools
- SSL verification disabled (`verify_ssl=False`) for homelab environments
- Proper cleanup in `__aexit__` and `close()`
- Internal `_request()` method handles all HTTP errors and returns consistent error dicts

**src/n8n_mcp/utils.py** - Shared utilities
- `@handle_errors` decorator for consistent error handling across all MCP tools
- Catches JSON decode errors and general exceptions
- Returns error dicts in MCP-compatible format

**Architecture Pattern**: FastMCP tools → N8nClient methods → httpx HTTP calls → n8n API

**Key Design Decisions**:
- **Module-level client**: Single `N8nClient` instance shared across all tool invocations prevents connection overhead
- **Two-layer error handling**: Client `_request()` catches HTTP/network errors, `@handle_errors` decorator catches tool-level errors
- **Plugin-directory .env loading**: Ensures environment variables load correctly when installed as plugin vs development use

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
- **Line length**: 100 characters (ruff)
- **Target**: Python 3.12
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
5. Run: `ruff format --check src tests && ruff check src tests && mypy src && pytest`

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

## Project Structure (CM Plan)

```
n8n-mcp-server/
├── .claude-plugin/plugin.json    # Plugin manifest (REQUIRED)
├── config/mcp.json               # Dev MCP config (uses ${CLAUDE_PLUGIN_ROOT})
├── skills/n8n-setup/SKILL.md     # Setup skill
├── commands/                     # Slash commands
├── agents/                       # Subagents (empty)
├── hooks/hooks.json              # Event handlers
├── src/n8n_mcp/                  # MCP server source
├── tests/                        # pytest tests
├── docs/                         # Documentation
├── CHANGELOG.md                  # Version history
├── pyproject.toml                # Build config
└── uv.lock                       # Dependency lockfile
```

See `docs/SOFTWARE-CM-PLAN.md` for complete CM specifications.

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

See `docs/N8N_API_WORKFLOW_CREATION_REPORT.md` for detailed API research.

## CI/CD Pipeline

The project uses a **Jenkins Multibranch Pipeline** (`Jenkinsfile`) that runs in a Docker container (Ubuntu 24.04).

### Multibranch Pipeline Configuration

**Jenkins Job**: `n8n-plugin` (https://jenkins.homelab.com/job/n8n-plugin/)

**How it works**:
- Automatically detects branches in the Git repository
- Creates separate pipeline jobs for each branch
- Scans for new branches periodically (or on webhook trigger)
- Builds feature branches, main branch, and PRs independently

**Branch Workflow**:
1. Create feature branch: `git switch -c feature/my-feature`
2. Commit and push: `git push -u origin feature/my-feature`
3. Jenkins auto-detects the new branch (may take 10-30 seconds)
4. Pipeline runs automatically for the feature branch
5. Monitor build status using Jenkins MCP tools

**IMPORTANT**: When pushing a new branch, give Jenkins time to scan and detect it before attempting to trigger builds manually. The multibranch pipeline will automatically start a build once the branch is discovered.

### Quality Gates

All stages must pass for build to succeed:
- **Code formatting**: Ruff format (line-length: 100)
- **Linting**: Ruff check (0 critical errors allowed)
- **Type checking**: mypy (strict mode)
- **Testing**: pytest with 80% minimum coverage requirement
- **Security**: Semgrep SAST + pip-audit (no critical/high vulnerabilities)
- **SBOM**: CycloneDX SBOM generation and upload to Dependency-Track
- **SonarCloud**: Code quality analysis with quality gate enforcement

### Pipeline Stages

1. **Setup Environment** - Install Python 3.12, uv, and system dependencies
2. **Install Dependencies** - Use uv to install project and dev dependencies
3. **Code Quality Checks** - Ruff format/lint, mypy (all must pass)
4. **Security Scan** - Semgrep SAST + pip-audit for vulnerabilities
5. **Run Tests** - pytest with coverage reporting (XML for SonarCloud)
6. **Generate SBOM** - CycloneDX BOM file creation
7. **Upload to Dependency-Track** - SBOM upload for dependency monitoring
8. **SonarCloud Analysis** - Code quality scan and quality gate check

### Monitoring Builds with Jenkins MCP

```python
# List all jobs (including branch pipelines)
list_jobs = mcp__plugin_jenkins-ci_jenkins__jenkins_list_jobs({
    "folder": null,
    "limit": 50,
    "response_format": "markdown"
})

# Get specific job info
job_info = mcp__plugin_jenkins-ci_jenkins__jenkins_get_job_info({
    "job_name": "n8n-plugin",
    "response_format": "markdown"
})

# Get build queue status
queue = mcp__plugin_jenkins-ci_jenkins__jenkins_get_queue_info({
    "response_format": "markdown"
})

# Get build console output
console = mcp__plugin_jenkins-ci_jenkins__jenkins_get_build_console({
    "job_name": "n8n-plugin/feature/my-feature",
    "build_number": 1,
    "response_format": "text"
})
```

### Running Locally (Simulating CI)

```bash
# Full quality check sequence (same as Jenkins)
ruff format --check src tests && \
ruff check src tests && \
mypy src && \
pytest --cov=n8n_mcp --cov-report=xml --cov-report=term-missing
```

### Environment Variables Required (Jenkins Credentials)

- `SONARCLOUD_TOKEN` - SonarCloud authentication
- `DEPENDENCY_TRACK_URL` - Dependency-Track server URL (https://dtrack.homelab.com/api)
- `DEPENDENCY_TRACK_API_KEY` - Dependency-Track API key
