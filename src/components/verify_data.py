"""Sanity-check the downloaded Inside Airbnb files BEFORE building anything.

Run this straight after download_data.py. It only *inspects* the data - it
never cleans or modifies it. The goal is to catch problems (bad downloads,
broken keys, surprising nulls) before you invest a week on top of them.

Usage
-----
    python src/verify_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "cities.yml"


def active_city() -> str:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["active_city"]


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    city = active_city()
    raw = PROJECT_ROOT / "data" / "raw" / city
    if not raw.exists():
        sys.exit(f"No data at {raw}. Run:  python src/download_data.py")

    files = {
        "listings_detailed":  raw / "listings.csv.gz",
        "calendar":           raw / "calendar.csv.gz",
        "reviews_detailed":   raw / "reviews.csv.gz",
        "listings_summary":   raw / "listings.csv",
        "reviews_summary":    raw / "reviews.csv",
        "neighbourhoods":     raw / "neighbourhoods.csv",
        "neighbourhoods_geo": raw / "neighbourhoods.geojson",
    }

    # ------------------------------------------------------------------ 1
    section("1. FILE INVENTORY")
    for key, p in files.items():
        size = f"{p.stat().st_size/1e6:8.1f} MB" if p.exists() else "  MISSING"
        print(f"  {key:20s} {size}   {p.name}")

    # ------------------------------------------------------------------ 2
    section("2. DETAILED LISTINGS  (the master table)")
    listings = pd.read_csv(files["listings_detailed"], compression="infer", low_memory=False)
    print(f"  Shape: {listings.shape[0]:,} rows x {listings.shape[1]} columns")
    print(f"  'id' is unique (primary-key check): {listings['id'].is_unique}")

    if "price" in listings.columns:
        sample = listings["price"].dropna().head(3).tolist()
        print(f"  Raw 'price' samples: {sample}")
        print(f"  -> price stored as text needing $/comma cleaning: "
              f"{listings['price'].dtype == object}")

    key_cols = ["room_type", "property_type", "neighbourhood_cleansed", "host_id",
                "minimum_nights", "availability_365", "number_of_reviews",
                "review_scores_rating", "price"]
    print("  Null rates on key columns:")
    for c in [c for c in key_cols if c in listings.columns]:
        print(f"      {c:26s} {listings[c].isna().mean()*100:5.1f}% null")

    # ------------------------------------------------------------------ 3
    section("3. CALENDAR  (availability - the big file)")
    cal_cols = pd.read_csv(files["calendar"], compression="infer", nrows=0).columns.tolist()
    print(f"  Columns: {cal_cols}")
    use = [c for c in ["listing_id", "date", "available", "price"] if c in cal_cols]
    cal = pd.read_csv(files["calendar"], compression="infer", usecols=use,
                      parse_dates=["date"] if "date" in use else None)
    n_listings = cal["listing_id"].nunique()
    print(f"  Shape: {cal.shape[0]:,} rows  (loaded {len(use)} of {len(cal_cols)} columns)")
    print(f"  Distinct listings: {n_listings:,}")
    print(f"  Rows per listing (expect ~365): {cal.shape[0]/max(n_listings,1):.0f}")
    if "date" in use:
        print(f"  Date range: {cal['date'].min().date()} -> {cal['date'].max().date()}")

    # ------------------------------------------------------------------ 4
    section("4. DETAILED REVIEWS")
    rev = pd.read_csv(files["reviews_detailed"], compression="infer",
                      usecols=["listing_id", "date"])
    rev["date"] = pd.to_datetime(rev["date"], errors="coerce")
    print(f"  Shape: {rev.shape[0]:,} rows")
    print(f"  Review date range: {rev['date'].min().date()} -> {rev['date'].max().date()}")

    # ------------------------------------------------------------------ 5
    section("5. KEY RELATIONSHIPS  (foreign-key integrity)")
    lid = set(listings["id"].unique())
    cid = set(cal["listing_id"].unique())
    rid = set(rev["listing_id"].unique())
    print(f"  Listings (id):                       {len(lid):,}")
    print(f"  Calendar listing_ids also in listings: {len(cid & lid):,}")
    print(f"  Calendar listing_ids NOT in listings:  {len(cid - lid):,}  (should be ~0)")
    print(f"  Review listing_ids NOT in listings:    {len(rid - lid):,}  (should be ~0)")
    print(f"  Listings with >=1 review: {len(rid & lid)/max(len(lid),1)*100:.1f}%")

    # ------------------------------------------------------------------
    section("VERDICT")
    print("  Healthy signs: 'id' unique, calendar ~365 rows/listing, calendar &")
    print("  review keys overlap cleanly with listings, price flagged as text.")
    print("  Note anything surprising in DECISIONS.md, then build the pipeline.")
    print("  (neighbourhoods.geojson is intentionally not loaded here - it needs")
    print("   geopandas, which you'll add when you start the maps in the EDA stage.)")


if __name__ == "__main__":
    main()
