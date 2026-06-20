import duckdb
import pandas as pd
import numpy as np

def run_distribution_analysis(db_path="data/airbnb_warehouse.db"):
    """
    Computes rigorous analytical metrics from the warehouse to profile
    market distributions, pricing metrics, rating inflation, and host power-laws.
    """
    conn = duckdb.connect(db_path)
    
    print("=======================================================")
    print("      SECTION 4.1: WAREHOUSE DISTRIBUTION ANALYSIS    ")
    print("=======================================================\n")
    
    # 1. Core Summary Metrics Across Markets
    print("📊 1. METROPOLITAN MARKET PROFILES (SUMMARY STATISTICS)")
    print("-" * 55)
    summary_df = conn.execute("""
        SELECT 
            city,
            COUNT(listing_id) as total_properties,
            ROUND(AVG(price), 2) as mean_price,
            ROUND(MEDIAN(price), 2) as median_price,
            ROUND(MIN(price), 2) as min_price,
            ROUND(MAX(price), 2) as max_price,
            ROUND(AVG(review_rating), 2) as mean_rating
        FROM dim_listings
        WHERE is_current = TRUE
        GROUP BY city;
    """).df()
    print(summary_df.to_string(index=False))
    print("\n")
    
    # 2. Host Portfolio Concentration (Power-Law Dynamics)
    print("🦅 2. HOST SUPPLY CONCENTRATION (POWER-LAW PROFILE)")
    print("-" * 55)
    # We break down hosts into distinct market tiers based on property count
    host_tiers = conn.execute("""
        WITH host_counts AS (
            SELECT host_id, city, COUNT(listing_id) as portfolio_size
            FROM dim_listings
            WHERE is_current = TRUE
            GROUP BY host_id, city
        )
        SELECT 
            city,
            CASE 
                WHEN portfolio_size = 1 THEN '1. Casual Single-Listing Host'
                WHEN portfolio_size BETWEEN 2 AND 5 THEN '2. Small Multi-Listing Operator'
                WHEN portfolio_size BETWEEN 6 AND 20 THEN '3. Commercial Boutique Agency'
                ELSE '4. Mega Enterprise Aggregator (21+)'
            END as host_segment,
            COUNT(host_id) as distinct_hosts_in_segment,
            SUM(portfolio_size) as total_listings_controlled,
            ROUND(100.0 * COUNT(host_id) / SUM(COUNT(host_id)) OVER(PARTITION BY city), 2) as percent_of_total_hosts,
            ROUND(100.0 * SUM(portfolio_size) / SUM(SUM(portfolio_size)) OVER(PARTITION BY city), 2) as percent_of_market_supply
        FROM host_counts
        GROUP BY city, host_segment
        ORDER BY city, host_segment;
    """).df()
    print(host_tiers.to_string(index=False))
    print("\n")

    # 3. Review Rating Inflation Assessment
    print("⭐ 3. CUSTOMER REVIEW RATING INFLATION ANALYSIS")
    print("-" * 55)
    rating_profile = conn.execute("""
        SELECT 
            city,
            ROUND(AVG(review_rating), 3) as average_score,
            ROUND(100.0 * COUNT(CASE WHEN review_rating >= 4.5 THEN 1 END) / COUNT(*), 2) as percent_above_4_5,
            ROUND(100.0 * COUNT(CASE WHEN review_rating >= 4.8 THEN 1 END) / COUNT(*), 2) as percent_above_4_8
        FROM dim_listings
        WHERE is_current = TRUE AND review_rating IS NOT NULL
        GROUP BY city;
    """).df()
    print(rating_profile.to_string(index=False))
    print("\n")

    conn.close()

if __name__ == "__main__":
    run_distribution_analysis()