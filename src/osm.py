"""OSM download (per city and tag key, cached), classification and audit of third-space candidates."""
import time
from datetime import datetime, timezone

import geopandas as gpd
import osmnx as ox
import pandas as pd
import requests
from shapely.geometry import MultiPolygon, Polygon

from . import config as C


# ---------------------------------------------------------------- Overpass access
def configure_overpass() -> None:
    if C.OVERPASS_URL:
        ox.settings.overpass_url = C.OVERPASS_URL
    ox.settings.http_user_agent = C.USER_AGENT
    ox.settings.requests_timeout = C.REQUEST_TIMEOUT_S
    ox.settings.use_cache = True
    if C.USE_DATE_PIN:
        ox.settings.overpass_settings = (
            f'[out:json][timeout:{{timeout}}][date:"{C.OSM_SNAPSHOT}"]{{maxsize}}'
        )
    else:
        ox.settings.overpass_settings = "[out:json][timeout:{timeout}]{maxsize}"


def ping() -> None:
    """Time one tiny query against the configured server."""
    configure_overpass()
    base = (C.OVERPASS_URL or "https://overpass-api.de/api").rstrip("/")
    q = '[out:json][timeout:25];node["amenity"="cafe"](14.55,121.02,14.56,121.03);out count;'
    t = time.time()
    try:
        r = requests.post(base + "/interpreter", data={"data": q}, timeout=120,
                          headers={"User-Agent": C.USER_AGENT})
        print(f"HTTP {r.status_code} in {time.time() - t:.1f}s")
    except Exception as e:
        print(f"FAILED after {time.time() - t:.1f}s: {type(e).__name__}")


