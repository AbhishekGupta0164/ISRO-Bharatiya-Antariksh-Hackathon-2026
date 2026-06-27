import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin

class GeographicallyWeightedRegression(BaseEstimator, RegressorMixin):
    """
    Geographically Weighted Regression (GWR) baseline model.
    Calibrates AOD to PM2.5 using distance-weighted local linear regression.
    Includes ridge regularization to prevent singularity.
    """
    def __init__(self, bandwidth=1.5, ridge_alpha=1e-4):
        self.bandwidth = bandwidth
        self.ridge_alpha = ridge_alpha
        self.train_coords = None
        self.train_aod = None
        self.train_pm25 = None
        self.global_slope = 80.0
        self.global_intercept = 15.0

    def fit(self, coords, aod, pm25):
        """
        Fit the GWR model.
        coords: np.ndarray of shape (N, 2) representing [lat, lon]
        aod: np.ndarray of shape (N,) representing AOD
        pm25: np.ndarray of shape (N,) representing CPCB PM2.5
        """
        self.train_coords = np.asarray(coords, dtype=np.float32)
        self.train_aod = np.asarray(aod, dtype=np.float32)
        self.train_pm25 = np.asarray(pm25, dtype=np.float32)
        
        # Fit a global linear fallback model
        if len(self.train_aod) > 1:
            try:
                A = np.vstack([self.train_aod, np.ones_like(self.train_aod)]).T
                slope, intercept = np.linalg.lstsq(A, self.train_pm25, rcond=None)[0]
                self.global_slope = float(slope)
                self.global_intercept = float(intercept)
            except Exception:
                pass
        return self

    def predict(self, target_coords, target_aod):
        """
        Predict PM2.5 for target coordinates and AODs.
        target_coords: np.ndarray of shape (M, 2)
        target_aod: np.ndarray of shape (M,)
        """
        target_coords = np.asarray(target_coords, dtype=np.float32)
        target_aod = np.asarray(target_aod, dtype=np.float32)
        
        if self.train_coords is None or len(self.train_coords) == 0:
            # Fallback to simple scaling if no training data
            return target_aod * self.global_slope + self.global_intercept

        predictions = np.zeros(len(target_coords), dtype=np.float32)
        
        for i, (t_lat, t_lon) in enumerate(target_coords):
            t_aod = target_aod[i]
            
            # Compute Euclidean distances to all training points
            dists = np.sqrt(np.sum((self.train_coords - np.array([t_lat, t_lon]))**2, axis=1))
            
            # Compute Gaussian weights: w = exp(-0.5 * (d / b)^2)
            weights = np.exp(-0.5 * (dists / self.bandwidth)**2)
            
            # Weighted Least Squares (WLS)
            # Y = X * Beta
            # Beta = (X.T * W * X)^-1 * X.T * W * Y
            X = np.vstack([self.train_aod, np.ones_like(self.train_aod)]).T # (N, 2)
            W = np.diag(weights)
            
            XTW = X.T @ W # (2, N)
            XTWX = XTW @ X # (2, 2)
            
            # Add Ridge penalty to guarantee invertibility
            XTWX += np.eye(2) * self.ridge_alpha
            
            try:
                XTWY = XTW @ self.train_pm25
                beta = np.linalg.solve(XTWX, XTWY)
                slope, intercept = beta[0], beta[1]
                
                # Sanity bounding (prevent negative slope or extreme values)
                slope = np.clip(slope, 10.0, 300.0)
                intercept = np.clip(intercept, 2.0, 100.0)
                
                pred = slope * t_aod + intercept
            except np.linalg.LinAlgError:
                # Fallback to global model
                pred = self.global_slope * t_aod + self.global_intercept
                
            predictions[i] = pred
            
        return predictions

def train_gwr_baseline(date_str: str) -> GeographicallyWeightedRegression:
    """Convenience helper to fit GWR on simulated aligned data."""
    # Create mock CPCB ground stations (10 key cities)
    station_coords = np.array([
        [28.6139, 77.2090], # Delhi
        [19.0760, 72.8777], # Mumbai
        [22.5726, 88.3639], # Kolkata
        [13.0827, 80.2707], # Chennai
        [12.9716, 77.5946], # Bengaluru
        [17.3850, 78.4867], # Hyderabad
        [22.7196, 75.8577], # Indore
        [26.8467, 80.9462], # Lucknow
        [25.6093, 85.1376], # Patna
        [23.0225, 72.5714], # Ahmedabad
    ], dtype=np.float32)
    
    # Mock aligned inputs
    # AOD values: higher in north/east, lower in south/west
    aod_values = np.array([0.75, 0.32, 0.61, 0.22, 0.25, 0.28, 0.40, 0.58, 0.65, 0.38], dtype=np.float32)
    
    # Ground truth CPCB PM2.5 readings (ug/m^3)
    pm25_readings = np.array([165.0, 48.0, 110.0, 32.0, 35.0, 42.0, 68.0, 95.0, 130.0, 62.0], dtype=np.float32)
    
    gwr = GeographicallyWeightedRegression(bandwidth=2.0)
    gwr.fit(station_coords, aod_values, pm25_readings)
    return gwr
