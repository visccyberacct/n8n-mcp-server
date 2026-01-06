---
name: n8n-setup
description: |
  Configure n8n MCP server connection credentials (API key and base URL).
  Use when the user needs to set up or update their n8n API credentials.
---

# n8n Setup Skill

Guide users through configuring their n8n API credentials for the MCP server.

## When to Use

- User mentions setting up n8n
- User asks how to configure n8n credentials
- User reports authentication errors with n8n
- User needs to change their n8n instance URL or API key

## Setup Process

### 1. Collect Required Information

Ask the user for:
- **n8n Base URL**: The full URL of their n8n instance (e.g., `https://n8n.homelab.com`)
- **n8n API Key**: Their n8n API key from Settings > API

### 2. Create/Update .env File

Create or update the `.env` file in the plugin root directory with:

```
N8N_BASE_URL=<user's n8n URL>
N8N_API_KEY=<user's API key>
```

**Location**: `${CLAUDE_PLUGIN_ROOT}/.env`

### 3. Verify and Restart

After configuration:
1. Inform user the credentials have been saved
2. Remind them to restart Claude Code
3. Suggest testing with: "List my n8n workflows"

## Example Interaction

**User**: "How do I set up n8n?"

**Assistant**: "I'll help you configure the n8n MCP server. I need two pieces of information:

1. **n8n Instance URL**: What's your n8n base URL? (e.g., https://n8n.homelab.com)
2. **API Key**: What's your n8n API key? You can get this from n8n under Settings > API > Create API Key

Please provide these details."

**User**: "URL is https://n8n.homelab.com and key is n8n_api_abc123xyz..."

**Assistant**:
*[Creates/updates .env file at ${CLAUDE_PLUGIN_ROOT}/.env]*

"✓ Configuration saved!

**Next steps:**
1. Restart Claude Code for changes to take effect
2. Test the connection: 'List my n8n workflows'

Your n8n instance at https://n8n.homelab.com is now configured."

## Getting an API Key

Guide users to get their API key:
1. Log into their n8n instance
2. Go to Settings > API
3. Click "Create API Key"
4. Copy the generated key (they won't be able to see it again)

## Security Notes

- Credentials are stored in `.env` (not committed to git)
- API keys should be kept secure and never shared
- If compromised, user should regenerate the key in n8n
- To update credentials, simply re-run this setup process

## Troubleshooting

**401 Unauthorized**: API key is invalid or expired
- Verify the key is correct
- Regenerate key in n8n if needed

**Connection refused**: Cannot reach n8n instance
- Verify the base URL is correct
- Check network connectivity
- Ensure n8n instance is running
