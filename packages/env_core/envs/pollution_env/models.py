"""OpenEnv-compliant typed models for the EcoNav Exposure Credit environment.

Defines Pydantic models for observation space, action space, state,
step results, and task/grading structures following OpenEnv spec.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Observation & Action spaces
# ---------------------------------------------------------------------------


class NeighborInfo(BaseModel):
    """Information about a reachable neighboring city."""

    city: str = Field(description="City code")
    city_name: str = Field(description="City name")
    distance: float = Field(description="Distance in km")
    aqi: int = Field(description="Current real-time AQI")
    grade: str = Field(description="Exposure grade (A-F)")
    credit_delta: int = Field(description="Credits gained/lost for this segment")


class Observation(BaseModel):
    """Full observation returned to the agent at each step."""

    current_city: str = Field(description="Current city code")
    current_city_name: str = Field(description="Human-readable city name")
    destination: str = Field(description="Target destination code")
    destination_name: str = Field(description="Target destination name")
    visited: List[str] = Field(description="Already visited city codes")
    neighbors: List[NeighborInfo] = Field(description="Available next moves")
    exposure_credits: int = Field(description="Current credit balance")
    total_exposure: float = Field(description="Cumulative exposure so far")
    steps_taken: int = Field(description="Steps used")
    max_steps: int = Field(description="Maximum steps allowed")
    done: bool = Field(default=False, description="Episode finished?")


class Action(BaseModel):
    """Action the agent takes — choose next city to move to."""

    city: str = Field(description="City code to move to (must be a valid neighbor)")


# ---------------------------------------------------------------------------
# Step result
# ---------------------------------------------------------------------------


class StepResult(BaseModel):
    """Result of executing an action in the environment."""

    observation: Observation
    reward: float = Field(description="Reward for this step")
    done: bool = Field(description="Episode finished?")
    info: dict = Field(default_factory=dict, description="Extra metadata")


# ---------------------------------------------------------------------------
# Episode state (for state() endpoint)
# ---------------------------------------------------------------------------


class EpisodeState(BaseModel):
    """Full episode metadata accessible via state() endpoint."""

    episode_id: str
    task_id: str
    step_count: int
    current_city: str
    destination: str
    visited: List[str]
    exposure_credits: int
    total_exposure: float
    done: bool
    max_steps: int
    route_taken: List[str]


# ---------------------------------------------------------------------------
# Task & Grading
# ---------------------------------------------------------------------------


class TaskConfig(BaseModel):
    """Task definition for the environment."""

    id: str
    name: str
    description: str
    difficulty: str
    start: str
    destination: str
    max_steps: int
    passing_score: float


class GradeResult(BaseModel):
    """Grading result for a completed episode."""

    task_id: str
    score: float = Field(ge=0.0, le=1.0, description="Final score 0.0-1.0")
    reached_destination: bool
    exposure_credits_final: int
    total_exposure: float
    steps_used: int
    route: List[str]
    grade_letter: str = Field(description="A-F grade")
    feedback: str = Field(description="Human-readable feedback")


# ---------------------------------------------------------------------------
# API request/response wrappers
# ---------------------------------------------------------------------------


class ResetRequest(BaseModel):
    """Request body for reset() endpoint."""

    task_id: str = Field(default="easy_route", description="Which task to start")


class StepRequest(BaseModel):
    """Request body for step() endpoint."""

    action: Action
