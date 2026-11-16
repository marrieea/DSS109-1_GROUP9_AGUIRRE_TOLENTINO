"""Boundary and census preparation.

extract_ncr()        national boundary file -> NCR barangays (data/interim/ncr_adm4.gpkg)
build_study_table()  NCR barangays + 2020 census -> study barangays (data/processed/study_brgy.gpkg)

Join rule: city + normalized barangay name. The census Bgy_Code for Manila is offset by one
from the barangay number (from Barangay 202-A), so a code join mispairs 66 barangays.
"""
import geopandas as gpd
import pandas as pd

from . import config as C


def normalize_name(s: pd.Series) -> pd.Series:
    """Lowercase, drop '(Pob.)'-style tags, collapse spaces."""
    s = s.str.lower().str.replace(r"\s*\(.*?\)", "", regex=True)
    return s.str.replace(r"\s+", " ", regex=True).str.strip()


def extract_ncr(save: bool = True) -> gpd.GeoDataFrame:
    """Read the nationwide barangay file (slow) and keep only NCR barangays."""
    b = gpd.read_file(C.BOUNDARY_SHP)
    ncr = b[b["adm4_pcode"].str.startswith(C.NCR_PREFIX)].copy()
    if save:
        C.INTERIM.mkdir(parents=True, exist_ok=True)
        ncr.to_file(C.NCR_GPKG, driver="GPKG")
    return ncr


def load_ncr() -> gpd.GeoDataFrame:
    return gpd.read_file(C.NCR_GPKG)


def load_census() -> pd.DataFrame:
    c = pd.read_excel(C.CENSUS_XLSX, sheet_name=0)
    c.columns = [x.replace("\n", " ") for x in c.columns]
    return c[c["Region"].str.contains("National Capital")].copy()


def build_study_table(save: bool = True, verbose: bool = True) -> gpd.GeoDataFrame:
    """Join census population to boundaries for the four study cities."""
    ncr, census = load_ncr(), load_census()
    bs = ncr[ncr["adm3_name"].isin(C.STUDY_CITIES)].copy()
    cs = census[census["Mun_City"].isin(C.STUDY_CITIES)].copy()
    bs["name_key"] = normalize_name(bs["adm4_name"])
    cs["name_key"] = normalize_name(cs["Barangay"])

    assert not bs.duplicated(["adm3_name", "name_key"]).any(), "duplicate boundary names"
    assert not cs.duplicated(["Mun_City", "name_key"]).any(), "duplicate census names"

    j = cs.merge(
        bs[["adm3_name", "name_key", "adm4_pcode"]],
        left_on=["Mun_City", "name_key"], right_on=["adm3_name", "name_key"],
        how="outer", indicator=True,
    )
    both = j[j["_merge"] == "both"]
    census_only = j[j["_merge"] == "left_only"]
    boundary_only = j[j["_merge"] == "right_only"]

    if verbose:
        print("join result:", j["_merge"].value_counts().to_dict())
        if len(boundary_only):
            print("boundary polygons with no census row (excluded):")
            x = bs[bs["adm4_pcode"].isin(boundary_only["adm4_pcode"])]
            print(x[["adm3_name", "adm4_name", "adm4_pcode"]].to_string(index=False))

    assert len(census_only) == 0, "census rows without a boundary polygon"
    assert both["adm4_pcode"].is_unique

    geo = bs[["adm4_pcode", "area_sqkm", "geometry"]]
    gdf = geo.merge(
        both[["adm4_pcode", "Mun_City", "Barangay", "2020 Census Popn"]],
        on="adm4_pcode", how="inner",
    )
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=bs.crs).to_crs(C.CRS_METRIC)
    gdf = gdf.rename(columns={"2020 Census Popn": "pop2020", "area_sqkm": "area_km2_src"})
    gdf["area_km2"] = gdf.geometry.area / 1e6
    gdf["density"] = gdf["pop2020"] / gdf["area_km2"]
    gdf = gdf[["adm4_pcode", "Mun_City", "Barangay", "pop2020",
               "area_km2", "area_km2_src", "density", "geometry"]]

    if verbose:
        print(len(gdf), "study barangays")
        print(gdf.groupby("Mun_City").size().to_string())
    if save:
        C.PROCESSED.mkdir(parents=True, exist_ok=True)
        gdf.to_file(C.STUDY_GPKG, driver="GPKG")
    return gdf


def load_study_table() -> gpd.GeoDataFrame:
    return gpd.read_file(C.STUDY_GPKG)