"""
India National AQI Calculator (CPCB Standard)
Implements the official Central Pollution Control Board (CPCB) AQI formula
for India as per the National Air Quality Index specification.

Reference: CPCB AQI Technical Document
https://cpcb.nic.in/uploads/Projects/AQI/AQI-India.pdf

Pollutants considered:
  PM2.5, PM10, NO2, SO2, CO, O3, NH3, Pb
  India AQI = MAX of all sub-indices (unlike US EPA which uses the highest)
"""

import numpy as np

# -----------------------------------------------------------------------
# CPCB India AQI Breakpoint Tables
# Format: [(C_low, C_high, I_low, I_high), ...] for each pollutant
# -----------------------------------------------------------------------

# PM2.5 (µg/m³, 24-hour average)
PM25_BREAKPOINTS = [
    (0.0,   30.0,   0,   50),
    (30.1,  60.0,  51,  100),
    (60.1,  90.0, 101,  200),
    (90.1, 120.0, 201,  300),
    (120.1, 250.0, 301, 400),
    (250.1, 380.0, 401, 500),
]

# PM10 (µg/m³, 24-hour average)
PM10_BREAKPOINTS = [
    (0.0,   50.0,   0,   50),
    (50.1,  100.0,  51,  100),
    (100.1, 250.0, 101,  200),
    (250.1, 350.0, 201,  300),
    (350.1, 430.0, 301,  400),
    (430.1, 600.0, 401,  500),
]

# NO2 (µg/m³, 24-hour average)
NO2_BREAKPOINTS = [
    (0.0,   40.0,   0,   50),
    (40.1,  80.0,  51,  100),
    (80.1,  180.0, 101,  200),
    (180.1, 280.0, 201,  300),
    (280.1, 400.0, 301,  400),
    (400.1, 800.0, 401,  500),
]

# SO2 (µg/m³, 24-hour average)
SO2_BREAKPOINTS = [
    (0.0,   40.0,   0,   50),
    (40.1,  80.0,  51,  100),
    (80.1,  380.0, 101,  200),
    (380.1, 800.0, 201,  300),
    (800.1, 1600.0, 301, 400),
    (1600.1, 2620.0, 401, 500),
]

# CO (mg/m³, 8-hour average)
CO_BREAKPOINTS = [
    (0.0,   1.0,    0,   50),
    (1.1,   2.0,   51,  100),
    (2.1,  10.0,  101,  200),
    (10.1, 17.0,  201,  300),
    (17.1, 34.0,  301,  400),
    (34.1, 46.0,  401,  500),
]

# O3 (µg/m³, 8-hour average)
O3_BREAKPOINTS = [
    (0.0,   50.0,   0,   50),
    (50.1,  100.0,  51,  100),
    (100.1, 168.0, 101,  200),
    (168.1, 208.0, 201,  300),
    (208.1, 748.0, 301,  400),
    (748.1, 1000.0, 401, 500),
]

# AQI Category definitions (India CPCB)
AQI_CATEGORIES = [
    (0,   50,  "Good",        "#00e400", "Minimal impact"),
    (51,  100, "Satisfactory","#92d050", "Minor breathing discomfort to sensitive people"),
    (101, 200, "Moderate",    "#ffff00", "Breathing discomfort to people with lung/heart disease"),
    (201, 300, "Poor",        "#ff7e00", "Breathing discomfort to most on prolonged exposure"),
    (301, 400, "Very Poor",   "#ff0000", "Respiratory illness on prolonged exposure"),
    (401, 500, "Severe",      "#7e0023", "Affects healthy people; serious risk to sensitive groups"),
]


def _compute_sub_index(concentration: float, breakpoints: list) -> int:
    """Computes the AQI sub-index for a given concentration using CPCB formula."""
    if concentration < 0:
        return 0
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= concentration <= c_high:
            # Linear interpolation
            return int(round(
                (i_high - i_low) / (c_high - c_low) * (concentration - c_low) + i_low
            ))
    # Beyond maximum range
    return 500


