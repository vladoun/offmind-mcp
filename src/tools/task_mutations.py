"""Mutation tools for creating and modifying tasks."""

import json
from typing import Any, Optional
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession


def create_task(
    title: str,
    date: str,
    description: str = "",
    checklist: Optional[list[dict[str, Any]]] = None,
    recurrent_task_id: Optional[str] = None,
    ctx: Context[ServerSession, "AppContext"] = None
) -> str:
    """Create a new task.

    Args:
        title: Task title
        date: Task date in format YYYY-MM-DD (e.g., 2025-08-28)
        description: Task description (optional)
        checklist: List of checklist items with 'title' and 'done' fields (optional)
        recurrent_task_id: ID of the recurrent task if this is generated from one (optional)
    """
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.create_task(
        title=title,
        date=date,
        description=description,
        checklist=checklist,
        recurrent_task_id=recurrent_task_id
    )
    return json.dumps(result, indent=2)


def toggle_task_completion(
    task_id: str,
    ctx: Context[ServerSession, "AppContext"]
) -> str:
    """Toggle task completion status.

    Args:
        task_id: ID of the task to toggle
    """
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.toggle_task_completion(task_id)
    return json.dumps(result, indent=2)


def toggle_checklist_item(
    task_id: str,
    checklist_index: int,
    ctx: Context[ServerSession, "AppContext"]
) -> str:
    """Toggle a checklist item's done status.

    Args:
        task_id: ID of the task containing the checklist
        checklist_index: Index of the checklist item to toggle (0-based)
    """
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.toggle_checklist_item(task_id, checklist_index)
    return json.dumps(result, indent=2)


def create_recurrent_task(
    title: str,
    recurrence_rule: str,
    generate_from_date: str,
    description: str = "",
    checklist: Optional[list[dict[str, Any]]] = None,
    ctx: Context[ServerSession, "AppContext"] = None
) -> str:
    """Create a new recurrent task.

    Args:
        title: Recurrent task title
        recurrence_rule: Recurrence rule string (e.g., "daily", "weekly", "monthly")
        generate_from_date: Date to start generating tasks from, in format YYYY-MM-DD
        description: Task description (optional)
        checklist: List of checklist items with 'title' and 'done' fields (optional)
    """
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.create_recurrent_task(
        title=title,
        recurrence_rule=recurrence_rule,
        generate_from_date=generate_from_date,
        description=description,
        checklist=checklist
    )
    return json.dumps(result, indent=2)