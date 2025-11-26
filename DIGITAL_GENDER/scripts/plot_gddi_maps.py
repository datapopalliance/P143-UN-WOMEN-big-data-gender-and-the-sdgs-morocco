#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plot maps for GDDI prototype:

1) Facebook vs Google Trends F/M indices.
2) Smoothed female-to-male internet access index.
3) Smoothed female-to-male mobile phone use index.

Data loading helper:
    - load_gdf_for_maps() reads:
        * data/gdf_gddi_26-11-25.geojson   (geometry + base data)
        * results/gddi_indices_26-11-25.csv (indices from models)
      and returns a merged GeoDataFrame ready for plotting.

All plotting functions expect a GeoDataFrame `gdf` that already contains:
    - geometry (ADM1 regions)
    - ADM1_FR (region name, human-readable)
    - FMIndex_Monthly_MAU
    - GT_FM_index
    - FM_final
    - FM_mobile_final
"""

import os
from typing import Optional

import geopandas as gpd  # only for type hints
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, Normalize
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# Data loading helper
# ============================================================

def load_gdf_for_maps(
    root_dir: Optional[str] = None,
    geojson_name: str = "gdf_gddi_26-11-25.geojson",
    indices_csv_name: str = "gddi_indices_26-11-25.csv",
) -> gpd.GeoDataFrame:
    """
    Load base GeoDataFrame (geometry + ADM1) and merge final indices
    (Facebook, Trends, Internet, Mobile) from results CSV.

    Parameters
    ----------
    root_dir : str or None
        Project root directory. If None, it is inferred as one level up from this file.
    geojson_name : str
        Filename of the base GeoJSON in data/.
    indices_csv_name : str
        Filename of the indices CSV in results/.

    Returns
    -------
    gdf : GeoDataFrame
        GeoDataFrame with geometry and the following columns:
        - ADM1_FR
        - FMIndex_Monthly_MAU
        - GT_FM_index
        - FM_final
        - FM_mobile_final
    """
    if root_dir is None:
        root_dir = ROOT_DIR

    data_dir = os.path.join(root_dir, "data")
    results_dir = os.path.join(root_dir, "results")

    geojson_path = os.path.join(data_dir, geojson_name)
    indices_path = os.path.join(results_dir, indices_csv_name)

    print(f"Loading base GeoJSON from: {geojson_path}")
    gdf_base = gpd.read_file(geojson_path)

    print(f"Loading indices CSV from: {indices_path}")
    df_idx = pd.read_csv(indices_path)

    # Basic checks
    if "ADM1_FR" not in gdf_base.columns:
        raise ValueError("gdf_base is missing 'ADM1_FR' column.")
    if "ADM1_FR" not in df_idx.columns:
        raise ValueError("indices CSV is missing 'ADM1_FR' column.")

    # Drop any old index columns from GeoDataFrame to avoid _x/_y suffixes
    cols_to_drop = [
        "FMIndex_Monthly_MAU",
        "GT_FM_index",
        "FM_final",
        "FM_mobile_final",
    ]
    gdf_base = gdf_base.drop(columns=[c for c in cols_to_drop if c in gdf_base.columns])

    # Merge indices from CSV
    gdf = gdf_base.merge(df_idx, on="ADM1_FR", how="left")

    print("Merged GeoDataFrame columns:")
    print(gdf.columns.tolist())

    return gdf


# ============================================================
# Plotting functions
# ============================================================

def plot_fb_vs_trends(
    gdf: gpd.GeoDataFrame,
    fb_col: str = "FMIndex_Monthly_MAU",
    gt_col: str = "GT_FM_index",
    figsize=(14, 7),
) -> None:
    """
    Plot side-by-side maps of:
    - Female-to-Male index – Facebook (monthly)
    - Female-to-Male index – Google Trends

    Also saves the figure to results/map_fb_vs_trends.png
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    to_plot = [
        (fb_col, "Female-to-Male index – Facebook (monthly)"),
        (gt_col, "Female-to-Male index – Google Trends"),
    ]

    for ax, (col, title) in zip(axes, to_plot):
        valid = gdf[col].dropna()
        if valid.empty:
            ax.set_axis_off()
            ax.set_title(f"{title}\n(No data)", fontsize=11)
            continue

        vmin, vmax = valid.min(), valid.max()

        # Center at 1 if index crosses 1; otherwise use sequential
        if vmin < 1.0 < vmax:
            norm_scale = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
            cmap = "RdBu_r"
        else:
            norm_scale = Normalize(vmin=vmin, vmax=vmax)
            cmap = "OrRd"

        gdf.plot(
            column=col,
            ax=ax,
            legend=True,
            cmap=cmap,
            norm=norm_scale,
            edgecolor="black",
            linewidth=0.3,
            missing_kwds={
                "color": "lightgrey",
                "hatch": "///",
                "label": "No data",
            },
        )

        ax.set_axis_off()
        ax.set_title(title, fontsize=11)

    plt.tight_layout()

    out_path = os.path.join(RESULTS_DIR, "map_fb_vs_trends.png")
    print(f"Saving Facebook vs Trends map to: {out_path}")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")

    plt.show()


