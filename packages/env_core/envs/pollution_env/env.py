from __future__ import annotations

import uuid

from apps.backend.services.aqi_service import (
    CITY_PROFILES,
    _cache,
    fetch_route_cities_aqi,
)
from apps.backend.services.exposure_credit import (
    DEFAULT_STARTING_CREDITS,
    MAX_CREDITS,
    MIN_CREDITS,
    get_grade_for_aqi,
    grade_segment,
)
from packages.env_core.envs.pollution_env.models import (
    Action,
    EpisodeState,
    GradeResult,
    NeighborInfo,
    Observation,
    StepResult,
    TaskConfig,
)

# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

TASKS: dict[str, TaskConfig] = {
    "easy_route": TaskConfig(
        id="easy_route",
        name="Easy — Delhi to Kolkata",
        description="Navigate from Delhi(A) to Kolkata(F) with generous step budget.",
        difficulty="easy",
        start="A",
        destination="F",
        max_steps=15,
        passing_score=0.5,
    ),
    "medium_route": TaskConfig(
        id="medium_route",
        name="Medium — Delhi to Kolkata (tight budget)",
        description="Same route but fewer steps, credit-aware scoring.",
        difficulty="medium",
        start="A",
        destination="F",
        max_steps=8,
        passing_score=0.6,
    ),
    "hard_pollution_dodge": TaskConfig(
        id="hard_pollution_dodge",
        name="Hard — Agra to Kolkata (dodge pollution)",
        description="Start from polluted Agra, reach Kolkata, maximize credits.",
        difficulty="hard",
        start="C",
        destination="F",
        max_steps=6,
        passing_score=0.7,
    ),
    "expert_credit_max": TaskConfig(
        id="expert_credit_max",
        name="Expert — Maximize credits Delhi→Kolkata",
        description="Reach destination AND end with maximum exposure credits.",
        difficulty="expert",
        start="A",
        destination="F",
        max_steps=10,
        passing_score=0.8,
    ),
}

# Edge distances (km) between route cities
EDGE_DISTANCES: dict[tuple[str, str], float] = {
    ("A", "B"): 280,
    ("A", "C"): 230,
    ("B", "D"): 680,
    ("C", "D"): 540,
    ("C", "E"): 330,
    ("D", "E"): 300,
    ("D", "F"): 680,
    ("E", "F"): 990,
}

# Adjacency list (bidirectional)
ADJACENCY: dict[str, list[str]] = {}
for c1, c2 in EDGE_DISTANCES:
    ADJACENCY.setdefault(c1, []).append(c2)
    ADJACENCY.setdefault(c2, []).append(c1)


def _get_distance(a: str, b: str) -> float:
    return EDGE_DISTANCES.get((a, b), EDGE_DISTANCES.get((b, a), 500))


def _get_city_name(code: str) -> str:
    return CITY_PROFILES.get(code, {}).get("name", code)


def _get_city_aqi(code: str) -> int:
    cached = _cache.data.get(code)
    if cached:
        return cached.aqi
    return 100  # default moderate


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


