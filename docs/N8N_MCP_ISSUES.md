# n8n MCP Plugin - Issues and Limitations

**Date**: 2026-01-13
**Plugin**: `n8n-api@homelab-plugins`
**n8n Version**: 1.114.3
**Context**: Workflow creation and management via MCP tools

---

## Critical Issues

### 1. Workflow Update API is Essentially Broken

**Severity**: 🔴 Critical

**Problem**: The `update_workflow` endpoint is unusable due to overly strict validation.

**Error Messages**:
```
HTTP 400: "request/body must NOT have additional properties"
HTTP 400: "request/body must have required property 'settings'"
```

**What Happens**:
- Attempting to update a workflow with the complete workflow structure (including all fields returned by `get_workflow`) results in 400 errors
- The API simultaneously requires certain fields and rejects them
- No combination of fields successfully updates a workflow

**Impact**:
- Cannot modify existing workflows via MCP
- Must delete and recreate workflows for any changes
- Loses execution history when recreating workflows

**Attempted Workarounds**:
1. ✗ Include all fields from `get_workflow` - rejected with "additional properties"
2. ✗ Include only name/nodes/connections/settings - rejected with missing fields
3. ✗ Include minimal fields - rejected for various reasons
4. ✓ Create new workflow and delete old one - only working solution

**Recommendation**:
- Fix the update endpoint validation logic
- OR document exactly which fields are required/allowed
- OR remove the tool entirely if it cannot work

---

### 2. Missing Credential Discovery Tool

**Severity**: 🔴 Critical

**Problem**: No MCP tool exists to list credentials, only create/update/delete.

**What's Missing**:
```javascript
// This tool does not exist:
mcp__plugin_n8n-api_n8n-api__list_credentials()
```

**Impact**:
- Cannot discover existing credential IDs programmatically
- Cannot verify credentials exist before referencing them in workflows
- Must manually check n8n UI or ask user for credential information
- Cannot audit which credentials are available

**Comparison**:
- Jenkins MCP has `jenkins_list_credentials` ✓
- n8n MCP has no equivalent ✗

**Use Cases Blocked**:
1. "Show me all configured credentials"
2. "Find the SSH credential for server X"
3. "Verify Proxmox API credential exists before creating workflow"
4. "List all credentials of type httpHeaderAuth"

**Recommendation**: Add `list_credentials` tool that returns:
```json
{
  "data": [
    {
      "id": "JqjYAZQmSZQenJJ3",
      "name": "Proxmox API",
      "type": "httpHeaderAuth"
    }
  ]
}
```

---

### 3. Undocumented Field Restrictions

**Severity**: 🟡 High

**Problem**: API rejects fields without clear documentation of which fields are allowed.

**Examples**:

**Example 1 - `active` field**:
```json
// This FAILS:
{
  "name": "My Workflow",
  "nodes": [...],
  "connections": {...},
  "active": false  // ✗ Causes 400 error
}

// This WORKS:
{
  "name": "My Workflow",
  "nodes": [...],
  "connections": {...}
  // ✓ Omit active field entirely
}
```

**Example 2 - `description` field**:
```json
// This FAILS:
{
  "name": "My Workflow",
  "description": "Does something",  // ✗ Causes 400 error
  "nodes": [...],
  "connections": {...}
}
```

**Why This Is Problematic**:
- These fields are returned by `get_workflow`, implying they're part of the workflow structure
- Natural assumption is that fields returned by GET are accepted by POST
- Error message doesn't specify which field is problematic
- Required trial-and-error to determine valid structure

**Information Found Later**:
- `N8N_API_SCHEMA.md` documents this: "Do NOT include `active` field in request body (read-only, causes 400 error)"
- BUT this is not in the MCP tool description
- AND it's counter-intuitive since API returns these fields

**Recommendation**:
1. Update MCP tool descriptions to explicitly list forbidden fields
2. Improve API error messages to specify which field caused the error
3. Consider accepting-but-ignoring read-only fields instead of rejecting the request

---

### 4. Credential Resolution Inconsistency

**Severity**: 🟡 High

**Problem**: Credentials can be specified by name or ID, but resolution is unpredictable.

**What Happened**:
```javascript
// Specified in workflow JSON:
"credentials": {
  "sshPassword": {
    "name": "n8n-automation"  // Requested this credential
  }
}

// What n8n actually used:
"credentials": {
  "sshPassword": {
    "id": "QVJjCflucAyEvYn9",
    "name": "SSH Password account"  // Different credential!
  }
}
```

**Impact**:
- Uncertainty about which credential will be used
- Potential security issues if wrong credential is selected
- Workflows may fail if n8n selects non-existent or incorrect credential

**Root Cause**: Unknown. Possible reasons:
- Name matching is fuzzy/substring-based
- n8n auto-selects "compatible" credentials
- Multiple credentials with similar names
- Credential name doesn't uniquely identify

**Recommendation**:
1. Always require credential ID instead of name
2. OR make name matching exact and error if not found
3. Add validation error if credential name is ambiguous

---

## High Priority Issues

### 5. Large Response Handling

