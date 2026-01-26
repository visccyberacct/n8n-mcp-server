# Agents

This directory contains specialized subagent configurations for the n8n-api plugin.

Agents are Markdown files that define autonomous task handlers with specific tool access and system prompts.

## Structure

Each agent is a Markdown file with YAML frontmatter:

```yaml
---
name: agent-name
description: When to use this agent
allowed-tools: Tool1, Tool2
model: sonnet
---

# Agent Title

System prompt content here...
```

## Current Agents

None defined yet. Add agents as needed for specialized n8n operations.
