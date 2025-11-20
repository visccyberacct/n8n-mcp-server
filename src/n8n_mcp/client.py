"""
n8n API Client - Async HTTP client for n8n REST API.

Version: 0.1.0
Created: 2025-11-20
"""

import httpx
from typing import Optional, Dict, Any


class N8nClient:
    """Async HTTP client for n8n REST API."""

    def __init__(self, base_url: str, api_key: str):
        """Initialize the n8n API client.

        Args:
            base_url: Base URL of the n8n instance (e.g., https://n8n-backend.homelab.com)
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-N8N-API-KEY": self.api_key},
            timeout=30.0,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Common request handler with error handling.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response as dict

        Raises:
            httpx.HTTPError: On HTTP errors
            httpx.RequestError: On network errors
        """
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}",
                "message": str(e),
                "details": e.response.text,
            }
        except httpx.RequestError as e:
            return {"error": "Network error", "message": str(e)}
        except Exception as e:
            return {"error": "Unknown error", "message": str(e)}

    async def list_workflows(self) -> Dict[str, Any]:
        """Get all workflows from n8n.

        Returns:
            Response data with workflows list
        """
        return await self._request("GET", "/api/v1/workflows")

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get specific workflow by ID.

        Args:
            workflow_id: The workflow ID

        Returns:
            Response data with workflow details
        """
        return await self._request("GET", f"/api/v1/workflows/{workflow_id}")

    async def execute_workflow(
        self, workflow_id: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Trigger workflow execution.

        Args:
            workflow_id: The workflow ID to execute
            data: Optional data to pass to the workflow

        Returns:
            Response data with execution details
        """
        json_data = data if data is not None else {}
        return await self._request(
            "POST", f"/api/v1/workflows/{workflow_id}/execute", json=json_data
        )

    async def get_executions(
        self, workflow_id: Optional[str] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """List workflow execution history.

        Args:
            workflow_id: Optional workflow ID to filter executions
            limit: Maximum number of executions to return (default: 20)

        Returns:
            Response data with executions list
        """
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        return await self._request("GET", "/api/v1/executions", params=params)

    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get specific execution details by ID.

        Args:
            execution_id: The execution ID

        Returns:
            Response data with execution details
        """
        return await self._request("GET", f"/api/v1/executions/{execution_id}")

    async def activate_workflow(
        self, workflow_id: str, active: bool
    ) -> Dict[str, Any]:
        """Activate or deactivate a workflow.

        Args:
            workflow_id: The workflow ID
            active: True to activate, False to deactivate

        Returns:
            Response data with updated workflow
        """
        return await self._request(
            "PATCH", f"/api/v1/workflows/{workflow_id}", json={"active": active}
        )
