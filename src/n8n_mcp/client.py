"""
n8n API Client - Async HTTP client for n8n REST API.

Version: 0.1.0
Created: 2025-11-20
"""

from typing import Any

import httpx


class N8nClient:
    """Async HTTP client for n8n REST API."""

    def __init__(self, base_url: str, api_key: str, verify_ssl: bool = False):
        """Initialize the n8n API client.

        Args:
            base_url: Base URL of the n8n instance (e.g., https://n8n.homelab.com)
            api_key: API key for authentication
            verify_ssl: Whether to verify SSL certificates (default: False for homelab)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-N8N-API-KEY": self.api_key},
            timeout=30.0,
            verify=verify_ssl,
        )

    async def __aenter__(self) -> "N8nClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Common request handler with error handling.

        This method catches all exceptions and returns error dictionaries
        instead of raising exceptions, making responses consistent and
        MCP-friendly.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response dict on success, or error dict with 'error' key on failure.
            Error dict format: {"error": "error_type", "message": "details", ...}
        """
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
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

    async def list_workflows(self) -> dict[str, Any]:
        """Get all workflows from n8n.

        Returns:
            Response data with workflows list
        """
        return await self._request("GET", "/api/v1/workflows")

    async def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Get specific workflow by ID.

        Args:
            workflow_id: The workflow ID

        Returns:
            Response data with workflow details
        """
        return await self._request("GET", f"/api/v1/workflows/{workflow_id}")

    async def execute_workflow(
        self, workflow_id: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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
        self, workflow_id: str | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """List workflow execution history.

        Args:
            workflow_id: Optional workflow ID to filter executions
            limit: Maximum number of executions to return (default: 20)

        Returns:
            Response data with executions list
        """
        params: dict[str, str | int] = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        return await self._request("GET", "/api/v1/executions", params=params)

    async def get_execution(self, execution_id: str) -> dict[str, Any]:
        """Get specific execution details by ID.

        Args:
            execution_id: The execution ID

        Returns:
            Response data with execution details
        """
        return await self._request("GET", f"/api/v1/executions/{execution_id}")

    async def delete_execution(self, execution_id: str) -> dict[str, Any]:
        """Delete an execution history entry.

        Args:
            execution_id: The execution ID to delete

        Returns:
            Response data confirming deletion
        """
        return await self._request("DELETE", f"/api/v1/executions/{execution_id}")

    async def retry_execution(self, execution_id: str) -> dict[str, Any]:
        """Retry a failed execution.

        Args:
            execution_id: The execution ID to retry

        Returns:
            Response data with new execution details from retry
        """
        return await self._request("POST", f"/api/v1/executions/{execution_id}/retry")

    async def activate_workflow(self, workflow_id: str, active: bool) -> dict[str, Any]:
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

    async def create_workflow(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new workflow.

        Args:
            workflow_data: Workflow definition dictionary with required fields:
                - name (str): Workflow name
                - nodes (list): List of workflow nodes
                - connections (dict): Node connections
                - settings (dict, optional): Workflow settings
                - active (bool, optional): Whether to activate immediately

        Returns:
            Response data with created workflow details including ID

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
                "active": false,
                "settings": {}
            }
        """
        return await self._request("POST", "/api/v1/workflows", json=workflow_data)

    async def update_workflow(
        self, workflow_id: str, workflow_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing workflow.

        Args:
            workflow_id: The workflow ID to update
            workflow_data: Partial or complete workflow definition to update

        Returns:
            Response data with updated workflow details
        """
        return await self._request("PUT", f"/api/v1/workflows/{workflow_id}", json=workflow_data)

    async def delete_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Delete a workflow.

        Args:
            workflow_id: The workflow ID to delete

        Returns:
            Response data confirming deletion
        """
        return await self._request("DELETE", f"/api/v1/workflows/{workflow_id}")

    async def get_workflow_version(self, workflow_id: str, version_id: str) -> dict[str, Any]:
        """Get a specific version of a workflow.

        Args:
            workflow_id: The workflow ID
            version_id: The version ID to retrieve

        Returns:
            Response data with workflow version details
        """
        return await self._request("GET", f"/api/v1/workflows/{workflow_id}/{version_id}")

    async def transfer_workflow(
        self, workflow_id: str, destination_project_id: str
    ) -> dict[str, Any]:
        """Transfer a workflow to a different project.

        Args:
            workflow_id: The workflow ID to transfer
            destination_project_id: The ID of the destination project

        Returns:
            Response data with updated workflow
        """
        return await self._request(
            "PUT",
            f"/api/v1/workflows/{workflow_id}/transfer",
            json={"destinationProjectId": destination_project_id},
        )

    async def get_workflow_tags(self, workflow_id: str) -> dict[str, Any]:
        """Get tags assigned to a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Response data with workflow tags
        """
        return await self._request("GET", f"/api/v1/workflows/{workflow_id}/tags")

    async def update_workflow_tags(self, workflow_id: str, tag_ids: list[str]) -> dict[str, Any]:
        """Update tags assigned to a workflow.

        Args:
            workflow_id: The workflow ID
            tag_ids: List of tag IDs to assign to the workflow

        Returns:
            Response data with updated workflow tags
        """
        return await self._request(
            "PUT", f"/api/v1/workflows/{workflow_id}/tags", json={"tags": tag_ids}
        )

    async def deactivate_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Deactivate a workflow.

        Args:
            workflow_id: The workflow ID to deactivate

        Returns:
            Response data with deactivated workflow
        """
        return await self._request("POST", f"/api/v1/workflows/{workflow_id}/deactivate")

    # Credential Management

    async def list_credentials(self) -> dict[str, Any]:
        """List all credentials from n8n.

        Returns:
            Response data with list of credentials (id, name, type).
            Credential data is redacted for security.
        """
        return await self._request("GET", "/api/v1/credentials")

    async def create_credential(self, credential_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new credential.

        Args:
            credential_data: Credential definition dictionary with required fields:
                - name (str): Credential name
                - type (str): Credential type (e.g., 'githubApi', 'slackApi')
                - data (dict): Credential data specific to the type

        Returns:
            Response data with created credential details including ID
        """
        return await self._request("POST", "/api/v1/credentials", json=credential_data)

    async def update_credential(
        self, credential_id: str, credential_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing credential.

        Args:
            credential_id: The credential ID to update
            credential_data: Partial or complete credential definition to update

        Returns:
            Response data with updated credential details
        """
        return await self._request(
            "PATCH", f"/api/v1/credentials/{credential_id}", json=credential_data
        )

    async def delete_credential(self, credential_id: str) -> dict[str, Any]:
        """Delete a credential.

        Args:
            credential_id: The credential ID to delete

        Returns:
            Response data confirming deletion
        """
        return await self._request("DELETE", f"/api/v1/credentials/{credential_id}")

    async def get_credential_schema(self, credential_type_name: str) -> dict[str, Any]:
        """Get schema for a credential type.

        Args:
            credential_type_name: Name of credential type (e.g., 'githubApi', 'slackApi')

        Returns:
            Response data with credential schema definition
        """
        return await self._request("GET", f"/api/v1/credentials/schema/{credential_type_name}")

    async def transfer_credential(
        self, credential_id: str, destination_project_id: str
    ) -> dict[str, Any]:
        """Transfer a credential to a different project.

        Args:
            credential_id: The credential ID to transfer
            destination_project_id: The ID of the destination project

        Returns:
            Response data with updated credential
        """
        return await self._request(
            "PUT",
            f"/api/v1/credentials/{credential_id}/transfer",
            json={"destinationProjectId": destination_project_id},
        )

    # Tag Management

    async def list_tags(self) -> dict[str, Any]:
        """List all tags.

        Returns:
            Response data with list of tags
        """
        return await self._request("GET", "/api/v1/tags")

    async def create_tag(self, tag_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new tag.

        Args:
            tag_data: Tag definition dictionary with required fields:
                - name (str): Tag name

        Returns:
            Response data with created tag details including ID
        """
        return await self._request("POST", "/api/v1/tags", json=tag_data)

    async def get_tag(self, tag_id: str) -> dict[str, Any]:
        """Get a specific tag by ID.

        Args:
            tag_id: The tag ID

        Returns:
            Response data with tag details
        """
        return await self._request("GET", f"/api/v1/tags/{tag_id}")

    async def update_tag(self, tag_id: str, tag_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing tag.

        Args:
            tag_id: The tag ID to update
            tag_data: Partial or complete tag definition to update

        Returns:
            Response data with updated tag details
        """
        return await self._request("PUT", f"/api/v1/tags/{tag_id}", json=tag_data)

    async def delete_tag(self, tag_id: str) -> dict[str, Any]:
        """Delete a tag.

        Args:
            tag_id: The tag ID to delete

        Returns:
            Response data confirming deletion
        """
        return await self._request("DELETE", f"/api/v1/tags/{tag_id}")
