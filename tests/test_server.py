"""
Tests for n8n MCP server.

Version: 0.1.0
Created: 2025-11-20
"""

from unittest.mock import MagicMock, patch

import pytest

from n8n_mcp.client import N8nClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test N8nClient initialization with base URL and API key."""
    client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
    assert client.base_url == "https://n8n-backend.homelab.com"
    assert client.api_key == "test_key"
    assert client.client.headers["X-N8N-API-KEY"] == "test_key"
    await client.close()


@pytest.mark.asyncio
async def test_authentication_header():
    """Test that API key is included in request headers."""
    client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_api_key")
    assert "X-N8N-API-KEY" in client.client.headers
    assert client.client.headers["X-N8N-API-KEY"] == "test_api_key"
    await client.close()


@pytest.mark.asyncio
async def test_list_workflows_success():
    """Test listing workflows with successful response."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "1", "name": "Test Workflow"}]}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.list_workflows()

        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "Test Workflow"
        await client.close()


@pytest.mark.asyncio
async def test_get_workflow_success():
    """Test getting specific workflow by ID."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "name": "My Workflow",
            "active": True,
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_workflow("123")

        assert result["id"] == "123"
        assert result["name"] == "My Workflow"
        assert result["active"] is True
        await client.close()


@pytest.mark.asyncio
async def test_execute_workflow_success():
    """Test executing workflow with data."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "executionId": "exec-123",
            "status": "running",
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.execute_workflow("workflow-123", {"input": "test"})

        assert result["executionId"] == "exec-123"
        assert result["status"] == "running"
        await client.close()


@pytest.mark.asyncio
async def test_get_executions_success():
    """Test listing workflow executions."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "exec-1", "status": "success"},
                {"id": "exec-2", "status": "failed"},
            ]
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_executions(limit=10)

        assert "data" in result
        assert len(result["data"]) == 2
        await client.close()


@pytest.mark.asyncio
async def test_get_execution_success():
    """Test getting specific execution by ID."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "exec-456",
            "status": "success",
            "data": {"result": "completed"},
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_execution("exec-456")

        assert result["id"] == "exec-456"
        assert result["status"] == "success"
        await client.close()


@pytest.mark.asyncio
async def test_activate_workflow_success():
    """Test activating/deactivating workflow."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "workflow-789",
            "active": True,
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.activate_workflow("workflow-789", True)

        assert result["id"] == "workflow-789"
        assert result["active"] is True
        await client.close()


@pytest.mark.asyncio
async def test_api_error_handling():
    """Test error handling for HTTP errors."""
    with patch("httpx.AsyncClient.request") as mock_request:
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_workflow("nonexistent")

        assert "error" in result
        assert "HTTP 404" in result["error"]
        await client.close()


@pytest.mark.asyncio
async def test_network_error_handling():
    """Test error handling for network errors."""
    with patch("httpx.AsyncClient.request") as mock_request:
        import httpx

        mock_request.side_effect = httpx.RequestError("Connection failed")

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.list_workflows()

        assert "error" in result
        assert result["error"] == "Network error"
        await client.close()


# Additional Workflow Tests


@pytest.mark.asyncio
async def test_get_workflow_version():
    """Test getting a specific workflow version."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "workflow_123",
            "versionId": "v2",
            "name": "Test Workflow V2",
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_workflow_version("workflow_123", "v2")

        assert result["id"] == "workflow_123"
        assert result["versionId"] == "v2"
        await client.close()


@pytest.mark.asyncio
async def test_transfer_workflow():
    """Test transferring a workflow to a project."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "workflow_123",
            "projectId": "project_456",
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.transfer_workflow("workflow_123", "project_456")

        assert result["id"] == "workflow_123"
        assert result["projectId"] == "project_456"
        await client.close()


@pytest.mark.asyncio
async def test_get_workflow_tags():
    """Test getting workflow tags."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tags": ["tag1", "tag2"]}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_workflow_tags("workflow_123")

        assert "tags" in result
        assert len(result["tags"]) == 2
        await client.close()


@pytest.mark.asyncio
async def test_update_workflow_tags():
    """Test updating workflow tags."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "workflow_123",
            "tags": ["tag1", "tag2"],
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.update_workflow_tags("workflow_123", ["tag1", "tag2"])

        assert result["id"] == "workflow_123"
        assert result["tags"] == ["tag1", "tag2"]
        await client.close()


@pytest.mark.asyncio
async def test_deactivate_workflow():
    """Test deactivating a workflow."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "workflow_123", "active": False}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.deactivate_workflow("workflow_123")

        assert result["id"] == "workflow_123"
        assert result["active"] is False
        await client.close()


