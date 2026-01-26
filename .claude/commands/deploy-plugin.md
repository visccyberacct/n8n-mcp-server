---
description: Deploy plugin to marketplace (version managed by git hook)
---

# Deploy Plugin to Marketplace

Deploy the n8n-api to claude-marketplace **from the main branch**. Version is automatically managed by the global git pre-push hook based on Conventional Commits.

## Configuration

Replace these placeholders before using:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `n8n-api` | Plugin name (kebab-case) | `jenkins-mcp` |
| `MCP Server for n8n workflow automation API` | Short description | `MCP Server for Jenkins CI/CD API` |
| `n8n_mcp` | Python package (snake_case) | `jenkins_mcp` |
| `/home/kviscount.adm@homelab.com/projects/n8n-mcp-server` | Development project path | `/home/user/projects/my-plugin` |
| `/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api` | Marketplace plugin path | `/home/user/projects/claude-marketplace/plugins/my-plugin` |

## What This Does

1. **Switches to main branch** (saves current branch to return later)
2. **Pulls latest changes** from origin/main
3. **Reads current version** from pyproject.toml (set by git hook)
4. **Copies all source files** to marketplace
5. **Updates marketplace** plugin.json with version from development
6. **Updates marketplace.json registry** with version from development
7. **Verifies .mcp.json exists** (creates if missing)
8. **Validates** deployment
9. **Commits changes** to marketplace feature branch
10. **Pushes** feature branch and creates PR
11. **Auto-merges** PR to marketplace main
12. **Returns to original branch**
13. **Reports** what changed

**IMPORTANT:** This command always deploys from the `main` branch, regardless of which branch you're currently on.

## Version Management

**IMPORTANT:** Version is managed by git pre-push hook, NOT this command.

To bump version:
1. Make changes in development
2. Commit with Conventional Commits:
   - `feat:` -> MINOR bump (0.1.2 -> 0.2.0)
   - `fix:` / `chore:` -> PATCH bump (0.1.2 -> 0.1.3)
   - `BREAKING CHANGE:` -> MAJOR bump (0.1.2 -> 1.0.0)
3. Run `git push` -> hook auto-bumps version and commits
4. Run `/deploy-plugin` -> syncs to marketplace

## Process

Execute these steps:

### 1. Switch to Main Branch

```bash
# Save current branch name for later return
ORIGINAL_BRANCH=$(git branch --show-current)
echo "Current branch: $ORIGINAL_BRANCH"

# Stash any uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
  git stash push -m "deploy-plugin-auto-stash"
  echo "Stashed uncommitted changes"
  STASHED=true
else
  STASHED=false
fi

# Switch to main and pull latest
git switch main
git pull origin main
echo "Switched to main branch and pulled latest"
```

Store ORIGINAL_BRANCH and STASHED values for the final step.

### 2. Read Current Version

```bash
# Get version from pyproject.toml (already bumped by git hook)
grep '^version = ' pyproject.toml | cut -d'"' -f2
```

Store the output as CURRENT_VERSION for use in subsequent steps.

### 3. Copy Source Files

```bash
MARKETPLACE="/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"

# Clean and recreate necessary directories
rm -rf "$MARKETPLACE/src"
rm -rf "$MARKETPLACE/config"
mkdir -p "$MARKETPLACE/src"
mkdir -p "$MARKETPLACE/config"
mkdir -p "$MARKETPLACE/skills"
mkdir -p "$MARKETPLACE/commands"
mkdir -p "$MARKETPLACE/agents"
mkdir -p "$MARKETPLACE/hooks"
mkdir -p "$MARKETPLACE/.claude-plugin"

# Copy source code
cp -r src/* "$MARKETPLACE/src/"

# Copy config files
cp -r config/* "$MARKETPLACE/config/"

# Copy metadata files
cp pyproject.toml "$MARKETPLACE/"
cp README.md "$MARKETPLACE/"
cp .env.example "$MARKETPLACE/" 2>/dev/null || true

# Copy plugin manifest
cp .claude-plugin/plugin.json "$MARKETPLACE/.claude-plugin/"

# Copy hooks
cp -r hooks/* "$MARKETPLACE/hooks/"

echo "Source files copied"
```

