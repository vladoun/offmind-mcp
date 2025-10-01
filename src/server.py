"""MCP server for Firebase Realtime Database todo app."""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession

from .api_client import APIClient
from .firebase_auth import FirebaseAuthManager
from .tools import (
    get_all_tasks,
    get_all_recurrent_tasks,
    get_today_tasks,
    get_incomplete_tasks,
    get_completed_tasks,
    search_tasks,
    get_tasks_by_date,
    create_task,
    toggle_task_completion,
    toggle_checklist_item,
    create_recurrent_task,
)


@dataclass
class AppContext:
    """Application context with API client."""

    api_client: APIClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with API client initialization."""
    # Hardcoded configuration
    api_url = "https://offmind-proxy-798066310667.europe-west1.run.app"
    firebase_api_key = "AIzaSyAlwhSoC3xMsn2jgVzAy1sNebaXnbAxvOY"

    # Initialize Firebase Auth manager and API client
    auth_manager = FirebaseAuthManager(firebase_api_key, api_url)
    api_client = APIClient(api_url, auth_manager)

    try:
        yield AppContext(api_client=api_client)
    finally:
        # Cleanup
        api_client.close()


# Create FastMCP server with lifespan management
mcp = FastMCP("Firebase Todos", lifespan=app_lifespan)


# ============================================================================
# REGISTER TOOLS
# ============================================================================

# Query tools
mcp.tool()(get_all_tasks)
mcp.tool()(get_all_recurrent_tasks)
mcp.tool()(get_today_tasks)
mcp.tool()(get_incomplete_tasks)
mcp.tool()(get_completed_tasks)
mcp.tool()(search_tasks)
mcp.tool()(get_tasks_by_date)

# Mutation tools
mcp.tool()(create_task)
mcp.tool()(toggle_task_completion)
mcp.tool()(toggle_checklist_item)
mcp.tool()(create_recurrent_task)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()