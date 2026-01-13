"""
Utility functions and decorators for n8n MCP server.

Version: 0.1.0
Created: 2025-11-22
"""

import json
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: F) -> F:
    """Decorator to handle errors in MCP tool functions.

    Catches all exceptions and returns them as error dictionaries
    compatible with MCP tool response format.

    Args:
        func: The async function to wrap

    Returns:
        Wrapped function that returns error dicts on exceptions
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return await func(*args, **kwargs)  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            return {"error": "Invalid JSON", "message": str(e)}
        except Exception as e:
            return {"error": str(e)}

    return cast(F, wrapper)
