# Software Configuration Management Plan
# n8n MCP Server Plugin

| Document Information | |
|---------------------|---|
| Version | 1.0 |
| Status | Active |
| Effective Date | January 2026 |
| Review Cycle | Annual |
| Project Type | Claude Code Plugin with MCP Server |
| Standards Reference | IEEE 828-2012, ISO 10007:2017, Model Context Protocol |

---

## 1. Introduction

### 1.1 Purpose

This Software Configuration Management Plan (SCMP) establishes procedures for managing configuration of the n8n MCP Server plugin for Claude Code. It defines:

- **Configuration Identification** — Plugin components under version control
- **Configuration Control** — How changes flow from development to marketplace
- **Configuration Status Accounting** — How plugin versions are tracked
- **Configuration Verification** — Automated quality gates for releases

This plan adapts IEEE 828-2012 and ISO 10007:2017 principles for Claude Code plugin development with MCP server integration.

### 1.2 Scope

This plan applies to:

- Plugin manifest and component files
- MCP server implementation
- Skills, commands, agents, and hooks
- Build and dependency configurations
- CI/CD pipeline definitions
- Documentation and examples
- Software Bill of Materials (SBOM)

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Agent** | Specialized subagent configuration that Claude invokes for specific task types |
| **Baseline** | A tagged release serving as a reference point for further development |
| **CI** | Configuration Item — a file or artifact under version control |
| **CM** | Configuration Management |
| **Command** | Simple Markdown file that creates a slash command |
| **Hook** | Event handler that runs on specific Claude Code events |
| **Marketplace** | Repository containing installable Claude Code plugins |
| **MCP** | Model Context Protocol — standard for LLM tool integration |
| **Plugin** | Packaged extension for Claude Code with manifest and components |
| **SBOM** | Software Bill of Materials |
| **Skill** | Primary extensibility mechanism — directory with SKILL.md and supporting files |
| **SLSA** | Supply-chain Levels for Software Artifacts |

### 1.4 References

| Standard | Relevance |
|----------|-----------|
| IEEE 828-2012 | CM framework |
| ISO 10007:2017 | CM guidelines |
| PEP 8 | Python style guide |
| PEP 440 | Python version identification |
| PEP 621 | Project metadata (pyproject.toml) |
| Semantic Versioning 2.0.0 | Version numbering |
| Model Context Protocol | MCP specification |

---

## 2. Roles and Tools

### 2.1 Roles

| Role | Responsibility |
|------|----------------|
| **Developer** (you) | All development, review, release decisions |
| **CI Pipeline** | Automated quality gates, security scanning |
| **Pre-commit/Pre-push Hooks** | Local enforcement of standards, version bumping |

### 2.2 Tools

| Function | Tool | Purpose |
|----------|------|---------|
| Source Control | Git / GitHub | Version control, history, collaboration |
| CI/CD | Jenkins | Automated testing, security scanning, releases |
| Dependency Management | uv | Fast, lockfile-based Python dependencies |
| Linting/Formatting | Ruff | Unified linter and formatter |
| Type Checking | mypy | Static type verification |
| Testing | pytest | Test execution and coverage |
| SAST | Bandit, Semgrep | Security vulnerability detection |
| Dependency Scanning | pip-audit, Trivy | CVE detection |
| SBOM Generation | CycloneDX | Software bill of materials |
| Code Quality | SonarCloud | Coverage, duplication, code smells |
| Plugin Validation | Claude Code CLI | Plugin structure validation |

---

## 3. Configuration Identification

### 3.1 Configuration Items

| Category | Items | Location |
|----------|-------|----------|
| **Plugin Manifest** | plugin.json | `.claude-plugin/` |
| **MCP Configuration** | mcp.json | `config/` (dev), `.mcp.json` (deployed) |
| **Skills** | SKILL.md + supporting files | `skills/<name>/` |
| **Commands** | Command Markdown files | `commands/`, `.claude/commands/` |
| **Agents** | Agent Markdown files | `agents/` |
| **Hooks** | hooks.json + scripts | `hooks/` |
| **MCP Server Source** | Python modules | `src/n8n_mcp/` |
| **Tests** | Test files, fixtures | `tests/` |
| **Build Config** | pyproject.toml, uv.lock | Root |
| **Pipeline** | Jenkinsfile | Root |
| **Documentation** | README, CHANGELOG, docs | Root, `docs/` |

