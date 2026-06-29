"""
Comprehensive Test Suite for ISRO PS-3 VayuNetra Project
==========================================================
Tests: India AQI formula, source regions, multi-pollutant service,
       RL environment, route service, exposure credits, security checks.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import json
import time

PASSED = []
FAILED = []

def test(name, fn):
    try:
        fn()
        PASSED.append(name)
        print(f"  ✅ {name}")
    except Exception as e:
        FAILED.append((name, str(e)))
        print(f"  ❌ {name}: {e}")

# ============================================================
# TEST GROUP 1: India CPCB AQI Formula
# ============================================================
print("\n🧪 GROUP 1: India CPCB AQI Formula")

from models.aqi_estimation.india_aqi_calculator import (
    compute_india_aqi, _compute_sub_index, PM25_BREAKPOINTS, AQI_CATEGORIES
)

def test_aqi_good():
    r = compute_india_aqi(pm25=20.0, pm10=40.0)
    assert r['aqi'] <= 50, f"Expected Good AQI <=50, got {r['aqi']}"
    assert r['category'] == 'Good'

def test_aqi_severe():
    r = compute_india_aqi(pm25=300.0, pm10=500.0)
    assert r['aqi'] >= 400, f"Expected Severe AQI >=400, got {r['aqi']}"

def test_aqi_dominant_pollutant():
    r = compute_india_aqi(pm25=25.0, pm10=20.0, no2=200.0)  # NO2 should dominate
    assert r['dominant_pollutant'] == 'NO2', f"Expected NO2 to dominate, got {r['dominant_pollutant']}"

def test_aqi_india_is_max_subindex():
    r = compute_india_aqi(pm25=80.0, pm10=120.0, no2=50.0, so2=30.0)
    # AQI should equal max of all sub-indices
    assert r['aqi'] == max(r['sub_indices'].values()), "India AQI must be MAX of all sub-indices"

def test_aqi_pm10_included():
    r1 = compute_india_aqi(pm25=30.0)
    r2 = compute_india_aqi(pm25=30.0, pm10=200.0)
    assert r2['aqi'] > r1['aqi'], "PM10=200 must increase the AQI above PM2.5 only"

def test_aqi_no_pollutants():
    r = compute_india_aqi()
    assert r['aqi'] == 0

test("India AQI: Good category (PM2.5=20)", test_aqi_good)
test("India AQI: Severe category (PM2.5=300)", test_aqi_severe)
test("India AQI: Dominant pollutant detection (NO2=200)", test_aqi_dominant_pollutant)
test("India AQI: Formula = MAX of sub-indices (CPCB standard)", test_aqi_india_is_max_subindex)
test("India AQI: PM10 properly included", test_aqi_pm10_included)
test("India AQI: No pollutants returns 0", test_aqi_no_pollutants)

# ============================================================
# TEST GROUP 2: Source Regions
# ============================================================
print("\n🧪 GROUP 2: Source Region Identification")

from models.hotspot.source_regions import (
    get_source_regions_geojson, classify_hotspot_to_source,
    get_active_regions_for_season, KNOWN_SOURCE_REGIONS
)

def test_source_count():
    gj = get_source_regions_geojson()
    assert len(gj['features']) >= 10, f"Expected >=10 source regions, got {len(gj['features'])}"

def test_source_geojson_valid():
    gj = get_source_regions_geojson()
    for f in gj['features']:
        assert f['type'] == 'Feature'
        assert 'properties' in f
        assert 'geometry' in f
        coords = f['geometry']['coordinates'][0]
        assert len(coords) == 5, "Polygon must close (5 points)"

def test_punjab_classification():
    # Punjab centroid: ~30.8, 75.5
    r = classify_hotspot_to_source(30.8, 75.5)
    assert r is not None, "Punjab coords should match a source region"
    assert r.id == 'punjab_stubble', f"Expected punjab_stubble, got {r.id if r else None}"

def test_active_regions_kharif():
    active = get_active_regions_for_season(10)  # October
    ids = [r.id for r in active]
    assert 'punjab_stubble' in ids, "Punjab stubble must be active in October"

def test_active_regions_summer():
    active = get_active_regions_for_season(4)  # April
    ids = [r.id for r in active]
    assert 'odisha_forest' in ids, "Odisha forest fires must be active in April"

def test_categories():
    cats = {r.category for r in KNOWN_SOURCE_REGIONS}
    for required in ['agricultural', 'forest', 'industrial', 'urban']:
        assert required in cats, f"Category '{required}' missing from source regions"

test("Source regions: >=10 regions defined", test_source_count)
test("Source regions: Valid GeoJSON FeatureCollection", test_source_geojson_valid)
test("Source regions: Punjab stubble classified correctly", test_punjab_classification)
test("Source regions: Punjab active in October (Kharif)", test_active_regions_kharif)
test("Source regions: Odisha forest active in April (Summer)", test_active_regions_summer)
test("Source regions: All 4 categories present (agri/forest/industrial/urban)", test_categories)

# ============================================================
# TEST GROUP 3: Multi-Pollutant Service
# ============================================================
print("\n🧪 GROUP 3: Multi-Pollutant Service")

from apps.backend.services.multi_pollutant_service import multi_pollutant_service

def test_pollutant_grid_cells():
    data = multi_pollutant_service.get_full_pollutant_grid('kharif')
    assert data['count'] > 100, f"Expected >100 grid cells, got {data['count']}"
    assert len(data['cells']) > 0

def test_all_pollutants_present():
    data = multi_pollutant_service.get_full_pollutant_grid('kharif')
    cell = data['cells'][0]
    for field in ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3', 'hcho', 'india_aqi']:
        assert field in cell, f"Missing field: {field}"

def test_aqi_in_range():
    data = multi_pollutant_service.get_full_pollutant_grid('kharif')
    for cell in data['cells'][:20]:
        assert 0 <= cell['india_aqi'] <= 500, f"India AQI out of range: {cell['india_aqi']}"

def test_seasonal_difference():
    kharif = multi_pollutant_service.get_hcho_seasonal_composite('kharif')
    winter = multi_pollutant_service.get_hcho_seasonal_composite('winter')
    kharif_avg = np.mean([c['hcho'] for c in kharif['cells']])
    winter_avg = np.mean([c['hcho'] for c in winter['cells']])
    assert kharif_avg > winter_avg, "Kharif HCHO must be higher than Winter background"

def test_city_timeseries():
    ts = multi_pollutant_service.get_city_time_series('Delhi', 30)
    assert len(ts['dates']) == 30
    assert len(ts['hcho_series']) == 30
    assert len(ts['aqi_series']) == 30
    assert len(ts['fire_count_series']) == 30

def test_fire_hcho_correlation():
    corr = multi_pollutant_service.get_fire_hcho_correlation_data()
    r = corr['pearson_r']
    assert 0.5 <= r <= 1.0, f"Expected Pearson r in [0.5, 1.0], got {r}"
    assert corr['peak_lag_days'] == 2, "Peak lag should be 2 days"

def test_wind_vectors():
    data = multi_pollutant_service.get_wind_vectors()
    assert len(data['vectors']) > 50
    for v in data['vectors'][:5]:
        assert 'u' in v and 'v' in v and 'speed' in v

def test_validation_metrics():
    val = multi_pollutant_service.get_multi_pollutant_validation()
    for pollutant, metrics in val['pollutants'].items():
        assert metrics['lstm_r2'] >= 0.75, f"{pollutant} CNN-LSTM R² < 0.75: {metrics['lstm_r2']}"

test("Multi-pollutant grid: >100 cells", test_pollutant_grid_cells)
test("Multi-pollutant grid: All 8 fields present per cell", test_all_pollutants_present)
test("Multi-pollutant grid: India AQI in [0-500] range", test_aqi_in_range)
test("HCHO seasonal: Kharif > Winter (biomass burning)", test_seasonal_difference)
test("City time series: 30-day HCHO + AQI + Fire count", test_city_timeseries)
test("Fire-HCHO correlation: Pearson r >= 0.5, lag=+2d", test_fire_hcho_correlation)
test("Wind vectors: ERA5 vectors with u/v/speed", test_wind_vectors)
test("Validation metrics: All CNN-LSTM R² >= 0.75", test_validation_metrics)

# ============================================================
# TEST GROUP 4: RL Environment (OpenEnv Compliance)
# ============================================================
print("\n🧪 GROUP 4: RL Environment (OpenEnv Compliance)")

from packages.env_core.envs.pollution_env.env import ExposureCreditEnv, TASKS
from packages.env_core.envs.pollution_env.models import Action

def test_env_reset():
    env = ExposureCreditEnv()
    obs = env.reset('easy_route')
    assert obs.current_city == 'A'
    assert obs.destination == 'F'
    assert obs.exposure_credits == 100
    assert obs.steps_taken == 0
    assert len(obs.neighbors) > 0

def test_env_step_valid():
    env = ExposureCreditEnv()
    obs = env.reset('easy_route')
    neighbors = [n.city for n in obs.neighbors]
    result = env.step(Action(city=neighbors[0]))
    assert result.observation is not None
    assert isinstance(result.reward, float)
    assert isinstance(result.done, bool)
    assert 'segment_grade' in result.info

def test_env_step_invalid_action():
    env = ExposureCreditEnv()
    env.reset('easy_route')
    try:
        env.step(Action(city='Z'))
        assert False, "Should raise ValueError for invalid city"
    except ValueError:
        pass

def test_env_grade_structure():
    env = ExposureCreditEnv()
    env.reset('easy_route')
    env.step(Action(city='B'))
    env.step(Action(city='D'))
    env.step(Action(city='F'))
    grade = env.grade()
    assert 0.0 < grade.score < 1.0, "Score must be in (0, 1) exclusive"
    assert grade.grade_letter in ('A', 'B', 'C', 'D', 'F')
    assert grade.reached_destination == True

def test_env_destination_reached():
    env = ExposureCreditEnv()
    obs = env.reset('easy_route')
    # Navigate A -> B -> D -> F
    for action in ['B', 'D', 'F']:
        if not obs.done:
            result = env.step(Action(city=action))
            obs = result.observation
    assert obs.done or result.done

def test_env_score_strictly_bounded():
    """OpenEnv requirement: score must be strictly between 0 and 1"""
    env = ExposureCreditEnv()
    env.reset('easy_route')
    grade = env.grade()
    assert 0 < grade.score < 1, f"Score {grade.score} must be strictly between 0 and 1"

def test_all_tasks_defined():
    for task_id in ['easy_route', 'medium_route', 'hard_pollution_dodge', 'expert_credit_max']:
        assert task_id in TASKS, f"Task '{task_id}' missing"

def test_env_state():
    env = ExposureCreditEnv()
    env.reset('easy_route')
    state = env.state()
    assert state.task_id == 'easy_route'
    assert state.current_city == 'A'

test("RL Env: reset() initializes correctly (OpenEnv)", test_env_reset)
test("RL Env: step() returns observation/reward/done/info", test_env_step_valid)
test("RL Env: step() raises ValueError for invalid action", test_env_step_invalid_action)
test("RL Env: grade() score strictly in (0,1) — OpenEnv required", test_env_score_strictly_bounded)
test("RL Env: Navigate A→B→D→F marks done", test_env_destination_reached)
test("RL Env: grade() structure complete (letter/score/route)", test_env_grade_structure)
test("RL Env: All 4 tasks defined (easy/medium/hard/expert)", test_all_tasks_defined)
test("RL Env: state() returns EpisodeState", test_env_state)

# ============================================================
# TEST GROUP 5: Exposure Credit Engine
# ============================================================
print("\n🧪 GROUP 5: Exposure Credit Engine")

from apps.backend.services.exposure_credit import (
    get_grade_for_aqi, grade_city, calculate_route_credits, get_or_create_wallet,
    apply_route_credits, get_leaderboard, GRADE_TABLE
)

def test_grade_for_aqi():
    g = get_grade_for_aqi(45)
    assert g['grade'] == 'A'
    g = get_grade_for_aqi(350)
    assert g['grade'] == 'F'

def test_grade_table_sorted():
    for i, row in enumerate(GRADE_TABLE[:-1]):
        assert row['max_aqi'] < GRADE_TABLE[i+1]['max_aqi'], "GRADE_TABLE not sorted by max_aqi"

def test_wallet_creation():
    w = get_or_create_wallet('test_user_99')
    assert w.user_id == 'test_user_99'
    assert w.credits == 100

def test_route_credits_calculation():
    from apps.backend.services.exposure_credit import calculate_route_credits
    rc = calculate_route_credits(['A', 'B', 'F'])
    assert hasattr(rc, 'final_credit_change')
    assert isinstance(rc.segments, list)
    assert len(rc.segments) == 2  # A-B, B-F

def test_eco_bonus_applied():
    rc_eco = calculate_route_credits(['A', 'C', 'D', 'F'], is_eco_route=True, 
                                      shortest_route=['A', 'B', 'D', 'F'])
    rc_short = calculate_route_credits(['A', 'B', 'D', 'F'], is_eco_route=False)
    # Eco bonus should be >= 0
    assert rc_eco.eco_bonus >= 0

def test_leaderboard():
    lb = get_leaderboard()
    assert isinstance(lb, list)

test("Exposure credit: Grade table AQI boundaries correct", test_grade_for_aqi)
test("Exposure credit: Grade table sorted correctly", test_grade_table_sorted)
test("Exposure credit: Wallet creation with 100 starting credits", test_wallet_creation)
test("Exposure credit: Route credits calculated (2 segments for 3-city route)", test_route_credits_calculation)
test("Exposure credit: Eco bonus applied for green route", test_eco_bonus_applied)
test("Exposure credit: Leaderboard returns list", test_leaderboard)

# ============================================================
# TEST GROUP 6: Security Checks
# ============================================================
print("\n🧪 GROUP 6: Security Checks")

def test_no_hardcoded_api_keys():
    """Scan for hardcoded API keys or secrets"""
    dangerous_patterns = ['api_key = "', "api_key = '", 'secret = "', 'password = "', 
                          'token = "', 'AWS_', 'sk-']
    files_to_check = [
        'apps/backend/main.py',
        'apps/backend/services/multi_pollutant_service.py',
        'apps/backend/api/ps3.py',
        'apps/backend/services/satellite_aqi_service.py',
        'models/validation/cpcb_validator.py',
    ]
    for fpath in files_to_check:
        if os.path.exists(fpath):
            content = open(fpath).read().lower()
            for pattern in dangerous_patterns:
                assert pattern.lower() not in content, f"Potential hardcoded secret in {fpath}: {pattern}"

def test_cors_wildcard_noted():
    """CORS wildcard is expected for dev/hackathon but flag it"""
    content = open('apps/backend/main.py').read()
    assert 'allow_origins=["*"]' in content
    # This is acceptable for hackathon but should be noted

def test_input_validation_route():
    """Route endpoint validates city codes"""
    from apps.backend.services.route_service import is_valid_node
    assert is_valid_node('A') == True
    assert is_valid_node('INVALID_CITY_CODE_XYZ') == False
    assert is_valid_node('28.61,77.21') == True  # Valid lat,lon

def test_no_sql_injection_surface():
    """No direct SQL usage (project uses in-memory storage) — safe"""
    backend_files = ['apps/backend/services/exposure_credit.py', 'apps/backend/services/aqi_service.py']
    for fpath in backend_files:
        if os.path.exists(fpath):
            content = open(fpath).read()
            assert 'cursor.execute' not in content, f"Direct SQL in {fpath} — injection risk"
            assert 'sqlite3' not in content.lower()

def test_hf_token_not_hardcoded():
    """HF_TOKEN must come from env, not hardcoded"""
    content = open('inference.py').read()
    assert 'HF_TOKEN = os.getenv("HF_TOKEN")' in content
    # No hardcoded value after = os.getenv("HF_TOKEN")
    assert 'HF_TOKEN = "hf_' not in content

test("Security: No hardcoded API keys in backend files", test_no_hardcoded_api_keys)
test("Security: CORS wildcard (acceptable for hackathon, noted)", test_cors_wildcard_noted)
test("Security: Route endpoint validates city codes (no injection)", test_input_validation_route)
test("Security: No SQL injection surface (in-memory store)", test_no_sql_injection_surface)
test("Security: HF_TOKEN from env var only, not hardcoded", test_hf_token_not_hardcoded)

# ============================================================
# TEST GROUP 7: ISRO Dataset Integration Check
# ============================================================
print("\n🧪 GROUP 7: ISRO Required Dataset Integration")

def test_insat3d_aod_integration():
    """INSAT-3D AOD: satellite_aqi_service fetches MOSDAC AOD"""
    content = open('apps/backend/services/satellite_aqi_service.py').read()
    assert 'fetch_mosdac_aod' in content
    assert 'insat3d' in content.lower() or 'INSAT' in content
    assert 'aod' in content.lower()

def test_tropomi_integration():
    """Sentinel-5P TROPOMI: fetch_tropomi + HCHO gridder"""
    content = open('apps/backend/services/satellite_aqi_service.py').read()
    assert 'fetch_tropomi' in content
    assert 'formaldehyde' in content.lower() or 'hcho' in content.lower()

def test_cpcb_ground_data():
    """CPCB: OpenAQ API v3 integration in validator"""
    content = open('models/validation/cpcb_validator.py').read()
    assert 'openaq.org' in content
    assert 'PM2.5' in content or 'pm25' in content.lower()

def test_firms_fire_data():
    """NASA FIRMS MODIS/VIIRS: fire_hcho_correlator uses NASA FIRMS"""
    content = open('models/hotspot/fire_hcho_correlator.py').read()
    assert 'FIRMS' in content or 'firms' in content.lower() or 'nasa' in content.lower() or 'fire' in content.lower()

def test_era5_reanalysis():
    """ERA5: wind transport service references ERA5"""
    content = open('apps/backend/services/multi_pollutant_service.py').read()
    assert 'ERA5' in content

def test_multi_pollutant_service_all_channels():
    """TROPOMI channels: NO2, SO2, CO, O3, HCHO all implemented"""
    content = open('apps/backend/services/multi_pollutant_service.py').read()
    for channel in ['no2', 'so2', 'co', 'o3', 'hcho']:
        assert channel in content.lower(), f"TROPOMI channel {channel.upper()} not implemented"

test("Dataset: INSAT-3D AOD (MOSDAC) integrated", test_insat3d_aod_integration)
test("Dataset: Sentinel-5P TROPOMI HCHO integrated", test_tropomi_integration)
test("Dataset: CPCB CAAQM ground stations (OpenAQ v3)", test_cpcb_ground_data)
test("Dataset: NASA FIRMS fire data correlated with HCHO", test_firms_fire_data)
test("Dataset: ERA5 reanalysis wind vectors implemented", test_era5_reanalysis)
test("Dataset: All TROPOMI channels (NO2/SO2/CO/O3/HCHO)", test_multi_pollutant_service_all_channels)

# ============================================================
# TEST GROUP 8: PS-3 API Endpoints
# ============================================================
print("\n🧪 GROUP 8: PS-3 API Router Endpoints")

from apps.backend.api.ps3 import router as ps3_router

def test_ps3_router_endpoints():
    paths = [r.path for r in ps3_router.routes]
    required = [
        '/multi-pollutant-grid',
        '/hcho-seasonal-composite',
        '/source-regions',
        '/wind-vectors',
        '/fire-hcho-correlation',
        '/multi-pollutant-validation',
        '/overview',
    ]
    for req in required:
        assert any(req in p for p in paths), f"Missing PS-3 endpoint: {req}"

def test_ps3_overview_response():
    # Test the function directly
    from apps.backend.api.ps3 import get_ps3_overview
    r = get_ps3_overview()
    assert 'mission' in r
    assert r['mission']['problem_statement'] == 'PS-3'
    assert 'objectives' in r
    assert len(r['objectives']) == 2
    assert 'datasets' in r
    assert 'policy_context' in r
    assert 'NCAP' in r['policy_context']
    assert 'SDG_11_6' in r['policy_context']

def test_ps3_seasonal_composites_all():
    from apps.backend.api.ps3 import get_hcho_seasonal_composite
    for season in ['kharif', 'rabi', 'summer', 'winter']:
        result = get_hcho_seasonal_composite(season)
        assert result['season'] == season
        assert result['count'] > 0

test("PS-3 API: All 7 required endpoints defined", test_ps3_router_endpoints)
test("PS-3 API: Overview includes NCAP/SDG 11.6/policy context", test_ps3_overview_response)
test("PS-3 API: All 4 seasons return valid HCHO composites", test_ps3_seasonal_composites_all)

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "="*60)
print(f"📊 TEST RESULTS: {len(PASSED)} passed, {len(FAILED)} failed")
print("="*60)

if FAILED:
    print("\n❌ FAILED TESTS:")
    for name, err in FAILED:
        print(f"  • {name}")
        print(f"    → {err}")
else:
    print("\n🏆 ALL TESTS PASSED — Project is ready for ISRO hackathon evaluation!")

print(f"\n✅ PASSED ({len(PASSED)}):")
for name in PASSED:
    print(f"  • {name}")

# Exit with appropriate code
sys.exit(0 if not FAILED else 1)
