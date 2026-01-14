"""
n8n MCP Server - FastMCP server for n8n workflow automation.

Version: 0.1.0
Created: 2025-11-20
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import N8nClient
from .utils import handle_errors
from .validator import validate_workflow as _validate_workflow

# Load environment variables from .env file in the plugin's directory
# This ensures .env works when running as an installed plugin
_plugin_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_plugin_dir / ".env")

# Initialize FastMCP server
mcp = FastMCP("n8n-api")

# Initialize n8n client from environment
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://n8n.homelab.com")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

if not N8N_API_KEY:
    raise ValueError("N8N_API_KEY environment variable is required")

# Module-level client instance with lifecycle management
client = N8nClient(base_url=N8N_BASE_URL, api_key=N8N_API_KEY)


# Cleanup handler for server shutdown
async def cleanup_client() -> None:
    """Close the n8n client connection on server shutdown."""
    await client.close()


@mcp.tool()
@handle_errors
async def list_workflows(
    name_contains: str | None = None,
    active: bool | None = None,
    tag_ids: str | None = None,
) -> dict[str, Any]:
    """List workflows from n8n with optional filtering.

    All filters are optional. When multiple filters are specified, they are
    combined with AND logic (workflows must match ALL criteria).

    Args:
        name_contains: Filter by name substring (case-insensitive).
                       Example: "email" matches "Send Email", "EMAIL_notify", etc.
        active: Filter by active status. True=active only, False=inactive only,
                None (default)=all workflows.
        tag_ids: JSON array of tag IDs to filter by. Workflows must have ALL
                 specified tags. Example: '["tag1", "tag2"]'

    Returns:
        Dictionary containing filtered workflows data from n8n API

    Examples:
        # List all active workflows
        list_workflows(active=True)

        # Find workflows with "backup" in the name
        list_workflows(name_contains="backup")

        # Find inactive workflows tagged with specific tag
        list_workflows(active=False, tag_ids='["abc123"]')
    """
    tag_list = json.loads(tag_ids) if tag_ids else None
    return await client.list_workflows(
        name_contains=name_contains,
        active=active,
        tag_ids=tag_list,
    )


@mcp.tool()
@handle_errors
async def get_workflow(workflow_id: str) -> dict[str, Any]:
    """Get a specific workflow by ID.

    Args:
        workflow_id: The ID of the workflow to retrieve

    Returns:
        Dictionary containing workflow details from n8n API
    """
    return await client.get_workflow(workflow_id)


@mcp.tool()
@handle_errors
async def execute_workflow(workflow_id: str, data: str | None = None) -> dict[str, Any]:
    """Execute a workflow by ID.

    Args:
        workflow_id: The ID of the workflow to execute
        data: Optional JSON string with input data for the workflow

    Returns:
        Dictionary containing execution result from n8n API
    """
    workflow_data = json.loads(data) if data else None
    return await client.execute_workflow(workflow_id, workflow_data)


@mcp.tool()
@handle_errors
async def get_executions(workflow_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    """List workflow execution history.

    Args:
        workflow_id: Optional workflow ID to filter executions
        limit: Maximum number of executions to return (default: 20)

    Returns:
        Dictionary containing executions list from n8n API
    """
    return await client.get_executions(workflow_id, limit)


@mcp.tool()
@handle_errors
async def get_execution(execution_id: str) -> dict[str, Any]:
    """Get specific execution details by ID.

    Args:
        execution_id: The ID of the execution to retrieve

    Returns:
        Dictionary containing execution details from n8n API
    """
    return await client.get_execution(execution_id)


@mcp.tool()
@handle_errors
async def activate_workflow(workflow_id: str, active: bool) -> dict[str, Any]:
    """Activate or deactivate a workflow.

    Args:
        workflow_id: The ID of the workflow to activate/deactivate
        active: True to activate, False to deactivate

    Returns:
        Dictionary containing updated workflow from n8n API
    """
    return await client.activate_workflow(workflow_id, active)


@mcp.tool()
@handle_errors
async def validate_workflow(workflow_data: str) -> dict[str, Any]:
    """Validate a workflow definition before creating or updating.

    Checks the workflow against n8n API requirements and reports errors
    and warnings. Use this BEFORE create_workflow or update_workflow to
    catch issues early with clear, actionable messages.

    Validation checks include:
    - Forbidden fields that cause "must NOT have additional properties" errors
    - Missing required fields (name, nodes, connections)
    - Node structure validation (id, name, type, typeVersion, position)
    - Connection references to existing nodes
    - Credential references (warns if using name instead of id)
    - Recommended settings (executionOrder)

    Args:
        workflow_data: JSON string containing workflow definition to validate

    Returns:
        Dictionary with validation results:
        - valid (bool): True if no errors found
        - errors (list): List of error messages (will cause API rejection)
        - warnings (list): List of warning messages (may cause issues)
        - error_count (int): Number of errors
        - warning_count (int): Number of warnings

    Example usage:
        1. validate_workflow(workflow_json)  # Check for issues
        2. If valid=True, proceed with create_workflow(workflow_json)
        3. If valid=False, fix the errors listed and re-validate

    Example response:
        {
            "valid": false,
            "errors": [
                "Forbidden field 'active' present. Remove it to avoid error.",
                "Node 'HTTP Request' missing required field 'typeVersion'."
            ],
            "warnings": [
                "Node 'HTTP Request' references credential 'My API' by name. Use 'id'."
            ],
            "error_count": 2,
            "warning_count": 1
        }
    """
    workflow_dict = json.loads(workflow_data)
    result = _validate_workflow(workflow_dict)
    return result.to_dict()


@mcp.tool()
@handle_errors
async def create_workflow(workflow_data: str) -> dict[str, Any]:
    """Create a new workflow in n8n.

    ⚠️ IMPORTANT - Forbidden Fields:
    DO NOT include these fields (will cause 400 error):
    - active, description, id, versionId, createdAt, updatedAt
    - staticData, meta, pinData, triggerCount, versionCounter

    Use activate_workflow tool to activate after creation.

    Required Fields:
    - name (str): Workflow name
    - nodes (list): List of workflow nodes
    - connections (dict): Node connections

    Node Required Fields (each node in nodes array):
    - id (str): Unique node identifier
    - name (str): Node display name
    - type (str): Node type (e.g., "n8n-nodes-base.start")
    - typeVersion (int): Node type version
    - position (list): [x, y] coordinates

    Optional Fields:
    - settings (dict): Workflow settings (recommended: {"executionOrder": "v1"})
    - tags (list): Tag IDs to assign to workflow

    Args:
        workflow_data: JSON string containing workflow definition

    Returns:
        Dictionary containing created workflow details including ID

    Common Errors:
    - 'must NOT have additional properties' → Remove forbidden fields above
    - 'missing required property settings' → Add {"settings": {"executionOrder": "v1"}}
    - 'credentials by name may be unreliable' → Use credential IDs from list_credentials

    Example workflow_data:
        {
            "name": "My Workflow",
            "settings": {
                "executionOrder": "v1"
            },
            "nodes": [
                {
                    "id": "node-1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {}
                }
            ],
            "connections": {}
        }

    Documentation:
    - Field reference: docs/WORKFLOW_FIELD_REFERENCE.md
    - Connection types: docs/CONNECTION_TYPES.md
    - Credential types: docs/CREDENTIAL_TYPES.md
    """
    workflow_dict = json.loads(workflow_data)
    return await client.create_workflow(workflow_dict)


@mcp.tool()
@handle_errors
async def update_workflow(workflow_id: str, workflow_data: str) -> dict[str, Any]:
    """Update an existing workflow in n8n.

    ⚠️ ⚠️ ⚠️ CRITICAL WARNING ⚠️ ⚠️ ⚠️

    This endpoint has KNOWN ISSUES with n8n API v1 that make it nearly unusable:
    - Rejects workflows with fields returned by get_workflow
    - Error messages don't specify which field is problematic
    - No combination of fields reliably succeeds

    STRONGLY RECOMMENDED WORKAROUND - Delete and Recreate:
    1. old_wf = get_workflow(workflow_id)
    2. delete_workflow(workflow_id)
    3. new_wf = create_workflow(modified_workflow_json)
    4. If was active: activate_workflow(new_wf["id"], True)

    Consequences of workaround:
    - ✅ Works reliably
    - ❌ Loses execution history
    - ❌ Workflow ID changes (update any references)
    - ❌ Tags are lost (must reapply)

    If you must try updating (expect 400 errors):
    - Use ONLY: name, nodes, connections, settings
    - DO NOT include: active, id, description, versionId, createdAt, updatedAt
    - DO NOT include: staticData, meta, pinData, triggerCount, versionCounter

    Args:
        workflow_id: The ID of the workflow to update
        workflow_data: JSON string with minimal workflow fields (expect failures)

    Returns:
        Dictionary containing updated workflow details (if successful, which is unlikely)

    Documentation:
    - Full details: docs/KNOWN_LIMITATIONS.md#1-workflow-update-api-is-broken
    - Field reference: docs/WORKFLOW_FIELD_REFERENCE.md
    """
    workflow_dict = json.loads(workflow_data)
    return await client.update_workflow(workflow_id, workflow_dict)


@mcp.tool()
@handle_errors
async def delete_workflow(workflow_id: str) -> dict[str, Any]:
    """Delete a workflow from n8n.

    Args:
        workflow_id: The ID of the workflow to delete

    Returns:
        Dictionary confirming deletion or error details
    """
    return await client.delete_workflow(workflow_id)


@mcp.tool()
@handle_errors
async def get_workflow_version(workflow_id: str, version_id: str) -> dict[str, Any]:
    """Get a specific version of a workflow.

    Args:
        workflow_id: The ID of the workflow
        version_id: The version ID to retrieve

    Returns:
        Dictionary containing workflow version details from n8n API
    """
    return await client.get_workflow_version(workflow_id, version_id)


@mcp.tool()
@handle_errors
async def transfer_workflow(workflow_id: str, destination_project_id: str) -> dict[str, Any]:
    """Transfer a workflow to a different project.

    Args:
        workflow_id: The ID of the workflow to transfer
        destination_project_id: The ID of the destination project

    Returns:
        Dictionary containing updated workflow from n8n API
    """
    return await client.transfer_workflow(workflow_id, destination_project_id)


@mcp.tool()
@handle_errors
async def get_workflow_tags(workflow_id: str) -> dict[str, Any]:
    """Get tags assigned to a workflow.

    Args:
        workflow_id: The ID of the workflow

    Returns:
        Dictionary containing workflow tags from n8n API
    """
    return await client.get_workflow_tags(workflow_id)


@mcp.tool()
@handle_errors
async def update_workflow_tags(workflow_id: str, tag_ids: str) -> dict[str, Any]:
    """Update tags assigned to a workflow.

    Args:
        workflow_id: The ID of the workflow
        tag_ids: JSON array string of tag IDs (e.g., '["tag1", "tag2"]')

    Returns:
        Dictionary containing updated workflow with tags from n8n API
    """
    tag_list = json.loads(tag_ids)
    return await client.update_workflow_tags(workflow_id, tag_list)


@mcp.tool()
@handle_errors
async def deactivate_workflow(workflow_id: str) -> dict[str, Any]:
    """Deactivate a workflow in n8n.

    Args:
        workflow_id: The ID of the workflow to deactivate

    Returns:
        Dictionary containing deactivated workflow from n8n API
    """
    return await client.deactivate_workflow(workflow_id)


@mcp.tool()
@handle_errors
async def delete_execution(execution_id: str) -> dict[str, Any]:
    """Delete an execution history entry.

    Args:
        execution_id: The ID of the execution to delete

    Returns:
        Dictionary confirming deletion from n8n API
    """
    return await client.delete_execution(execution_id)


@mcp.tool()
@handle_errors
async def retry_execution(execution_id: str) -> dict[str, Any]:
    """Retry a failed execution.

    Args:
        execution_id: The ID of the execution to retry

    Returns:
        Dictionary containing new execution details from retry
    """
    return await client.retry_execution(execution_id)


@mcp.tool()
@handle_errors
async def list_credentials() -> dict[str, Any]:
    """List all credentials from n8n.

    Returns:
        Dictionary containing credentials list with id, name, and type for each credential.
        Credential data is redacted for security.

    Example response:
        {
            "data": [
                {
                    "id": "cred_123",
                    "name": "GitHub API Token",
                    "type": "githubApi"
                }
            ]
        }

    Note: Use this to discover existing credential IDs. When creating workflows,
    always reference credentials by ID (not name) to ensure correct credential is used.
    """
    return await client.list_credentials()


@mcp.tool()
@handle_errors
async def create_credential(credential_data: str) -> dict[str, Any]:
    """Create a new credential in n8n.

    Args:
        credential_data: JSON string containing credential definition with required fields:
            - name (str): Credential name
            - type (str): Credential type (e.g., 'githubApi', 'slackApi')
            - data (dict): Credential data specific to the type

    Returns:
        Dictionary containing created credential details including ID

    Example credential_data:
        {
            "name": "My GitHub Credential",
            "type": "githubApi",
            "data": {
                "accessToken": "ghp_xxxxxxxxxxxx"
            }
        }
    """
    credential_dict = json.loads(credential_data)
    return await client.create_credential(credential_dict)


@mcp.tool()
@handle_errors
async def update_credential(credential_id: str, credential_data: str) -> dict[str, Any]:
    """Update an existing credential in n8n.

    Args:
        credential_id: The ID of the credential to update
        credential_data: JSON string with credential fields to update (partial or complete)

    Returns:
        Dictionary containing updated credential details
    """
    credential_dict = json.loads(credential_data)
    return await client.update_credential(credential_id, credential_dict)


@mcp.tool()
@handle_errors
async def delete_credential(credential_id: str) -> dict[str, Any]:
    """Delete a credential from n8n.

    Args:
        credential_id: The ID of the credential to delete

    Returns:
        Dictionary confirming deletion or error details
    """
    return await client.delete_credential(credential_id)


@mcp.tool()
@handle_errors
async def get_credential_schema(credential_type_name: str) -> dict[str, Any]:
    """Get schema for a credential type.

    Args:
        credential_type_name: Name of credential type (e.g., 'githubApi', 'slackApi')

    Returns:
        Dictionary containing credential schema definition from n8n API
    """
    return await client.get_credential_schema(credential_type_name)


@mcp.tool()
@handle_errors
async def transfer_credential(credential_id: str, destination_project_id: str) -> dict[str, Any]:
    """Transfer a credential to a different project.

    Args:
        credential_id: The ID of the credential to transfer
        destination_project_id: The ID of the destination project

    Returns:
        Dictionary containing updated credential from n8n API
    """
    return await client.transfer_credential(credential_id, destination_project_id)


@mcp.tool()
@handle_errors
async def list_tags() -> dict[str, Any]:
    """List all tags from n8n.

    Returns:
        Dictionary containing list of tags from n8n API
    """
    return await client.list_tags()


@mcp.tool()
@handle_errors
async def create_tag(tag_data: str) -> dict[str, Any]:
    """Create a new tag in n8n.

    Args:
        tag_data: JSON string containing tag definition with required fields:
            - name (str): Tag name

    Returns:
        Dictionary containing created tag details including ID

    Example tag_data:
        {
            "name": "Production"
        }
    """
    tag_dict = json.loads(tag_data)
    return await client.create_tag(tag_dict)


@mcp.tool()
@handle_errors
async def get_tag(tag_id: str) -> dict[str, Any]:
    """Get a specific tag by ID.

    Args:
        tag_id: The ID of the tag to retrieve

    Returns:
        Dictionary containing tag details from n8n API
    """
    return await client.get_tag(tag_id)


@mcp.tool()
@handle_errors
async def update_tag(tag_id: str, tag_data: str) -> dict[str, Any]:
    """Update an existing tag in n8n.

    Args:
        tag_id: The ID of the tag to update
        tag_data: JSON string with tag fields to update (partial or complete)

    Returns:
        Dictionary containing updated tag details
    """
    tag_dict = json.loads(tag_data)
    return await client.update_tag(tag_id, tag_dict)


@mcp.tool()
@handle_errors
async def delete_tag(tag_id: str) -> dict[str, Any]:
    """Delete a tag from n8n.

    Args:
        tag_id: The ID of the tag to delete

    Returns:
        Dictionary confirming deletion or error details
    """
    return await client.delete_tag(tag_id)


def main() -> None:
    """Entry point for the n8n MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
