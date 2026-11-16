"""Project-wide paths and settings. Change decisions here, not inside notebooks."""
from pathlib import Path

# --- paths ---
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

BOUNDARY_SHP = RAW / "phl_admin_boundaries.shp" / "phl_admin4.shp"
CENSUS_XLSX = RAW / "2020-census-total-popn-brgy_adm4_new-pcode.xlsx"
OSM_DIR = RAW / "osm"                      # one cache file per city and tag key, plus DOWNLOAD_LOG.txt
NCR_GPKG = INTERIM / "ncr_adm4.gpkg"
STUDY_GPKG = PROCESSED / "study_brgy.gpkg"

# --- study area ---
STUDY_CITIES = ["City of Manila", "Quezon City", "City of Makati", "City of Pasig"]
NCR_PREFIX = "PH13"          # boundary adm4_pcode prefix for the National Capital Region
CRS_METRIC = 32651           # UTM zone 51N: all distances and areas
CRS_WGS84 = 4326

# --- OSM download (Overpass) ---
OVERPASS_URL = None          # None = OSMnx default (overpass-api.de). private.coffee and maps.mail.ru
                             # timed out in testing on 16 Nov 2026, the main server answered (slowly).
OVERPASS_RETRIES = 5         # attempts per request; waits OVERPASS_WAIT_S, x2, x4, ...
OVERPASS_WAIT_S = 30
REQUEST_TIMEOUT_S = 600      # how long to wait for one reply
USER_AGENT = "DSS109-Group9-thirdspace-study (student research project)"
USE_DATE_PIN = False         # historical queries are heavier; snapshot = download date in DOWNLOAD_LOG.txt
OSM_SNAPSHOT = "2026-11-16T00:00:00Z"      # only used when USE_DATE_PIN is True
QUERY_BUFFER_M = 50          # buffer around each city outline sent to Overpass
QUERY_SIMPLIFY_M = 30        # simplification tolerance (avoids HTTP 413 errors)

OSM_TAGS = {
    "amenity": ["cafe", "library", "community_centre", "social_centre",
                "townhall", "place_of_worship", "marketplace"],
    "leisure": ["park", "garden", "playground", "pitch", "sports_centre", "fitness_station"],
    "place": ["square"],
}

# --- third-space definition (README section 7; provisional until notebook 03 confirms the counts) ---
RESTRICTED_ACCESS = {"private", "customers", "permit", "residents", "destination"}
COURT_SPORTS = ("basketball", "multi", "soccer", "volleyball")
MIN_OPEN_SPACE_AREA_M2 = 200   # main threshold; test 500 and 1000 as sensitivity

# --- accessibility ---
WALK_THRESHOLD_M = 1200        # 15-minute walk
WALK_THRESHOLD_ALT_M = 800     # alternative threshold