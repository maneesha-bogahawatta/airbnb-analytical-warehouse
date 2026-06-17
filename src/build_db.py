import os
import duckdb

def build_relational_warehouse():
    db_path = "data/airbnb_warehouse.db"
    os.makedirs("data", exist_ok=True)
    
    print(f"Connecting to DuckDB Analytical Warehouse: {db_path}")
    conn = duckdb.connect(db_path)
    
    # Configure performance parameters for your Mac
    conn.execute("SET threads TO 4;")
    
    print("\nExecuting DDL: Establishing Relational Constraints...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_neighbourhoods (
            neighbourhood_id VARCHAR PRIMARY KEY,
            city VARCHAR NOT NULL,
            neighbourhood_name VARCHAR NOT NULL,
            neighbourhood_group VARCHAR
        );
        
        CREATE TABLE IF NOT EXISTS dim_hosts (
            host_id BIGINT PRIMARY KEY,
            host_name VARCHAR,
            host_since DATE,
            is_superhost BOOLEAN,
            total_host_listings INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS dim_listings (
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
            regulatory_status VARCHAR
        );
        
        CREATE TABLE IF NOT EXISTS fact_reviews (
            review_id BIGINT PRIMARY KEY,
            listing_id BIGINT,
            city VARCHAR NOT NULL,
            review_date DATE
        );
    """)
    
    active_markets = ["barcelona", "madrid"]
    
    for city in active_markets:
        raw_dir = f"data/raw/{city}"
        if not os.path.exists(raw_dir):
            print(f"⚠️ Directory missing, skipping market: {raw_dir}")
            continue
            
        print(f"\nProcessing ETL Pipeline for Market: {city.upper()}")
        
        # Ingest Neighborhood Dimension
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
            
        # Ingest Host Dimension (Reading .gz directly using DuckDB's native parser)
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
        
        # Extract Summary Prices to fix the Null values
        print(" -> Caching recovery price matrices...")
        conn.execute(f"""
            CREATE OR REPLACE TEMP TABLE temp_summary_prices AS
            SELECT 
                CAST(id AS BIGINT) as listing_id,
                CAST(price AS DOUBLE) as base_price
            FROM '{raw_dir}/listings.csv';
        """)
        
        # Ingest Listings Dimension
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
                COALESCE(p.base_price, 0.0) as price,
                CAST(l.review_scores_rating AS DOUBLE) as review_rating,
                l.license,
                CASE 
                    WHEN l.license IS NULL OR l.license = '' OR l.license = 'Exempt' THEN 'Unlicensed / Missing'
                    ELSE 'License Registered'
                END as regulatory_status
            FROM read_csv_auto('{raw_dir}/listings.csv.gz', ignore_errors=True) l
            LEFT JOIN temp_summary_prices p ON CAST(l.id AS BIGINT) = p.listing_id;
        """)
        
        # Ingest Review Facts
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

    print("\n=======================================================")
    print("      RELATIONAL WAREHOUSE COMPILED SUCCESSFULLY       ")
    print("=======================================================")
    for table in ['dim_neighbourhoods', 'dim_hosts', 'dim_listings', 'fact_reviews']:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"Table: {table:<25} | Verified Row Count: {count:,}")
        
    conn.close()

if __name__ == "__main__":
    build_relational_warehouse()