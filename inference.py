"""
Inference Script — Compliance Optimized
=======================================

MANDATORY Checklist:
1. Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN strictly defined.
2. HF_TOKEN has NO default value (set via HF environment/secrets).
3. LLM calls use the OpenAI Client globally or within functions using these variables.
4. Stdout logs follow the required structured format ([START]/[STEP]/[END]) exactly.
"""

import os

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Environment config (Checklist Compliance)
# ---------------------------------------------------------------------------

ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional – if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")


# ---------------------------------------------------------------------------
# OpenAI client is initialized inside functions to handle missing tokens gracefully.


# ---------------------------------------------------------------------------
# Environment interaction helpers
# ---------------------------------------------------------------------------

def env_reset(task_id: str = "easy_route") -> dict:
    resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def env_step(city: str) -> dict:
    resp = requests.post(f"{ENV_URL}/step", json={"action": {"city": city}}, timeout=10)
    resp.raise_for_status()
    return resp.json()

def env_grade() -> dict:
    resp = requests.get(f"{ENV_URL}/grade", timeout=10)
    resp.raise_for_status()
    return resp.json()

def env_tasks() -> list[dict]:
    """Fetch tasks with retry logic to wait for environment startup."""
    max_retries = 5
    for i in range(max_retries):
        try:
            resp = requests.get(f"{ENV_URL}/tasks", timeout=10)
            resp.raise_for_status()
            return resp.json()["tasks"]
        except Exception:
            if i == max_retries - 1:
                raise # Re-raise on last try
            print(f"Waiting for environment... (attempt {i+1}/{max_retries})")
            import time
            time.sleep(5)
    return []


# ---------------------------------------------------------------------------
# LLM Agent
# ---------------------------------------------------------------------------

def get_llm_action(observation: dict) -> str:
    """Ask the LLM to choose the next city based on observation."""
    neighbors = observation.get("neighbors", [])
    neighbor_text = "\n".join(
        f"  - {n['city']} ({n['city_name']}): AQI={n['aqi']}, Grade={n['grade']}, "
        f"Credits={n['credit_delta']:+d}, Distance={n['distance']}km"
        for n in neighbors
    )

    prompt = f"""You are an AI navigation agent in the EcoNav environment.
Your goal: reach {observation["destination"]} ({observation["destination_name"]}) while maximizing exposure credits.

Current state:
- Location: {observation["current_city"]} ({observation["current_city_name"]})
- Destination: {observation["destination"]} ({observation["destination_name"]})
- Credits: {observation["exposure_credits"]}
- Steps: {observation["steps_taken"]}/{observation["max_steps"]}
- Visited: {observation["visited"]}
- Total exposure: {observation["total_exposure"]}

Available moves:
{neighbor_text}

Rules:
- Choose cities with lower AQI (Grade A/B) to EARN credits
- Avoid high-AQI cities (Grade D/E/F) that LOSE credits
- You MUST reach the destination before running out of steps
- Balance: short path vs clean-air path

Reply with ONLY the city code (e.g., "E") — nothing else."""

    try:
        client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.0, # Deterministic for evaluation
        )
        action = response.choices[0].message.content.strip().upper()
        # Clean up in case model outputs more than one word
        action = action.split()[0].replace('"', '').replace('.', '').replace(',', '')
        
        valid = [n["city"] for n in neighbors]
        if action in valid:
            return action
        # Fallback to first unvisited neighbor if any, then first neighbor
        visited = set(observation.get("visited", []))
        unvisited = [v for v in valid if v not in visited]
        return unvisited[0] if unvisited else valid[0]
    except Exception:
        # Final fallback - prioritize first neighbor's city
        if neighbors:
            return neighbors[0]["city"]
        return "F" # Hard fallback if everything fails


# ---------------------------------------------------------------------------
# Main Evaluation Loop (Structured Logging)
# ---------------------------------------------------------------------------

def run_evaluation():
    try:
        tasks = env_tasks()
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return

    for task in tasks:
        try:
            task_id = task["id"]
            # [START] Marker
            print(f"[START] task_id={task_id}")
            
            obs = env_reset(task_id)
            done = False
            step_count = 0
            
            while not done:
                # Agent chooses action
                action = get_llm_action(obs)
                
                # Environment step
                result = env_step(action)
                obs = result["observation"]
                reward = result["reward"]
                done = result["done"]
                
                # [STEP] Marker
                print(f"[STEP] step={step_count} action={action} reward={reward:.4f}")
                step_count += 1
                
                if step_count > 20: # Safety break
                    break
            
            # Ending task
            grade = env_grade()
            
            # [END] Marker
            print(f"[END] score={grade['score']:.4f} grade={grade['grade_letter']} reached={grade['reached_destination']}")
            
        except Exception as e:
            print(f"Error during task: {e}")
            print("[END] score=0.0001 grade=F reached=False")


if __name__ == "__main__":
    if not HF_TOKEN:
        print("Warning: HF_TOKEN not set. Remote LLM calls will fail.")
    run_evaluation()