class ExposureCreditEnv:
    """OpenEnv-compliant RL environment for exposure-credit navigation."""

    def __init__(self):
        self._episode_id: str = ""
        self._task: TaskConfig | None = None
        self._current: str = ""
        self._destination: str = ""
        self._visited: list[str] = []
        self._credits: int = DEFAULT_STARTING_CREDITS
        self._total_exposure: float = 0.0
        self._steps: int = 0
        self._max_steps: int = 15
        self._done: bool = True
        self._route: list[str] = []
        self._rewards: list[float] = []

    # -----------------------------------------------------------------------
    # reset() — OpenEnv standard
    # -----------------------------------------------------------------------
    def reset(self, task_id: str = "easy_route") -> Observation:
        """Reset environment for a new episode."""
        task = TASKS.get(task_id)
        if not task:
            raise ValueError(f"Unknown task: {task_id}. Valid: {list(TASKS.keys())}")

        # Ensure AQI data is loaded
        fetch_route_cities_aqi()

        self._episode_id = str(uuid.uuid4())
        self._task = task
        self._current = task.start
        self._destination = task.destination
        self._visited = [task.start]
        self._credits = DEFAULT_STARTING_CREDITS
        self._total_exposure = 0.0
        self._steps = 0
        self._max_steps = task.max_steps
        self._done = False
        self._route = [task.start]
        self._rewards = []

        return self._build_observation()

    # -----------------------------------------------------------------------
    # step(action) — OpenEnv standard
    # -----------------------------------------------------------------------
    def step(self, action: Action) -> StepResult:
        """Execute one step: move to chosen city."""
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")

        city = action.city.strip().upper()
        neighbors = ADJACENCY.get(self._current, [])

        if city not in neighbors:
            raise ValueError(
                f"Invalid action '{city}'. Valid moves from {self._current}: {neighbors}"
            )

        if city in self._visited:
            # Allow revisiting but with penalty
            revisit_penalty = -10.0
        else:
            revisit_penalty = 0.0

        # Calculate segment metrics
        distance = _get_distance(self._current, city)
        seg = grade_segment(self._current, city, distance)

        # Update state
        self._current = city
        self._visited.append(city)
        self._route.append(city)
        self._steps += 1

        # Exposure
        from_aqi = _get_city_aqi(self._route[-2])
        to_aqi = _get_city_aqi(city)
        exposure = distance * (from_aqi + to_aqi) / 2 / 100  # normalized
        self._total_exposure += exposure

        # Credit change
        self._credits = max(MIN_CREDITS, min(MAX_CREDITS, self._credits + seg.credit_delta))

        # Reward computation
        reward = float(seg.credit_delta)  # Base: grade-based credit
        reward -= distance / 1000  # Small distance penalty (normalized)
        reward += revisit_penalty

        # Destination bonus
        reached = city == self._destination
        if reached:
            reward += 100.0
            self._done = True

        # Step limit
        if self._steps >= self._max_steps:
            if not reached:
                reward -= 50.0  # Penalty for running out of steps
            self._done = True

        self._rewards.append(reward)

        info = {
            "segment_grade": seg.grade,
            "segment_credit_delta": seg.credit_delta,
            "segment_avg_aqi": seg.avg_aqi,
            "distance_km": distance,
            "exposure_added": round(exposure, 2),
            "reached_destination": reached,
        }

        obs = self._build_observation()
        return StepResult(observation=obs, reward=reward, done=self._done, info=info)

    # -----------------------------------------------------------------------
    # state() — OpenEnv standard
    # -----------------------------------------------------------------------
    def state(self) -> EpisodeState:
        """Return current episode metadata."""
        return EpisodeState(
            episode_id=self._episode_id,
            task_id=self._task.id if self._task else "",
            step_count=self._steps,
            current_city=self._current,
            destination=self._destination,
            visited=list(self._visited),
            exposure_credits=self._credits,
            total_exposure=round(self._total_exposure, 2),
            done=self._done,
            max_steps=self._max_steps,
            route_taken=list(self._route),
        )

    # -----------------------------------------------------------------------
    # grade() — evaluate completed episode
    # -----------------------------------------------------------------------
    def grade(self) -> GradeResult:
        """Grade the completed episode."""
        if not self._task:
            raise RuntimeError("No task loaded. Call reset() first.")

        reached = self._current == self._destination
        task = self._task

        # Score components (each 0-1)
        # 1. Destination reached (40%)
        dest_score = 1.0 if reached else 0.0

        # 2. Credit performance (30%)
        credit_diff = self._credits - DEFAULT_STARTING_CREDITS
        # Max possible gain ~40 (4 segments × 10), max loss ~100 (4 × -25)
        credit_score = max(0.0, min(1.0, (credit_diff + 50) / 100))

        # 3. Exposure minimization (20%)
        # Lower exposure = better. Normalize against a baseline
        exposure_score = max(0.0, min(1.0, 1.0 - self._total_exposure / 5000))

        # 4. Step efficiency (10%)
        if reached:
            # Fewer steps = more efficient
            step_score = max(0.0, 1.0 - (self._steps - 3) / task.max_steps)
        else:
            step_score = 0.0

        # Component scores aggregated to [0.0, 1.0]
        final_score = (
            0.4 * dest_score + 0.3 * credit_score + 0.2 * exposure_score + 0.1 * step_score
        )

        # MANDATORY: Clamp to strictly between (0, 1) as required by evaluation platform.
        # Exactly 0.0 or 1.0 will cause Phase 2 failure.
        final_score = round(max(0.0001, min(0.9999, final_score)), 4)

        # Grade letter
        if final_score >= 0.9:
            grade_letter = "A"
        elif final_score >= 0.75:
            grade_letter = "B"
        elif final_score >= 0.6:
            grade_letter = "C"
        elif final_score >= 0.4:
            grade_letter = "D"
        else:
            grade_letter = "F"

        # Feedback
        parts = []
        if reached:
            parts.append(f"✅ Reached {_get_city_name(self._destination)} in {self._steps} steps.")
        else:
            parts.append(f"❌ Failed to reach {_get_city_name(self._destination)}.")
        parts.append(f"Credits: {self._credits} ({credit_diff:+d} from start).")
        parts.append(f"Total exposure: {self._total_exposure:.1f}.")
        parts.append(f"Route: {' → '.join(_get_city_name(c) for c in self._route)}.")

        return GradeResult(
            task_id=task.id,
            score=final_score,
            reached_destination=reached,
            exposure_credits_final=self._credits,
            total_exposure=round(self._total_exposure, 2),
            steps_used=self._steps,
            route=list(self._route),
            grade_letter=grade_letter,
            feedback=" ".join(parts),
        )

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _build_observation(self) -> Observation:
        """Build the observation dict for the agent."""
        neighbors_info: list[NeighborInfo] = []
        for nb in ADJACENCY.get(self._current, []):
            aqi = _get_city_aqi(nb)
            g = get_grade_for_aqi(aqi)
            neighbors_info.append(
                NeighborInfo(
                    city=nb,
                    city_name=_get_city_name(nb),
                    distance=_get_distance(self._current, nb),
                    aqi=aqi,
                    grade=g["grade"],
                    credit_delta=g["credits"],
                )
            )

        return Observation(
            current_city=self._current,
            current_city_name=_get_city_name(self._current),
            destination=self._destination,
            destination_name=_get_city_name(self._destination),
            visited=list(self._visited),
            neighbors=neighbors_info,
            exposure_credits=self._credits,
            total_exposure=round(self._total_exposure, 2),
            steps_taken=self._steps,
            max_steps=self._max_steps,
            done=self._done,
        )

    def get_tasks(self) -> list[TaskConfig]:
        return list(TASKS.values())
