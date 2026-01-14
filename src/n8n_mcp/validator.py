"""
Workflow validation utilities for n8n MCP server.

Validates workflow definitions against n8n API requirements before submission,
catching common errors early with clear, actionable messages.

Version: 0.1.0
Created: 2026-01-13
"""

from typing import Any

# Fields that n8n API rejects in workflow creation/update requests
FORBIDDEN_FIELDS = frozenset(
    {
        "active",
        "createdAt",
        "description",
        "id",
        "meta",
        "pinData",
        "staticData",
        "triggerCount",
        "updatedAt",
        "versionCounter",
        "versionId",
    }
)

# Required fields at workflow root level
REQUIRED_WORKFLOW_FIELDS = frozenset({"name", "nodes", "connections"})

# Required fields for each node in the nodes array
REQUIRED_NODE_FIELDS = frozenset({"id", "name", "type", "typeVersion", "position"})


class ValidationResult:
    """Container for validation results with errors and warnings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, message: str) -> None:
        """Add a validation error (will cause API rejection)."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a validation warning (may cause issues)."""
        self.warnings.append(message)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP response."""
        return {
            "valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


def validate_workflow(workflow: dict[str, Any]) -> ValidationResult:
    """Validate a workflow definition against n8n API requirements.

    Performs comprehensive validation including:
    - Required field checks
    - Forbidden field detection
    - Node structure validation
    - Connection reference validation

    Args:
        workflow: Workflow definition dictionary

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()

    # Check for forbidden fields
    _check_forbidden_fields(workflow, result)

    # Check for required fields
    _check_required_fields(workflow, result)

    # Validate nodes array
    _validate_nodes(workflow, result)

    # Validate connections reference existing nodes
    _validate_connections(workflow, result)

    # Check for recommended settings
    _check_recommended_settings(workflow, result)

    return result


def _check_forbidden_fields(workflow: dict[str, Any], result: ValidationResult) -> None:
    """Check for fields that will cause API rejection."""
    present_forbidden = set(workflow.keys()) & FORBIDDEN_FIELDS
    for field in sorted(present_forbidden):
        result.add_error(
            f"Forbidden field '{field}' present. "
            f"Remove it to avoid 'must NOT have additional properties' error."
        )


def _check_required_fields(workflow: dict[str, Any], result: ValidationResult) -> None:
    """Check for required workflow fields."""
    missing = REQUIRED_WORKFLOW_FIELDS - set(workflow.keys())
    for field in sorted(missing):
        result.add_error(f"Required field '{field}' is missing.")


def _validate_nodes(workflow: dict[str, Any], result: ValidationResult) -> None:
    """Validate the nodes array structure."""
    nodes = workflow.get("nodes")

    if nodes is None:
        return  # Already reported as missing required field

    if not isinstance(nodes, list):
        result.add_error("Field 'nodes' must be an array.")
        return

    if len(nodes) == 0:
        result.add_warning("Workflow has no nodes. Consider adding at least a trigger node.")
        return

    node_ids: set[str] = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            result.add_error(f"Node at index {i} must be an object, got {type(node).__name__}.")
            continue

        # Check required node fields
        missing_node_fields = REQUIRED_NODE_FIELDS - set(node.keys())
        for field in sorted(missing_node_fields):
            result.add_error(
                f"Node '{node.get('name', f'index {i}')}' missing required field '{field}'."
            )

        # Track node IDs for connection validation
        node_id = node.get("id")
        if node_id:
            if node_id in node_ids:
                result.add_error(f"Duplicate node ID '{node_id}' found.")
            node_ids.add(node_id)

        # Validate position format
        position = node.get("position")
        if position is not None:
            if not isinstance(position, list) or len(position) != 2:
                result.add_error(
                    f"Node '{node.get('name', f'index {i}')}' position must be [x, y] array."
                )

        # Check for credentials by name (warning)
        credentials = node.get("credentials", {})
        for _cred_type, cred_ref in credentials.items():
            if isinstance(cred_ref, dict) and "name" in cred_ref and "id" not in cred_ref:
                result.add_warning(
                    f"Node '{node.get('name', f'index {i}')}' references credential "
                    f"'{cred_ref.get('name')}' by name. Use 'id' for reliability."
                )


def _validate_connections(workflow: dict[str, Any], result: ValidationResult) -> None:
    """Validate connections reference existing nodes."""
    connections = workflow.get("connections")
    nodes = workflow.get("nodes", [])

    if connections is None:
        return  # Already reported as missing required field

    if not isinstance(connections, dict):
        result.add_error("Field 'connections' must be an object.")
        return

    # Build set of valid node names
    node_names = {node.get("name") for node in nodes if isinstance(node, dict)}

    # Check each connection source
    for source_name in connections.keys():
        if source_name not in node_names:
            result.add_error(f"Connection source '{source_name}' does not match any node name.")


def _check_recommended_settings(workflow: dict[str, Any], result: ValidationResult) -> None:
    """Check for recommended settings."""
    settings = workflow.get("settings")

    if settings is None:
        result.add_warning(
            "Missing 'settings' field. Recommend adding: " '{"settings": {"executionOrder": "v1"}}'
        )
    elif isinstance(settings, dict):
        if "executionOrder" not in settings:
            result.add_warning(
                "Missing 'executionOrder' in settings. Recommend: " '{"executionOrder": "v1"}'
            )