### 3.2 Directory Structure

```
n8n-mcp-server/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (REQUIRED)
│
├── .claude/
│   └── commands/                # Project-specific commands
│       └── deploy-plugin.md
│
├── skills/                      # Model-invokable capabilities
│   └── n8n-setup/
│       └── SKILL.md
│
├── commands/                    # Slash command shortcuts
│   └── n8n-setup.command.md
│
├── agents/                      # Specialized subagents
│
├── hooks/                       # Event handlers
│   ├── hooks.json
│   └── scripts/
│
├── config/                      # Configuration files
│   └── mcp.json                 # MCP server config template
│
├── src/
│   └── n8n_mcp/
│       ├── __init__.py
│       ├── server.py            # MCP server entry point
│       ├── client.py            # N8n API client
│       ├── models.py            # Pydantic models
│       ├── utils.py             # Utilities
│       └── validator.py         # Workflow validation
│
├── tests/
│   ├── conftest.py
│   ├── test_server.py
│   └── test_validator.py
│
├── docs/
│   ├── SOFTWARE-CM-PLAN.md      # This document
│   └── ...
│
├── pyproject.toml               # Python project configuration
├── uv.lock                      # Dependency lockfile
├── Jenkinsfile                  # CI/CD pipeline
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .env.example
└── .gitignore
```

### 3.3 Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Plugin name | lowercase, hyphens | `n8n-api` |
| Skills | lowercase, hyphens (directory) | `skills/n8n-setup/` |
| Commands | lowercase, hyphens | `commands/deploy.md` |
| Python packages | lowercase, underscores | `n8n_mcp` |
| Python modules | lowercase, underscores | `server.py` |
| Classes | PascalCase | `N8nClient` |
| Functions | lowercase, underscores | `list_workflows()` |
| Constants | UPPERCASE | `MAX_CHUNK_SIZE` |
| Tests | `test_` prefix | `test_server.py` |

### 3.4 Version Identification

#### Semantic Versioning

All releases use Semantic Versioning 2.0.0:

```
MAJOR.MINOR.PATCH[-PRERELEASE]
```

| Component | Increment When |
|-----------|----------------|
| **MAJOR** | Breaking changes to MCP tools or plugin API |
| **MINOR** | New skills, commands, agents, or MCP tools |
| **PATCH** | Bug fixes, documentation updates |

#### Version Sources

Version MUST be consistent across:

| File | Field |
|------|-------|
| `plugin.json` | `version` |
| `pyproject.toml` | `version` |
| `CHANGELOG.md` | Release header |
| Git tag | Tag name |

#### Version Bumping (Global Pre-Push Hook)

Version is managed by git pre-push hook based on Conventional Commits:
- `feat:` → MINOR bump (0.1.2 → 0.2.0)
- `fix:` / `chore:` → PATCH bump (0.1.2 → 0.1.3)
- `BREAKING CHANGE:` → MAJOR bump (0.1.2 → 1.0.0)

---

## 4. Configuration Control

### 4.1 Repository Structure

This plugin uses a **two-repository model**:

| Repository | Purpose | Location |
|------------|---------|----------|
| **Development** | Active development, testing | `/home/kviscount.adm@homelab.com/projects/n8n-mcp-server/` |
| **Marketplace** | Distribution, installation | `/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api/` |

### 4.2 Branch Strategy

```
feature/* ──┐
bugfix/*  ──┼──► dev ──► main ──► marketplace
hotfix/*  ──┘
```

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Production-ready releases | Protected, requires CI pass |
| `dev` | Integration/staging | Protected, requires CI pass |
| `feature/*` | New features | Developer branch |

### 4.3 Commit Message Format

Use Conventional Commits:

```
<type>(<scope>): <description>
```

