"""Utility functions for handling Firebase data."""

from typing import Any


def normalize_tasks(tasks: Any) -> list[tuple[str, dict[str, Any]]]:
    """Normalize Firebase tasks data into a consistent list format.

    Firebase returns a list when keys are numeric, and a dict when keys are strings.
    This function normalizes both formats into a list of (task_id, task_data) tuples.

    Args:
        tasks: Tasks data from Firebase (can be list, dict, or None)

    Returns:
        List of (task_id, task_data) tuples
    """
    if not tasks:
        return []

    if isinstance(tasks, list):
        return [(str(i), task) for i, task in enumerate(tasks) if task is not None]
    elif isinstance(tasks, dict):
        return list(tasks.items())

    return []