**Severity**: 🟡 High

**Problem**: `list_workflows` returns extremely large JSON that exceeds token limits.

**Details**:
- Response size: 97,802 characters for 8 workflows (~12KB per workflow)
- Claude Code auto-saves to file when response exceeds limits
- Cannot process response directly in conversation

**Impact**:
- Must use `jq`, `grep`, or file reads to query results
- Slower workflow development (extra steps required)
- Cannot provide immediate answers to "how many workflows?" type questions

**Example**:
```bash
# Instead of getting answer directly, must do:
jq '.data | length' /path/to/saved-response.txt
jq '.data[] | select(.name == "My workflow")' /path/to/saved-response.txt
```

**Why This Happens**:
- Each workflow includes full node definitions, parameters, credentials, execution history
- No filtering or field selection options
- No pagination support

**Recommendation**:
1. Add `summary` parameter to return minimal workflow info (id, name, active, nodeCount)
2. Add pagination (`limit`, `offset` parameters)
3. Add field selection (`fields=id,name,active`)
4. Add filtering (`active=true`, `name=contains:proxmox`)

---

### 6. Incomplete Error Messages

**Severity**: 🟡 High

**Problem**: API errors don't specify which property is invalid.

**Example Error**:
```json
{
  "message": "request/body must NOT have additional properties"
}
```

**What's Missing**: Which property is "additional"?

**Result**: Must guess and remove fields one by one:
1. Try with all fields → Error
2. Remove `description` → Error
3. Remove `active` → Success!

**Impact**:
- Wastes development time
- Frustrating debugging experience
- Discourages use of the API

**Better Error Message Would Be**:
```json
{
  "message": "request/body must NOT have additional properties",
  "additionalProperties": ["active", "description"],
  "hint": "These fields are read-only and should not be included in the request"
}
```

**Recommendation**:
- Update n8n API error responses to include field-specific information
- List which fields are problematic in validation errors

---

### 7. No Workflow Validation Endpoint

**Severity**: 🟡 High

**Problem**: Cannot validate workflow structure without creating it.

**Missing Capability**:
```javascript
// This tool does not exist:
mcp__plugin_n8n-api_n8n-api__validate_workflow(workflow_data)
```

**Impact**:
- Must create workflow to discover errors
- Creates clutter with failed/test workflows
- No way to dry-run workflow changes

**Use Cases**:
1. "Validate this workflow structure before creating"
2. "Check if all required credentials exist"
3. "Verify node connections are valid"
4. "Lint workflow JSON for common issues"

**Recommendation**:
Add validation tool that checks:
- JSON structure validity
- Required fields present
- Node types exist
- Credentials referenced exist
- Connections are valid
- Returns errors without creating workflow

---

### 8. Credential Creation Requires Type Knowledge

**Severity**: 🟢 Medium

**Problem**: Must know exact credential type strings without discovery mechanism.

**Required Knowledge**:
```javascript
// Must know these exact strings:
"httpHeaderAuth"      // For API tokens
"sshPassword"         // For SSH connections
"googlePalmApi"       // For Gemini AI
"httpBasicAuth"       // For basic auth
// ... etc (50+ types?)
```

**Impact**:
- Must reference documentation or existing workflows
- Cannot discover available credential types
- Typos cause silent failures (wrong credential selected)

**Current Workarounds**:
1. Check `N8N_API_SCHEMA.md` for common types
2. Export workflow from UI and inspect credential types
3. Trial and error

**Recommendation**:
Add `list_credential_types` tool that returns:
```json
{
  "types": [
    {
      "name": "httpHeaderAuth",
      "displayName": "Header Auth",
      "description": "HTTP Header authentication"
    },
    {
      "name": "sshPassword",
      "displayName": "SSH",
      "description": "SSH password or private key"
    }
  ]
}
```

---

## Medium Priority Issues

### 9. Connection Object Complexity

**Severity**: 🟢 Medium

**Problem**: Workflow connection structure is complex and undocumented.

**Example - Standard Connection**:
```json
"connections": {
  "Node Name": {
    "main": [[{"node": "Target Node", "type": "main", "index": 0}]]
  }
}
```

**Example - AI Model Connection**:
```json
"connections": {
  "Gemini Model": {
    "ai_languageModel": [[{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]]
  }
}
```