| Type | Description | Version Impact |
|------|-------------|----------------|
| `feat` | New feature (skill, command, MCP tool) | MINOR bump |
| `fix` | Bug fix | PATCH bump |
| `feat!` or `BREAKING CHANGE` | Breaking change | MAJOR bump |
| `docs` | Documentation | None |
| `refactor` | Code restructure | None |
| `test` | Test changes | None |
| `chore` | Maintenance | None |

**Scope Examples:**
- `skill` — Changes to skills
- `command` — Changes to commands
- `mcp` — Changes to MCP server
- `config` — Configuration changes

### 4.4 Marketplace Deployment

Deployment is a **one-way sync** from development `main` to marketplace:

```
Development Repository          Marketplace Repository
        │                               │
      main ────────────────────────► main
        │         /deploy-plugin        │
```

The `/deploy-plugin` command:
1. Switches to development `main` branch
2. Reads current version from `pyproject.toml`
3. Copies source files to marketplace plugin directory
4. Updates `plugin.json` version in marketplace
5. Updates `marketplace.json` registry
6. Validates deployment
7. Commits and pushes to marketplace
8. Creates PR and auto-merges

---

## 5. Configuration Status Accounting

### 5.1 Status Tracking

| Information | Source | How to Access |
|-------------|--------|---------------|
| Plugin version | `plugin.json` | `jq .version .claude-plugin/plugin.json` |
| Change history | Git log | `git log --oneline` |
| Release history | Git tags | `git tag -l` |
| Dependency versions | `uv.lock` | `uv tree` |
| CI status | Jenkins | Dashboard |
| Marketplace version | `marketplace.json` | Check registry |

### 5.2 Release Documentation

| Artifact | Description | Generated By |
|----------|-------------|--------------|
| **CHANGELOG entry** | Human-readable changes | Manual |
| **Git tag** | Version marker | Manual |
| **SBOM** | Dependency manifest | CI (CycloneDX) |
| **Test report** | Test results + coverage | CI (pytest) |
| **Security report** | Vulnerability findings | CI |

---

## 6. Configuration Verification

### 6.1 Automated Verification

#### Pre-commit Hooks (Local)

| Hook | Purpose | Blocking |
|------|---------|----------|
| ruff format | Code formatting | Yes |
| ruff check | Linting | Yes |
| mypy | Type checking | Yes |
| JSON validation | Validate plugin.json, mcp.json | Yes |

#### CI Pipeline Stages

| Stage | Checks | Failure Action |
|-------|--------|----------------|
| **Quality** | ruff format, ruff check, mypy | Block merge |
| **Validation** | Plugin structure validation | Block merge |
| **Test** | pytest with coverage | Block merge if <80% |
| **Security** | Bandit, Semgrep, pip-audit, Trivy | Block on high/critical |
| **SBOM** | CycloneDX generation | Alert on failure |

### 6.2 Quality Gates

| Gate | Threshold | Enforcement |
|------|-----------|-------------|
| Lint errors | 0 | CI blocks merge |
| Type errors | 0 | CI blocks merge |
| Test coverage | ≥80% per module | CI blocks merge |
| Critical CVEs | 0 | CI blocks merge |
| High CVEs | 0 (or documented exception) | CI blocks merge |
| Plugin validation | Pass | CI blocks merge |

### 6.3 Plugin-Specific Validation

| Validation | Requirement |
|------------|-------------|
| `plugin.json` syntax | Valid JSON |
| `plugin.json` schema | Required fields present |
| `config/mcp.json` syntax | Valid JSON if present |
| `.mcp.json` absent | Not in root during development |
| Skill structure | SKILL.md exists in each skill dir |
| MCP server | Server module imports without error |

---

## 7. Plugin Component Standards

### 7.1 Skill Development Standards

#### Quick Reference

```yaml
---
name: skill-name
description: What the skill does. Use when [trigger conditions].
disable-model-invocation: false
user-invocable: true
argument-hint: "[argument]"
allowed-tools: Read, Grep, Glob
model: sonnet
---

# Skill Title

## Overview
Brief description of what this skill does.

## Workflows
1. Step one
2. Step two
```

