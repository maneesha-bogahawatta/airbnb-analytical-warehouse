import os
import yaml
import duckdb

def build_relational_warehouse():
    db_path = "data/airbnb_warehouse.db"
    config_path = "config/cities.yml"
    os.makedirs("data", exist_ok=True)

    # 1. Config parse.
    # FIX: the config defines `active_city` (singular) and a `cities:` map, so the
    # old `active_cities` lookup always failed and silently hardcoded the cities.
    # Read both forms so it actually honours the config.
    active_markets = ["barcelona", "madrid"]
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        if "active_cities" in config:                 # explicit list wins
            active_markets = config["active_cities"]
        elif "cities" in config:                      # else use every city defined
            active_markets = list(config["cities"].keys())
        elif "active_city" in config:                 # else the single active one
            active_markets = [config["active_city"]]
    print(f"Active markets from config: {active_markets}")

    print(f"Connecting to DuckDB Analytical Warehouse: {db_path}")
    conn = duckdb.connect(db_path)
    conn.execute("SET threads TO 4;")

    print("\nExecuting DDL: Establishing Relational Constraints...")
    conn.execute("""
        CREATE OR REPLACE TABLE dim_neighbourhoods (
            neighbourhood_id VARCHAR PRIMARY KEY,
            city VARCHAR NOT NULL,
            neighbourhood_name VARCHAR NOT NULL,
            neighbourhood_group VARCHAR
        );

        CREATE OR REPLACE TABLE dim_hosts (
            host_id BIGINT PRIMARY KEY,
            host_name VARCHAR,
            host_since DATE,
            is_superhost BOOLEAN,
            total_host_listings INTEGER
        );

        CREATE OR REPLACE TABLE dim_listings (
            listing_id BIGINT PRIMARY KEY,
            city VARCHAR NOT NULL,
            host_id BIGINT,
            neighbourhood_id VARCHAR,
            room_type VARCHAR,
            property_type VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            accommodates INTEGER,
            bedrooms INTEGER,
            beds INTEGER,
            price DOUBLE,
            review_rating DOUBLE,
            license VARCHAR,
            regulatory_status VARCHAR,
            -- FIX: SCD Type 2 / temporal columns. The EDA scripts filter on
            -- is_current and scd2_listings_update.py writes valid_to/is_current,
            -- so the table must actually have these columns.
            valid_from TIMESTAMP,
            valid_to TIMESTAMP,
            is_current BOOLEAN
        );

        CREATE OR REPLACE TABLE fact_reviews (
            review_id BIGINT PRIMARY KEY,
            listing_id BIGINT,
            city VARCHAR NOT NULL,
            review_date DATE
        );
    """)

    for city in active_markets:
        raw_dir = f"data/raw/{city}"
        if not os.path.exists(raw_dir):
            print(f"⚠️ Directory missing, skipping market: {raw_dir}")
            continue

        print(f"\nProcessing ETL Pipeline for Market: {city.upper()}")

        # Neighbourhood dimension
        print(" -> Building dim_neighbourhoods...")
        if os.path.exists(f"{raw_dir}/neighbourhoods.csv"):
            conn.execute(f"""
                INSERT OR IGNORE INTO dim_neighbourhoods
                SELECT DISTINCT
                    '{city}_' || neighbourhood as neighbourhood_id,
                    '{city}' as city,
                    neighbourhood as neighbourhood_name,
                    neighbourhood_group
                FROM '{raw_dir}/neighbourhoods.csv'
                WHERE neighbourhood IS NOT NULL;
            """)

        # Host dimension
        print(" -> Extracting dim_hosts...")
        conn.execute(f"""
            INSERT OR IGNORE INTO dim_hosts
            SELECT DISTINCT
                CAST(host_id AS BIGINT) as host_id,
                host_name,
                CAST(host_since AS DATE) as host_since,
                CASE WHEN host_is_superhost = 't' THEN TRUE ELSE FALSE END as is_superhost,
                CAST(host_listings_count AS INTEGER) as total_host_listings
            FROM read_csv_auto('{raw_dir}/listings.csv.gz', ignore_errors=True)
            WHERE host_id IS NOT NULL;
        """)

        # Summary-file price recovery (note: still NULL for snapshots where the
        # scrape lost price, e.g. Barcelona 2025-12-14 — see find_priced_snapshot.py)
        print(" -> Caching recovery price matrices...")
        conn.execute(f"""
            CREATE OR REPLACE TEMP TABLE temp_summary_prices AS
            SELECT
                CAST(id AS BIGINT) as listing_id,
                CAST(price AS DOUBLE) as base_price
            FROM '{raw_dir}/listings.csv';
        """)

        # Listings dimension — note the three temporal columns at the end
        print(" -> Mapping dim_listings and joining dimensions...")
        conn.execute(f"""
            INSERT OR REPLACE INTO dim_listings
            SELECT
                CAST(l.id AS BIGINT) as listing_id,
                '{city}' as city,
                CAST(l.host_id AS BIGINT) as host_id,
                '{city}_' || l.neighbourhood_cleansed as neighbourhood_id,
                l.room_type,
                l.property_type,
                CAST(l.latitude AS DOUBLE) as latitude,
                CAST(l.longitude AS DOUBLE) as longitude,
                CAST(l.accommodates AS INTEGER) as accommodates,
                CAST(l.bedrooms AS INTEGER) as bedrooms,
                CAST(l.beds AS INTEGER) as beds,
                CAST(p.base_price AS DOUBLE) as price,
                CAST(l.review_scores_rating AS DOUBLE) as review_rating,
                l.license,
                CASE
                    WHEN l.license IS NULL OR l.license = '' OR l.license = 'Exempt' THEN 'Unlicensed / Missing'
                    ELSE 'License Registered'
                END as regulatory_status,
                -- FIX: initialise SCD2 state on first load
                CURRENT_TIMESTAMP        as valid_from,
                CAST(NULL AS TIMESTAMP)  as valid_to,
                TRUE                     as is_current
            FROM read_csv_auto('{raw_dir}/listings.csv.gz', ignore_errors=True) l
            LEFT JOIN temp_summary_prices p ON CAST(l.id AS BIGINT) = p.listing_id;
        """)

        # Review facts
        print(" -> Loading fact_reviews timeline records...")
        conn.execute(f"""
            INSERT OR REPLACE INTO fact_reviews
            SELECT
                CAST(id AS BIGINT) as review_id,
                CAST(listing_id AS BIGINT) as listing_id,
                '{city}' as city,
                CAST(date AS DATE) as review_date
            FROM read_csv_auto('{raw_dir}/reviews.csv.gz', ignore_errors=True);
        """)

    # ----------------------------------------------------------------------
    # DATA QUALITY AUDIT
    # ----------------------------------------------------------------------
    print("\n=======================================================")
    print("      RUNNING DATA QUALITY ASSURANCE AUDIT LAYERS      ")
    print("=======================================================")

    dup_listings = conn.execute(
        "SELECT COUNT(*) - COUNT(DISTINCT listing_id) FROM dim_listings"
    ).fetchone()[0]
    print(" ✅ Pass: dim_listings primary key unique."
          if dup_listings == 0 else
          f" ❌ Fail: {dup_listings} duplicate listing_id values.")

    orphans = conn.execute("""
        SELECT COUNT(*) FROM dim_listings l
        LEFT JOIN dim_neighbourhoods n ON l.neighbourhood_id = n.neighbourhood_id
        WHERE n.neighbourhood_id IS NULL
    """).fetchone()[0]
    print(" ✅ Pass: neighbourhood foreign keys resolve."
          if orphans == 0 else
          f" ⚠️ Warning: {orphans} listings unmatched to a neighbourhood.")

    # FIX: surface the price coverage explicitly so a null-price snapshot
    # can never silently pass unnoticed again.
    price_cov = conn.execute("""
        SELECT city,
               COUNT(*) AS listings,
               ROUND(100.0 * COUNT(price) / COUNT(*), 1) AS pct_with_price
        FROM dim_listings GROUP BY city ORDER BY city
    """).df()
    print("\nPrice coverage by city (watch for 0.0% — that city has no usable price):")
    print(price_cov.to_string(index=False))

    print("\n=======================================================")
    print("      RELATIONAL WAREHOUSE COMPILED SUCCESSFULLY       ")
    print("=======================================================")
    for table in ['dim_neighbourhoods', 'dim_hosts', 'dim_listings', 'fact_reviews']:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"Table: {table:<25} | Verified Row Count: {count:,}")

    conn.close()


if __name__ == "__main__":
    build_relational_warehouse()