### 4. Copy Skills, Commands, and Agents

```bash
MARKETPLACE="/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"

# Helper: Check if directory has real content (not just .gitkeep)
has_real_content() {
  local dir="$1"
  [ -d "$dir" ] && [ -n "$(find "$dir" -type f ! -name '.gitkeep' 2>/dev/null | head -1)" ]
}

# Copy skills if they have real content
if has_real_content "skills"; then
  rm -rf "$MARKETPLACE/skills"
  cp -r skills "$MARKETPLACE/"
  echo "Skills copied"
else
  rm -rf "$MARKETPLACE/skills"
  echo "Skills: empty or .gitkeep only, skipped"
fi

# Copy commands if they have real content
if has_real_content "commands"; then
  rm -rf "$MARKETPLACE/commands"
  cp -r commands "$MARKETPLACE/"
  echo "Commands copied"
else
  rm -rf "$MARKETPLACE/commands"
  echo "Commands: empty or .gitkeep only, skipped"
fi

# Copy agents if they have real content
if has_real_content "agents"; then
  rm -rf "$MARKETPLACE/agents"
  cp -r agents "$MARKETPLACE/"
  echo "Agents copied"
else
  rm -rf "$MARKETPLACE/agents"
  echo "Agents: empty or .gitkeep only, skipped"
fi
```

### 5. Update plugin.json Version

Replace `<VERSION>` with the CURRENT_VERSION from step 2.

```bash
MARKETPLACE="/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"

# Update version in plugin.json using jq
jq --arg v "<VERSION>" '.version = $v' "$MARKETPLACE/.claude-plugin/plugin.json" > "$MARKETPLACE/.claude-plugin/plugin.json.tmp"
mv "$MARKETPLACE/.claude-plugin/plugin.json.tmp" "$MARKETPLACE/.claude-plugin/plugin.json"

# Verify update
grep '"version":' "$MARKETPLACE/.claude-plugin/plugin.json"
```

### 5a. Remove Empty Directory References from plugin.json

The plugin validator rejects references to empty directories. Remove `skills`, `agents`, and `commands` fields if those directories don't exist or are empty in the marketplace.

```bash
MARKETPLACE="/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"

# Helper: Check if marketplace directory has content
has_content() {
  local dir="$MARKETPLACE/$1"
  [ -d "$dir" ] && [ -n "$(find "$dir" -type f ! -name '.gitkeep' 2>/dev/null | head -1)" ]
}

# Build jq filter to remove empty directory references
JQ_FILTER="."
if ! has_content "skills"; then
  JQ_FILTER="$JQ_FILTER | del(.skills)"
  echo "Removing skills from plugin.json (empty directory)"
fi
if ! has_content "agents"; then
  JQ_FILTER="$JQ_FILTER | del(.agents)"
  echo "Removing agents from plugin.json (empty directory)"
fi
if ! has_content "commands"; then
  JQ_FILTER="$JQ_FILTER | del(.commands)"
  echo "Removing commands from plugin.json (empty directory)"
fi

# Apply filter
jq "$JQ_FILTER" "$MARKETPLACE/.claude-plugin/plugin.json" > "$MARKETPLACE/.claude-plugin/plugin.json.tmp"
mv "$MARKETPLACE/.claude-plugin/plugin.json.tmp" "$MARKETPLACE/.claude-plugin/plugin.json"

echo "plugin.json cleaned of empty directory references"
```

### 6. Update marketplace.json Registry

Replace `<VERSION>` with the CURRENT_VERSION from step 2.

