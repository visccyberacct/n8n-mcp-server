"""
n8n MCP Server - FastMCP server for n8n workflow automation.

Version: 0.1.0
Created: 2025-11-20
"""

import os
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from .client import N8nClient

# Initialize FastMCP server
mcp = FastMCP("n8n-api")

# Initialize n8n client from environment
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://n8n-backend.homelab.com")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

if not N8N_API_KEY:
    raise ValueError("N8N_API_KEY environment variable is required")

client = N8nClient(base_url=N8N_BASE_URL, api_key=N8N_API_KEY)


@mcp.tool()
async def list_workflows() -> Dict[str, Any]:
    """List all workflows from n8n.

    Returns:
        Dictionary containing workflows data from n8n API
    """
    try:
        result = await client.list_workflows()
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get a specific workflow by ID.

    Args:
        workflow_id: The ID of the workflow to retrieve

    Returns:
        Dictionary containing workflow details from n8n API
    """
    try:
        result = await client.get_workflow(workflow_id)
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def execute_workflow(
    workflow_id: str, data: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a workflow by ID.

    Args:
        workflow_id: The ID of the workflow to execute
        data: Optional JSON string with input data for the workflow

    Returns:
        Dictionary containing execution result from n8n API
    """
    try:
        import json

        workflow_data = json.loads(data) if data else None
        result = await client.execute_workflow(workflow_id, workflow_data)
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_executions(
    workflow_id: Optional[str] = None, limit: int = 20
) -> Dict[str, Any]:
    """List workflow execution history.

    Args:
        workflow_id: Optional workflow ID to filter executions
        limit: Maximum number of executions to return (default: 20)

    Returns:
        Dictionary containing executions list from n8n API
    """
    try:
        result = await client.get_executions(workflow_id, limit)
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_execution(execution_id: str) -> Dict[str, Any]:
    """Get specific execution details by ID.

    Args:
        execution_id: The ID of the execution to retrieve

    Returns:
        Dictionary containing execution details from n8n API
    """
    try:
        result = await client.get_execution(execution_id)
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def activate_workflow(workflow_id: str, active: bool) -> Dict[str, Any]:
    """Activate or deactivate a workflow.

    Args:
        workflow_id: The ID of the workflow to activate/deactivate
        active: True to activate, False to deactivate

    Returns:
        Dictionary containing updated workflow from n8n API
    """
    try:
        result = await client.activate_workflow(workflow_id, active)
        return result
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