#### Key Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name (uses directory name if omitted) |
| `description` | Recommended | What skill does and when to use it |
| `argument-hint` | No | Hint for autocomplete |
| `disable-model-invocation` | No | `true` = user-only invocation |
| `user-invocable` | No | `false` = Claude-only invocation |
| `allowed-tools` | No | Tools Claude can use without permission |

#### Best Practices

| Practice | Rationale |
|----------|-----------|
| Keep SKILL.md under 500 lines | Performance |
| Write specific descriptions | Claude knows when to invoke |
| Use supporting files for details | Keeps main file focused |
| Set `allowed-tools` appropriately | Security |

### 7.2 Command Development Standards

Commands are single Markdown files:

```yaml
---
description: Command description
---

# Command Title

## Process

### 1. First Step
```bash
command here
```
```

### 7.3 Hook Development Standards

#### hooks.json Structure

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

#### Hook Events

| Event | When | Use For |
|-------|------|---------|
| `PreToolUse` | Before tool execution | Validation, permission override |
| `PostToolUse` | After tool succeeds | Auto-formatting, auditing |
| `UserPromptSubmit` | User submits prompt | Validation, context injection |
| `Stop` | Claude finishes | Decide if should continue |
| `SessionStart` | Session begins | Environment setup |
| `SessionEnd` | Session ends | Cleanup |

---

## 8. MCP Server Configuration

### 8.1 Configuration Structure

#### Development Config (config/mcp.json)

Store MCP configuration as `config/mcp.json` during development:

```json
{
  "mcpServers": {
    "n8n-api": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "n8n-mcp-server"],
      "env": {
        "N8N_BASE_URL": "${N8N_BASE_URL}",
        "N8N_API_KEY": "${N8N_API_KEY}"
      }
    }
  }
}
```

**Why not `.mcp.json` in root?** Claude Code auto-discovers `.mcp.json` files and attempts to connect. During development, `${CLAUDE_PLUGIN_ROOT}` isn't set, causing warnings.

#### .gitignore Entry

```gitignore
# MCP config is auto-generated during build
.mcp.json
```

### 8.2 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `N8N_BASE_URL` | n8n instance URL | Yes |
| `N8N_API_KEY` | n8n API token | Yes |
| `CLAUDE_PLUGIN_ROOT` | Plugin directory (auto-set) | Auto |

### 8.3 MCP Server Best Practices

| Practice | Rationale |
|----------|-----------|
| Store config as `config/mcp.json` | Avoid auto-discovery during development |
| Use `${CLAUDE_PLUGIN_ROOT}` for paths | Portability |
| Document required environment variables | User experience |
| Keep startup fast | User experience |
| Use lazy loading for heavy components | Performance |
| Implement health checks | Diagnostics |

---

## 9. Software Supply Chain Security

### 9.1 SBOM Requirements

| Requirement | Specification |
|-------------|---------------|
| Format | CycloneDX 1.5+ (JSON) |
| Generation | Automated in CI pipeline |
| Contents | All direct and transitive dependencies |
| Source | Generated from lockfile |

### 9.2 Dependency Management

| Policy | Requirement |
|--------|-------------|
| Lockfile | All dependencies pinned in `uv.lock` |
| Updates | Security patches within 72 hours |
| Regular updates | Monthly dependency refresh |
| License | Only permissive licenses (MIT, Apache 2.0, BSD) |
| Source | PyPI only (trusted registry) |

### 9.3 Plugin Distribution Security

| Control | Purpose |
|---------|---------|
| Signed commits | Verify commit authenticity |
| Protected branches | Prevent unauthorized changes |
| Marketplace validation | Verify plugin structure |
| Version pinning | Reproducible installations |
| SBOM tracking | Dependency visibility |

---

## 10. CI/CD Pipeline

### 10.1 Pipeline Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      Jenkins Pipeline                        │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   Quality   │  Validate   │    Test     │     Security      │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ • ruff fmt  │ • plugin    │ • pytest    │ • Bandit          │
│ • ruff chk  │   structure │ • coverage  │ • Semgrep         │
│ • mypy      │ • JSON      │   report    │ • pip-audit       │
│             │   syntax    │             │ • Trivy           │
└─────────────┴─────────────┴─────────────┴───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Release                               │
├─────────────────────────────────────────────────────────────┤
│ • Generate SBOM • Upload to Dependency-Track • SonarCloud   │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Failure Handling

