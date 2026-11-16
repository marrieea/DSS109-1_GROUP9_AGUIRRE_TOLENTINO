# Mapping Third-Space Accessibility and Walkability across Selected Metro Manila Cities

**A Barangay-Level Geospatial and Clustering Analysis Using Open Data**

**Course:** DSS109-1 | **Group:** 9 | **Authors:** Aguirre, Tolentino
**Status:** In progress | **Last updated:** 16 November 2026

## 1. Overview

This project measures how accessible third spaces are on foot, and how walkable barangays are, in four Metro Manila cities. It builds a third-space accessibility index and a walkability index from OpenStreetMap (OSM) data, groups barangays into profiles through clustering, locates hotspots and coldspots, and examines how accessibility relates to walkability and population density using spatial regression. Results are published in a web map.

## 2. Study area and unit of analysis

The unit of analysis is the barangay. The four cities were chosen purposively for contrast in urban form and for a benchmark, and results are not generalized to all of Metro Manila.

| City | Barangays | 2020 population | Median barangay population | Role |
|---|---|---|---|---|
| Manila | 897 | 1,846,513 | 1,474 | Dense historic core, very small barangays |
| Quezon City | 142 | 2,960,048 | 7,252 | Large, mixed |
| Makati | 33 | 629,616 | 14,978 | Central business district |
| Pasig | 30 | 803,159 | 16,661 | Benchmark against Mañago et al. (2025) |
| **Total** | **1,102** | **6,239,336** | | |

## 3. Data sources

| Dataset | Source | Obtained | Notes |
|---|---|---|---|
| 2020 Census of Population and Housing, total population by barangay | Philippine Statistics Authority (PSA) | 31 Oct 2026 | `2020-census-total-popn-brgy_adm4_new-pcode.xlsx`. URL: https://data.humdata.org/dataset/186f5609-e970-4165-86a0-a87a770532e2/resource/dd6fb33a-a91b-450c-a0f8-0b760a75458e/download/2020-census-total-popn-brgy_adm4_new-pcode.xlsx |
| Barangay boundaries (admin level 4) | OCHA Humanitarian Data Exchange (HDX), "Philippines – Subnational Administrative Boundaries" (PSA and NAMRIA) | 13 Nov 2026 | Layer `phl_admin4`, attribute `version` = v03. Publication date: 28 May 2026|
| Third-space features | OpenStreetMap contributors, via Overpass API (overpass-api.de) and OSMnx 2.1.2 | 16 Nov 2026, 13:41 to 14:20 UTC (21:41 to 22:20 PHT). Live query, not date-pinned | Twelve cached pieces (city × tag key) in `data/raw/osm/` |
| Street network | OpenStreetMap contributors, via Overpass API and OSMnx | Not yet downloaded (notebook 04) | |
| Spot-check reference | Google Maps (manual lookups only, nothing scraped) | Pending (Planned for future Notebook) | Planned, see section 8 |

© OpenStreetMap contributors, available under the Open Database License (ODbL).

## 4. Repository structure

```
DSS109-1_GROUP9_AGUIRRE_TOLENTINO/
├── data/raw | interim | processed    (not tracked by Git)
├── notebooks/                        stage notebooks, run in numerical order
├── src/                              config.py, boundaries.py, osm.py
├── outputs/                          figures and tables (not tracked)
├── validation/                       Google Maps spot-check sheets
├── docs/                             web map (GitHub Pages)
├── environment.yml
└── README.md
```

## 5. Pipeline

| Notebook | Purpose | Status |
|---|---|---|
| 00_setup_check | Check packages and raw files | Done |
| 01_extract_ncr_boundaries | National barangay file to NCR (1,712 polygons) | Done |
| 02_build_study_table | Join census to boundaries, 1,102 study barangays | Done |
| 03_osm_third_space_audit | Download, classify and audit OSM features | Done |
| 04_walking_network_origins | Walking network, origin-point test | Planned |
| 05_accessibility_index | Network distances and counts within 1.2 km and 800 m | Planned |
| 06_walkability_index | Street and pedestrian indicators | Planned |
| 07_clustering_hotspots | Clustering, Getis-Ord Gi* / local Moran's I | Planned |
| 08_spatial_regression | Accessibility vs walkability and density | Planned |
| 09_validation | Google Maps spot check, sensitivity analysis | Planned |
| 10_webmap_export | GeoJSON and web map in `docs/` | Planned |

## 6. Data preparation decisions

