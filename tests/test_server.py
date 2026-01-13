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


# ============================================================================
# MCP Tool Wrapper Tests
# Tests for the server.py MCP tool functions that wrap client methods
# ============================================================================


@pytest.mark.asyncio
async def test_mcp_list_workflows():
    """Test list_workflows MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "list_workflows") as mock_method:
        mock_method.return_value = {"data": [{"id": "1"}]}
        result = await server.list_workflows()
        assert result == {"data": [{"id": "1"}]}
        mock_method.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_get_workflow():
    """Test get_workflow MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "get_workflow") as mock_method:
        mock_method.return_value = {"id": "123", "name": "Test"}
        result = await server.get_workflow("123")
        assert result == {"id": "123", "name": "Test"}
        mock_method.assert_called_once_with("123")


@pytest.mark.asyncio
async def test_mcp_execute_workflow():
    """Test execute_workflow MCP tool with JSON data."""
    from n8n_mcp import server

    with patch.object(server.client, "execute_workflow") as mock_method:
        mock_method.return_value = {"id": "exec_1"}
        result = await server.execute_workflow("wf_123", '{"input": "test"}')
        assert result == {"id": "exec_1"}
        mock_method.assert_called_once_with("wf_123", {"input": "test"})


@pytest.mark.asyncio
async def test_mcp_execute_workflow_no_data():
    """Test execute_workflow MCP tool without data."""
    from n8n_mcp import server

    with patch.object(server.client, "execute_workflow") as mock_method:
        mock_method.return_value = {"id": "exec_1"}
        result = await server.execute_workflow("wf_123", None)
        assert result == {"id": "exec_1"}
        mock_method.assert_called_once_with("wf_123", None)


@pytest.mark.asyncio
async def test_mcp_get_executions():
    """Test get_executions MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "get_executions") as mock_method:
        mock_method.return_value = {"data": []}
        result = await server.get_executions("wf_123", 10)
        assert result == {"data": []}
        mock_method.assert_called_once_with("wf_123", 10)


@pytest.mark.asyncio
async def test_mcp_get_execution():
    """Test get_execution MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "get_execution") as mock_method:
        mock_method.return_value = {"id": "exec_1"}
        result = await server.get_execution("exec_1")
        assert result == {"id": "exec_1"}
        mock_method.assert_called_once_with("exec_1")


@pytest.mark.asyncio
async def test_mcp_activate_workflow():
    """Test activate_workflow MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "activate_workflow") as mock_method:
        mock_method.return_value = {"active": True}
        result = await server.activate_workflow("wf_123", True)
        assert result == {"active": True}
        mock_method.assert_called_once_with("wf_123", True)


@pytest.mark.asyncio
async def test_mcp_create_workflow():
    """Test create_workflow MCP tool with JSON parsing."""
    from n8n_mcp import server

    with patch.object(server.client, "create_workflow") as mock_method:
        mock_method.return_value = {"id": "new_wf"}
        workflow_json = '{"name": "Test", "nodes": [], "connections": {}}'
        result = await server.create_workflow(workflow_json)
        assert result == {"id": "new_wf"}
        mock_method.assert_called_once_with({"name": "Test", "nodes": [], "connections": {}})


@pytest.mark.asyncio
async def test_mcp_update_workflow():
    """Test update_workflow MCP tool with JSON parsing."""
    from n8n_mcp import server

    with patch.object(server.client, "update_workflow") as mock_method:
        mock_method.return_value = {"id": "wf_123"}
        result = await server.update_workflow("wf_123", '{"name": "Updated"}')
        assert result == {"id": "wf_123"}
        mock_method.assert_called_once_with("wf_123", {"name": "Updated"})


@pytest.mark.asyncio
async def test_mcp_delete_workflow():
    """Test delete_workflow MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "delete_workflow") as mock_method:
        mock_method.return_value = {"success": True}
        result = await server.delete_workflow("wf_123")
        assert result == {"success": True}
        mock_method.assert_called_once_with("wf_123")


@pytest.mark.asyncio
async def test_mcp_get_workflow_version():
    """Test get_workflow_version MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "get_workflow_version") as mock_method:
        mock_method.return_value = {"versionId": "v1"}
        result = await server.get_workflow_version("wf_123", "v1")
        assert result == {"versionId": "v1"}
        mock_method.assert_called_once_with("wf_123", "v1")


@pytest.mark.asyncio
async def test_mcp_transfer_workflow():
    """Test transfer_workflow MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "transfer_workflow") as mock_method:
        mock_method.return_value = {"projectId": "proj_2"}
        result = await server.transfer_workflow("wf_123", "proj_2")
        assert result == {"projectId": "proj_2"}
        mock_method.assert_called_once_with("wf_123", "proj_2")


