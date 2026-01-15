"""
n8n MCP Server - FastMCP server for n8n workflow automation.

Version: 0.1.0
Created: 2025-11-20
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import N8nClient
from .utils import handle_errors
from .validator import FORBIDDEN_FIELDS
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


@mcp.tool()
@handle_errors
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
async def get_workflow_health(workflow_id: str, execution_limit: int = 20) -> dict[str, Any]:
    """Get health status and metrics for a workflow.

    Analyzes recent executions to compute health metrics including:
    - Health status (healthy/degraded/unhealthy/unknown)
    - Success rate percentage
    - Execution counts (total, success, failed)
    - Average execution duration
    - Issues and recommendations

    Health Status Thresholds:
    - healthy: >95% success rate
    - degraded: 80-95% success rate
    - unhealthy: <80% success rate
    - unknown: No execution history

    Args:
        workflow_id: The ID of the workflow to analyze
        execution_limit: Number of recent executions to analyze (default: 20)

    Returns:
        Dictionary containing health metrics:
        - workflow_id (str): The workflow ID
        - workflow_name (str): The workflow name
        - health_status (str): "healthy", "degraded", "unhealthy", or "unknown"
        - success_rate (float): Percentage of successful executions (0-100)
        - total_executions (int): Number of executions analyzed
        - successful_executions (int): Number of successful executions
        - failed_executions (int): Number of failed executions
        - avg_duration_seconds (float|null): Average execution duration
        - issues (list): List of identified issues
        - recommendations (list): List of recommendations

    Example response:
        {
            "workflow_id": "abc123",
            "workflow_name": "Daily Backup",
            "health_status": "degraded",
            "success_rate": 85.0,
            "total_executions": 20,
            "successful_executions": 17,
            "failed_executions": 3,
            "avg_duration_seconds": 12.5,
            "issues": ["3 failed executions in recent history"],
            "recommendations": ["Review failed execution logs to identify root cause"]
        }
    """
    # Get workflow details
    workflow = await client.get_workflow(workflow_id)
    if "error" in workflow:
        return workflow

    workflow_name = workflow.get("name", "Unknown")

    # Get recent executions
    executions_response = await client.get_executions(workflow_id, execution_limit)
    if "error" in executions_response:
        return executions_response

    executions = executions_response.get("data", [])

    # Initialize metrics
    issues: list[str] = []
    recommendations: list[str] = []

    # Handle no execution history
    if not executions:
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "health_status": "unknown",
            "success_rate": None,
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_duration_seconds": None,
            "issues": ["No execution history available"],
            "recommendations": ["Execute the workflow to establish baseline metrics"],
        }

    # Calculate metrics
    total = len(executions)
    # Successful: finished with success status (or no error status)
    successful = sum(1 for e in executions if e.get("finished") and e.get("status") != "error")
    # Failed: has error status or was stopped without finishing
    failed = sum(
        1
        for e in executions
        if e.get("status") == "error" or (e.get("stoppedAt") and not e.get("finished"))
    )
    # Adjust for executions that are still running or have unknown status
    running = total - successful - failed

    # Calculate success rate based on completed executions
    completed = successful + failed
    if completed > 0:
        success_rate = (successful / completed) * 100
    else:
        success_rate = 100.0 if running == total else 0.0

    # Calculate average duration
    durations = []
    for execution in executions:
        started = execution.get("startedAt")
        stopped = execution.get("stoppedAt")
        if started and stopped:
            # Parse ISO timestamps and calculate duration
            try:
                start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                stop_dt = datetime.fromisoformat(stopped.replace("Z", "+00:00"))
                duration = (stop_dt - start_dt).total_seconds()
                if duration >= 0:
                    durations.append(duration)
            except (ValueError, TypeError):
                pass

    avg_duration = sum(durations) / len(durations) if durations else None

    # Determine health status
    if completed == 0:
        health_status = "unknown"
        issues.append("No completed executions to analyze")
    elif success_rate > 95:
        health_status = "healthy"
    elif success_rate >= 80:
        health_status = "degraded"
        issues.append(f"{failed} failed executions in recent history")
        recommendations.append("Review failed execution logs to identify root cause")
    else:
        health_status = "unhealthy"
        issues.append(f"High failure rate: {failed} of {completed} executions failed")
        recommendations.append("Investigate workflow configuration and external dependencies")
        recommendations.append("Consider disabling workflow until issues are resolved")

    # Additional checks
    if running > 0:
        issues.append(f"{running} executions currently running or in unknown state")

    if not workflow.get("active"):
        issues.append("Workflow is currently inactive")
        recommendations.append("Activate workflow if it should be running")

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "health_status": health_status,
        "success_rate": round(success_rate, 1),
        "total_executions": total,
        "successful_executions": successful,
        "failed_executions": failed,
        "avg_duration_seconds": round(avg_duration, 2) if avg_duration else None,
        "issues": issues,
        "recommendations": recommendations,
    }


@mcp.tool()
@handle_errors
async def clone_workflow(
    source_workflow_id: str,
    new_name: str,
    activate: bool = False,
) -> dict[str, Any]:
    """Clone an existing workflow with automatic field cleanup.

    Creates a copy of a workflow, automatically removing read-only fields
    that would cause API errors. Credentials are preserved (same IDs).

    This is useful for:
    - Creating workflow templates
    - Testing workflow modifications safely
    - Duplicating workflows across environments

    Args:
        source_workflow_id: The ID of the workflow to clone
        new_name: Name for the cloned workflow
        activate: Whether to activate the cloned workflow (default: False)

    Returns:
        Dictionary containing:
        - cloned_workflow: The newly created workflow details
        - source_workflow_id: The original workflow ID
        - fields_removed: List of fields that were automatically removed

    Example:
        clone_workflow("abc123", "My Workflow - Copy", activate=False)

    Note:
        - The cloned workflow gets a new ID
        - Execution history is NOT copied
        - Tags are NOT copied (use update_workflow_tags to add tags)
        - Credentials are preserved (references same credential IDs)
    """
    # Get source workflow
    source = await client.get_workflow(source_workflow_id)
    if "error" in source:
        return source

    # Track removed fields for transparency
    fields_removed: list[str] = []

    # Create clean workflow data
    clean_workflow: dict[str, Any] = {}

    # Copy allowed fields
    allowed_fields = {"name", "nodes", "connections", "settings"}
    for field in allowed_fields:
        if field in source:
            clean_workflow[field] = source[field]

    # Track which forbidden fields were present and removed
    for field in FORBIDDEN_FIELDS:
        if field in source:
            fields_removed.append(field)

    # Set new name
    clean_workflow["name"] = new_name

    # Ensure settings exist with recommended executionOrder
    if "settings" not in clean_workflow:
        clean_workflow["settings"] = {"executionOrder": "v1"}
    elif "executionOrder" not in clean_workflow.get("settings", {}):
        clean_workflow["settings"]["executionOrder"] = "v1"

    # Create the cloned workflow
    result = await client.create_workflow(clean_workflow)
    if "error" in result:
        return result

    # Optionally activate
    if activate and "id" in result:
        activation_result = await client.activate_workflow(result["id"], True)
        if "error" not in activation_result:
            result = activation_result

    return {
        "cloned_workflow": result,
        "source_workflow_id": source_workflow_id,
        "fields_removed": sorted(fields_removed),
    }


def main() -> None:
    """Entry point for the n8n MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
