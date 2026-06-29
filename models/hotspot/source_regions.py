"""
Source Region Identification Module
Identifies and classifies major HCHO/pollution source regions over India.

Source categories:
  1. Agricultural Burning — Punjab, Haryana, western UP (Oct-Nov Kharif; Apr-May Rabi)
  2. Forest Fires — Odisha, Chhattisgarh, Uttarakhand, Himachal Pradesh (Mar-May)
  3. Industrial — Indo-Gangetic Plain industrial belt, Jharia coalfield
  4. Urban Emission — Metro cities (Delhi, Mumbai, Kolkata, Chennai)
  5. Background — Remainder of India

Reference: NCAP (National Clean Air Programme), SDG 11.6
"""

from dataclasses import dataclass, field
from typing import List, Tuple

# -----------------------------------------------------------------------
# Source Region Definitions
# Each region: (name, lat_min, lat_max, lon_min, lon_max, category, season, description)
# -----------------------------------------------------------------------

@dataclass
class SourceRegion:
    id: str
    name: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    category: str          # agricultural / forest / industrial / urban / background
    season: str            # kharif (Oct-Nov) / rabi (Apr-May) / year-round / summer
    description: str
    color: str             # Hex for map rendering
    centroid_lat: float = 0.0
    centroid_lon: float = 0.0
    
    def __post_init__(self):
        self.centroid_lat = (self.lat_min + self.lat_max) / 2
        self.centroid_lon = (self.lon_min + self.lon_max) / 2


# Known major source regions over India
KNOWN_SOURCE_REGIONS: List[SourceRegion] = [
    # ---- Agricultural Burning ----
    SourceRegion(
        id="punjab_stubble",
        name="Punjab Stubble Burning",
        lat_min=29.5, lat_max=32.5,
        lon_min=73.5, lon_max=77.0,
        category="agricultural",
        season="kharif (Oct–Nov)",
        description=(
            "Largest agricultural fire hotspot in India. Post-Kharif paddy harvest "
            "results in widespread stubble burning, releasing massive HCHO, CO and PM2.5 "
            "plumes that transport into Delhi-NCR via north-westerly winds."
        ),
        color="#ff6b00",
    ),
    SourceRegion(
        id="haryana_burning",
        name="Haryana Crop Residue Burning",
        lat_min=28.5, lat_max=30.5,
        lon_min=74.5, lon_max=77.5,
        category="agricultural",
        season="kharif (Oct–Nov) & rabi (Apr–May)",
        description=(
            "Haryana contributes significantly to the Indo-Gangetic Plain biomass burning "
            "with dual-season fires. HCHO enhancement of 3–6×10¹⁵ mol/cm² observed "
            "during peak burning days."
        ),
        color="#ff8c00",
    ),
    SourceRegion(
        id="up_western_burning",
        name="Western Uttar Pradesh Agricultural Fires",
        lat_min=26.5, lat_max=29.5,
        lon_min=77.0, lon_max=82.0,
        category="agricultural",
        season="kharif (Oct–Nov)",
        description=(
            "Western UP belt contributes to the eastward extension of the IGP burning plume. "
            "MODIS/VIIRS fire counts peak at 200–400/day during October."
        ),
        color="#ffa500",
    ),
    
    # ---- Indo-Gangetic Plain ----
    SourceRegion(
        id="igp_main",
        name="Indo-Gangetic Plain (IGP) Core",
        lat_min=25.0, lat_max=30.5,
        lon_min=75.0, lon_max=88.0,
        category="industrial",
        season="year-round",
        description=(
            "The IGP is India's most polluted airshed year-round. High population density, "
            "industrial activity, vehicle emissions, and crop burning combine to produce "
            "persistent AQI > 200. PM2.5 often exceeds 150 µg/m³ in winter (Dec-Feb) "
            "due to temperature inversions trapping pollutants."
        ),
        color="#e63946",
    ),
    
    # ---- Forest Fires ----
    SourceRegion(
        id="odisha_forest",
        name="Odisha–Chhattisgarh Forest Fires",
        lat_min=18.5, lat_max=23.0,
        lon_min=80.0, lon_max=86.5,
        category="forest",
        season="summer (Mar–May)",
        description=(
            "One of India's highest forest fire zones. Dry deciduous forests ignite in pre-monsoon "
            "months (Mar–May), releasing large VOC plumes. HCHO columns peak at 4–8×10¹⁵ mol/cm² "
            "during severe fire years."
        ),
        color="#8b4513",
    ),
    SourceRegion(
        id="uttarakhand_forest",
        name="Uttarakhand–Himachal Forest Fires",
        lat_min=29.0, lat_max=32.5,
        lon_min=77.0, lon_max=81.0,
        category="forest",
        season="summer (Apr–Jun)",
        description=(
            "High-altitude conifer and oak forests in the Himalayan foothills are susceptible "
            "to intense fire seasons during drought years. Smoke plumes affect air quality "
            "across Delhi-NCR via valley channeling."
        ),
        color="#6b3a2a",
    ),
    SourceRegion(
        id="northeast_forest",
        name="Northeast India Forest Fires",
        lat_min=23.0, lat_max=27.5,
        lon_min=91.0, lon_max=97.0,
        category="forest",
        season="summer (Feb–Apr)",
        description=(
            "Jhum (slash-and-burn) cultivation and dry season fires in Mizoram, Manipur, "
            "and Nagaland contribute significantly to HCHO enhancements over Northeast India "
            "during pre-monsoon months."
        ),
        color="#7b4f2e",
    ),
    
    # ---- Urban Emission Zones ----
    SourceRegion(
        id="delhi_ncr",
        name="Delhi-NCR Urban Emission Zone",
        lat_min=28.0, lat_max=29.0,
        lon_min=76.5, lon_max=78.0,
        category="urban",
        season="year-round",
        description=(
            "Delhi-NCR is consistently India's most polluted urban cluster. Vehicle exhaust, "
            "construction dust, industrial units, and biomass transport create extreme PM2.5 "
            "and NO2 levels. Winter AQI frequently exceeds 400 (Severe category)."
        ),
        color="#c0392b",
    ),
    SourceRegion(
        id="mumbai_urban",
        name="Mumbai–Pune Urban Corridor",
        lat_min=18.0, lat_max=20.5,
        lon_min=72.5, lon_max=74.5,
        category="urban",
        season="year-round",
        description=(
            "Dense vehicular traffic, shipping emissions from Mumbai port, and industrial "
            "zones in Pune contribute to moderate-poor AQI year-round. O3 levels are "
            "elevated due to high NOx + VOC precursor mix."
        ),
        color="#e74c3c",
    ),
    SourceRegion(
        id="kolkata_urban",
        name="Kolkata Urban Emission Zone",
        lat_min=22.0, lat_max=23.0,
        lon_min=87.5, lon_max=89.0,
        category="urban",
        season="year-round",
        description=(
            "Kolkata's dense industrial belt (Hooghly river corridor) and high vehicular density "
            "lead to chronic PM2.5 and NO2 pollution. Proximity to the Damodar Valley "
            "coalfields adds SO2 background."
        ),
        color="#d35400",
    ),
    
    # ---- Industrial/Coal ----
    SourceRegion(
        id="jharia_coalfield",
        name="Jharia–Damodar Coalfield (Jharkhand)",
        lat_min=23.5, lat_max=24.5,
        lon_min=85.5, lon_max=87.0,
        category="industrial",
        season="year-round",
        description=(
            "Coal mine fires in Jharia coalfield have burned for decades, emitting continuous "
            "SO2, CO, and particulate matter. The region shows persistent TROPOMI SO2 column "
            "enhancements of 2–5 DU above background."
        ),
        color="#7f8c8d",
    ),
]