def _log(city: str, key: str, n: int) -> None:
    """Append one line per downloaded piece: this is the record of your OSM snapshot."""
    C.OSM_DIR.mkdir(parents=True, exist_ok=True)
    server = getattr(ox.settings, "overpass_url", None) or getattr(ox.settings, "overpass_endpoint", "default")
    line = "\t".join([
        datetime.now(timezone.utc).isoformat(timespec="seconds"), city, key, str(n),
        f"osmnx {ox.__version__}", str(server), f"date_pin={C.USE_DATE_PIN}",
    ])
    with open(C.OSM_DIR / "DOWNLOAD_LOG.txt", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _fetch_one(poly, tags):
    """One Overpass request with exponential backoff when the server is busy."""
    last = None
    for attempt in range(1, C.OVERPASS_RETRIES + 1):
        try:
            return ox.features_from_polygon(poly, tags)
        except Exception as e:
            if type(e).__name__ == "InsufficientResponseError":     # query worked, nothing found
                return gpd.GeoDataFrame()
            last = e
            wait = C.OVERPASS_WAIT_S * 2 ** (attempt - 1)
            print(f"  {list(tags)} attempt {attempt} failed ({type(e).__name__}); waiting {wait}s")
            time.sleep(wait)
    raise last


# ---------------------------------------------------------------- query outlines
def _strip_holes(geom):
    if geom.geom_type == "Polygon":
        return Polygon(geom.exterior)
    return MultiPolygon([Polygon(p.exterior) for p in geom.geoms])


def query_polygon(g: gpd.GeoDataFrame, city: str):
    """Simplified outline of one city, in lat/lon, small enough for Overpass."""
    u = g.loc[g["Mun_City"] == city, "geometry"].union_all()          # metres
    u = _strip_holes(u.buffer(C.QUERY_BUFFER_M).simplify(C.QUERY_SIMPLIFY_M))
    return gpd.GeoSeries([u], crs=C.CRS_METRIC).to_crs(C.CRS_WGS84).iloc[0]


def n_vertices(geom) -> int:
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    return sum(len(p.exterior.coords) for p in polys)


# ---------------------------------------------------------------- download and cache
def _slug(city: str) -> str:
    return city.lower().replace(" ", "_")


def _cache_path(city: str, key: str):
    return C.OSM_DIR / f"osm_{_slug(city)}_{key}.pkl"


def cache_status() -> pd.DataFrame:
    """Which (city, tag key) pieces are already downloaded."""
    rows = [{"city": c, "key": k, "cached": _cache_path(c, k).exists()}
            for c in C.STUDY_CITIES for k in C.OSM_TAGS]
    return pd.DataFrame(rows).pivot(index="city", columns="key", values="cached")


def download_city(g: gpd.GeoDataFrame, city: str) -> pd.DataFrame:
    """One city: one request per tag key, each cached separately, then combined."""
    configure_overpass()
    C.OSM_DIR.mkdir(parents=True, exist_ok=True)
    poly, parts = None, []
    for key, values in C.OSM_TAGS.items():
        cache = _cache_path(city, key)
        if cache.exists():
            part = pd.read_pickle(cache)
            print(f"{city} / {key}: cache ({len(part)})")
        else:
            if poly is None:
                poly = query_polygon(g, city)
            print(f"{city} / {key}: downloading ...")
            raw = _fetch_one(poly, {key: values})
            part = raw.reset_index() if len(raw) else pd.DataFrame()
            part["downloaded_for"] = city
            part.to_pickle(cache)
            _log(city, key, len(part))
            print(f"{city} / {key}: {len(part)}")
        parts.append(part)

    f = pd.concat([p for p in parts if len(p)], ignore_index=True)
    ids = [c for c in ("element", "id") if c in f.columns] or ["element_type", "osmid"]
    return f.drop_duplicates(subset=ids)          # a feature can match two tag keys


def load_features(g: gpd.GeoDataFrame) -> pd.DataFrame:
    """All study cities (downloads whatever is missing, loads the rest from cache)."""
    return pd.concat([download_city(g, c) for c in C.STUDY_CITIES], ignore_index=True)


# ---------------------------------------------------------------- classification
def classify(r) -> str:
    """Raw OSM tags -> OSM type."""
    a, l = r.get("amenity"), r.get("leisure")
    if a == "cafe": return "cafe"
    if a == "library": return "library"
    if a == "community_centre": return "community_centre"
    if a == "social_centre": return "social_centre"
    if a == "townhall": return "townhall"
    if a == "place_of_worship": return "worship"
    if a == "marketplace": return "market"
    if l in ("park", "garden"): return "park"
    if r.get("place") == "square": return "plaza"
    if l == "pitch": return "pitch"
    if l in ("playground", "sports_centre", "fitness_station"): return "other_leisure"
    return "other"


def final_type(r):
    """OSM type -> third-space group, or None if excluded (README section 7)."""
    t, acc = r["osm_type"], r.get("access")
    if t in ("park", "plaza"):
        if acc in C.RESTRICTED_ACCESS: return None
        if r["geom_type"] != "Point" and r["area_m2"] < C.MIN_OPEN_SPACE_AREA_M2: return None
        return "open_space"
    if t in ("community_centre", "library", "social_centre"):
        return "community_learning"
    if t == "pitch":
        if acc in C.RESTRICTED_ACCESS: return None
        return "public_court" if r.get("sport") in C.COURT_SPORTS else None
    if t == "cafe":
        return "cafe"
    return None


def assign_types(feat: pd.DataFrame, g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Classify features, make one point each, and keep those inside study barangays."""
    feat = gpd.GeoDataFrame(feat, geometry="geometry", crs=C.CRS_WGS84)
    feat["osm_type"] = feat.apply(classify, axis=1)
    feat["named"] = feat["name"].notna() if "name" in feat.columns else False
    feat["geom_type"] = feat.geometry.geom_type

    metric = feat.to_crs(C.CRS_METRIC)
    feat["area_m2"] = metric.geometry.area
    rp = metric.geometry.representative_point()
    pts = gpd.GeoDataFrame(feat.drop(columns="geometry"), geometry=rp, crs=C.CRS_METRIC)

    pts = gpd.sjoin(pts, g[["adm4_pcode", "Mun_City", "geometry"]], how="inner", predicate="within")
    ids = [c for c in ("element", "id") if c in pts.columns] or ["element_type", "osmid"]
    pts = pts.drop_duplicates(subset=ids)          # features near city borders can appear twice
    pts["final_type"] = pts.apply(final_type, axis=1)
    return pts


# ---------------------------------------------------------------- audit
def audit(pts: gpd.GeoDataFrame, g: gpd.GeoDataFrame) -> dict:
    """Tables used to judge whether OSM is complete and consistent enough."""
    counts = pts.groupby(["Mun_City", "osm_type"]).size().unstack(fill_value=0)
    area = g.groupby("Mun_City")["area_km2"].sum()
    return {
        "counts": counts,
        "named_share": pts.groupby(["Mun_City", "osm_type"])["named"].mean().unstack().round(2),
        "geometry_types": pts.groupby(["osm_type", "geom_type"]).size().unstack(fill_value=0),
        "per_km2": counts.div(area, axis=0).round(2),
        "final_groups": pts.groupby(["Mun_City", "final_type"]).size().unstack(fill_value=0),
    }


def tag_checks(pts: gpd.GeoDataFrame) -> None:
    """Print access, sport, town-hall type and park-size statistics."""
    def tab(col, types):
        if col not in pts.columns:
            print(col, "-> column not present\n"); return
        s = pts[pts["osm_type"].isin(types)].groupby("osm_type")[col].value_counts(dropna=False)
        print(s.groupby(level=0).head(8), "\n")

    tab("access", ["park", "pitch", "community_centre"])
    tab("sport", ["pitch"])
    tab("townhall:type", ["townhall"])
    p = pts[(pts["osm_type"] == "park") & (pts["geom_type"] != "Point")]
    print("PARK AREA (m2)"); print(p["area_m2"].describe().round(0))
    print("parks under 200 m2:", (p["area_m2"] < 200).sum(), "| under 1000 m2:", (p["area_m2"] < 1000).sum())