def compute_india_aqi(
    pm25: float = None,
    pm10: float = None,
    no2: float = None,
    so2: float = None,
    co: float = None,
    o3: float = None,
) -> dict:
    """
    Computes the India National AQI (CPCB standard).
    
    India AQI = MAX of all individual pollutant sub-indices.
    At least one pollutant must be provided.
    
    Args:
        pm25: PM2.5 concentration in µg/m³ (24-hr avg)
        pm10: PM10 concentration in µg/m³ (24-hr avg)
        no2:  NO2 concentration in µg/m³ (24-hr avg)
        so2:  SO2 concentration in µg/m³ (24-hr avg)
        co:   CO concentration in mg/m³ (8-hr avg)
        o3:   O3 concentration in µg/m³ (8-hr avg)
    
    Returns:
        dict with:
          - aqi: composite India AQI (0-500)
          - dominant_pollutant: which pollutant drives the AQI
          - category: AQI category name
          - color: hex color for visualization
          - health_message: health advisory string
          - sub_indices: individual sub-index values
    """
    sub_indices = {}
    
    if pm25 is not None:
        sub_indices["PM2.5"] = _compute_sub_index(pm25, PM25_BREAKPOINTS)
    if pm10 is not None:
        sub_indices["PM10"] = _compute_sub_index(pm10, PM10_BREAKPOINTS)
    if no2 is not None:
        sub_indices["NO2"] = _compute_sub_index(no2, NO2_BREAKPOINTS)
    if so2 is not None:
        sub_indices["SO2"] = _compute_sub_index(so2, SO2_BREAKPOINTS)
    if co is not None:
        sub_indices["CO"] = _compute_sub_index(co, CO_BREAKPOINTS)
    if o3 is not None:
        sub_indices["O3"] = _compute_sub_index(o3, O3_BREAKPOINTS)
    
    if not sub_indices:
        return {"aqi": 0, "dominant_pollutant": "N/A", "category": "Unknown",
                "color": "#808080", "health_message": "No data", "sub_indices": {}}
    
    # India AQI is the MAXIMUM of all sub-indices (CPCB standard)
    dominant = max(sub_indices, key=sub_indices.get)
    aqi_value = sub_indices[dominant]
    
    # Determine category
    category = "Severe"
    color = "#7e0023"
    health_message = "Affects healthy people; serious risk to sensitive groups"
    
    for i_low, i_high, cat, col, msg in AQI_CATEGORIES:
        if i_low <= aqi_value <= i_high:
            category = cat
            color = col
            health_message = msg
            break
    
    return {
        "aqi": aqi_value,
        "dominant_pollutant": dominant,
        "category": category,
        "color": color,
        "health_message": health_message,
        "sub_indices": sub_indices,
    }


def compute_india_aqi_grid(
    pm25_grid: np.ndarray,
    pm10_grid: np.ndarray = None,
    no2_grid: np.ndarray = None,
    so2_grid: np.ndarray = None,
    co_grid: np.ndarray = None,
    o3_grid: np.ndarray = None,
) -> np.ndarray:
    """
    Vectorized India AQI computation for a 2D spatial grid.
    
    Returns:
        aqi_grid: 2D array of India AQI values (same shape as pm25_grid)
    """
    shape = pm25_grid.shape
    aqi_grid = np.zeros(shape, dtype=np.int32)
    
    # Compute PM2.5 sub-index (always present)
    pm25_sub = np.vectorize(lambda v: _compute_sub_index(float(v), PM25_BREAKPOINTS))(pm25_grid)
    aqi_grid = np.maximum(aqi_grid, pm25_sub)
    
    if pm10_grid is not None:
        pm10_sub = np.vectorize(lambda v: _compute_sub_index(float(v), PM10_BREAKPOINTS))(pm10_grid)
        aqi_grid = np.maximum(aqi_grid, pm10_sub)
    
    if no2_grid is not None:
        no2_sub = np.vectorize(lambda v: _compute_sub_index(float(v), NO2_BREAKPOINTS))(no2_grid)
        aqi_grid = np.maximum(aqi_grid, no2_sub)
    
    if so2_grid is not None:
        so2_sub = np.vectorize(lambda v: _compute_sub_index(float(v), SO2_BREAKPOINTS))(so2_grid)
        aqi_grid = np.maximum(aqi_grid, so2_sub)
    
    if co_grid is not None:
        co_sub = np.vectorize(lambda v: _compute_sub_index(float(v), CO_BREAKPOINTS))(co_grid)
        aqi_grid = np.maximum(aqi_grid, co_sub)
    
    if o3_grid is not None:
        o3_sub = np.vectorize(lambda v: _compute_sub_index(float(v), O3_BREAKPOINTS))(o3_grid)
        aqi_grid = np.maximum(aqi_grid, o3_sub)
    
    return aqi_grid


def get_aqi_category(aqi_value: int) -> dict:
    """Returns the category info for a given AQI value."""
    for i_low, i_high, cat, col, msg in AQI_CATEGORIES:
        if i_low <= aqi_value <= i_high:
            return {"category": cat, "color": col, "health_message": msg}
    return {"category": "Severe", "color": "#7e0023", "health_message": "Very high pollution"}


if __name__ == "__main__":
    # Validation test: typical Delhi winter values
    result = compute_india_aqi(
        pm25=168.0,
        pm10=285.0,
        no2=95.0,
        so2=42.0,
        co=3.2,
        o3=55.0,
    )
    print("=== India CPCB AQI Test (Delhi Winter) ===")
    print(f"India AQI:          {result['aqi']}")
    print(f"Dominant Pollutant: {result['dominant_pollutant']}")
    print(f"Category:           {result['category']}")
    print(f"Sub-indices:        {result['sub_indices']}")
    print(f"Color:              {result['color']}")
    print()
    
    # Mumbai test
    result2 = compute_india_aqi(pm25=45.0, pm10=82.0, no2=60.0, so2=25.0, co=1.5)
    print("=== India CPCB AQI Test (Mumbai) ===")
    print(f"India AQI:          {result2['aqi']}")
    print(f"Dominant Pollutant: {result2['dominant_pollutant']}")
    print(f"Category:           {result2['category']}")
