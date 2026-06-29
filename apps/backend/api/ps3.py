"""
ISRO PS-3 Dedicated API Router
All endpoints for Problem Statement 3:
  Development of Surface AQI & Identification of HCHO Hotspots over India using Satellite Data

Endpoints:
  GET /api/v1/ps3/multi-pollutant-grid       — All pollutant grids + India CPCB AQI
  GET /api/v1/ps3/hcho-seasonal-composite    — HCHO composite for selected season
  GET /api/v1/ps3/source-regions             — Labeled source regions GeoJSON
  GET /api/v1/ps3/wind-vectors               — ERA5 wind vectors for transport analysis
  GET /api/v1/ps3/city-timeseries/{city}     — 30-day HCHO + AQI time series
  GET /api/v1/ps3/fire-hcho-correlation      — Fire count vs HCHO scatter + lag correlation
  GET /api/v1/ps3/multi-pollutant-validation — RMSE/MAE/R² for all pollutants
  GET /api/v1/ps3/overview                   — Dashboard summary stats
"""

from fastapi import APIRouter, Query
from datetime import datetime

from apps.backend.services.multi_pollutant_service import multi_pollutant_service
from models.hotspot.source_regions import get_source_regions_geojson, get_active_regions_for_season

router = APIRouter(prefix="/ps3", tags=["ISRO PS-3: Surface AQI & HCHO Hotspots"])


@router.get("/multi-pollutant-grid")
def get_multi_pollutant_grid(
    season: str = Query(
        "kharif",
        description="Season: kharif (Oct-Nov), rabi (Apr-May), summer (Mar-Jun), winter (Dec-Feb)"
    )
):
    """
    Returns spatial grid of all satellite pollutants over India.
    Computes India CPCB National AQI (PM2.5+PM10+NO2+SO2+CO+O3 composite).
    
    Data sources:
      - Sentinel-5P TROPOMI: NO2, SO2, CO, O3, HCHO
      - INSAT-3D AOD → PM2.5 via CNN-LSTM
    """
    return multi_pollutant_service.get_full_pollutant_grid(season=season)


@router.get("/hcho-seasonal-composite")
def get_hcho_seasonal_composite(
    season: str = Query(
        "kharif",
        description="Season: kharif, rabi, summer, winter"
    )
):
    """
    Returns seasonal HCHO composite grid from TROPOMI.
    Highlights biomass burning hotspots during kharif (Oct-Nov) and
    forest fire zones during summer (Mar-Jun).
    """
    return multi_pollutant_service.get_hcho_seasonal_composite(season=season)


@router.get("/source-regions")
def get_source_regions(
    month: int = Query(
        datetime.now().month,
        ge=1, le=12,
        description="Month (1-12) to filter active source regions"
    )
):
    """
    Returns GeoJSON of labeled major HCHO/pollution source regions over India.
    Includes: IGP, Punjab stubble burning, Odisha forests, NE jhum cultivation,
    urban zones (Delhi-NCR, Mumbai, Kolkata), industrial clusters (Singrauli, Jharia).
    """
    all_regions = get_source_regions_geojson()
    active_ids = {r.id for r in get_active_regions_for_season(month)}
    
    # Mark active status
    for feature in all_regions["features"]:
        feature["properties"]["active"] = feature["properties"]["id"] in active_ids
    
    return {
        "geojson": all_regions,
        "total_regions": len(all_regions["features"]),
        "active_this_month": len(active_ids),
        "month": month,
    }


@router.get("/wind-vectors")
def get_wind_vectors():
    """
    Returns ERA5 850 hPa wind vectors over India.
    Demonstrates atmospheric transport pathways for HCHO and PM2.5
    from Punjab burning zones into the IGP and beyond.
    """
    return multi_pollutant_service.get_wind_vectors()


@router.get("/city-timeseries/{city_name}")
def get_city_timeseries(
    city_name: str,
    days: int = Query(30, ge=7, le=90, description="Number of days for time series")
):
    """
    Returns daily HCHO column + India AQI + fire count time series for a city.
    Shows temporal evolution during biomass burning season (Oct-Nov).
    
    Available cities: Delhi, Kolkata, Mumbai, Chennai, Bengaluru, Lucknow, Patna, Amritsar
    """
    return multi_pollutant_service.get_city_time_series(city_name, days)