def plot_smoothed_internet_index(
    gdf: gpd.GeoDataFrame,
    col: str = "FM_final",
    title: str = "Smoothed Female-to-Male Internet Access Index by Region (2021)",
    cmap: str = "OrRd",
    figsize=(8, 8),
) -> None:
    """
    Plot single map for the smoothed female-to-male internet access index.

    Also saves the figure to results/map_internet_smoothed.png
    """
    gdf_nonan = gdf[~gdf[col].isna()].copy()
    if gdf_nonan.empty:
        print(f"No data in column '{col}' to plot.")
        return

    vmin = gdf_nonan[col].min()
    vmax = gdf_nonan[col].max()

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Choropleth
    gdf_nonan.plot(
        column=col,
        ax=ax,
        cmap=cmap,
        linewidth=0.5,
        edgecolor="white",
        vmin=vmin,
        vmax=vmax,
    )

    # Hatched polygons for regions without data
    gdf[gdf[col].isna()].plot(
        ax=ax,
        color="none",
        edgecolor="lightgrey",
        hatch="///",
        linewidth=0.5,
    )

    ax.set_axis_off()

    # Colorbar
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []
    cbar = fig.colorbar(sm, ax=ax, shrink=0.7)
    cbar.set_label("Smoothed female-to-male internet access index", fontsize=10)

    ax.set_title(title, fontsize=12)

    plt.tight_layout()

    out_path = os.path.join(RESULTS_DIR, "map_internet_smoothed.png")
    print(f"Saving smoothed internet index map to: {out_path}")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")

    plt.show()


def plot_smoothed_mobile_index(
    gdf: gpd.GeoDataFrame,
    mobile_fm_ratio_national: float,
    col: str = "FM_mobile_final",
    title: str = "Smoothed Female-to-Male Mobile Phone Use Index by Region (2023)",
    cmap: str = "OrRd",
    band: float = 0.2,
    figsize=(8, 8),
) -> None:
    """
    Plot single map for the smoothed female-to-male mobile phone use index.

    Also saves the figure to results/map_mobile_smoothed.png
    """
    gdf_nonan = gdf[~gdf[col].isna()].copy()
    if gdf_nonan.empty:
        print(f"No data in column '{col}' to plot.")
        return

    vmin = mobile_fm_ratio_national * (1 - band)
    vmax = mobile_fm_ratio_national * (1 + band)

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Choropleth
    gdf_nonan.plot(
        column=col,
        ax=ax,
        cmap=cmap,
        linewidth=0.5,
        edgecolor="white",
        vmin=vmin,
        vmax=vmax,
    )

    # Hatched polygons for regions without data
    gdf[gdf[col].isna()].plot(
        ax=ax,
        color="none",
        edgecolor="lightgrey",
        hatch="///",
        linewidth=0.5,
    )

    ax.set_axis_off()

    # Colorbar
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []
    cbar = fig.colorbar(sm, ax=ax, shrink=0.7)
    cbar.set_label("Smoothed female-to-male mobile phone use index", fontsize=10)

    ax.set_title(title, fontsize=12)

    plt.tight_layout()

    out_path = os.path.join(RESULTS_DIR, "map_mobile_smoothed.png")
    print(f"Saving smoothed mobile index map to: {out_path}")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")

    plt.show()
