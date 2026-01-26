# Changelog

All notable changes to the n8n MCP Server plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.6.5] - 2025-01-25

### Added
- Software Configuration Management Plan (CM Plan)
- Plugin structure compliance with Claude Code standards

### Changed
- Reorganized project structure per CM Plan specifications

## [0.6.4] - 2025-01-24

### Fixed
- Resolve Pylint issues and update Dependency Track UUID

### Changed
- Updated uv.lock with dev dependencies

## [0.6.3] - 2025-01-24

### Added
- Comprehensive validator tests with 98% coverage

### Fixed
- Resolved Pylint issues

## [0.6.2] - 2025-01-23

### Changed
- Updated uv.lock with dev dependencies

## [0.6.1] - 2025-01-23

### Added
- Comprehensive validator tests with 98% coverage

## [0.6.0] - 2025-01-22

### Added
- Phase 3: Workflow health monitoring tool
- Phase 3: Workflow cloning functionality
- Phase 3: Connection documentation improvements
- Initial marketplace release
- MCP server with 26 tools for n8n workflow management
- Skills: n8n-setup for credential configuration
- Commands: n8n-setup.command for slash command access

## [0.5.0] - 2025-01-21

### Added
- Phase 2: Workflow filtering capabilities
- Phase 2: Workflow validation tool
- Phase 2: Credential documentation

## [0.4.0] - 2025-01-20

### Added
- list_credentials tool for credential management
- Fixed CI pipeline configuration

## [0.3.2] - 2025-01-19

### Fixed
- Added pytest conftest to set N8N_API_KEY for CI tests

## [0.3.1] - 2025-01-19

### Added
- Comprehensive MCP tool and model tests for 96% coverage

## [0.3.0] - 2025-01-18

### Added
- Expanded API coverage from 9 to 26 tools
- Credentials management tools
- Tags management tools

## [0.2.0] - 2025-01-17

### Added
- `/n8n-setup` command for interactive credential configuration
- Jenkins CI/CD pipeline with full quality gates
- n8n-setup skill for guided configuration

## [0.1.1] - 2025-01-16

### Fixed
- Load .env from plugin directory instead of cwd
- Ensures server works when installed as a Claude Code plugin

## [0.1.0] - 2025-01-15

### Added
- Initial release with 9 MCP tools for n8n workflow management
- Python SDK support with mcp[cli]
- N8nClient async HTTP client
- Basic workflow CRUD operations (list, get, create, update, delete)
- Workflow activation/deactivation
- Workflow execution
- Execution history retrieval
- Error handling with @handle_errors decorator
- Type hints and mypy strict mode support
