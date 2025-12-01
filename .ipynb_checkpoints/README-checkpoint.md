# UN Women Big Data: Gender and SDGs – Morocco (P143)

This consolidated repository brings together four workstreams developed to support UN Women Morocco with big-data-informed insights for gender equality and the Sustainable Development Goals (SDGs). It integrates digital gender divide analytics, road access and isolation modelling, health access preparation via AccessMod, and an applied use case with ready-to-use maps and indicators.

---

## Repository Structure

- **ACCES_MOD/**
  - Jupyter notebooks for AccessMod-related workflows:
    - `1. AccessMod - Data Collection.ipynb`
    - `2. AccessMod - Data Processing.ipynb`
    - `3. Data Analysis - Indicators.ipynb`
  - Focus: preparing inputs, processing outputs, and deriving indicators for accessibility analyses using AccessMod.

- **DIGITAL_GENDER/**
  - Digital gender divide analysis combining Meta (Facebook) audience data, official population statistics, and SDG indicators to compute Female-to-Male digital usage indices at regional level.
  - Main assets: `APP1.ipynb`, harmonized datasets, maps, and documentation.
  - See detailed docs: `DIGITAL_GENDER/README.md`.

- **MOROCCO_ROAD_ACCES/**
  - Road access and isolation analysis using OpenStreetMap, WorldPop, and OpenRouteService (ORS) to estimate the share of population with limited access to all-weather roads and essential services.
  - Includes a ready-to-run notebook and ORS configuration.
  - See detailed docs: `MOROCCO_ROAD_ACCES/Readme.md`.

- **USE_CASE/**
  - End-to-end, applied workflow that consolidates accessibility results, indicators, and cartographic outputs.
  - Contents:
    - `QGIS_maps/` with ready-to-use map projects and exported images.
    - `accessibility/` with AccessMod exports (tables, gpkg, zip projects).
    - `indicator/` with compiled indicators in CSV/XLSX/GPKG formats and typology.
    - `data_raw/` (e.g., HOT Export road data with metadata in `road/README.txt`).
    - `python scripts/` with the three AccessMod notebooks for reproducibility.

  Note: The complete `USE_CASE` package (including large datasets and maps) is hosted on Google Drive due to size constraints:
  https://drive.google.com/drive/folders/1h9CFIaFVMTjE1CbKV2MQRkbC9w2dVpMN?usp=drive_link

---

## Objectives

- **Digital Gender Divide**: quantify and map gender differences in Facebook, internet, and mobile usage; provide regional indices aligned with SDG indicators (e.g., SDG 5.b.1, SDG 17.8.1).
- **Road Access & Isolation**: compute isochrones and overlay with population to estimate isolated territories and population shares.
- **Access to Services (AccessMod)**: prepare, process, and derive indicators from AccessMod workflows to support health/service accessibility assessments.
- **Applied Use Case**: deliver curated indicators and cartographic outputs for direct consumption and decision support.

---

## Data Sources (examples)

- Meta for Developers – Graph API (Facebook audience data)
- Humanitarian Data Exchange (HDX) boundaries and geospatial datasets
- Haut-Commissariat au Plan (HCP) official statistics
- World Bank Open Data
- ITU SDG DataHub
- OpenStreetMap (road network)
- Humanitarian OpenStreetMap Team (HOT) Export Tool metadata and extracts
- WorldPop (population distribution)

Specific sources, preprocessing steps, and schema are documented inside each module’s README or notebooks.

---

## Environments and Requirements

- Recommended Python: 3.12
- Common Python libraries used across modules include: pandas, geopandas, matplotlib, shapely, rasterstats, requests, python-dotenv, openrouteservice, and Jupyter.
- Module-specific requirements:
  - `DIGITAL_GENDER/` provides environment details in its README and may use a `environment.yml` or equivalent.
  - `MOROCCO_ROAD_ACCES/` includes `requirements.txt` and `ors-config.yml` for local ORS setup.
  - `ACCES_MOD/` notebooks are designed to interoperate with AccessMod outputs/inputs; install GIS/rasters toolchain as needed.

---

## Quick Start

- **1) Clone and open notebooks**
  - Use your preferred environment manager (conda or venv).
  - Install dependencies per module (see each subfolder’s README or `requirements.txt`).

- **2) DIGITAL_GENDER**
  - Create a `.env` with Meta credentials if pulling fresh data via Graph API:
    - `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`, and (if applicable) `META_APP_ID`, `META_APP_SECRET`.
  - Open `DIGITAL_GENDER/APP1.ipynb` to run acquisition, harmonization, and visualization.

- **3) MOROCCO_ROAD_ACCES**
  - Install a local OpenRouteService instance via Docker and place Morocco OSM extract alongside `ors-config.yml` as instructed in `MOROCCO_ROAD_ACCES/Readme.md`.
  - Run `MOROCCO_ROAD_ACCES/Road_Access.ipynb` to compute isochrones and isolation metrics.

- **4) ACCES_MOD**
  - Follow the three notebooks in order for collection, processing, and indicator derivation:
    1) `1. AccessMod - Data Collection.ipynb`
    2) `2. AccessMod - Data Processing.ipynb`
    3) `3. Data Analysis - Indicators.ipynb`
  - Ensure AccessMod inputs/outputs are correctly referenced in the notebooks.

- **5) USE_CASE**
  - Access the full `USE_CASE` (maps, indicators, raw and processed data) on Google Drive:
    https://drive.google.com/drive/folders/1h9CFIaFVMTjE1CbKV2MQRkbC9w2dVpMN?usp=drive_link

---

## Outputs

- Regional digital usage indices and maps (female-to-male ratios) for Morocco.
- Isochrones, isolation shares, and illustrative interactive maps for road access.
- Accessibility indicators and supporting tables from AccessMod workflows.
- Use-case deliverables: QGIS map projects/exports and consolidated indicator files (CSV/XLSX/GPKG).

---

## Notes and Governance

- Credentials and tokens must not be committed. Use `.env` and secure secret storage.
- Large datasets and intermediate artifacts may be excluded from version control.
- See submodule READMEs for detailed methods, limitations, and reproducibility notes.

---

## Contact

For questions or collaboration, please reach out to the project maintainers or UN Women Morocco focal points associated with this work.

