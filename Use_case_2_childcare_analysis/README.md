# Mapping Barriers to Women’s Employment (Care Systems Mapping)

## 1. Overview and Goal

This repository contains the analytical workflow and data processing scripts used to assess childcare demand, supply, and spatial accessibility in Casablanca, Morocco. The primary objective is to provide a **transparent and replicable account** of how demographic, administrative, and geospatial data were integrated to identify structural barriers to women’s employment associated with care deficits.

The methodology emphasizes the use of **open-source tools** and robust data validation techniques to support gender-responsive urban planning.

## 2. Technical Requirements and Software Stack

All analyses were performed using open-source tools to ensure reproducibility and long-term sustainability.

| Software / Library | Version | Purpose | 
| :--- | :--- | :--- | 
| **AccessMod** | 5.8 | Geospatial accessibility modeling and travel-time estimation. | 
| **Python** | 3.13.5 | Scripting for data collection, cleaning, harmonization, and indicator computation. |
| **QGIS** | 3.40 (LTS) | Spatial visualization, mapping, and analysis validation. |

## 3. Data Sources and Data Architecture

The analysis integrates demographic, administrative, and geospatial raster and vector data at high resolution, harmonized to a **100-meter grid resolution** for consistency.

### 3.1 Data Source Summary (Table 1 adapted)

| Category | Type | Source | Granularity / Resolution | Details | 
| :--- | :--- | :--- | :--- | :--- |
| **Demand (Gridded)** | Raster | WorldPop | ~ 100 m | Estimated population density per grid-cell, calibrated to official census totals. |
| **Demand (Census)** | Table | Census | Commune (ADM3) | Population groups (0–4 yrs, 15–59 yrs) used for calibration and indicator generation. |
| **Supply (Facilities)** | Point/Table | Administrative, Google Maps, HDX (OSM) | Point (Geocoded) | Locations of municipal, private, and informal childcare facilities. |
| **Road Network** | Shapefile | Humanitarian Data Exchange | Vector | Classified roads and streets used for transport and accessibility analysis. |
| **Land Cover** | Raster | ESA | ~ 10 m (resampled to 100m) | Classification (urban, water, forest) used to build the travel friction surface. |
| **DEM** | Raster | CGIAR CSI | ~ 90 m (resampled to 100m) | Elevation data for slope analysis, influencing travel speed adjustments. |

## 4. Data Processing and Validation Pipeline

The workflow involved structured processing steps to harmonize disparate data types (raster, vector, and tabular data) and calibrate modeled data against statistical reliability.

### 4.1 Supply Data Processing (Facility Harmonization)

1.  **Geocoding:** 39 facilities from the Portail Officiel de la Ville de Casablanca (administrative data) were geocoded using Google Sheets extensions, as coordinates were initially missing.
2.  **Crowd-sourced Integration:** 193 validated childcare facilities were extracted from Google My Maps via keyword scraping (e.g., `Kindergarten`, `Crèche`). One facility was retained from OpenStreetMap.
3.  **Duplicate Detection:** Pairwise comparisons were conducted between the three facility sources using a **200-meter spatial proximity threshold** to identify potential duplicates in the dense urban environment. All validated facilities (233 total: 39 administrative, 193 Google Maps, 1 OSM) were retained after manual verification.

### 4.2 Demand Data Calibration (WorldPop Adjustment)

The analysis relies on the WorldPop 2024 total population raster (~100 m resolution), which provides fine-scale spatial detail.

1.  **Census Calibration:** WorldPop estimates were validated and calibrated against official **2024 Moroccan Census totals** at the commune level (ADM3).
2.  **Ratio Calculation:** Adjustment ratios (Census 2024 total population $\div$ WorldPop 2024 total population) were calculated and applied to the WorldPop raster.
    *   *Note:* Calibration was critical as discrepancies between WorldPop and Census totals exceeded **200%** in central districts (e.g., Anfa, Méchouar de Casablanca) and were negative in peripheral areas (e.g., Sidi Moumen, Ben-M'sick).
3.  **Indicator Derivation:** The adjusted raster was disaggregated using Census proportions to generate layers for key groups: Children aged 0–4 and Women aged 15–59.

### 4.3 Supporting Layer Standardization

DEM, land cover, and road network data were prepared for AccessMod:
*   **Clipping and Reprojection:** All layers were clipped to the Casablanca administrative boundary and reprojected to a common coordinate system.
*   **Raster Harmonization:** DEM and ESA Land Cover rasters were resampled to match the **100-meter resolution** of the calibrated WorldPop data.

## 5. Accessibility Modeling Methodology (AccessMod)

Accessibility analysis was performed using **AccessMod 5.8** to quantify the proportion of the child population (0–4 years) who can reach a facility within a defined travel-time threshold (15 minutes).

### 5.1 Travel Friction Surface Generation

1.  **Barrier Identification:** Land cover categories (e.g., water bodies, dense vegetation) and slope derived from the DEM were designated as barriers or exclusion zones that slow or prevent travel.
2.  **Friction Surface:** The land cover/elevation data were integrated with the classified road network to generate a **composite travel friction surface**. This raster quantifies the time cost required to reach any facility.

### 5.2 Travel Speed Parameterization

Travel speeds were rigorously adjusted to reflect realistic urban conditions in Casablanca, particularly congestion and mobility constraints associated with children.

*   **Walking Mode:** Speeds were adjusted to reflect an adult walking with a young child. General walking speeds were set at **4 km/h** for typical built-up areas and grasslands, slightly reduced in difficult terrain (e.g., shrubland, bare land).
*   **Motorized Mode:** Speeds were set conservatively due to Casablanca’s high traffic congestion. Speeds ranged from **45 km/h** (Primary roads) to **20 km/h** (Tertiary roads), reflecting empirical findings that median urban speeds are between 18 and 48 km/h.

### 5.3 Outputs

AccessMod generated:
*   Travel time rasters (in minutes per 100m pixel).
*   Accessibility coverage tables summarizing the proportion of children within the **15-minute** threshold per commune.
*   Commune-level summary layers for spatial visualization in QGIS.

## 6. Implementation and Reproducibility

The workflow is implemented using sequential, fully reproducible Python notebooks.

### 6.1 Data Structure

The project uses a structured folder system for traceability and version control:
https://drive.google.com/drive/folders/1k2YNm9KEwSHujgnW0OmsZE528kH9d2zd?usp=sharing

```
├── data/
│   ├── data_raw/            (Original downloaded datasets)
│   ├── data_processed/      (Cleaned, harmonized datasets)
│   ├── indicator/           (Tabular indicator data)
│   ├── accessibility/       (AccessMod outputs and results)
│   └── QGIS_maps/           (QGIS project files and map compositions)
└── outputs/
    ├── Methodological notes
    └── Report
```

### 6.2 Python Workflow Notebooks

| Notebook Name | Function | Outputs | Citation |
| :--- | :--- | :--- | :--- |
| **`AccessMod - Data Collection.ipynb`** | Automates downloading and cataloguing of public datasets (WorldPop, HDX, ESA, CGIAR-CSI). | Consistent naming and metadata storage. | |
| **`AccessMod - Data Processing.ipynb`** | Cleans, standardizes, and harmonizes input data. Aggregates raster data (WorldPop) to commune boundaries (ADM3). | Standardized commune-level datasets (.csv, .gpkg) in `/data_processed`. | |
| **`Data Analysis - Indicators.ipynb`** | Computes all commune-level indicators (e.g., Child–women ratio, Childcare Coverage Ratio). | Consolidated indicator table and GeoPackage used in QGIS. | |

