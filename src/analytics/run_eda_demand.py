import duckdb
import pandas as pd

def run_demand_analysis(db_path="data/airbnb_warehouse.db"):
    conn = duckdb.connect(db_path)
    
    print("=======================================================")
    print("        SECTION 4.5: REVIEW & DEMAND-SIDE ANALYSIS     ")
    print("=======================================================\n")
    
    # 1. Investigate outliers across all markets
    print("🚨 1. HIGH-PRICE, LOW-SATISFACTION PROPERTIES (MARKET ANOMALIES)")
    print("-" * 80)
    # Added city to the selection to show cross-market distribution
    anomalies = conn.execute("""
        SELECT 
            city,
            listing_id,
            canonical_property_type,
            price,
            review_rating
        FROM dim_listings
        WHERE is_current = TRUE 
          AND review_rating < 4.0 
          AND price > 200
        ORDER BY price DESC
        LIMIT 10;
    """).df()
    print(anomalies.to_string(index=False))
    print("\n")
    
    conn.close()

if __name__ == "__main__":
    run_demand_analysis()