**Issues**:
- Different node types use different connection types (`main`, `ai_languageModel`, `ai_tool`, `ai_memory`)
- Not documented in MCP tool descriptions
- Easy to create invalid connections
- Connections fail silently (workflow creates but doesn't work)

**Impact**:
- Must inspect existing workflows to learn connection patterns
- Cannot programmatically determine valid connection types
- Errors only appear when workflow executes

**Recommendation**:
1. Document all connection types
2. Add validation for connection structures
3. Provide examples for each node type category
4. Add connection validation to hypothetical `validate_workflow` tool

---

### 10. No Workflow Template Retrieval

**Severity**: 🟢 Medium

**Problem**: Cannot easily copy/template existing workflows.

**What Works**:
```javascript
get_workflow(workflow_id="existing-id")  // Returns full structure
```

**What Doesn't Work**:
- Returned structure cannot be directly used to create new workflow (see Issue #3)
- Must manually clean up fields (remove `id`, `versionId`, `active`, etc.)
- Credential IDs may not be valid for different credentials

**Use Case**:
"Create a new workflow based on the Proxmox SSH workflow but with different credentials"

**Current Process**:
1. Get existing workflow
2. Manually remove: `id`, `versionId`, `activeVersionId`, `createdAt`, `updatedAt`, `active`, `description`, `staticData`, `meta`, `pinData`, `triggerCount`, `versionCounter`
3. Update credential IDs
4. Update node IDs to prevent conflicts
5. Create new workflow

**Recommendation**:
Add `clone_workflow` or `get_workflow_template` tool:
```javascript
mcp__plugin_n8n-api_n8n-api__clone_workflow({
  source_workflow_id: "existing-id",
  new_name: "New Workflow Name",
  credential_mapping: {
    "old-cred-id": "new-cred-id"
  }
})
```

---

## Lower Priority Issues

### 11. SSH Credential Type Ambiguity

**Severity**: 🟢 Low

**Problem**: SSH credentials can use multiple type names.

**Examples**:
- `sshPassword` (documented)
- `ssh` (sometimes seen)
- Unclear which to use

**Impact**: Minor confusion, usually auto-resolved

**Recommendation**: Standardize on one type name

---

### 12. Missing Execution Management Tools

**Severity**: 🟢 Low

**Problem**: Limited execution management capabilities.

**What Exists**:
- `execute_workflow` ✓
- `get_executions` ✓
- `get_execution` ✓

**What's Missing**:
- `retry_execution` ✗
- `stop_execution` ✗
- `delete_execution` ✗
- `get_execution_logs` ✗ (only full execution data)

**Impact**:
- Cannot manage long-running workflows
- Cannot clean up failed executions
- Cannot retry specific executions

**Recommendation**: Add execution management tools

---

### 13. No Workflow Status/Health Check

**Severity**: 🟢 Low

**Problem**: Cannot quickly check if workflow is healthy.

**What's Needed**:
```javascript
mcp__plugin_n8n-api_n8n-api__get_workflow_health({
  workflow_id: "abc123"
})

// Returns:
{
  "healthy": true,
  "last_execution": "2026-01-13T20:00:00Z",
  "success_rate": 0.875,
  "avg_execution_time": 1250,
  "issues": []
}
```

**Current Workaround**:
1. Get workflow
2. Get executions
3. Manually calculate success rate
4. Check for common issues

**Recommendation**: Add health check tool

---

## Summary Statistics

**Total Issues Identified**: 13

**By Severity**:
- 🔴 Critical: 2 (15%)
- 🟡 High: 5 (38%)
- 🟢 Medium: 3 (23%)
- 🟢 Low: 3 (23%)

**By Category**:
- API Design/Validation: 5
- Missing Tools/Features: 6
- Documentation/UX: 2

**Top 3 Most Impactful**:
1. **Workflow Update API is broken** - Blocks primary use case
2. **Missing credential listing** - No way to discover credentials
3. **Large response handling** - Makes list operations cumbersome

---

## Recommended Priority Order for Fixes

### Must Fix (Blocking Core Functionality)
1. Fix `update_workflow` API or remove it
2. Add `list_credentials` tool
3. Improve error messages to specify problematic fields

### Should Fix (Major UX Improvements)
4. Add workflow validation endpoint
5. Add pagination/filtering to `list_workflows`
6. Document credential types and connection structures

### Nice to Have (Enhancement)
7. Add workflow cloning/templating tool
8. Add workflow health check tool
9. Add execution management tools
10. Standardize credential type names

---

## Testing Notes

All issues were encountered during development of the "Proxmox VM Status and Updates" workflow on 2026-01-13.

**Environment**:
- n8n instance: https://n8n.homelab.com
- MCP Plugin: n8n-api@homelab-plugins
- Claude Code version: Latest
- Workflow complexity: 11 nodes, 3 credential types, AI integration

**Workflow Creation Success**: Yes (after resolving all issues above)

**Time Spent on MCP Issues**: ~45 minutes of the total development time

**Time Saved by Having MCP**: Still significant compared to manual UI workflow creation, but could be much better with fixes.

---

## Appendix: Working Workflow Structure

For reference, here's the minimal working structure for workflow creation:

```json
{
  "name": "Workflow Name",
  "settings": {
    "executionOrder": "v1"
  },
  "nodes": [
    {
      "id": "unique-id",
      "name": "Node Name",
      "type": "n8n-nodes-base.nodeType",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {},
      "credentials": {
        "credentialType": {
          "id": "credential-id"
        }
      }
    }
  ],
  "connections": {
    "Node Name": {
      "main": [[{"node": "Target Node", "type": "main", "index": 0}]]
    }
  }
}
```

**Do NOT include**: `active`, `description`, `id`, `versionId`, `createdAt`, `updatedAt`, `staticData`, `meta`, `pinData`

These fields will be added by the API automatically.
