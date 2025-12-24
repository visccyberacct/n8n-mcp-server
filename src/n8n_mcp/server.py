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
async def list_workflows() -> dict[str, Any]:
    """List all workflows from n8n.

    Returns:
        Dictionary containing workflows data from n8n API
    """
    return await client.list_workflows()


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
async def create_workflow(workflow_data: str) -> dict[str, Any]:
    """Create a new workflow in n8n.

    Args:
        workflow_data: JSON string containing workflow definition with required fields:
            - name (str): Workflow name
            - nodes (list): List of workflow nodes, each with:
                - id (str): Unique node identifier
                - name (str): Node display name
                - type (str): Node type (e.g., "n8n-nodes-base.start")
                - typeVersion (int): Node type version
                - position (list): [x, y] coordinates
            - connections (dict): Node connections (use {} for single-node workflows)
            - settings (dict, optional): Workflow settings
            - active (bool, optional): Whether to activate immediately (default: false)

    Returns:
        Dictionary containing created workflow details including ID

    Example workflow_data:
        {
            "name": "My Workflow",
            "nodes": [
                {
                    "id": "node-1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300]
                }
            ],
            "connections": {},
            "active": false
        }
    """
    workflow_dict = json.loads(workflow_data)
    return await client.create_workflow(workflow_dict)


@mcp.tool()
@handle_errors
async def update_workflow(workflow_id: str, workflow_data: str) -> dict[str, Any]:
    """Update an existing workflow in n8n.

    Args:
        workflow_id: The ID of the workflow to update
        workflow_data: JSON string with workflow fields to update (partial or complete)

    Returns:
        Dictionary containing updated workflow details

    Example workflow_data:
        {
            "name": "Updated Workflow Name",
            "active": true
        }
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


def main() -> None:
    """Entry point for the n8n MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
