from fastapi import APIRouter
import numpy as np

from apps.backend.services.satellite_aqi_service import satellite_service
from apps.backend.services.route_service import get_hcho_hotspots

router = APIRouter(tags=["Satellite Data Layer"])

@router.get("/satellite/pm25-grid")
def get_satellite_pm25_grid():
    """Returns the 300x300 satellite PM2.5/AQI grid downsampled to 0.5 degree resolution for performance."""
    pm25_grid, aqi_grid = satellite_service.get_latest_satellite_grid()
    
    lats = np.arange(7.0, 37.0, 0.5)
    lons = np.arange(68.0, 98.0, 0.5)
    
    downsampled = []
    for r_idx, lat in enumerate(lats):
        grid_r = int(np.clip(r_idx * 5, 0, 299))
        for c_idx, lon in enumerate(lons):
            grid_c = int(np.clip(c_idx * 5, 0, 299))
            
            pm25_val = float(pm25_grid[grid_r, grid_c])
            aqi_val = int(aqi_grid[grid_r, grid_c])
            
            downsampled.append({
                "lat": float(lat),
                "lon": float(lon),
                "pm25": pm25_val,
                "aqi": aqi_val
            })
            
    return {"grid": downsampled, "resolution": 0.5, "count": len(downsampled)}

@router.get("/satellite/hotspots")
def get_satellite_hotspots():
    """Returns HCHO hotspot clusters detected by TROPOMI HCHO gridding and DBSCAN."""
    hotspots = get_hcho_hotspots()
    return {
        "hotspots": [
            {
                "id": hs.id,
                "centroid_lat": hs.centroid_lat,
                "centroid_lon": hs.centroid_lon,
                "cell_count": hs.cell_count,
                "mean_hcho": hs.mean_hcho,
                "cells": hs.cells
            }
            for hs in hotspots
        ],
        "count": len(hotspots)
    }

@router.get("/satellite/validation")
def get_satellite_validation_report():
    """Generates the CPCB Ground Truth validation table."""
    from models.validation.cpcb_validator import validate_models
    report_md = validate_models()
    return {"report": report_md}
