import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def run_temporal_analysis(db_path="data/airbnb_warehouse.db"):
    os.makedirs("reports/figures", exist_ok=True)
    conn = duckdb.connect(db_path)
    
    print("=======================================================")
    print("        SECTION 4.3: TEMPORAL & SEASONAL ANALYSIS      ")
    print("=======================================================\n")
    
    # 1. Profile review volume over time as a proxy for historical demand growth
    print("📅 1. HISTORICAL DEMAND GROWTH PROXIED BY REVIEW VOLUME TIER")
    print("-" * 70)
    monthly_reviews = conn.execute("""
        SELECT 
            EXTRACT(YEAR FROM review_date)::INT as review_year,
            COUNT(*) as total_reviews_filed
        FROM fact_reviews
        WHERE review_date IS NOT NULL AND EXTRACT(YEAR FROM review_date) BETWEEN 2018 AND 2024
        GROUP BY review_year
        ORDER BY review_year ASC;
    """).df()
    print(monthly_reviews.to_string(index=False))
    print("\n")

    # 2. Extracting Host Tenure Pricing Evolution Matrix (Fixed Join Layer)
    print("⏳ 2. HOST EXPERIENCE AND TENURE PRICING GRADIENTS")
    print("-" * 70)
    host_tenure = conn.execute("""
        SELECT 
            l.city,
            CASE 
                WHEN h.host_since < '2015-01-01' THEN '1. Legacy Veteran (Pre-2015)'
                WHEN h.host_since BETWEEN '2015-01-01' AND '2020-01-01' THEN '2. Established Expansionist'
                ELSE '3. Modern New Entrant (Post-2020)'
            END as host_tenure_tier,
            COUNT(l.listing_id) as property_count,
            ROUND(AVG(l.review_rating), 2) as mean_rating
        FROM dim_listings l
        JOIN dim_hosts h ON l.host_id = h.host_id
        WHERE h.host_since IS NOT NULL AND l.review_rating IS NOT NULL
        GROUP BY l.city, host_tenure_tier
        ORDER BY l.city, host_tenure_tier;
    """).df()
    print(host_tenure.to_string(index=False))
    print("\n")
    
    # 3. Generating a Graphical Review Volume Timeline
    print("📈 Generating high-resolution temporal tracking trends line chart...")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=monthly_reviews, x="review_year", y="total_reviews_filed", marker="o", color="crimson", linewidth=2.5, ax=ax)
    ax.set_title("Market Velocity: Annual Review Volume Timeline Trends")
    ax.set_xlabel("Historical Calendar Operating Year")
    ax.set_ylabel("Total Documented Reviews Count")
    
    plt.tight_layout()
    plt.savefig("reports/figures/temporal_demand_trends.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/temporal_demand_trends.png'")

    conn.close()

if __name__ == "__main__":
    run_temporal_analysis()