@pytest.mark.asyncio
async def test_mcp_get_workflow_tags():
    """Test get_workflow_tags MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "get_workflow_tags") as mock_method:
        mock_method.return_value = {"tags": []}
        result = await server.get_workflow_tags("wf_123")
        assert result == {"tags": []}
        mock_method.assert_called_once_with("wf_123")


@pytest.mark.asyncio
async def test_mcp_update_workflow_tags():
    """Test update_workflow_tags MCP tool with JSON parsing."""
    from n8n_mcp import server

    with patch.object(server.client, "update_workflow_tags") as mock_method:
        mock_method.return_value = {"tags": ["tag1", "tag2"]}
        result = await server.update_workflow_tags("wf_123", '["tag1", "tag2"]')
        assert result == {"tags": ["tag1", "tag2"]}
        mock_method.assert_called_once_with("wf_123", ["tag1", "tag2"])


@pytest.mark.asyncio
async def test_mcp_deactivate_workflow():
    """Test deactivate_workflow MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "deactivate_workflow") as mock_method:
        mock_method.return_value = {"active": False}
        result = await server.deactivate_workflow("wf_123")
        assert result == {"active": False}
        mock_method.assert_called_once_with("wf_123")


@pytest.mark.asyncio
async def test_mcp_delete_execution():
    """Test delete_execution MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "delete_execution") as mock_method:
        mock_method.return_value = {"success": True}
        result = await server.delete_execution("exec_123")
        assert result == {"success": True}
        mock_method.assert_called_once_with("exec_123")


@pytest.mark.asyncio
async def test_mcp_retry_execution():
    """Test retry_execution MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "retry_execution") as mock_method:
        mock_method.return_value = {"id": "exec_retry"}
        result = await server.retry_execution("exec_123")
        assert result == {"id": "exec_retry"}
        mock_method.assert_called_once_with("exec_123")


@pytest.mark.asyncio
async def test_mcp_create_credential():
    """Test create_credential MCP tool with JSON parsing."""
    from n8n_mcp import server

    with patch.object(server.client, "create_credential") as mock_method:
        mock_method.return_value = {"id": "cred_1"}
        cred_json = '{"name": "Test Cred", "type": "githubApi", "data": {}}'
        result = await server.create_credential(cred_json)
        assert result == {"id": "cred_1"}
        mock_method.assert_called_once_with({"name": "Test Cred", "type": "githubApi", "data": {}})


@pytest.mark.asyncio
async def test_mcp_update_credential():
    """Test update_credential MCP tool with JSON parsing."""
    from n8n_mcp import server

    with patch.object(server.client, "update_credential") as mock_method:
        mock_method.return_value = {"id": "cred_1"}
        result = await server.update_credential("cred_1", '{"name": "Updated"}')
        assert result == {"id": "cred_1"}
        mock_method.assert_called_once_with("cred_1", {"name": "Updated"})


@pytest.mark.asyncio
async def test_mcp_delete_credential():
    """Test delete_credential MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "delete_credential") as mock_method:
        mock_method.return_value = {"success": True}
        result = await server.delete_credential("cred_1")
        assert result == {"success": True}
        mock_method.assert_called_once_with("cred_1")


@pytest.mark.asyncio
async def test_mcp_get_credential_schema():
    """Test get_credential_schema MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "get_credential_schema") as mock_method:
        mock_method.return_value = {"schema": {}}
        result = await server.get_credential_schema("githubApi")
        assert result == {"schema": {}}
        mock_method.assert_called_once_with("githubApi")


@pytest.mark.asyncio
async def test_mcp_transfer_credential():
    """Test transfer_credential MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "transfer_credential") as mock_method:
        mock_method.return_value = {"projectId": "proj_2"}
        result = await server.transfer_credential("cred_1", "proj_2")
        assert result == {"projectId": "proj_2"}
        mock_method.assert_called_once_with("cred_1", "proj_2")


@pytest.mark.asyncio
async def test_mcp_list_tags():
    """Test list_tags MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "list_tags") as mock_method:
        mock_method.return_value = {"data": []}
        result = await server.list_tags()
        assert result == {"data": []}
        mock_method.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_create_tag():
    """Test create_tag MCP tool with JSON parsing."""
    from n8n_mcp import server

    with patch.object(server.client, "create_tag") as mock_method:
        mock_method.return_value = {"id": "tag_1"}
        result = await server.create_tag('{"name": "Production"}')
        assert result == {"id": "tag_1"}
        mock_method.assert_called_once_with({"name": "Production"})