```bash
MARKETPLACE_ROOT="/home/kviscount.adm@homelab.com/projects/claude-marketplace"

# Update or create the plugin entry in the central marketplace.json registry
python3 << 'PYEOF'
import json

marketplace_file = "/home/kviscount.adm@homelab.com/projects/claude-marketplace/.claude-plugin/marketplace.json"

with open(marketplace_file, 'r') as f:
    data = json.load(f)

# Find existing entry
found = False
for plugin in data.get('plugins', []):
    if plugin.get('name') == 'n8n-api':
        plugin['version'] = '<VERSION>'
        found = True
        print("marketplace.json updated with version <VERSION>")
        break

# Create entry if not found
if not found:
    new_entry = {
        "name": "n8n-api",
        "version": "<VERSION>",
        "description": "MCP Server for n8n workflow automation API",
        "path": "plugins/n8n-api"
    }
    data['plugins'].insert(0, new_entry)
    print("marketplace.json: created new entry for n8n-api v<VERSION>")

with open(marketplace_file, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PYEOF

# Verify the update
grep -A5 '"name": "n8n-api"' "$MARKETPLACE_ROOT/.claude-plugin/marketplace.json" | grep version
```

### 7. Verify .mcp.json Exists

Only include this step if your plugin has an MCP server. Customize the server configuration as needed.

```bash
MARKETPLACE="/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"

# Check if .mcp.json exists at plugin root
if [ -f "$MARKETPLACE/.mcp.json" ]; then
  echo ".mcp.json exists"
else
  echo "Creating .mcp.json..."
  cat > "$MARKETPLACE/.mcp.json" << 'EOF'
{
  "mcpServers": {
    "n8n-api": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "n8n-api"],
      "env": {
        "EXAMPLE_VAR": "${EXAMPLE_VAR}"
      }
    }
  }
}
EOF
  echo ".mcp.json created"
fi
```

### 8. Validate Deployment

Replace `<VERSION>` with the CURRENT_VERSION from step 2.

```bash
MARKETPLACE="/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"

# Verify critical files exist
echo ""
echo "Validating deployment..."

[ -f "$MARKETPLACE/.claude-plugin/plugin.json" ] && echo "plugin.json exists" || echo "plugin.json MISSING"
[ -f "$MARKETPLACE/.mcp.json" ] && echo ".mcp.json exists" || echo ".mcp.json MISSING"
[ -f "$MARKETPLACE/src/n8n_mcp/mcp/server.py" ] && echo "server.py exists" || echo "server.py MISSING"
[ -f "$MARKETPLACE/pyproject.toml" ] && echo "pyproject.toml exists" || echo "pyproject.toml MISSING"
[ -d "$MARKETPLACE/config" ] && echo "config/ exists" || echo "config/ MISSING"

# Validate JSON files
python3 -m json.tool "$MARKETPLACE/.claude-plugin/plugin.json" > /dev/null 2>&1 && echo "plugin.json valid JSON" || echo "plugin.json INVALID JSON"
python3 -m json.tool "$MARKETPLACE/.mcp.json" > /dev/null 2>&1 && echo ".mcp.json valid JSON" || echo ".mcp.json INVALID JSON"
python3 -m json.tool "$MARKETPLACE/hooks/hooks.json" > /dev/null 2>&1 && echo "hooks.json valid JSON" || echo "hooks.json INVALID JSON"

echo "Versions synced: <VERSION>"
```

### 9. Commit and Push to Marketplace

Replace `<VERSION>` with the CURRENT_VERSION from step 2.

```bash
MARKETPLACE="/home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"

# Navigate to marketplace root (not plugin subdirectory)
cd "/home/kviscount.adm@homelab.com/projects/claude-marketplace"

# Check if there are changes
git diff --quiet && git diff --cached --quiet
```

If there are NO changes (exit code 0), output "No changes to commit in marketplace" and skip to step 11.

If there ARE changes (exit code 1), continue with these commands:

```bash
# Create feature branch (replace <VERSION> with actual version)
BRANCH_NAME="feature/n8n-api-v<VERSION>"
git switch -c "$BRANCH_NAME" 2>/dev/null || git switch "$BRANCH_NAME"

# Stage all changes
git add -A

# Commit changes (replace <VERSION> with actual version in commit message)
git commit -m "$(cat <<'EOF'
chore: update n8n-api to v<VERSION>

- Sync source files from development
- Update plugin version to <VERSION>
- Update marketplace.json registry

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"

# Push feature branch
git push -u origin "$BRANCH_NAME"
```

### 10. Create and Merge Pull Request

Replace `<VERSION>` with the CURRENT_VERSION from step 2.