| Failure Type | Action |
|--------------|--------|
| Lint/format failure | Fix code, push again |
| Plugin validation failure | Fix structure, push again |
| Test failure | Fix test or code, push again |
| Coverage below threshold | Add tests, push again |
| Security finding (critical/high) | Fix or document exception |

---

## 11. Metrics

### 11.1 Key Metrics

| Metric | Target | Where to Check |
|--------|--------|----------------|
| Test coverage | ≥80% | SonarCloud / CI report |
| Open security findings | 0 critical/high | DefectDojo |
| Dependency freshness | <30 days stale | `uv outdated` |
| Build success rate | >95% | Jenkins |
| Plugin validation | 100% pass | CI logs |

---

## 12. Exceptions and Waivers

### 12.1 Documenting Exceptions

Document exceptions in:

1. **Issue tracker**: Create an issue explaining the exception
2. **Code comment**: If suppressing a warning (rarely), explain why
3. **This document**: For project-wide exceptions

### 12.2 Exception Format

```markdown
## Exception: [Brief description]

- **Finding**: [What tool reported]
- **Reason**: [Why it can't be fixed now]
- **Risk**: [Impact assessment]
- **Mitigation**: [What's being done instead]
- **Review date**: [When to revisit]
```

---

## Appendix A: Quick Reference

### Common Commands

```bash
# Development
uv sync                      # Install dependencies
uv run pytest               # Run tests
uv run ruff check --fix .   # Lint and auto-fix
uv run ruff format .        # Format code
uv run mypy src/            # Type check

# Plugin Testing
claude --plugin-dir .       # Load plugin locally
claude --debug --plugin-dir .  # Debug mode

# Validation
python -m json.tool .claude-plugin/plugin.json  # Validate JSON
python -m json.tool config/mcp.json             # Validate MCP config

# Release
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Deploy to Marketplace
/deploy-plugin
```

### Development Workflow

```bash
# 1. Make changes in development
vim src/n8n_mcp/server.py

# 2. Commit with Conventional Commit
git add .
git commit -m "feat(mcp): add new capability"

# 3. Push (git hook auto-bumps version)
git push
# Hook outputs: "pyproject.toml: 0.1.2 -> 0.2.0 (minor)"

# 4. Deploy to marketplace
/deploy-plugin
```

---

## Appendix B: Plugin Checklist

### Before First Release

- [ ] `plugin.json` has all required fields
- [ ] All skills have SKILL.md with proper frontmatter
- [ ] MCP server starts without error
- [ ] All JSON files are valid
- [ ] All referenced files exist
- [ ] README.md documents installation and usage
- [ ] CHANGELOG.md has initial entry
- [ ] Tests pass with coverage threshold
- [ ] Security scans show no critical/high findings
- [ ] Plugin validates with `claude --plugin-dir .`

### Before Each Release

- [ ] Version bumped consistently (plugin.json, pyproject.toml)
- [ ] CHANGELOG.md updated
- [ ] All tests pass
- [ ] Security scans clean
- [ ] Documentation updated
- [ ] Plugin validates locally

### After Marketplace Deployment

- [ ] Plugin appears in marketplace
- [ ] Version matches development
- [ ] Installation succeeds
- [ ] Skills/commands work as expected

---

## Appendix C: Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 2026 | Initial release - combined Python, Plugin, and MCP templates |

---

## Appendix D: References

- [IEEE 828-2012](https://standards.ieee.org/ieee/828/5367/) — CM Standard
- [ISO 10007:2017](https://www.iso.org/standard/70400.html) — CM Guidelines
- [Semantic Versioning](https://semver.org/) — Version numbering
- [Conventional Commits](https://www.conventionalcommits.org/) — Commit format
- [CycloneDX](https://cyclonedx.org/) — SBOM standard
- [Model Context Protocol](https://modelcontextprotocol.io/) — MCP specification
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code) — Official docs

---

*This plan combines Python project standards, Claude Code plugin conventions, and MCP server configuration management into a unified document for the n8n MCP Server plugin.*