@pytest.mark.asyncio
async def test_mcp_get_tag():
    """Test get_tag MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "get_tag") as mock_method:
        mock_method.return_value = {"id": "tag_1"}
        result = await server.get_tag("tag_1")
        assert result == {"id": "tag_1"}
        mock_method.assert_called_once_with("tag_1")


@pytest.mark.asyncio
async def test_mcp_update_tag():
    """Test update_tag MCP tool with JSON parsing."""
    from n8n_mcp import server

    with patch.object(server.client, "update_tag") as mock_method:
        mock_method.return_value = {"id": "tag_1"}
        result = await server.update_tag("tag_1", '{"name": "Prod"}')
        assert result == {"id": "tag_1"}
        mock_method.assert_called_once_with("tag_1", {"name": "Prod"})


@pytest.mark.asyncio
async def test_mcp_delete_tag():
    """Test delete_tag MCP tool."""
    from n8n_mcp import server

    with patch.object(server.client, "delete_tag") as mock_method:
        mock_method.return_value = {"success": True}
        result = await server.delete_tag("tag_1")
        assert result == {"success": True}
        mock_method.assert_called_once_with("tag_1")


@pytest.mark.asyncio
async def test_mcp_tool_error_handling():
    """Test that @handle_errors decorator catches exceptions in MCP tools."""
    from n8n_mcp import server

    with patch.object(server.client, "list_workflows") as mock_method:
        mock_method.side_effect = Exception("Test error")
        result = await server.list_workflows()
        assert "error" in result
        assert result["error"] == "Test error"


# ============================================================================
# Model Tests
# Tests for Pydantic models in models.py
# ============================================================================


def test_workflow_node_model():
    """Test WorkflowNode model instantiation."""
    from n8n_mcp.models import WorkflowNode

    node = WorkflowNode(
        id="node-1",
        name="Start",
        type="n8n-nodes-base.start",
        typeVersion=1,
        position=[250.0, 300.0],
    )
    assert node.id == "node-1"
    assert node.name == "Start"
    assert node.type == "n8n-nodes-base.start"
    assert node.typeVersion == 1
    assert node.position == [250.0, 300.0]


def test_workflow_settings_model():
    """Test WorkflowSettings model instantiation."""
    from n8n_mcp.models import WorkflowSettings

    settings = WorkflowSettings(
        saveExecutionProgress=True,
        saveManualExecutions=True,
        executionTimeout=60,
    )
    assert settings.saveExecutionProgress is True
    assert settings.saveManualExecutions is True
    assert settings.executionTimeout == 60


def test_workflow_model():
    """Test Workflow model instantiation."""
    from n8n_mcp.models import Workflow, WorkflowNode

    workflow = Workflow(
        name="Test Workflow",
        nodes=[
            WorkflowNode(
                id="node-1",
                name="Start",
                type="n8n-nodes-base.start",
                typeVersion=1,
                position=[250.0, 300.0],
            )
        ],
        connections={},
        active=False,
    )
    assert workflow.name == "Test Workflow"
    assert len(workflow.nodes) == 1
    assert workflow.nodes[0].name == "Start"
    assert workflow.active is False


def test_execution_data_model():
    """Test ExecutionData model instantiation."""
    from n8n_mcp.models import ExecutionData

    exec_data = ExecutionData(
        resultData={"output": "test"},
        executionData={"metadata": "info"},
    )
    assert exec_data.resultData == {"output": "test"}
    assert exec_data.executionData == {"metadata": "info"}


def test_execution_model():
    """Test Execution model instantiation."""
    from n8n_mcp.models import Execution, ExecutionData

    execution = Execution(
        id="exec-123",
        workflowId="wf-456",
        mode="manual",
        status="success",
        finished=True,
        data=ExecutionData(resultData={"result": "ok"}),
    )
    assert execution.id == "exec-123"
    assert execution.workflowId == "wf-456"
    assert execution.mode == "manual"
    assert execution.status == "success"
    assert execution.finished is True


def test_workflow_list_response_model():
    """Test WorkflowListResponse model instantiation."""
    from n8n_mcp.models import WorkflowListResponse

    response = WorkflowListResponse(data=[{"id": "1", "name": "Test"}])
    assert len(response.data) == 1
    assert response.data[0]["id"] == "1"


def test_execution_list_response_model():
    """Test ExecutionListResponse model instantiation."""
    from n8n_mcp.models import ExecutionListResponse

    response = ExecutionListResponse(data=[{"id": "1"}], count=1)
    assert len(response.data) == 1
    assert response.count == 1
