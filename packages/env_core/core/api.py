"""OpenEnv-compliant HTTP endpoints: /reset, /step, /state, /grade, /tasks.

These are the standard RL loop endpoints required by the OpenEnv spec.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from packages.env_core.envs.pollution_env.env import TASKS, ExposureCreditEnv
from packages.env_core.envs.pollution_env.models import (
    ResetRequest,
    StepRequest,
)

router = APIRouter(tags=["OpenEnv RL Environment"])

# Single global environment instance (per-process)
_env = ExposureCreditEnv()


# ---------------------------------------------------------------------------
# OpenEnv standard endpoints
# ---------------------------------------------------------------------------


@router.post("/reset")
def reset(request: ResetRequest | None = None):
    """Reset the environment and start a new episode.

    Returns the initial observation for the agent.
    """
    task_id = request.task_id if request else "easy_route"
    try:
        obs = _env.reset(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return obs.model_dump()


@router.post("/step")
def step(request: StepRequest):
    """Execute an action (move to a city) and return the new observation.

    Returns: observation, reward, done, info.
    """
    try:
        result = _env.step(request.action)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result.model_dump()


@router.get("/state")
def state():
    """Get current episode state/metadata.

    Includes episode_id, step_count, current position, credits, etc.
    """
    try:
        s = _env.state()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return s.model_dump()


# ---------------------------------------------------------------------------
# Task & Grading endpoints
# ---------------------------------------------------------------------------


@router.get("/tasks")
def get_tasks():
    """List all available tasks with difficulty levels."""
    return {
        "tasks": [t.model_dump() for t in _env.get_tasks()],
        "count": len(TASKS),
    }


@router.get("/grade")
def grade():
    """Grade the current (completed) episode.

    Returns score 0.0-1.0, grade letter, feedback, and detailed metrics.
    """
    try:
        result = _env.grade()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result.model_dump()


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    """Get details of a specific task."""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{task_id}' not found. Available: {list(TASKS.keys())}",
        )
    return task.model_dump()
