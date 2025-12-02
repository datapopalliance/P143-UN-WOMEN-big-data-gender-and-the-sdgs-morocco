#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build smoothed female-to-male internet and mobile indices (FM_final, FM_mobile_final)
for Moroccan regions, using combined Meta + Google Trends signals and ITU/SDG anchors.

Inputs (relative to project root):
    data/gdf_gddi_26-11-25.geojson
    data/2025 SDG 17.8.1_REV.xlsx
    data/2025 SDG 5.b.1.xlsx

Output (relative to project root):
    results/gddi_indices_26-11-25.csv
"""

import os
import numpy as np
import geopandas as gpd
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

GDF_INPUT = os.path.join(DATA_DIR, "gdf_gddi_26-11-25.geojson")
SDG_INTERNET_FILE = os.path.join(DATA_DIR, "2025 SDG 17.8.1_REV.xlsx")
SDG_MOBILE_FILE = os.path.join(DATA_DIR, "2025 SDG 5.b.1.xlsx")

RESULT_CSV = os.path.join(RESULTS_DIR, "gddi_indices_26-11-25.csv")


# ============================================================
# 1. Load base GeoDataFrame
# ============================================================

print(f"Loading base GeoDataFrame from: {GDF_INPUT}")
gdf = gpd.read_file(GDF_INPUT)

required_cols = ["FMIndex_Monthly_MAU", "GT_FM_index", "ADM1_FR"]
missing = [c for c in required_cols if c not in gdf.columns]
if missing:
    raise ValueError(f"Missing required columns in gdf: {missing}")

print("Columns in gdf:", gdf.columns.tolist())


# ============================================================
# 2. National Internet F/M ratio (SDG 17.8.1)
# ============================================================

print("\nLoading SDG 17.8.1 (Internet usage) for national F/M ratio...")
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
print(f"  Female: {internet_female}")
print(f"  Male:   {internet_male}")
print(f"  Both:   {internet_both}")
print(f"  National Internet F/M ratio: {internet_fm_ratio_national:.3f}")


# ============================================================
# 3. National Mobile F/M ratio (SDG 5.b.1)
# ============================================================

print("\nLoading SDG 5.b.1 (Mobile phone usage) for national F/M ratio...")
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

print("Mobile phone use (Morocco, 2023)")
print(f"  Female: {mobile_female}")
print(f"  Male:   {mobile_male}")
print(f"  Both:   {mobile_both}")
print(f"  National Mobile F/M ratio: {mobile_fm_ratio_national:.3f}")


# ============================================================
# 4. Build smoothed Internet and Mobile indices
# ============================================================

gdf = gdf.copy()

# Only compute where both FB and Trends indices exist
mask_valid = gdf["FMIndex_Monthly_MAU"].notna() & gdf["GT_FM_index"].notna()

FM_fb = gdf.loc[mask_valid, "FMIndex_Monthly_MAU"]
FM_gt = gdf.loc[mask_valid, "GT_FM_index"]

# 2. Log-space difference
gdf.loc[mask_valid, "log_fb"] = np.log(FM_fb)
gdf.loc[mask_valid, "log_gt"] = np.log(FM_gt)
gdf.loc[mask_valid, "F_raw"] = gdf.loc[mask_valid, "log_fb"] - gdf.loc[mask_valid, "log_gt"]

# 3. Center by median
median_F = gdf.loc[mask_valid, "F_raw"].median()
gdf.loc[mask_valid, "F_centered"] = gdf.loc[mask_valid, "F_raw"] - median_F

# 4. Clip extreme differences
L = 0.3  # max deviation in log-space before shrink
gdf.loc[mask_valid, "F_centered_clipped"] = gdf.loc[mask_valid, "F_centered"].clip(
    lower=-L, upper=L
)

# 5. Shrink factor
beta = 0.5  # 0.3 more conservative, 0.5 less
gdf.loc[mask_valid, "F_scaled"] = beta * gdf.loc[mask_valid, "F_centered_clipped"]

# 6. Internet national F/M as anchor
FM_national = internet_fm_ratio_national

# 7. Smoothed internet index
gdf["FM_final"] = np.nan
gdf.loc[mask_valid, "FM_final"] = FM_national * np.exp(gdf.loc[mask_valid, "F_scaled"])

# 8. Clamp internet index to ±20% around national
lower_bound_int = FM_national * 0.8
upper_bound_int = FM_national * 1.2
gdf["FM_final"] = gdf["FM_final"].clip(lower=lower_bound_int, upper=upper_bound_int)

# 9. Smoothed mobile index using same F_scaled pattern
FM_mobile_national = mobile_fm_ratio_national

gdf["FM_mobile_final"] = np.nan
gdf.loc[mask_valid, "FM_mobile_final"] = (
    FM_mobile_national * np.exp(gdf.loc[mask_valid, "F_scaled"])
)

lower_bound_mobile = FM_mobile_national * 0.8
upper_bound_mobile = FM_mobile_national * 1.2
gdf["FM_mobile_final"] = gdf["FM_mobile_final"].clip(
    lower=lower_bound_mobile, upper=upper_bound_mobile
)

print("\nPreview of final indices:")
print(
    gdf[
        ["ADM1_FR", "FMIndex_Monthly_MAU", "GT_FM_index", "FM_final", "FM_mobile_final"]
    ].head()
)


# ============================================================
# 5. Save results (clean CSV, human-readable)
# ============================================================

result_df = gdf[
    ["ADM1_FR", "FMIndex_Monthly_MAU", "GT_FM_index", "FM_final", "FM_mobile_final"]
].copy()

result_df = result_df.sort_values("ADM1_FR")

print(f"\nSaving final indices to: {RESULT_CSV}")
result_df.to_csv(RESULT_CSV, index=False)

print("\nDone. Results saved.")
