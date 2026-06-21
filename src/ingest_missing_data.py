import duckdb
import os

def ingest_missing_data():
    con = duckdb.connect("data/airbnb_warehouse.db")
    
    # 1. Load Review Counts (aggregating from reviews.csv)
    # This creates a summary table to map back to listings
    con.execute("""
        CREATE OR REPLACE TABLE dim_review_stats AS 
        SELECT listing_id, COUNT(*) as review_count
        FROM read_csv_auto('data/reviews.csv.gz')
        GROUP BY listing_id;
    """)
    
    # 2. Load Calendar Data (sampling to keep file size manageable for local machine)
    con.execute("""
        CREATE OR REPLACE TABLE fact_calendar AS 
        SELECT listing_id, date, price
        FROM read_csv_auto('data/calendar.csv.gz')
        WHERE price IS NOT NULL;
    """)
    
    con.close()
    print("✅ Missing data tables ingested successfully.")

if __name__ == "__main__":
    ingest_missing_data()