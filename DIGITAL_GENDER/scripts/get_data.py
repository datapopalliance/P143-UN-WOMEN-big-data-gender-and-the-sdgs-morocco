#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Get Google Trends and Meta/Facebook audience data for Morocco,
and build a regional female-to-male usage index dataset (df_wide).

Output:
    ../data/meta+trends_26-11-25.csv
"""

import os
import json
import re
import unicodedata

import requests
import pandas as pd
from dotenv import load_dotenv
from pytrends.request import TrendReq


# ============================================================
# 0. Paths and configuration
# ============================================================

# When running from scripts/, data is one level up
DATA_DIR = os.path.join("..", "data")

# Make sure output directory exists
os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# 1. Google Trends block
# ============================================================

pytrends = TrendReq(hl="en-US", tz=0)

# Keyword lists for female- and male-leaning interests
terms_female = ["skincare", "makeup", "hair care", "recipe"]
terms_male = ["football", "cars", "gaming", "crypto"]


def get_trends_score(terms, geo="MA", timeframe="today 12-m"):
    """
    Aggregate Google Trends interest scores for a list of search terms.

    Parameters
    ----------
    terms : list of str
        List of keyword strings to query in Google Trends.
    geo : str
        Country code (e.g., 'MA' for Morocco).
    timeframe : str
        Time range for Google Trends, e.g. 'today 12-m'.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by region (geoName), with one column 'score_sum'
        equal to the sum of scores across all terms in the list.
    """
    df_sum = None
    for t in terms:
        pytrends.build_payload([t], timeframe=timeframe, geo=geo)
        df = pytrends.interest_by_region()
        df = df.rename(columns={t: f"{t}_score"})
        df_sum = df if df_sum is None else df_sum.join(df, how="outer")

    # Sum across all keyword-specific score columns
    df_sum["score_sum"] = df_sum.sum(axis=1)
    return df_sum[["score_sum"]]


# Compute female-leaning and male-leaning scores by region
female_trends = get_trends_score(terms_female)
male_trends = get_trends_score(terms_male)

# Join and build F/M index
trends = female_trends.join(male_trends, lsuffix="_F", rsuffix="_M")
trends["GT_FM_index"] = trends["score_sum_F"] / trends["score_sum_M"]

# Reset index so that region name becomes a column
trends = trends.reset_index().rename(columns={"geoName": "GT_RegionName"})

# Optionally save raw Google Trends results
trends.to_csv(os.path.join(DATA_DIR, "google_trends_26-11-25.csv"), index=False)


# ============================================================
# 2. Meta / Facebook API block
# ============================================================

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")  # Should include 'act_'
BASE_URL = "https://graph.facebook.com/v24.0"


def get_delivery_estimate(targeting_spec, optimization_goal="REACH"):
    """
    Call Meta delivery_estimate endpoint for a given targeting_spec.

    Parameters
    ----------
    targeting_spec : dict
        Targeting specification for the audience query.
    optimization_goal : str
        Optimization goal for the estimate (e.g., "REACH").

    Returns
    -------
    dict
        Parsed JSON response from the Meta API.

    Raises
    ------
    ValueError
        If environment variables are missing.
    RuntimeError
        If Meta API returns an error.
    """
    if not ACCESS_TOKEN or not AD_ACCOUNT_ID:
        raise ValueError("Missing META_ACCESS_TOKEN or META_AD_ACCOUNT_ID env vars.")

    url = f"{BASE_URL}/{AD_ACCOUNT_ID}/delivery_estimate"
    params = {
        "access_token": ACCESS_TOKEN,
        "optimization_goal": optimization_goal,
        "targeting_spec": json.dumps(targeting_spec),
    }

    resp = requests.get(url, params=params)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Meta API error: {data['error']}")
    return data


def summarize_estimate(estimate):
    """
    Extract DAU and central MAU from a delivery_estimate response.

    Parameters
    ----------
    estimate : dict
        Response from Meta delivery_estimate endpoint.

    Returns
    -------
    tuple
        (dau, mau_mid, mau_low, mau_high)
    """
    if not estimate.get("data"):
        return None, None, None, None

    e = estimate["data"][0]
    dau = e.get("estimate_dau")
    low = e.get("estimate_mau_lower_bound")
    high = e.get("estimate_mau_upper_bound")

    mau_mid = (low + high) / 2 if low is not None and high is not None else None
    return dau, mau_mid, low, high


def get_regions(country_code="MA"):
    """
    Retrieve all available 'region' geo locations for a given country code.

    Parameters
    ----------
    country_code : str
        ISO country code (e.g. 'MA').

    Returns
    -------
    list of dict
        Each dict has keys: 'key', 'name', 'country_code'.
    """
    url = f"{BASE_URL}/search"
    params = {
        "access_token": ACCESS_TOKEN,
        "type": "adgeolocation",
        "location_types": "['region']",
        "country_code": country_code,
        "limit": 200,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Meta API error (regions): {data['error']}")
    return data.get("data", [])


def make_targeting_region(region_key, gender=None, age_min=18, age_max=65):
    """
    Build targeting_spec for a specific region (Meta region key).

    Parameters
    ----------
    region_key : str
        Meta region key.
    gender : int or None
        None (all), 1 (female), 2 (male).
    age_min : int
        Minimum age.
    age_max : int
        Maximum age.

    Returns
    -------
    dict
        Targeting specification for the region-level query.
    """
    spec = {
        "geo_locations": {
            "regions": [{"key": region_key}],
        },
        "age_min": age_min,
        "age_max": age_max,
    }
    if gender in (1, 2):
        spec["genders"] = [gender]
    return spec


def make_targeting_country_ma(gender=None, age_min=18, age_max=65):
    """
    Build targeting_spec for the whole country (Morocco).

    Parameters
    ----------
    gender : int or None
        None (all), 1 (female), 2 (male).
    age_min : int
        Minimum age.
    age_max : int
        Maximum age.

    Returns
    -------
    dict
        Targeting specification for country-level queries.
    """
    spec = {
        "geo_locations": {
            "countries": ["MA"],
        },
        "age_min": age_min,
        "age_max": age_max,
    }
    if gender in (1, 2):
        spec["genders"] = [gender]
    return spec


def get_region_rows_with_all_genders(regions, age_min=18, age_max=65):
    """
    For each region, compute audience estimates for:
        - ALL (no gender filter)
        - F (genders=[1])
        - M (genders=[2])

    Parameters
    ----------
    regions : list of dict
        Region descriptors from get_regions().
    age_min : int
        Minimum age.
    age_max : int
        Maximum age.

    Returns
    -------
    list of dict
        Rows with keys:
        ['region_key', 'region_name', 'gender', 'dau', 'mau_mid', 'mau_low', 'mau_high'].
    """
    rows = []
    gender_map = {
        "ALL": None,
        "F": 1,
        "M": 2,
    }

    for r in regions:
        region_key = r["key"]
        region_name = r.get("name", region_key)

        for gender_label, gender_code in gender_map.items():
            targeting_spec = make_targeting_region(
                region_key=region_key,
                gender=gender_code,
                age_min=age_min,
                age_max=age_max,
            )

            est = get_delivery_estimate(targeting_spec)
            dau, mau_mid, mau_low, mau_high = summarize_estimate(est)

            row = {
                "region_key": region_key,
                "region_name": region_name,
                "gender": gender_label,
                "dau": dau,
                "mau_mid": mau_mid,
                "mau_low": mau_low,
                "mau_high": mau_high,
            }
            rows.append(row)

    return rows


# ------------------------------------------------------------
# Fetch regions and build region-level rows
# ------------------------------------------------------------
regions_ma = get_regions("MA")
print("Available regions in MA:")
for r in regions_ma:
    print(f"- key={r['key']}, name={r['name']}")

region_rows = get_region_rows_with_all_genders(regions_ma)

print("Sample region rows:")
for row in region_rows[:5]:
    print(row)

# ------------------------------------------------------------
# National-level estimates (all, female, male)
# ------------------------------------------------------------
nat_all_est = get_delivery_estimate(make_targeting_country_ma(gender=None))
nat_all_dau, nat_all_mau_mid, nat_all_mau_low, nat_all_mau_high = summarize_estimate(
    nat_all_est
)

nat_f_est = get_delivery_estimate(make_targeting_country_ma(gender=1))
nat_f_dau, nat_f_mau_mid, nat_f_mau_low, nat_f_mau_high = summarize_estimate(
    nat_f_est
)

nat_m_est = get_delivery_estimate(make_targeting_country_ma(gender=2))
nat_m_dau, nat_m_mau_mid, nat_m_mau_low, nat_m_mau_high = summarize_estimate(
    nat_m_est
)

nat_rows = [
    {
        "region_key": "MA",
        "region_name": "Morocco (all)",
        "gender": "ALL",
        "dau": nat_all_dau,
        "mau_mid": nat_all_mau_mid,
        "mau_low": nat_all_mau_low,
        "mau_high": nat_all_mau_high,
    },
    {
        "region_key": "MA",
        "region_name": "Morocco (all)",
        "gender": "F",
        "dau": nat_f_dau,
        "mau_mid": nat_f_mau_mid,
        "mau_low": nat_f_mau_low,
        "mau_high": nat_f_mau_high,
    },
    {
        "region_key": "MA",
        "region_name": "Morocco (all)",
        "gender": "M",
        "dau": nat_m_dau,
        "mau_mid": nat_m_mau_mid,
        "mau_low": nat_m_mau_low,
        "mau_high": nat_m_mau_high,
    },
]

# Combine all rows (regional + national)
all_rows = region_rows + nat_rows

df_long = pd.DataFrame(all_rows)
print("df_long preview:")
print(df_long.head())
print(df_long[df_long["region_key"] == "MA"])


# ============================================================
# 3. Build wide Meta table and merge with Google Trends
# ============================================================

# Rename columns to clearer names
df_long = df_long.rename(
    columns={
        "region_key": "RegionCode",
        "region_name": "RegionName",
        "gender": "Gender",
        "dau": "DailyActiveUsers",
        "mau_mid": "MonthlyActiveUsersMid",
        "mau_low": "MonthlyActiveUsersLow",
        "mau_high": "MonthlyActiveUsersHigh",
    }
)

# Pivot into wide format for DAU and MAU
df_wide = (
    df_long.pivot_table(
        index=["RegionCode", "RegionName"],
        columns="Gender",
        values=["DailyActiveUsers", "MonthlyActiveUsersMid"],
    )
    .reset_index()
)

# Flatten multi-level column names
df_wide.columns = [
    f"{metric}_{gender}" if metric not in ["RegionCode", "RegionName"] else metric
    for metric, gender in df_wide.columns
]

# Calculate Facebook F/M indexes
if "MonthlyActiveUsersMid_F" in df_wide.columns and "MonthlyActiveUsersMid_M" in df_wide.columns:
    df_wide["FMIndex_Monthly_MAU"] = (
        df_wide["MonthlyActiveUsersMid_F"] / df_wide["MonthlyActiveUsersMid_M"]
    )

if "DailyActiveUsers_F" in df_wide.columns and "DailyActiveUsers_M" in df_wide.columns:
    df_wide["FMIndex_Daily_DAU"] = (
        df_wide["DailyActiveUsers_F"] / df_wide["DailyActiveUsers_M"]
    )


def normalize_region_name(name: str) -> str:
    """
    Normalize region names: lowercase, strip, remove accents, unify dashes, collapse spaces.

    Parameters
    ----------
    name : str
        Region name.

    Returns
    -------
    str
        Normalized region name.
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


# Prepare Google Trends table for merge
df_trends = trends.copy()
df_trends["RegionName_norm"] = df_trends["GT_RegionName"].apply(normalize_region_name)

gt_region_index = (
    df_trends[["RegionName_norm", "GT_FM_index"]]
    .drop_duplicates(subset="RegionName_norm")
)

# Normalize Meta region names and merge GT_FM_index
df_wide["RegionName_norm"] = df_wide["RegionName"].apply(normalize_region_name)

df_wide = df_wide.merge(gt_region_index, on="RegionName_norm", how="left")

print("df_wide with Google Trends merged:")
print(df_wide.head())

# Save final table
output_path = os.path.join(DATA_DIR, "meta+trends_26-11-25.csv")
df_wide.to_csv(output_path, index=False)
print(f"\nSaved df_wide to: {output_path}")