```bash
cd "/home/kviscount.adm@homelab.com/projects/claude-marketplace"

# Create pull request (replace <VERSION> with actual version)
gh pr create --title "n8n-api: Update to v<VERSION>" --body "$(cat <<'EOF'
Update n8n-api to version <VERSION>

## Changes
- Synced source files from development repository
- Updated plugin.json version to <VERSION>
- Updated marketplace.json registry version to <VERSION>
- Synced config files

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" --base main
```

Store the PR URL output from the command above. Extract the PR number from the URL (last numeric segment after the final `/`).

```bash
# Auto-merge PR (replace <PR_NUMBER> with the extracted number)
gh pr merge <PR_NUMBER> --squash --auto

# Switch back to main and pull
git switch main
git pull

echo "Marketplace updated and merged"
```

### 11. Return to Original Branch

Use the ORIGINAL_BRANCH and STASHED values from step 1. Replace `<ORIGINAL_BRANCH>` with the actual branch name.

```bash
cd "/home/kviscount.adm@homelab.com/projects/n8n-mcp-server"

# Switch back to original branch (replace <ORIGINAL_BRANCH> with actual value)
git switch <ORIGINAL_BRANCH>
echo "Returned to branch: <ORIGINAL_BRANCH>"
```

If STASHED was `true` in step 1, run this additional command:

```bash
# Restore stashed changes
git stash pop
echo "Restored stashed changes"
```

### 12. Report Status

Replace `<VERSION>` with the CURRENT_VERSION from step 2.

```bash
echo ""
echo "========================================="
echo "  Plugin Deployed to Marketplace"
echo "========================================="
echo ""
echo "Version: <VERSION>"
echo "Location: /home/kviscount.adm@homelab.com/projects/claude-marketplace/plugins/n8n-api"
echo ""
echo "Files Updated:"
echo "  Marketplace:"
echo "    - .claude-plugin/plugin.json"
echo "    - .mcp.json (MCP server config)"
echo "    - .claude-plugin/marketplace.json (registry)"
echo "    - src/n8n_mcp/"
echo "    - config/"
echo "    - pyproject.toml"
echo "    - README.md"
echo ""
echo "Status:"
echo "  - Files copied and validated"
echo "  - Changes committed to marketplace"
echo "  - Feature branch pushed"
echo "  - Pull request created and merged"
echo "  - Marketplace main branch updated"
echo ""
echo "========================================="
```

## Workflow Example

```bash
# 1. Make changes in development
vim src/n8n_mcp/mcp/server.py

# 2. Commit with Conventional Commit
git add .
git commit -m "feat: add new capability"

# 3. Push (git hook auto-bumps version)
git push
# Hook outputs: "plugin.json: 0.1.2 -> 0.2.0 (minor)"
# Hook creates commit: "chore: bump version to 0.2.0"

# 4. Deploy to marketplace
/deploy-plugin
# Copies files and updates marketplace plugin.json to 0.2.0
```

## Important Notes

- **Always deploys from main branch** - regardless of your current branch
- **Version is managed by git hook** - do NOT manually edit version in plugin.json
- One-way sync: main branch -> marketplace
- **Fully automated**: Commits, pushes, creates PR, and merges to marketplace
- Automatically stashes uncommitted changes and restores them after deployment
- Marketplace git hook is disabled (excluded directory)
- Validates all critical files exist and are valid JSON
- Requires `gh` CLI to be installed and authenticated
- **CRITICAL**: Replace all instances of `<VERSION>`, `<PR_NUMBER>`, and `<ORIGINAL_BRANCH>` with actual values during execution

## Troubleshooting

**Version not bumped**: Check your commit message follows Conventional Commits format

**JSON validation fails**: Check plugin.json or .mcp.json for syntax errors

**Files missing**: Verify source files exist in development directory

**Hook not working**: Check `git config --global core.hooksPath` points to `~/.git-hooks`

**Bash syntax errors**: Avoid using `$(command)` subshells in compound commands with `&&`. Execute commands separately and use the output in subsequent commands.

**Plugin not showing in marketplace**: Ensure Step 6 created/updated the entry in marketplace.json. The script now creates entries if missing.
