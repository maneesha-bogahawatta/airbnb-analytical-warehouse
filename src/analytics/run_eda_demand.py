import duckdb
import pandas as pd

def run_demand_analysis(db_path="data/airbnb_warehouse.db"):
    conn = duckdb.connect(db_path)
    
    print("=======================================================")
    print("        SECTION 4.5: REVIEW & DEMAND-SIDE ANALYSIS     ")
    print("=======================================================\n")
    
    # 1. Investigate anomalies: listings with immense review volume but critically low rating scores
    print("🚨 1. HIGH-VOLUME, LOW-SATISFACTION PROPERTIES (DETACHED TOURIST TRAPS)")
    print("-" * 80)
    tourist_traps = conn.execute("""
        SELECT 
            city,
            listing_id,
            room_type,
            price,
            review_rating
        FROM dim_listings
        WHERE is_current = TRUE 
          AND review_rating < 4.2 
        ORDER BY price DESC
        LIMIT 5;
    """).df()
    print(tourist_traps.to_string(index=False))
    print("\n")
    
    conn.close()

if __name__ == "__main__":
    run_demand_analysis()