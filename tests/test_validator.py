"""
Tests for workflow validation module.

Ensures comprehensive validation of workflow structures before API submission.
"""

import pytest

from n8n_mcp.validator import (
    FORBIDDEN_FIELDS,
    REQUIRED_NODE_FIELDS,
    REQUIRED_WORKFLOW_FIELDS,
    ValidationResult,
    validate_workflow,
)


class TestValidationResult:
    """Test ValidationResult class functionality."""

    def test_initialization(self):
        """Test ValidationResult initializes empty."""
        result = ValidationResult()
        assert result.errors == []
        assert result.warnings == []
        assert result.is_valid is True

    def test_add_error(self):
        """Test adding errors marks validation as invalid."""
        result = ValidationResult()
        result.add_error("Test error")
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"
        assert result.is_valid is False

    def test_add_warning(self):
        """Test adding warnings doesn't affect validity."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"
        assert result.is_valid is True  # Warnings don't invalidate

    def test_to_dict(self):
        """Test conversion to dictionary format."""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_warning("Warning 1")

        data = result.to_dict()
        assert data["valid"] is False
        assert data["errors"] == ["Error 1"]
        assert data["warnings"] == ["Warning 1"]
        assert data["error_count"] == 1
        assert data["warning_count"] == 1


class TestValidWorkflow:
    """Test validation of correctly structured workflows."""

    def test_minimal_valid_workflow(self):
        """Test minimal valid workflow passes validation."""
        workflow = {
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {},
                }
            ],
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_workflow_with_settings(self):
        """Test workflow with settings passes and doesn't generate warning."""
        workflow = {
            "name": "Test Workflow",
            "settings": {"executionOrder": "v1"},
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {},
                }
            ],
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True
        # Should not warn about missing settings
        assert not any("settings" in w.lower() for w in result.warnings)

    def test_workflow_with_tags(self):
        """Test workflow with tags passes validation."""
        workflow = {
            "name": "Test Workflow",
            "tags": ["tag1", "tag2"],
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {},
                }
            ],
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True


