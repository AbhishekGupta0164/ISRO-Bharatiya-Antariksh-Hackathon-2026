#!/usr/bin/env python3
"""
NASA FIRMS Active Fire Fetcher
Queries NASA FIRMS API to get MODIS C6.1/VIIRS active fires over India.
Falls back to a simulated active fire CSV when offline.
"""

import os
import argparse
from datetime import datetime
import pandas as pd
import requests

def generate_mock_fires(date_str: str, out_path: str):
    """Generates mock active fire CSV entries matching biomass burning regions in India."""
    print(f"[SIMULATOR] Generating mock active fire CSV for {date_str}...")
    
    # Coordinates of typical hotspots in India
    # 1. Punjab agricultural fires (Lat 30-31, Lon 74-76) in Oct-Nov
    # 2. Odisha/Chhattisgarh forest fires (Lat 19-22, Lon 81-84) in Mar-Apr
    # 3. Industrial IGP emissions general
    
    num_fires = 120
    lats = []
    lons = []
    frps = [] # Fire Radiative Power (MW)
    
    # Punjab cluster
    for _ in range(60):
        lats.append(np_random_cluster_point(30.6, 0.4))
        lons.append(np_random_cluster_point(75.6, 0.4))
        frps.append(float(np.random.exponential(45.0) + 10.0))
        
    # Odisha / Central India cluster
    for _ in range(40):
        lats.append(np_random_cluster_point(21.2, 0.8))
        lons.append(np_random_cluster_point(82.5, 0.8))
        frps.append(float(np.random.exponential(30.0) + 5.0))
        
    # Scatter other fires
    for _ in range(20):
        lats.append(float(np.random.uniform(8.0, 34.0)))
        lons.append(float(np.random.uniform(69.0, 95.0)))
        frps.append(float(np.random.exponential(15.0) + 2.0))
        
    df = pd.DataFrame({
        "latitude": lats,
        "longitude": lons,
        "frp": frps,
        "acq_date": [date_str] * num_fires,
        "satellite": ["MODIS"] * 60 + ["VIIRS"] * 60
    })
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[OK] Mock NASA FIRMS fire file saved to: {out_path}")

def np_random_cluster_point(center, std):
    import numpy as np
    return float(np.random.normal(center, std))

def fetch_firms_fires(date_str: str, out_path: str, simulate: bool = False):
    """Fetch from NASA FIRMS API. Fall back to simulation on error."""
    if simulate:
        generate_mock_fires(date_str, out_path)
        return out_path
        
    # FIRMS requires a MAP_KEY. Standard country queries:
    map_key = os.getenv("FIRMS_MAP_KEY")
    if not map_key:
        print("[WARN] NASA FIRMS MAP_KEY environment variable not set. Falling back to simulation.")
        generate_mock_fires(date_str, out_path)
        return out_path
        
    print(f"Requesting active fire data from NASA FIRMS for {date_str}...")
    try:
        # Query MODIS C6.1 active fires for India (IND)
        url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{map_key}/MODIS_SP/IND/1/{date_str}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        
        # Save to local file
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(resp.text)
        print(f"[OK] NASA FIRMS fire file downloaded to: {out_path}")
        return out_path
        
    except Exception as e:
        print(f"[WARN] NASA FIRMS fetch failed: {e}. Falling back to simulation mode.")
        generate_mock_fires(date_str, out_path)
        return out_path

import numpy as np # Needed for mock generation helper

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch NASA FIRMS Active Fires")
    parser.add_argument("--date", default=datetime.today().strftime("%Y-%m-%d"), help="Date in YYYY-MM-DD format")
    parser.add_argument("--out", default="data/firms/active_fires.csv", help="Output CSV path")
    parser.add_argument("--simulate", action="store_true", default=True, help="Force simulation mode")
    
    args = parser.parse_args()
    fetch_firms_fires(args.date, args.out, args.simulate)
