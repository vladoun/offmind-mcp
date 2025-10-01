"""HTTP client for communicating with the proxy API."""

from typing import Any, Optional

import httpx

from .firebase_auth import FirebaseAuthManager


class APIClient:
    """Client for making authenticated requests to the proxy API."""

    def __init__(self, api_url: str, auth_manager: FirebaseAuthManager):
        """Initialize API client.

        Args:
            api_url: Base URL of the proxy API
            auth_manager: Firebase auth manager for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.auth_manager = auth_manager
        self.client = httpx.Client(timeout=30.0)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with Firebase ID token.

        Returns:
            Headers dict with Authorization bearer token
        """
        id_token = self.auth_manager.ensure_authenticated()
        return {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            json: JSON body for request
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            Exception: If request fails
        """
        url = f"{self.api_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = self.client.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                params=params,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token might be expired, clear it and raise
                self.auth_manager.clear_tokens()
                raise Exception("Authentication failed. Please sign in again.")
            raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")

        except httpx.HTTPError as e:
            raise Exception(f"API request error: {e}")

    # ========================================================================
    # TASK QUERY METHODS
    # ========================================================================

    def get_all_tasks(self) -> dict[str, Any]:
        """Get all tasks."""
        return self._request("GET", "/api/tasks")

    def get_today_tasks(self) -> dict[str, Any]:
        """Get today's tasks."""
        return self._request("GET", "/api/tasks/today")

    def get_incomplete_tasks(self) -> dict[str, Any]:
        """Get incomplete tasks."""
        return self._request("GET", "/api/tasks", params={"status": "incomplete"})

    def get_completed_tasks(self) -> dict[str, Any]:
        """Get completed tasks."""
        return self._request("GET", "/api/tasks", params={"status": "completed"})

    def get_tasks_by_date(self, date: str) -> dict[str, Any]:
        """Get tasks for a specific date.

        Args:
            date: Date in YYYY-MM-DD format
        """
        return self._request("GET", "/api/tasks", params={"date": date})

    def search_tasks(self, query: str) -> dict[str, Any]:
        """Search tasks by title, description, or checklist.

        Args:
            query: Search query string
        """
        return self._request("GET", "/api/tasks/search", params={"q": query})

    # ========================================================================
    # TASK MUTATION METHODS
    # ========================================================================

    def create_task(
        self,
        title: str,
        date: str,
        description: str = "",
        checklist: Optional[list[dict[str, Any]]] = None,
        recurrent_task_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new task.

        Args:
            title: Task title
            date: Task date in YYYY-MM-DD format
            description: Task description (optional)
            checklist: List of checklist items (optional)
            recurrent_task_id: ID of recurrent task if applicable (optional)
        """
        json_data = {
            "title": title,
            "date": date,
            "description": description,
        }

        if checklist:
            json_data["checklist"] = checklist

        if recurrent_task_id:
            json_data["recurrentTaskId"] = recurrent_task_id

        return self._request("POST", "/api/tasks", json=json_data)

    def toggle_task_completion(self, task_id: str) -> dict[str, Any]:
        """Toggle task completion status.

        Args:
            task_id: ID of the task to toggle
        """
        return self._request("PUT", f"/api/tasks/{task_id}/toggle")

    def toggle_checklist_item(self, task_id: str, checklist_index: int) -> dict[str, Any]:
        """Toggle a checklist item's done status.

        Args:
            task_id: ID of the task
            checklist_index: Index of the checklist item (0-based)
        """
        return self._request("PUT", f"/api/tasks/{task_id}/checklist/{checklist_index}/toggle")

    # ========================================================================
    # RECURRENT TASK METHODS
    # ========================================================================

    def get_all_recurrent_tasks(self) -> dict[str, Any]:
        """Get all recurrent tasks."""
        return self._request("GET", "/api/recurrent-tasks")

    def create_recurrent_task(
        self,
        title: str,
        recurrence_rule: str,
        generate_from_date: str,
        description: str = "",
        checklist: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Create a new recurrent task.

        Args:
            title: Task title
            recurrence_rule: Recurrence rule string
            generate_from_date: Date to start generating from (YYYY-MM-DD)
            description: Task description (optional)
            checklist: List of checklist items (optional)
        """
        json_data = {
            "title": title,
            "recurrenceRule": recurrence_rule,
            "generateFromDate": generate_from_date,
            "description": description,
        }

        if checklist:
            json_data["checklist"] = checklist

        return self._request("POST", "/api/recurrent-tasks", json=json_data)

    def close(self):
        """Close the HTTP client."""
        self.client.close()