- **D1. Study area:** Manila, Quezon City, Makati and Pasig, at barangay level (1,102 barangays).
- **D2. Boundary–census join:** city plus normalized barangay name, not code. The census `Bgy_Code` for Manila is offset by one from the barangay number beginning at Barangay 202-A, which mispairs 66 barangays under a code join. Codes agree with names for all other study cities.
- **D3. Excluded polygons:** two non-barangay polygons with no census population (Manila North Cemetery, Tutuban Mall) were excluded.
- **D4. Makati/Taguig:** no adjustment needed. The boundary file and the census agree: Makati has 33 barangays, including the ten EMBO barangays, and Taguig has 28 (Taguig is outside the study area).
- **D5. Coordinate system:** EPSG:32651 (UTM zone 51N) for all areas and distances.
- **D6. OSM download:** one live snapshot (not date-pinned) from overpass-api.de on 16 Nov 2026, 13:41 to 14:20 UTC, using OSMnx 2.1.2. Each city outline was buffered 50 m and simplified (30 m tolerance) to avoid HTTP 413 errors, then queried in three pieces by tag key (amenity, leisure, place) with retries. Two alternative servers timed out in testing. 4,986 unique features were downloaded, and 4,844 fall inside the study barangays.
- **D7. Walking thresholds:** 850 m to 872.5 meters (85th percentile walking distance) as the main threshold and 680 m (75th percentile) as the alternative, based on Tolentino and Sigua (2022). 

## 7. Third-space definition

Third places follow Oldenburg (1999, 2nd ed.; original work published 1989). Candidate OSM types were audited, and four groups were defined:

| Group | OSM rule | Count (Makati / Manila / Pasig / QC) |
|---|---|---|
| Open space | `leisure=park`, `garden`, `place=square`; excluding explicit private or restricted access; polygons under 200 m² excluded | 123 / 163 / 68 / 206 |
| Community and learning | `amenity=community_centre`, `library`, `social_centre` | 35 / 50 / 55 / 129 |
| Public courts | `leisure=pitch` with sport basketball, multi, soccer or volleyball; excluding restricted access | 54 / 103 / 111 / 239 |
| Cafés | `amenity=cafe` | 322 / 286 / 137 / 544 |

Scenario-only types: barangay halls (`amenity=townhall`), places of worship, markets, tennis and other pitches, and private commercial spaces such as malls.

**Evidence behind the rules (from notebook 03):**
- Libraries total 63 (Makati 3, Pasig 4) and plazas (`place=square`) 26, too few to stand alone, so they were merged into larger groups.
- 88% of pitches and 96% of parks carry no `access` tag, so untagged features are assumed public. 11 parks and 44 pitches carry restricted access tags.
- Pitch sports: basketball 444, tennis 167, multi 51, soccer 29, badminton 23, volleyball 11. Tennis courts are mostly private clubs and subdivisions.
- Mapped park polygons are small: median 1,081 m², 147 under 200 m² and 309 under 1,000 m².
- Barangay halls: 261 tagged `barangay` and 58 `village` (to verify whether "village" means barangay), about a quarter of study barangays, too sparse as a core type.
- Café density per km² differs sharply across cities (Makati 12.9, Manila 6.9, Pasig 4.4, Quezon City 3.4), which may partly reflect mapping effort. This is why the validation step stratifies by city.
- Barangays with no core third space: Manila 662 of 897 (74%), Quezon City 23 of 142 (16%), Makati 1 of 33, Pasig 0 of 30. Manila's zeros mostly reflect barangay size, so barangay counts are not used as the accessibility measure.
- Cafés are 49% of the core set (1,289 of 2,625) and 60% of Makati's.
- Community centres carry no `access` tag, so none could be screened.
- Named share of parks is 37 to 38% in Manila and Makati and 52 to 53% in Pasig and Quezon City.
- Barangay hall counts (Makati: 15 of 33 mapped; Manila: 112 of 897; Pasig: 25 of 30; Quezon City: 109 of 142) are used as a completeness benchmark.

| Mun_City | barangay | city | district | village |
|---|---|---|---|---|
| City of Makati | 15 | 2 | 1 | 11 |
| City of Manila | 112 | 2 | 0 | 34 |
| City of Pasig | 25 | 1 | 0 | 10 |
| Quezon City | 109 | 1 | 0 | 3 |

- Minimum-area sensitivity (only open space changes):