# Execution Tests


@pytest.mark.asyncio
async def test_delete_execution():
    """Test deleting an execution."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.delete_execution("exec_123")

        assert result["success"] is True
        await client.close()


@pytest.mark.asyncio
async def test_retry_execution():
    """Test retrying a failed execution."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "exec_456",
            "status": "running",
            "retriedFrom": "exec_123",
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.retry_execution("exec_123")

        assert result["id"] == "exec_456"
        assert result["retriedFrom"] == "exec_123"
        await client.close()


# Credential Tests


@pytest.mark.asyncio
async def test_create_credential():
    """Test creating a credential."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cred_123",
            "name": "My GitHub Cred",
            "type": "githubApi",
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.create_credential(
            {"name": "My GitHub Cred", "type": "githubApi", "data": {}}
        )

        assert result["id"] == "cred_123"
        assert result["type"] == "githubApi"
        await client.close()


@pytest.mark.asyncio
async def test_update_credential():
    """Test updating a credential."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cred_123",
            "name": "Updated GitHub Cred",
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.update_credential("cred_123", {"name": "Updated GitHub Cred"})

        assert result["id"] == "cred_123"
        assert result["name"] == "Updated GitHub Cred"
        await client.close()


@pytest.mark.asyncio
async def test_delete_credential():
    """Test deleting a credential."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.delete_credential("cred_123")

        assert result["success"] is True
        await client.close()


@pytest.mark.asyncio
async def test_get_credential_schema():
    """Test getting credential schema."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "type": "githubApi",
            "properties": {"accessToken": {"type": "string"}},
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_credential_schema("githubApi")

        assert result["type"] == "githubApi"
        assert "properties" in result
        await client.close()


@pytest.mark.asyncio
async def test_transfer_credential():
    """Test transferring a credential to a project."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cred_123",
            "projectId": "project_456",
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.transfer_credential("cred_123", "project_456")

        assert result["id"] == "cred_123"
        assert result["projectId"] == "project_456"
        await client.close()


# Tag Tests


@pytest.mark.asyncio
async def test_list_tags():
    """Test listing all tags."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "tag1", "name": "Production"},
                {"id": "tag2", "name": "Development"},
            ]
        }
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.list_tags()

        assert "data" in result
        assert len(result["data"]) == 2
        await client.close()


@pytest.mark.asyncio
async def test_create_tag():
    """Test creating a tag."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "tag_123", "name": "Production"}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.create_tag({"name": "Production"})

        assert result["id"] == "tag_123"
        assert result["name"] == "Production"
        await client.close()


@pytest.mark.asyncio
async def test_get_tag():
    """Test getting a specific tag."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "tag_123", "name": "Production"}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_tag("tag_123")

        assert result["id"] == "tag_123"
        assert result["name"] == "Production"
        await client.close()


@pytest.mark.asyncio
async def test_update_tag():
    """Test updating a tag."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "tag_123", "name": "Prod"}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.update_tag("tag_123", {"name": "Prod"})

        assert result["id"] == "tag_123"
        assert result["name"] == "Prod"
        await client.close()


@pytest.mark.asyncio
async def test_delete_tag():
    """Test deleting a tag."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.delete_tag("tag_123")

        assert result["success"] is True
        await client.close()


# Error Handling Tests for New Endpoints


@pytest.mark.asyncio
async def test_credential_http_error():
    """Test credential operations with HTTP error."""
    with patch("httpx.AsyncClient.request") as mock_request:
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Credential not found"
        mock_request.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.get_credential_schema("nonexistent")

        assert "error" in result
        assert "HTTP 404" in result["error"]
        await client.close()


@pytest.mark.asyncio
async def test_tag_http_error():
    """Test tag operations with HTTP error."""
    with patch("httpx.AsyncClient.request") as mock_request:
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_request.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=mock_response
        )

        client = N8nClient(base_url="https://n8n-backend.homelab.com", api_key="test_key")
        result = await client.delete_tag("protected_tag")

        assert "error" in result
        assert "HTTP 403" in result["error"]
        await client.close()