def get_source_regions_geojson() -> dict:
    """
    Returns all source regions as a GeoJSON FeatureCollection for frontend rendering.
    """
    features = []
    for region in KNOWN_SOURCE_REGIONS:
        features.append({
            "type": "Feature",
            "properties": {
                "id": region.id,
                "name": region.name,
                "category": region.category,
                "season": region.season,
                "description": region.description,
                "color": region.color,
                "centroid_lat": region.centroid_lat,
                "centroid_lon": region.centroid_lon,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [region.lon_min, region.lat_min],
                    [region.lon_max, region.lat_min],
                    [region.lon_max, region.lat_max],
                    [region.lon_min, region.lat_max],
                    [region.lon_min, region.lat_min],
                ]]
            }
        })
    
    return {"type": "FeatureCollection", "features": features}


def classify_hotspot_to_source(centroid_lat: float, centroid_lon: float) -> SourceRegion | None:
    """
    Classifies a detected HCHO hotspot (centroid) to a known source region.
    Returns the first matching source region, or None if unclassified.
    """
    for region in KNOWN_SOURCE_REGIONS:
        if (region.lat_min <= centroid_lat <= region.lat_max and
                region.lon_min <= centroid_lon <= region.lon_max):
            return region
    return None


def get_active_regions_for_season(month: int) -> List[SourceRegion]:
    """
    Returns source regions active during the given month.
    month: 1-12
    """
    active = []
    for region in KNOWN_SOURCE_REGIONS:
        # Urban and industrial are year-round
        if region.season == "year-round":
            active.append(region)
        # Kharif stubble burning: Oct-Nov
        elif "kharif" in region.season and month in [10, 11]:
            active.append(region)
        # Rabi crop burning: Apr-May
        elif "rabi" in region.season and month in [4, 5]:
            active.append(region)
        # Summer forest fires: Mar-Jun
        elif "summer" in region.season and month in [3, 4, 5, 6]:
            active.append(region)
    return active


if __name__ == "__main__":
    import json
    gj = get_source_regions_geojson()
    print(f"Total source regions: {len(gj['features'])}")
    for f in gj["features"]:
        p = f["properties"]
        print(f"  [{p['category'].upper():12}] {p['name']} ({p['season']})")
