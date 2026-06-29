from dataclasses import dataclass
import numpy as np
import xarray as xr
from sklearn.cluster import DBSCAN

@dataclass
class Hotspot:
    id: int
    centroid_lat: float
    centroid_lon: float
    cell_count: int
    mean_hcho: float
    cells: list[tuple[float, float]] # List of (lat, lon) in this hotspot

def detect_hotspots(hcho_ds: xr.Dataset, eps: float = 0.5, min_samples: int = 5) -> list[Hotspot]:
    """
    Identifies HCHO hotspots using DBSCAN clustering.
    Flags cells with HCHO columns > mean + 2 * std.
    """
    if "hcho" not in hcho_ds:
        raise ValueError("Dataset does not contain 'hcho' data array.")
        
    hcho_arr = hcho_ds["hcho"].values
    lats = hcho_ds["lat"].values
    lons = hcho_ds["lon"].values
    
    # Calculate Z-score thresholds
    mean_val = np.mean(hcho_arr)
    std_val = np.std(hcho_arr)
    threshold = mean_val + 2.0 * std_val
    
    # Find coordinate indices of anomalies
    anom_indices = np.argwhere(hcho_arr > threshold)
    
    if len(anom_indices) < min_samples:
        print("[INFO] Not enough anomalous cells found to form a cluster.")
        return []
        
    # Translate indices to spatial coordinates [lat, lon]
    anom_coords = []
    anom_hcho = []
    for r, c in anom_indices:
        anom_coords.append([lats[r], lons[c]])
        anom_hcho.append(hcho_arr[r, c])
        
    anom_coords = np.array(anom_coords)
    anom_hcho = np.array(anom_hcho)
    
    # Fit DBSCAN (spatial clustering in degrees)
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(anom_coords)
    labels = db.labels_
    
    unique_labels = set(labels)
    hotspots = []
    
    hotspot_id = 0
    for k in unique_labels:
        if k == -1:
            continue # Noise points
            
        class_member_mask = (labels == k)
        cluster_coords = anom_coords[class_member_mask]
        cluster_hcho = anom_hcho[class_member_mask]
        
        centroid = np.mean(cluster_coords, axis=0)
        mean_hcho = float(np.mean(cluster_hcho))
        
        cells = [(float(coord[0]), float(coord[1])) for coord in cluster_coords]
        
        hs = Hotspot(
            id=hotspot_id,
            centroid_lat=float(centroid[0]),
            centroid_lon=float(centroid[1]),
            cell_count=len(cluster_coords),
            mean_hcho=mean_hcho,
            cells=cells
        )
        hotspots.append(hs)
        hotspot_id += 1
        
    print(f"[OK] Detected {len(hotspots)} HCHO hotspot clusters via DBSCAN.")
    for h in hotspots:
        print(f"  - Hotspot {h.id}: Centroid ({h.centroid_lat:.2f}, {h.centroid_lon:.2f}), Size={h.cell_count} cells, HCHO={h.mean_hcho:.2e}")
        
    return hotspots
