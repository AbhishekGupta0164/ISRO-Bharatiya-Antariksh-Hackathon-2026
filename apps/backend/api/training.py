import subprocess

from fastapi import APIRouter

from apps.backend.services.eco_route_model import reload_model

router = APIRouter()

@router.post("/trigger")
def trigger_training():
    """Manually triggers a training run and reloads the model."""
    try:
        # Run the training script synchronously so we can return success
        subprocess.run(["python", "models/train_model.py"], check=True)
        
        # Hot-reload the weights in the FastApi application
        reload_model()
        
        return {"status": "success", "message": "Training completed and model reloaded."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
