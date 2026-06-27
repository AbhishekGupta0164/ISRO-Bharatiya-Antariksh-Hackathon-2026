import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np

from models.aqi_estimation.cnn_lstm_model import SatAQIModel

def generate_synthetic_train_data(num_samples=1000, seq_len=14, num_features=8):
    """Generates synthetic time series input and target PM2.5 values for training."""
    # Features: [AOD, NO2, HCHO, SO2, CO, wind_speed, temp, RH]
    X = np.random.uniform(0.1, 1.0, size=(num_samples, seq_len, num_features)).astype(np.float32)
    # Scale wind, temp, RH to realistic scales
    X[:, :, 5] = X[:, :, 5] * 15.0 # wind speed (0 to 15 m/s)
    X[:, :, 6] = X[:, :, 6] * 15.0 + 15.0 # temp (15 to 30 C)
    X[:, :, 7] = X[:, :, 7] * 60.0 + 30.0 # RH (30 to 90 %)
    
    # Target PM2.5 depends on features in the last time step and previous AODs
    # PM2.5 = 120 * AOD + 40 * NO2 + 10 * HCHO - 1.5 * wind_speed + noise
    aod_last = X[:, -1, 0]
    no2_last = X[:, -1, 1]
    hcho_last = X[:, -1, 2]
    wind_last = X[:, -1, 5]
    
    y = (130.0 * aod_last + 45.0 * no2_last + 15.0 * hcho_last - 2.0 * wind_last + 15.0)
    y += np.random.normal(0, 5.0, size=num_samples)
    y = np.clip(y, 5.0, 350.0).astype(np.float32)
    
    return torch.tensor(X), torch.tensor(y)

def run_training_pipeline(epochs=10, batch_size=32):
    print("Initializing CNN-LSTM model training...")
    X_train, y_train = generate_synthetic_train_data(num_samples=1200)
    X_val, y_val = generate_synthetic_train_data(num_samples=200)
    
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using training device: {device}")
    
    model = SatAQIModel().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    os.makedirs("models/aqi_estimation", exist_ok=True)
    best_loss = float("inf")
    model_path = "models/aqi_estimation/cnn_lstm.pth"
    
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            predictions = model(batch_X)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * batch_X.size(0)
            
        train_loss /= len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                predictions = model(batch_X)
                loss = criterion(predictions, batch_y)
                val_loss += loss.item() * batch_X.size(0)
        val_loss /= len(val_loader.dataset)
        
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train MSE: {train_loss:.4f} | Val MSE: {val_loss:.4f}")
        
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), model_path)
            
    print(f"[OK] Training complete. Best model saved to {model_path}")
    return True

if __name__ == "__main__":
    run_training_pipeline()
