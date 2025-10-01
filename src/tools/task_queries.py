"""Query tools for retrieving tasks."""

import json
from datetime import datetime
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession


def get_all_tasks(ctx: Context[ServerSession, "AppContext"]) -> str:
    """Get all tasks for the user."""
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.get_all_tasks()
    return json.dumps(result, indent=2)


def get_all_recurrent_tasks(ctx: Context[ServerSession, "AppContext"]) -> str:
    """Get all recurrent tasks for the user."""
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.get_all_recurrent_tasks()
    return json.dumps(result, indent=2)


def get_today_tasks(ctx: Context[ServerSession, "AppContext"]) -> str:
    """Get tasks for today."""
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.get_today_tasks()
    return json.dumps(result, indent=2)


def get_incomplete_tasks(ctx: Context[ServerSession, "AppContext"]) -> str:
    """Get all incomplete tasks."""
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.get_incomplete_tasks()
    return json.dumps(result, indent=2)


def get_completed_tasks(ctx: Context[ServerSession, "AppContext"]) -> str:
    """Get all completed tasks."""
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.get_completed_tasks()
    return json.dumps(result, indent=2)


def search_tasks(
    query: str,
    ctx: Context[ServerSession, "AppContext"]
) -> str:
    """Search tasks by title, description, or checklist item titles.

    Args:
        query: Search query to match against task fields (case-insensitive)
    """
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.search_tasks(query)
    return json.dumps(result, indent=2)


def get_tasks_by_date(
    date: str,
    ctx: Context[ServerSession, "AppContext"]
) -> str:
    """Get tasks for a specific date.

    Args:
        date: Date in format YYYY-MM-DD (e.g., 2025-08-28)
    """
    app_ctx = ctx.request_context.lifespan_context
    result = app_ctx.api_client.get_tasks_by_date(date)
    return json.dumps(result, indent=2)