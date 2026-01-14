# Known Limitations and Workarounds

This document describes limitations imposed by the n8n API that cannot be fixed in the MCP layer. These are upstream API issues that require workarounds.

**Last Updated**: 2026-01-13
**n8n Version Tested**: 1.114.3

---

## 1. Workflow Update API is Broken

**Severity**: 🔴 Critical
**Affected Tool**: `update_workflow`
**Issue Number**: [#1 in N8N_MCP_ISSUES.md](N8N_MCP_ISSUES.md#1-workflow-update-api-is-essentially-broken)

### Problem

The `PUT /api/v1/workflows/{id}` endpoint has overly strict validation that makes it effectively unusable. Attempting to update workflows results in contradictory validation errors:

- **Error 1**: `"request/body must NOT have additional properties"` - when including fields returned by `get_workflow`
- **Error 2**: `"request/body must have required property 'settings'"` - when including minimal fields

The API simultaneously requires certain fields and rejects them as "additional properties."

### Impact

- Cannot modify existing workflows via MCP tools
- Must use workaround (delete and recreate) which loses execution history
- Workflow ID changes after recreation
- Active workflows experience brief downtime during recreation

### Workaround: Delete and Recreate

Instead of using `update_workflow`, use this pattern:

```python
# Step 1: Save the current workflow
old_workflow = get_workflow(workflow_id="abc123")

# Step 2: Prepare updated workflow (remove read-only fields)
updated_workflow = {
    "name": "Updated Name",  # Your changes here
    "nodes": old_workflow["nodes"],  # Preserve or modify nodes
    "connections": old_workflow["connections"],
    "settings": old_workflow.get("settings", {"executionOrder": "v1"})
}

# Remove ALL read-only fields (see WORKFLOW_FIELD_REFERENCE.md)
# active, id, versionId, createdAt, updatedAt, description, etc.

# Step 3: Delete old workflow
delete_workflow(workflow_id="abc123")

# Step 4: Recreate with modifications
new_workflow = create_workflow(json.dumps(updated_workflow))

# Step 5: If the workflow was active, activate the new one
activate_workflow(new_workflow["id"], active=True)
```

### Consequences of Workaround

| Aspect | Impact |
|--------|--------|
| **Execution History** | ❌ Lost completely |
| **Workflow ID** | ❌ Changes (update references in code/docs) |
| **Credentials** | ✅ Preserved (same credential IDs) |
| **Node IDs** | ✅ Preserved (if not regenerated) |
| **Downtime** | ⚠️ Brief downtime if workflow was active |
| **Tags** | ❌ Lost (must reapply using `update_workflow_tags`) |

### Why This Can't Be Fixed in MCP

This is a server-side validation bug in n8n's API implementation. The MCP server acts as a client and can only pass requests through - it cannot modify n8n's validation logic or fix the API's contradictory requirements.

**Upstream Issue**: This appears to be a long-standing n8n API issue. Consider reporting to the n8n project if not already tracked.

---

## 2. Credential Name Resolution is Unpredictable

**Severity**: 🟡 High
**Affected Tools**: `create_workflow` (when referencing credentials)
**Issue Number**: [#4 in N8N_MCP_ISSUES.md](N8N_MCP_ISSUES.md#4-credential-resolution-inconsistency)

### Problem

When creating workflows with credentials specified by name (instead of ID), n8n may select a different credential than requested. The credential selection logic appears to use:
- Fuzzy/substring matching
- "Compatibility" checks
- First-match or arbitrary selection

Example of unexpected behavior:
```python
# You request:
"credentials": {
    "sshPassword": {"name": "n8n-automation"}
}

# n8n actually uses:
"credentials": {
    "sshPassword": {
        "id": "QVJjCflucAyEvYn9",
        "name": "SSH Password account"  # Different credential!
    }
}
```

### Impact

- Uncertainty about which credential will be used
- Potential security issues if wrong credential is selected
- Workflows may fail if n8n selects non-existent or incorrect credential
- Debugging difficulty (workflow shows different credential than specified)

### Workaround: Always Use Credential IDs

**DON'T** use credential names:
```python
# ❌ AVOID - Unpredictable
"credentials": {
    "sshPassword": {
        "name": "my-server-ssh"  # May select wrong credential
    }
}
```

**DO** use credential IDs:
```python
# ✅ RECOMMENDED - Precise and reliable

# Step 1: Get credentials list
credentials = list_credentials()

# Step 2: Find the credential you want
ssh_cred = next(
    (c for c in credentials["data"] if c["name"] == "my-server-ssh"),
    None
)

if not ssh_cred:
    raise ValueError("Credential 'my-server-ssh' not found")

# Step 3: Use the credential ID in workflow
"credentials": {
    "sshPassword": {
        "id": ssh_cred["id"]  # Exact match guaranteed
    }
}
```

### Best Practices

1. **Always list credentials first**: Use `list_credentials()` to get available credentials
2. **Verify credential exists**: Check that the credential you need is in the list
3. **Use ID, never name**: Reference credentials by `id` field only
4. **Store credential mappings**: If using templates, maintain a mapping of credential names to IDs

### Why This Can't Be Fixed in MCP

Credential resolution happens server-side in n8n when processing workflow creation requests. The MCP server cannot control how n8n matches credential names to credential records or override the selection logic.

---

## 3. API Error Messages Lack Field-Specific Details

**Severity**: 🟡 High
**Affected Tools**: `create_workflow`, `update_workflow`, `create_credential`
**Issue Number**: [#6 in N8N_MCP_ISSUES.md](N8N_MCP_ISSUES.md#6-incomplete-error-messages)

### Problem

When validation fails, n8n API error messages are vague and don't specify which field caused the problem:

**Example vague errors**:
- `"request/body must NOT have additional properties"` - Which property?
- `"request/body must have required property"` - Which property?
- `"request/body/nodes/0 invalid"` - What about the node is invalid?

### Impact

- Wastes development time on trial-and-error debugging
- Frustrating user experience
- Difficult to diagnose complex validation failures
- No way to programmatically determine which field to fix

### Workaround: Binary Search Field Removal

When you get a validation error, use this strategy:

```python
# 1. Start with all your intended fields
full_data = {
    "name": "My Workflow",
    "description": "Does something",
    "active": False,
    "nodes": [...],
    "connections": {...},
    "settings": {...}
}

# 2. Error: "must NOT have additional properties"
# Remove half the optional fields
attempt_1 = {
    "name": "My Workflow",
    "nodes": [...],
    "connections": {...},
    "settings": {...}
}
# If this works, problem was in: description, active

# 3. Test each removed field individually
# (In this case: 'active' and 'description' are the culprits)
```

### Common Problematic Fields

Based on empirical testing, these fields commonly cause "additional properties" errors in workflow creation:

| Field | Allowed in | Forbidden in | Notes |
|-------|-----------|--------------|-------|
| `active` | Response | Request | Use `activate_workflow` instead |
| `description` | Response | Request | Not supported in v1 API |
| `id` | Response | Request | Auto-generated |
| `versionId` | Response | Request | Auto-generated |
| `createdAt` | Response | Request | Auto-generated |
| `updatedAt` | Response | Request | Auto-generated |

See [WORKFLOW_FIELD_REFERENCE.md](WORKFLOW_FIELD_REFERENCE.md) for complete list.

### Why This Can't Be Fixed in MCP

Error messages are generated by n8n's API server validation layer. The MCP server receives these messages as-is and cannot enhance them. This would require changes to n8n's error handling code.

**Suggestion**: The n8n project could improve API responses by including field paths in validation errors (following JSON Schema error formats).

---

## 4. No Pagination or Field Selection

**Severity**: 🟡 Medium
**Affected Tool**: `list_workflows`
**Issue Number**: [#5 in N8N_MCP_ISSUES.md](N8N_MCP_ISSUES.md#5-large-response-handling)

### Problem

The `list_workflows` endpoint returns complete workflow definitions with no options to:
- **Paginate results** (`limit`, `offset` parameters)
- **Select specific fields** (`fields=id,name,active`)
- **Request summary view** (minimal metadata only)

**Impact of large responses**:
- Individual workflow: ~10-12KB
- 8 workflows: ~97KB response
- Exceeds Claude token limits
- Slow network transfers
- Cannot process directly in conversation

### Partial Workarounds

#### 1. Use Filtering (Implemented in MCP)

The MCP layer now supports basic filtering:

```python
# Get only active workflows
active_workflows = list_workflows(active_only=True)

# Get workflows with specific tags
tagged_workflows = list_workflows(tag_filter="tag_id_1,tag_id_2")
```

This reduces the **number** of workflows returned but not the **size** of each workflow.

#### 2. Client-Side Processing

For very large responses, Claude Code will automatically save to file:

```python
# Response saved to file due to size
workflows = list_workflows()
# File path provided in output

# Use jq to extract just what you need
jq '.data[] | {id, name, active}' < /path/to/workflows.json
```

#### 3. Get Specific Workflow

If you know which workflow you need, fetch it directly:

```python
# Instead of listing all workflows
specific_workflow = get_workflow(workflow_id="abc123")
```

### Why This Can't Be Fixed in MCP

The n8n API doesn't support:
- `GET /api/v1/workflows?limit=10&offset=0` (pagination)
- `GET /api/v1/workflows?fields=id,name,active` (field selection)
- `GET /api/v1/workflows?summary=true` (summary mode)

Without API support, the MCP layer cannot add these capabilities. All workflow data must be retrieved and returned as-is.

---

## 5. SSH Credential Type Name Ambiguity

**Severity**: 🟢 Low
**Affected Tool**: `create_credential`
**Issue Number**: [#11 in N8N_MCP_ISSUES.md](N8N_MCP_ISSUES.md#11-ssh-credential-type-ambiguity)

### Problem

SSH credentials may accept multiple type name variants:
- `sshPassword` (documented, recommended)
- `ssh` (sometimes works)
- Unclear which is canonical

### Impact

Minor confusion when creating SSH credentials. Usually auto-resolved by n8n or results in clear error message.

### Workaround

**Always use `sshPassword`** for SSH credentials:

```python
credential = create_credential(json.dumps({
    "name": "My SSH Credential",
    "type": "sshPassword",  # ✅ Use this
    "data": {
        "host": "example.com",
        "username": "admin",
        "password": "secret"  # or use privateKey
    }
}))
```

If uncertain about any credential type name, use:
```python
# Discover the correct type name
schema = get_credential_schema("sshPassword")
# Check the schema to verify it's the right type
```

### Why This Can't Be Fixed in MCP

Credential type naming is defined by n8n's credential type system. The MCP server uses whatever type names n8n accepts. Standardization would require changes to n8n's credential type definitions.

---

## Summary Table

| Issue | Severity | Can MCP Fix? | Workaround Available? | Workaround Quality |
|-------|----------|--------------|----------------------|-------------------|
| Update workflow broken | 🔴 Critical | ❌ No | ✅ Yes | ⚠️ Lossy (history lost) |
| Credential name resolution | 🟡 High | ❌ No | ✅ Yes | ✅ Reliable |
| Vague error messages | 🟡 High | ❌ No | ⚠️ Partial | ⚠️ Trial-and-error |
| No pagination | 🟡 Medium | ❌ No | ⚠️ Partial | ⚠️ Limited |
| SSH type ambiguity | 🟢 Low | ❌ No | ✅ Yes | ✅ Reliable |

---

## Reporting Issues to n8n

If you encounter these issues and want to help improve n8n:

1. **Check existing issues**: Search [n8n GitHub Issues](https://github.com/n8n-io/n8n/issues)
2. **Report with details**: Include:
   - n8n version
   - Exact API request/response
   - Expected vs actual behavior
3. **Reference this doc**: Link to this limitations document for context

---

## Related Documentation

- [N8N_MCP_ISSUES.md](N8N_MCP_ISSUES.md) - Full issue analysis and details
- [WORKFLOW_FIELD_REFERENCE.md](WORKFLOW_FIELD_REFERENCE.md) - Complete field reference
- [CREDENTIAL_TYPES.md](CREDENTIAL_TYPES.md) - Credential type catalog
- [n8n API Documentation](https://docs.n8n.io/api/) - Official n8n API docs