class TestForbiddenFields:
    """Test detection of forbidden fields."""

    @pytest.mark.parametrize("forbidden_field", list(FORBIDDEN_FIELDS))
    def test_each_forbidden_field_detected(self, forbidden_field):
        """Test each forbidden field is detected individually."""
        workflow = {
            "name": "Test",
            "nodes": [],
            "connections": {},
            forbidden_field: "some_value",  # Add forbidden field
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any(forbidden_field in error for error in result.errors)

    def test_multiple_forbidden_fields(self):
        """Test multiple forbidden fields all detected."""
        workflow = {
            "name": "Test",
            "nodes": [],
            "connections": {},
            "id": "wf_123",
            "active": True,
            "versionId": "v1",
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        # All 3 forbidden fields should be reported
        forbidden_mentioned = sum(
            1 for error in result.errors if any(f in error for f in ["id", "active", "versionId"])
        )
        assert forbidden_mentioned >= 3


class TestRequiredFields:
    """Test detection of missing required fields."""

    @pytest.mark.parametrize("required_field", list(REQUIRED_WORKFLOW_FIELDS))
    def test_each_required_field(self, required_field):
        """Test each required field is enforced."""
        workflow = {
            "name": "Test",
            "nodes": [],
            "connections": {},
        }
        # Remove the field being tested
        del workflow[required_field]

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert any(required_field in error for error in result.errors)

    def test_all_required_fields_missing(self):
        """Test completely empty workflow fails validation."""
        workflow = {}

        result = validate_workflow(workflow)
        assert result.is_valid is False
        # Should have errors for all 3 required fields
        assert len(result.errors) >= 3


class TestNodeValidation:
    """Test node structure validation."""

    def test_empty_nodes_array_warning(self):
        """Test empty nodes array generates warning."""
        workflow = {"name": "Test", "nodes": [], "connections": {}}

        result = validate_workflow(workflow)
        assert result.is_valid is True  # Not an error, just a warning
        assert len(result.warnings) > 0
        assert any("no nodes" in w.lower() for w in result.warnings)

    def test_nodes_not_array(self):
        """Test nodes must be an array."""
        workflow = {
            "name": "Test",
            "nodes": "not an array",  # Wrong type
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert any("array" in error.lower() for error in result.errors)

    @pytest.mark.parametrize("required_field", list(REQUIRED_NODE_FIELDS))
    def test_node_missing_required_fields(self, required_field):
        """Test each required node field is enforced."""
        node = {
            "id": "node1",
            "name": "Test Node",
            "type": "n8n-nodes-base.start",
            "typeVersion": 1,
            "position": [250, 300],
        }
        del node[required_field]  # Remove the field being tested

        workflow = {"name": "Test", "nodes": [node], "connections": {}}

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert any(required_field in error for error in result.errors)

    def test_duplicate_node_ids(self):
        """Test duplicate node IDs are detected."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "id": "duplicate",  # Same ID
                    "name": "Node 1",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                },
                {
                    "id": "duplicate",  # Same ID
                    "name": "Node 2",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 3,
                    "position": [450, 300],
                },
            ],
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert any("duplicate" in error.lower() for error in result.errors)

    def test_invalid_position_format(self):
        """Test invalid position format is detected."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Test",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250],  # Wrong: needs 2 elements
                }
            ],
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert any("position" in error.lower() for error in result.errors)

    def test_credential_by_name_warning(self):
        """Test warning for credentials referenced by name."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "id": "node1",
                    "name": "HTTP",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 3,
                    "position": [250, 300],
                    "credentials": {"httpHeaderAuth": {"name": "My Credential"}},  # By name, not ID
                }
            ],
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True  # Valid but has warning
        assert len(result.warnings) > 0
        assert any("credential" in w.lower() and "name" in w.lower() for w in result.warnings)


class TestConnectionValidation:
    """Test connection structure validation."""

    def test_connections_not_dict(self):
        """Test connections must be a dictionary."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                }
            ],
            "connections": "not a dict",  # Wrong type
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert any("object" in error.lower() for error in result.errors)

    def test_connection_source_not_in_nodes(self):
        """Test connection source must reference existing node."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                }
            ],
            "connections": {
                "NonExistentNode": {  # This node doesn't exist
                    "main": [[{"node": "Start", "type": "main", "index": 0}]]
                }
            },
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        assert any("nonexistentnode" in error.lower() for error in result.errors)

    def test_valid_connections(self):
        """Test valid connections pass validation."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                },
                {
                    "id": "node2",
                    "name": "HTTP",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 3,
                    "position": [450, 300],
                },
            ],
            "connections": {"Start": {"main": [[{"node": "HTTP", "type": "main", "index": 0}]]}},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True


class TestRecommendedSettings:
    """Test warnings for recommended but optional settings."""

    def test_missing_settings_warning(self):
        """Test warning when settings field is missing."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                }
            ],
            "connections": {},
            # No settings field
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True  # Warning only
        assert len(result.warnings) > 0
        assert any("settings" in w.lower() for w in result.warnings)

    def test_missing_execution_order_warning(self):
        """Test warning when executionOrder is missing from settings."""
        workflow = {
            "name": "Test",
            "settings": {},  # Empty settings, no executionOrder
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                }
            ],
            "connections": {},
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True  # Warning only
        assert any("executionorder" in w.lower() for w in result.warnings)


class TestComplexWorkflows:
    """Test validation of complex workflow scenarios."""

    def test_multi_node_workflow_with_connections(self):
        """Test complex workflow with multiple nodes and connections."""
        workflow = {
            "name": "Complex Workflow",
            "settings": {"executionOrder": "v1"},
            "nodes": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {},
                },
                {
                    "id": "http",
                    "name": "HTTP Request",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 3,
                    "position": [450, 300],
                    "parameters": {"url": "https://api.example.com"},
                },
                {
                    "id": "code",
                    "name": "Code",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [650, 300],
                    "parameters": {"jsCode": "return items;"},
                },
            ],
            "connections": {
                "Start": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
                "HTTP Request": {"main": [[{"node": "Code", "type": "main", "index": 0}]]},
            },
        }

        result = validate_workflow(workflow)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_workflow_with_multiple_issues(self):
        """Test workflow with multiple validation issues."""
        workflow = {
            "name": "Bad Workflow",
            "id": "wf_123",  # Forbidden
            "active": True,  # Forbidden
            # Missing 'nodes' required field
            "connections": "not a dict",  # Wrong type
        }

        result = validate_workflow(workflow)
        assert result.is_valid is False
        # Should have multiple errors (forbidden fields, missing nodes, wrong connections type)
        assert len(result.errors) >= 3