| Minimum park/plaza area | Open space | Total core |
|---|---|---|
| 200 m² (main) | 560 | 2,625 |
| 500 m² | 467 | 2,532 |
| 1,000 m² | 390 | 2,455 |

## 8. Open decisions

| # | Decision | Plan |
|---|---|---|
| O1 | Origin points for distances | Compare representative point snapped to the network, several origins per barangay and a grid on about 20 barangays |
| O2 | Minimum open-space size | 200 m² main; test 500 and 1,000 m² |
| O3 | Index weighting | Equal weights as baseline; test PCA or entropy weights |
| O4 | Walkability indicators | Choose after checking sidewalk tag coverage |
| O5 | Manila's very small barangays | Robustness check with larger grouped units |
| O6 | Scenario types | Test barangay halls, worship, markets and malls one at a time |
| O7 | Validation design |Precision: 5 features per group per city (80 lookups). Completeness: 2 barangays per city, about 10 of the 23 zero-count Quezon City barangays, and barangay halls as a benchmark.|
| O8 | Cafés in the index | Report main results with and without cafés |
| O9 | Park quality | Test named parks only as a scenario |

## 9. Planned analysis

1. Walking network from OSM; network (not straight-line) distance from barangay origins to each group, and counts within 1.2 km and 800 m.
2. Third-space accessibility index per barangay (rescaled and combined transparently).
3. Walkability index from street and pedestrian features only, independent of destinations.
4. Clustering of barangays into profiles (compare k-means and hierarchical, validate with silhouette scores); hotspot and coldspot detection.
5. Spatial regression of accessibility on walkability and population density.
6. Validation against Google Maps; sensitivity analysis on thresholds, filters and weights.
7. Interactive web map of precomputed results.

## 10. Known limitations

- Accessibility reflects potential access, not actual use.
- Regression shows association, not causation. Walkability and accessibility are partly mechanically related because both depend on the street network.
- OSM completeness and tagging vary, and mapping effort may differ across areas. Public access is assumed where tags are missing.
- Census data is from 2020, while OSM is from 2026.
- Barangay size varies widely (Manila's median population is 1,474), so a single centroid is crude and results are sensitive to the unit of analysis.
- The web map shows precomputed results and does not update in real time.
- Counts per barangay are not comparable across cities because of size differences, and 74% of Manila's barangays contain no core third space, so accessibility is measured through the walking network.
- Cafés make up about half of the core set and tilt the index toward commercial areas, so results are reported with and without them.
- Informal gathering places (sari-sari stores, carinderia) are absent, and worship places, barangay halls and markets are tested only as scenarios.
- Public courts may be under-mapped in Manila (103 features for 897 barangays).
- Community centres could not be screened for access.

## 11. Setup and reproducibility

1. **Environment Setup:** Create and activate the conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate thirdspace
2. **Directory Structure & Data Placement:** Because data/ is excluded from Git, create the necessary local folders manually if they don't exist:
    ```bash
    mkdir -p data/raw/osm data/interim data/processed outputs validation docs
3. **Place Raw Data Files:** Ensure the datasets are placed in the correct directories:

Census Data: Place the Excel file at data/raw/2020-census-total-popn-brgy_adm4_new-pcode.xlsx.

Boundary Files: Place the shapefile package so that level 4 resides at data/raw/phl_admin_boundaries.shp/phl_admin4.shp.

OSM Snapshot Cache: Place the twelve .pkl files (osm_city_of_*_*.pkl) inside data/raw/osm/.

4. **Execution:** Run the pipeline based on your cached data:

If the twelve .pkl files are present in data/raw/osm/, skip notebook 03 to avoid triggering a fresh 40-minute Overpass API live query.

Run the pipeline sequentially starting from 04_walking_network_origins (or run 03_osm_third_space_audit only if you need to generate a brand-new snapshot from scratch).


## 12. Conventions

**Commit messages:** `Lastname - Action - module - short description`, for example `Aguirre - Add - boundaries - build study barangay table`. Actions: Add, Update, Fix, Remove, Refactor, Document. One logical change per commit.

**Branches:** `main` holds working code. Use `lastname/module-topic` for new work and merge through a pull request reviewed by the other member.

**Notebooks:** numbered in run order, a purpose cell at the top, relative paths only, outputs cleared before committing.

**Data:** never commit `data/`. Document every source and download date in section 3.

**Environment:** after adding a package, update `environment.yml` in the same commit.


## 13. License

Code: Licensed under the [MIT License](LICENSE). Data: See the licenses of the original sources.