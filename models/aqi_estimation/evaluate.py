import torch
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from models.aqi_estimation.cnn_lstm_model import SatAQIModel
from models.aqi_estimation.train import generate_synthetic_train_data

def evaluate_model(model_path="models/aqi_estimation/cnn_lstm.pth"):
    print(f"Evaluating model saved at: {model_path}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load model
    model = SatAQIModel()
    if not torch.cuda.is_available():
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    else:
        model.load_state_dict(torch.load(model_path))
    model = model.to(device)
    model.eval()
    
    # Generate evaluation data
    X_test, y_test = generate_synthetic_train_data(num_samples=300)
    
    # Predict
    with torch.no_grad():
        X_test = X_test.to(device)
        predictions = model(X_test).cpu().numpy()
        targets = y_test.numpy()
        
    # Metrics
    r2 = r2_score(targets, predictions)
    rmse = np.sqrt(mean_squared_error(targets, predictions))
    mae = mean_absolute_error(targets, predictions)
    
    print("\n==========================================")
    print("SATELLITE AQI MODEL EVALUATION REPORT")
    print("==========================================")
    print(f"Model Path:         {model_path}")
    print(f"Test Samples:       {len(targets)}")
    print(f"Coefficient (R²):   {r2:.4f} (Mandated > 0.75)")
    print(f"Root MSE (RMSE):    {rmse:.4f} ug/m³")
    print(f"Mean Abs Error (MAE):{mae:.4f} ug/m³")
    print("==========================================\n")
    
    return {"r2": r2, "rmse": rmse, "mae": mae}

if __name__ == "__main__":
    # Ensure a model file exists or train if missing
    import os
    if not os.path.exists("models/aqi_estimation/cnn_lstm.pth"):
        from models.aqi_estimation.train import run_training_pipeline
        run_training_pipeline(epochs=2)
    evaluate_model()
