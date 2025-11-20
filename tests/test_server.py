"""
Tests for n8n MCP server.

Version: 0.1.0
Created: 2025-11-20
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from n8n_mcp.client import N8nClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test N8nClient initialization with base URL and API key."""
    client = N8nClient(
        base_url="https://n8n-backend.homelab.com", api_key="test_key"
    )
    assert client.base_url == "https://n8n-backend.homelab.com"
    assert client.api_key == "test_key"
    assert client.client.headers["X-N8N-API-KEY"] == "test_key"
    await client.close()


@pytest.mark.asyncio
async def test_authentication_header():
    """Test that API key is included in request headers."""
    client = N8nClient(
        base_url="https://n8n-backend.homelab.com", api_key="test_api_key"
    )
    assert "X-N8N-API-KEY" in client.client.headers
    assert client.client.headers["X-N8N-API-KEY"] == "test_api_key"
    await client.close()


@pytest.mark.asyncio
async def test_list_workflows_success():
    """Test listing workflows with successful response."""
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "1", "name": "Test Workflow"}]
        }
        mock_request.return_value = mock_response

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
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

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
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

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
        result = await client.execute_workflow(
            "workflow-123", {"input": "test"}
        )

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

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
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

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
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

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
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

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
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

        client = N8nClient(
            base_url="https://n8n-backend.homelab.com", api_key="test_key"
        )
        result = await client.list_workflows()

        assert "error" in result
        assert result["error"] == "Network error"
        await client.close()
