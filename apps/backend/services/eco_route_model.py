import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
MODEL_PATH = os.path.join(BASE_DIR, "models", "eco_model.json")

DEFAULT_WEIGHTS = {
    "distance_weight": 0.15,
    "pollution_weight": 0.45,
    "exposure_weight": 0.4,
}

_weights = DEFAULT_WEIGHTS.copy()


def _load_weights() -> bool:
    global _weights
    if not os.path.exists(MODEL_PATH):
        _weights = DEFAULT_WEIGHTS.copy()
        return False

    with open(MODEL_PATH, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    _weights = {
        "distance_weight": float(data.get("distance_weight", DEFAULT_WEIGHTS["distance_weight"])),
        "pollution_weight": float(
            data.get("pollution_weight", DEFAULT_WEIGHTS["pollution_weight"])
        ),
        "exposure_weight": float(data.get("exposure_weight", DEFAULT_WEIGHTS["exposure_weight"])),
    }
    return True


_load_weights()


def reload_model():
    if _load_weights():
        print("[OK] Model weights hot-reloaded successfully!")
    else:
        print(f"[WARN] Model file not found at: {MODEL_PATH}. Using defaults.")


def predict_score_from_env(state, node, distance, pollution, route_type="full"):
    _ = node
    
    if route_type == "shortest":
        w_dist = 1.0
        w_poll = 0.0
        w_exp = 0.0
    elif route_type == "medium":
        w_dist = 0.5
        w_poll = 0.25
        w_exp = 0.25
    else:  # full eco
        w_dist = _weights["distance_weight"]
        w_poll = _weights["pollution_weight"]
        w_exp = _weights["exposure_weight"]
        
    return (
        distance * w_dist
        + pollution * w_poll
        + state.total_exposure * w_exp
    )


def choose_best_neighbor(state, neighbors, destination, route_type="full"):
    if not neighbors:
        raise ValueError("No neighbors available for decision")

    best_node = None
    best_score = float("inf")

    for node, distance, pollution in neighbors:
        model_score = predict_score_from_env(state, node, distance, pollution, route_type)
        goal_bonus = -10 if node == destination else 0
        final_score = model_score + goal_bonus

        if final_score < best_score:
            best_score = final_score
            best_node = node

    return best_node if best_node is not None else min(neighbors, key=lambda x: x[2])[0]
