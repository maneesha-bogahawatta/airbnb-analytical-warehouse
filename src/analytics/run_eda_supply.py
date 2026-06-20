import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def run_supply_analysis(db_path="data/airbnb_warehouse.db"):
    os.makedirs("reports/figures", exist_ok=True)
    conn = duckdb.connect(db_path)
    
    print("=======================================================")
    print("        SECTION 4.4: HOST & SUPPLY-SIDE ANALYSIS       ")
    print("=======================================================\n")
    
    # 1. Analyze the performance delta driven by Superhost designation status
    print("🏅 1. SUPERHOST STATUS VS. USER SATISFACTION OUTCOMES")
    print("-" * 75)
    superhost_perf = conn.execute("""
        SELECT 
            l.city,
            h.is_superhost,
            COUNT(l.listing_id) as total_listings,
            ROUND(AVG(l.review_rating), 2) as mean_rating
        FROM dim_listings l
        JOIN dim_hosts h ON l.host_id = h.host_id
        WHERE h.is_superhost IS NOT NULL AND l.review_rating IS NOT NULL
        GROUP BY l.city, h.is_superhost
        ORDER BY l.city, h.is_superhost;
    """).df()
    print(superhost_perf.to_string(index=False))
    print("\n")

    # 2. Supply Concentration Matrix: The Top 1% Accumulation Rate Check
    print("📊 2. MARKET POWER: PORTFOLIO SHARE CONTROLLED BY THE TOP 1% OF HOSTS")
    print("-" * 75)
    market_power = conn.execute("""
        WITH host_volumes AS (
            SELECT city, host_id, COUNT(listing_id) as properties_owned
            FROM dim_listings
            GROUP BY city, host_id
        ),
        ranked_hosts AS (
            SELECT 
                city,
                properties_owned,
                PERCENT_RANK() OVER (PARTITION BY city ORDER BY properties_owned DESC) as host_percentile
            FROM host_volumes
        )
        SELECT 
            city,
            COUNT(*) as total_hosts,
            SUM(CASE WHEN host_percentile <= 0.01 THEN properties_owned ELSE 0 END) as listings_held_by_top_1_percent,
            SUM(properties_owned) as total_market_listings,
            ROUND(100.0 * SUM(CASE WHEN host_percentile <= 0.01 THEN properties_owned ELSE 0 END) / SUM(properties_owned), 2) as top_1_percent_supply_share
        FROM ranked_hosts
        GROUP BY city;
    """).df()
    print(market_power.to_string(index=False))
    print("\n")

    conn.close()

if __name__ == "__main__":
    run_supply_analysis()