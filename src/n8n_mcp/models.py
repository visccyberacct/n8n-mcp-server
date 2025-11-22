"""
Pydantic models for n8n API data structures.

These models provide type hints and documentation for common n8n data structures.
They are used for IDE support and documentation, not for strict runtime validation.

Version: 0.1.0
Created: 2025-11-22
"""

from typing import Any

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    """Represents a node in an n8n workflow."""

    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Node display name")
    type: str = Field(..., description="Node type (e.g., 'n8n-nodes-base.start')")
    typeVersion: int = Field(..., description="Node type version")
    position: list[float] = Field(..., description="[x, y] coordinates for node position")
    parameters: dict[str, Any] | None = Field(default=None, description="Node-specific parameters")


class WorkflowSettings(BaseModel):
    """Workflow execution settings."""

    saveExecutionProgress: bool | None = Field(
        default=None, description="Whether to save execution progress"
    )
    saveManualExecutions: bool | None = Field(
        default=None, description="Whether to save manual executions"
    )
    saveDataErrorExecution: str | None = Field(
        default=None, description="How to handle error executions"
    )
    saveDataSuccessExecution: str | None = Field(
        default=None, description="How to handle success executions"
    )
    executionTimeout: int | None = Field(default=None, description="Execution timeout in seconds")


class Workflow(BaseModel):
    """Represents an n8n workflow."""

    id: str | None = Field(default=None, description="Workflow ID (assigned by n8n)")
    name: str = Field(..., description="Workflow name")
    active: bool | None = Field(default=False, description="Whether workflow is active")
    nodes: list[WorkflowNode] = Field(..., description="List of workflow nodes")
    connections: dict[str, Any] = Field(
        default_factory=dict, description="Node connections mapping"
    )
    settings: WorkflowSettings | None = Field(
        default=None, description="Workflow execution settings"
    )
    staticData: dict[str, Any] | None = Field(default=None, description="Static data for workflow")
    tags: list[str] | None = Field(default=None, description="Workflow tags")
    createdAt: str | None = Field(default=None, description="Creation timestamp")
    updatedAt: str | None = Field(default=None, description="Last update timestamp")


class ExecutionData(BaseModel):
    """Data associated with a workflow execution."""

    resultData: dict[str, Any] | None = Field(default=None, description="Execution result data")
    executionData: dict[str, Any] | None = Field(
        default=None, description="Detailed execution data"
    )


class Execution(BaseModel):
    """Represents a workflow execution."""

    id: str | None = Field(default=None, description="Execution ID")
    workflowId: str | None = Field(default=None, description="Associated workflow ID")
    mode: str | None = Field(
        default=None, description="Execution mode (manual, trigger, webhook, etc.)"
    )
    status: str | None = Field(
        default=None, description="Execution status (running, success, failed, etc.)"
    )
    startedAt: str | None = Field(default=None, description="Execution start timestamp")
    stoppedAt: str | None = Field(default=None, description="Execution stop timestamp")
    finished: bool | None = Field(default=None, description="Whether execution finished")
    data: ExecutionData | None = Field(default=None, description="Execution data")
    error: str | None = Field(default=None, description="Error message if execution failed")


class WorkflowListResponse(BaseModel):
    """Response model for workflow list endpoint."""

    data: list[dict[str, Any]] = Field(..., description="List of workflows")


class ExecutionListResponse(BaseModel):
    """Response model for execution list endpoint."""

    data: list[dict[str, Any]] = Field(..., description="List of executions")
    count: int | None = Field(default=None, description="Total count of executions")
