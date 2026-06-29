import torch
import torch.nn as nn

class SatAQIModel(nn.Module):
    """
    CNN-LSTM deep learning model for PM2.5 prediction.
    Inputs: (batch, seq_len=14, features=8)
      Features: [AOD, NO2, HCHO, SO2, CO, wind_speed, temperature, RH]
    Architecture:
      Conv1d x 2 (32 ch) -> LSTM x 2 (64 hidden) -> Linear -> PM2.5 scalar
    """
    def __init__(self, input_features=8, conv_channels=32, lstm_hidden=64, lstm_layers=2):
        super(SatAQIModel, self).__init__()
        
        # 1D CNN along the temporal sequence axis
        self.conv1 = nn.Conv1d(in_channels=input_features, out_channels=conv_channels, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(in_channels=conv_channels, out_channels=conv_channels, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        
        # LSTM sequence modeler
        self.lstm = nn.LSTM(
            input_size=conv_channels,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=0.2 if lstm_layers > 1 else 0.0
        )
        
        # Output predictor
        self.fc = nn.Linear(lstm_hidden, 1)

    def forward(self, x):
        # Input x: (batch, seq_len=14, features=8)
        # Conv1d expects: (batch, in_channels=8, seq_len=14)
        x = x.transpose(1, 2)
        
        # CNN layers
        out = self.conv1(x)
        out = self.relu1(out)
        out = self.conv2(out)
        out = self.relu2(out) # Shape: (batch, 32, 14)
        
        # LSTM expects: (batch, seq_len=14, input_size=32)
        out = out.transpose(1, 2)
        
        # LSTM layers
        lstm_out, _ = self.lstm(out) # Shape: (batch, 14, 64)
        
        # Take the output of the last time step
        last_timestep = lstm_out[:, -1, :] # Shape: (batch, 64)
        
        # Fully connected layer
        pm25_pred = self.fc(last_timestep) # Shape: (batch, 1)
        
        return pm25_pred.squeeze(-1) # Shape: (batch,)
