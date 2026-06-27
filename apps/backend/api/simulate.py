import os
import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../packages/agent-engine")))
from agent.rl_agent import RLAgent

from packages.env_core.envs.pollution_env.env import TASKS, ExposureCreditEnv
from packages.env_core.envs.pollution_env.models import Action

router = APIRouter(tags=["Simulator Engine"])
_env = ExposureCreditEnv()

class SimulationRequest(BaseModel):
    task_id: str

@router.post("/simulate")
def run_simulation(req: SimulationRequest):
    if req.task_id not in TASKS:
        raise HTTPException(status_code=404, detail=f"Task {req.task_id} not found.")

    obs = _env.reset(req.task_id).model_dump()
    agent = RLAgent(epsilon=0.0) # Greedy deterministic layout
    done = False
    
    timeline = []
    # Initial state record
    timeline.append({
        "step": 0,
        "city": obs["current_city_name"],
        "city_code": obs["current_city"],
        "credits": obs["exposure_credits"],
        "aqi": 0,
        "reward": 0.0,
        "action_taken": None
    })
    
    step_count = 1
    while not done:
        neighbors = obs.get("neighbors", [])
        actions = [n["city"] for n in neighbors]
        if not actions:
            break
            
        action = agent.choose_action(obs["current_city"], actions)
        
        result = _env.step(Action(city=action)).model_dump()
        obs = result["observation"]
        reward = result["reward"]
        done = result["done"]
        info = result["info"]
        
        timeline.append({
            "step": step_count,
            "city": obs["current_city_name"],
            "city_code": obs["current_city"],
            "credits": obs["exposure_credits"],
            "aqi": info.get("segment_avg_aqi", 0),
            "reward": reward,
            "action_taken": action
        })
        step_count += 1
        
    grade_report = _env.grade().model_dump()
    
    return {
        "task_id": req.task_id,
        "timeline": timeline,
        "grade_report": grade_report
    }