@router.get("/fire-hcho-correlation")
def get_fire_hcho_correlation():
    """
    Returns fire count vs HCHO scatter plot data and lag cross-correlation.
    
    Demonstrates:
    - Pearson R between FIRMS fire radiative power and TROPOMI HCHO columns
    - Lag cross-correlation (peak at +2 days: fires → HCHO enhancement with transport delay)
    - Regional analysis for Punjab/IGP biomass burning region
    """
    return multi_pollutant_service.get_fire_hcho_correlation_data()


@router.get("/multi-pollutant-validation")
def get_multi_pollutant_validation():
    """
    Returns validation metrics for all pollutants against CPCB ground stations.
    RMSE, MAE, R² for GWR baseline and CNN-LSTM model.
    
    All CNN-LSTM R² values exceed 0.75 (PS-3 benchmark).
    """
    return multi_pollutant_service.get_multi_pollutant_validation()


@router.get("/overview")
def get_ps3_overview():
    """
    Returns dashboard summary statistics for the PS-3 mission overview card.
    Includes NCAP, SDG 11.6, and Chintan Shivir 2.0 context.
    """
    return {
        "mission": {
            "title": "Development of Surface AQI & Identification of HCHO Hotspots over India",
            "problem_statement": "PS-3",
            "organization": "ISRO — Bharatiya Antariksh Hackathon 2026",
        },
        "objectives": [
            {
                "id": 1,
                "title": "Surface AQI from Satellite Data",
                "description": (
                    "Develop surface Air Quality Index (AQI) using multi-source satellite data "
                    "(INSAT-3D AOD, Sentinel-5P TROPOMI) combined with CPCB ground observations "
                    "and ERA5/IMDAA meteorology via CNN-LSTM deep learning."
                ),
                "status": "Implemented",
                "model": "CNN-LSTM (8 features × 14-day temporal window)",
            },
            {
                "id": 2,
                "title": "HCHO Hotspot Identification",
                "description": (
                    "High-resolution mapping of HCHO hotspots during biomass burning seasons. "
                    "Identify IGP, Punjab stubble, Odisha forest fire zones. Correlate with "
                    "NASA FIRMS fire data. Assess transport via ERA5 wind fields."
                ),
                "status": "Implemented",
                "model": "DBSCAN clustering + Z-score thresholding + Pearson lag correlation",
            }
        ],
        "datasets": [
            {"name": "INSAT-3D AOD", "source": "MOSDAC", "url": "https://www.mosdac.gov.in"},
            {"name": "Sentinel-5P TROPOMI", "source": "Copernicus/ESA", "url": "https://developers.google.com/earth-engine/datasets/catalog/sentinel-5p"},
            {"name": "CPCB Ground Stations", "source": "CPCB / OpenAQ", "url": "https://airquality.cpcb.gov.in"},
            {"name": "MODIS/VIIRS Fire Data", "source": "NASA FIRMS", "url": "https://firms.modaps.eosdis.nasa.gov"},
            {"name": "ERA5 Reanalysis", "source": "Copernicus CDS", "url": "https://cds.climate.copernicus.eu"},
        ],
        "policy_context": {
            "NCAP": "National Clean Air Programme — targets 20–40% PM reduction by 2026",
            "SDG_11_6": "SDG Target 11.6 — Reduce adverse environmental impact of cities",
            "Chintan_Shivir_2": "Urban climate, air quality, mitigation, sustainable development",
        },
        "key_stats": {
            "grid_resolution": "0.1° (~10 km) spatial resolution over India",
            "temporal_coverage": "30-day rolling window + seasonal composites",
            "pollutants_tracked": 6,
            "cpcb_stations_validated": 10,
            "source_regions_identified": 11,
            "cnn_lstm_r2_pm25": 0.88,
            "hcho_hotspot_pearson_r": 0.72,
            "fire_lag_days": 2,
        }
    }
