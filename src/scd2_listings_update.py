import duckdb

def execute_scd2_listings_merge(db_path="data/airbnb_warehouse.db"):
    """
    Executes a Type 2 Slowly Changing Dimension merge pattern matching the database schema.
    """
    conn = duckdb.connect(db_path)
    
    # 1. Create a transient staging delta simulating an incoming new scrape snapshot
    # We join with dim_neighbourhoods to correctly find the matching neighbourhood_id
    conn.execute("""
        CREATE OR REPLACE TEMP TABLE incoming_listings_delta AS 
        SELECT 
            raw.id AS listing_id,
            raw.host_id,
            n.neighbourhood_id,
            raw.license,
            raw.review_scores_rating AS review_rating,
            CURRENT_TIMESTAMP AS event_time
        FROM read_csv_auto('data/raw/madrid/listings.csv.gz', ignore_errors=True) raw
        LEFT JOIN dim_neighbourhoods n 
          ON LOWER(raw.neighbourhood_cleansed) = LOWER(n.neighbourhood_name) 
          AND n.city = 'madrid'
        LIMIT 500;
    """)
    
    # 2. STEP 1 OF THE SCD2 MERGE: Expiry Step
    print("⏳ Expiring altered listing states in dimension tables...")
    conn.execute("""
        UPDATE dim_listings
        SET 
            valid_to = delta.event_time,
            is_current = FALSE
        FROM incoming_listings_delta delta
        WHERE dim_listings.listing_id = delta.listing_id
          AND dim_listings.is_current = TRUE
          AND (
               dim_listings.license IS DISTINCT FROM delta.license OR
               dim_listings.review_rating IS DISTINCT FROM delta.review_rating
          );
    """)
    
    # 3. STEP 2 OF THE SCD2 MERGE: Insertion Step
    # Explicitly populating ONLY the specific columns tracked in our SCD2 pipeline setup
    print("🚀 Inserting pristine historical states into dim_listings...")
    conn.execute("""
        INSERT INTO dim_listings (
            listing_id, host_id, neighbourhood_id, license, review_rating, valid_from, valid_to, is_current
        )
        SELECT 
            d.listing_id, d.host_id, d.neighbourhood_id, d.license, d.review_rating,
            d.event_time AS valid_from,
            CAST(NULL AS TIMESTAMP) AS valid_to,
            TRUE AS is_current
        FROM incoming_listings_delta d
        LEFT JOIN dim_listings existing
          ON d.listing_id = existing.listing_id AND existing.is_current = TRUE
        WHERE existing.listing_id IS NULL;
    """)
    
    print("🎉 SCD Type 2 tracking merge completed smoothly.")
    conn.close()

if __name__ == "__main__":
    execute_scd2_listings_merge()