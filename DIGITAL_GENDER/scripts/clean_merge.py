#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Clean and merge Meta/Trends data with Moroccan ADM1 geometry, SDG indicators
and RGPH 2024 population, to produce a GeoDataFrame ready for analysis.

Inputs (relative to project root):
    data/meta+trends_26-11-25.csv
    data/mar_admbnda_hcp_20230925_shp/mar_admbnda_adm2_hcp_20230925.shp
    data/2025 SDG 17.8.1_REV.xlsx
    data/2025 SDG 5.b.1.xlsx
    data/Indicateurs démographiques et socioéconomiques du Royaume du Maroc selon les résultats du RGPH 2024 (1).xlsx

Outputs (relative to project root):
    data/gdf_gddi_26-11-25.geojson
    data/gdf_gddi_26-11-25.csv
"""

import os
import re
import unicodedata

import geopandas as gpd
import pandas as pd
from unidecode import unidecode


# ============================================================
# Paths
# ============================================================

# Script is in scripts/, data is one level up
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

META_TRENDS_FILE = os.path.join(DATA_DIR, "meta+trends_26-11-25.csv")
ADM2_SHP = os.path.join(
    DATA_DIR,
    "mar_admbnda_hcp_20230925_shp",
    "mar_admbnda_adm2_hcp_20230925.shp",
)
SDG_INTERNET_FILE = os.path.join(DATA_DIR, "2025 SDG 17.8.1_REV.xlsx")
SDG_MOBILE_FILE = os.path.join(DATA_DIR, "2025 SDG 5.b.1.xlsx")
POP_FILE = os.path.join(
    DATA_DIR,
    "Indicateurs démographiques et socioéconomiques du Royaume du Maroc selon les résultats du RGPH 2024 (1).xlsx",
)

OUTPUT_GEOJSON = os.path.join(DATA_DIR, "gdf_gddi_26-11-25.geojson")
OUTPUT_CSV = os.path.join(DATA_DIR, "gdf_gddi_26-11-25.csv")


# ============================================================
# Helper functions
# ============================================================

def norm_name(s: str) -> str:
    """
    Normalize strings for matching (accents, case, spacing).
    """
    return (
        unidecode(str(s))
        .strip()
        .lower()
        .replace("’", "'")
        .replace("  ", " ")
    )


def clean_pop_region_name(s: str) -> str:
    """
    Clean RGPH 2024 region labels:
    - Remove 'Région de ...' prefix (or 'Région de l'' etc.)
    - Normalize using norm_name
    - Fix special cases to match ADM1_FR_norm
    """
    s_norm = norm_name(s)
    if s_norm.startswith("region de l'"):
        s_norm = s_norm.replace("region de l'", "", 1)
    elif s_norm.startswith("region de "):
        s_norm = s_norm.replace("region de ", "", 1)
    s_norm = s_norm.strip()

    # Special case: Casablanca-Settat → Grand Casablanca-Settat
    if s_norm == "casablanca-settat":
        s_norm = "grand casablanca-settat"

    return s_norm


def normalize_region_name_shp(name: str) -> str:
    """
    Normalize region names from shapefile for robust matching.
    """
    if pd.isna(name):
        return None
    s = str(name).lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ============================================================
# 1. Load Meta + Trends data (df_wide)
# ============================================================

print("Loading Meta + Google Trends data...")
df_wide = pd.read_csv(META_TRENDS_FILE)

# Ensure RegionCode is string
df_wide["RegionCode"] = df_wide["RegionCode"].astype(str).str.strip()

print("df_wide columns:", df_wide.columns.tolist())


# ============================================================
# 2. Map legacy regions -> new ADM1 (16 -> 12)
# ============================================================

region_map = {
    "Grand Casablanca": "Grand Casablanca-Settat",
    "Fès-Boulemane": "Fès-Meknès",
    "Marrakesh-Tensift-El Haouz": "Marrakech-Safi",
    "Meknès-Tafilalet": "Fès-Meknès",
    "Rabat-Salè-Zemmour-Zaer": "Rabat-Salé-Kénitra",
    "Tangier-Tetouan": "Tanger-Tétouan-Al Hoceima",
    "Taza-Al Hoceima-Taounate": "Tanger-Tétouan-Al Hoceima",
    "Guelmim-Es Semara": "Guelmim-Oued Noun",
    "Laâyoune-Boujdour-Sakia El Hamra": "Laâyoune-Sakia El Hamra",
    "Dakhla-Oued Ed-Dahab": "Dakhla-Oued Ed Dahab",
    "Souss-Massa-Dràa": "Souss-Massa",
    "Gharb-Chrarda-Béni Hssen": "Rabat-Salé-Kénitra",
    "Chaouia-Ouardigha": "Grand Casablanca-Settat",
    "Oriental": "Oriental",
    "Doukkala-Abda": "Marrakech-Safi",
    "Tadla-Azilal": "Béni Mellal-Khénifra",
    "Morocco (all)": None,
}

# Normalized mapping (old normalized name -> new normalized ADM1 name)
region_map_norm = {
    norm_name(old): norm_name(new)
    for old, new in region_map.items()
    if new is not None
}

# Normalize region names in df_wide and map to ADM1
df_wide = df_wide.copy()
df_wide["RegionName_norm"] = df_wide["RegionName"].apply(norm_name)
df_wide["ADM1_target_norm"] = df_wide["RegionName_norm"].map(region_map_norm)

# Keep only rows that can be mapped (legacy regions only)
df_wide_mapped = df_wide.dropna(subset=["ADM1_target_norm"]).copy()

# Aggregate to new ADM1 level (average numeric columns if multiple legacy regions map to same ADM1)
df_adm1_idx = (
    df_wide_mapped
    .groupby("ADM1_target_norm", as_index=False)
    .mean(numeric_only=True)
)

print("Aggregated Meta + Trends indices at ADM1 level:")
print(df_adm1_idx[["ADM1_target_norm", "FMIndex_Monthly_MAU", "GT_FM_index"]])


# ============================================================
# 3. Build ADM1 geometries from ADM2 shapefile
# ============================================================

print("Loading ADM2 shapefile and building ADM1 geometries...")
adm2 = gpd.read_file(ADM2_SHP).to_crs(epsg=4326)
adm2["ADM1_FR_norm"] = adm2["ADM1_FR"].apply(normalize_region_name_shp)

adm1 = (
    adm2
    .dissolve(by="ADM1_FR_norm", as_index=False)[["ADM1_FR", "ADM1_FR_norm", "geometry"]]
)

print("ADM1 regions from shapefile:")
print(sorted(adm1["ADM1_FR_norm"].unique()))


# ============================================================
# 4. Merge Meta + Trends indices into GeoDataFrame
# ============================================================

gdf = adm1.merge(
    df_adm1_idx[["ADM1_target_norm", "FMIndex_Monthly_MAU", "GT_FM_index"]],
    left_on="ADM1_FR_norm",
    right_on="ADM1_target_norm",
    how="left",
)

print("\nGeoDataFrame after merging Meta + Trends indices:")
print(gdf[["ADM1_FR", "FMIndex_Monthly_MAU", "GT_FM_index"]].head())


# ============================================================
# 5. National Internet and Mobile F/M ratios (SDG indicators)
# ============================================================

print("\nLoading SDG 17.8.1 (Internet usage)...")
df_internet = pd.read_excel(SDG_INTERNET_FILE, sheet_name="Data")

mask_internet = (
    (df_internet["GeoAreaName"] == "Morocco") &
    (df_internet["Time_Detail"] == 2021) &
    (df_internet["Sex"].isin(["FEMALE", "MALE", "BOTHSEX"]))
)

internet_ma = df_internet[mask_internet].copy()

internet_pivot = (
    internet_ma
    .pivot_table(
        index=["GeoAreaName", "Time_Detail"],
        columns="Sex",
        values="Value",
        aggfunc="first",
    )
    .reset_index()
)

internet_female = float(internet_pivot.loc[0, "FEMALE"])
internet_male = float(internet_pivot.loc[0, "MALE"])
internet_both = float(internet_pivot.loc[0, "BOTHSEX"])
internet_fm_ratio_national = internet_female / internet_male

print("Internet usage (Morocco, 2021)")
print(f"Female: {internet_female}")
print(f"Male:   {internet_male}")
print(f"Both:   {internet_both}")
print(f"National Internet F/M ratio: {internet_fm_ratio_national:.3f}")


print("\nLoading SDG 5.b.1 (Mobile phone usage)...")
df_mobile = pd.read_excel(SDG_MOBILE_FILE, sheet_name="Data")

mask_mobile = (
    (df_mobile["GeoAreaName"] == "Morocco") &
    (df_mobile["Time_Detail"] == 2023) &
    (df_mobile["Sex"].isin(["FEMALE", "MALE", "BOTHSEX"]))
)

mobile_ma = df_mobile[mask_mobile].copy()

mobile_pivot = (
    mobile_ma
    .pivot_table(
        index=["GeoAreaName", "Time_Detail"],
        columns="Sex",
        values="Value",
        aggfunc="first",
    )
    .reset_index()
)

mobile_female = float(mobile_pivot.loc[0, "FEMALE"])
mobile_male = float(mobile_pivot.loc[0, "MALE"])
mobile_both = float(mobile_pivot.loc[0, "BOTHSEX"])
mobile_fm_ratio_national = mobile_female / mobile_male

print("\nMobile phone use (Morocco, 2023)")
print(f"Female: {mobile_female}")
print(f"Male:   {mobile_male}")
print(f"Both:   {mobile_both}")
print(f"National Mobile F/M ratio: {mobile_fm_ratio_national:.3f}")


# ============================================================
# 6. RGPH 2024 population by region and merge into gdf
# ============================================================

print("\nLoading RGPH 2024 population data...")
pop_raw = pd.read_excel(POP_FILE, skiprows=1)

# Keep only rows where "Unnamed: 1" starts with "Région"
mask_region = pop_raw["Unnamed: 1"].astype(str).str.startswith("Région")
pop_regions = pop_raw.loc[mask_region].copy()

# Select and rename relevant columns
pop_regions = pop_regions[
    ["Unnamed: 1", "Population municipale", "Sexe (%)", "Unnamed: 5"]
].copy()

pop_regions = pop_regions.rename(
    columns={
        "Unnamed: 1": "Region",
        "Population municipale": "TotalPopulation",
        "Sexe (%)": "MalePercent",
        "Unnamed: 5": "FemalePercent",
    }
)

# Convert to numeric
pop_regions["MalePercent"] = pd.to_numeric(pop_regions["MalePercent"], errors="coerce")
pop_regions["FemalePercent"] = pd.to_numeric(pop_regions["FemalePercent"], errors="coerce")
pop_regions["TotalPopulation"] = pd.to_numeric(pop_regions["TotalPopulation"], errors="coerce")

# Compute male/female population counts
pop_regions["MalePopulation"] = pop_regions["TotalPopulation"] * pop_regions["MalePercent"] / 100.0
pop_regions["FemalePopulation"] = pop_regions["TotalPopulation"] * pop_regions["FemalePercent"] / 100.0

# Normalized region names from RGPH
pop_regions["Region_norm"] = pop_regions["Region"].apply(clean_pop_region_name)

print("\nRGPH region_norm unique:")
print(sorted(pop_regions["Region_norm"].unique()))
print("\nADM1_FR_norm unique (from shapefile):")
print(sorted(gdf["ADM1_FR_norm"].unique()))

# Merge population into gdf
gdf = gdf.merge(
    pop_regions[["Region_norm", "TotalPopulation", "MalePopulation", "FemalePopulation"]],
    left_on="ADM1_FR_norm",
    right_on="Region_norm",
    how="left",
)

print("\nGeoDataFrame after merging population:")
print(
    gdf[
        [
            "ADM1_FR",
            "FMIndex_Monthly_MAU",
            "GT_FM_index",
            "TotalPopulation",
            "MalePopulation",
            "FemalePopulation",
        ]
    ].head()
)

# ============================================================
# 7. Save outputs
# ============================================================

print(f"\nSaving GeoJSON to: {OUTPUT_GEOJSON}")
gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")

print(f"Saving CSV (no geometry) to: {OUTPUT_CSV}")
gdf_no_geom = gdf.drop(columns="geometry")
gdf_no_geom.to_csv(OUTPUT_CSV, index=False)

print("\nDone. gdf_gddi_26-11-25 saved.")
