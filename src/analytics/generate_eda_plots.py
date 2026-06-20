import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_graphical_reports(db_path="data/airbnb_warehouse.db"):
    # Ensure target output directory exists
    os.makedirs("reports/figures", exist_ok=True)
    
    # Connect to the DuckDB semantic tier
    conn = duckdb.connect(db_path)
    
    # Set professional plotting aesthetics
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({'font.size': 11, 'axes.labelsize': 12, 'axes.titlesize': 14})
    
    print("📈 Generating high-resolution graphical reports...")

    # -----------------------------------------------------------------
    # VISUALIZATION 1: Madrid Price Distribution (Log Scale for Outliers)
    # -----------------------------------------------------------------
    df_madrid = conn.execute("""
        SELECT price, room_type 
        FROM dim_listings 
        WHERE city = 'madrid' AND price IS NOT NULL AND price > 0;
    """).df()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df_madrid, x="price", y="room_type", palette="Set2", log_scale=True, ax=ax)
    ax.set_title("Madrid Market Price Distribution across Room Types (Log Scale)")
    ax.set_xlabel("Price (€) - Log Scaled to Capture Outliers")
    ax.set_ylabel("Room Type Classification")
    plt.tight_layout()
    plt.savefig("reports/figures/madrid_price_distribution.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/madrid_price_distribution.png'")

    # -----------------------------------------------------------------
    # VISUALIZATION 2: Host Supply Concentration Bar Matrix
    # -----------------------------------------------------------------
    df_hosts = conn.execute("""
        WITH host_counts AS (
            SELECT host_id, city, COUNT(listing_id) as portfolio_size
            FROM dim_listings
            GROUP BY host_id, city
        )
        SELECT 
            city,
            CASE 
                WHEN portfolio_size = 1 THEN 'Casual (1)'
                WHEN portfolio_size BETWEEN 2 AND 5 THEN 'Small Multi (2-5)'
                WHEN portfolio_size BETWEEN 6 AND 20 THEN 'Boutique Agency (6-20)'
                ELSE 'Mega Enterprise (21+)'
            END as host_segment,
            SUM(portfolio_size) as total_listings
        FROM host_counts
        GROUP BY city, host_segment;
    """).df()
    
    # Calculate percentage share within each city market
    df_hosts['percent_share'] = df_hosts.groupby('city')['total_listings'].transform(lambda x: (x / x.sum()) * 100)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_hosts, x="host_segment", y="percent_share", hue="city", palette="muted", ax=ax)
    ax.set_title("Market Supply Share Concentration: Commercial vs. Casual Operators")
    ax.set_xlabel("Host Portfolio Segmentation Tier")
    ax.set_ylabel("Percentage (%) of Total City Housing Supply")
    plt.tight_layout()
    plt.savefig("reports/figures/market_supply_concentration.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/market_supply_concentration.png'")

    # -----------------------------------------------------------------
    # VISUALIZATION 3: Customer Review Score Rating Inflation Kernel Density
    # -----------------------------------------------------------------
    df_ratings = conn.execute("""
        SELECT city, review_rating 
        FROM dim_listings 
        WHERE review_rating IS NOT NULL;
    """).df()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.kdeplot(data=df_ratings, x="review_rating", hue="city", fill=True, common_norm=False, palette="dark", alpha=0.4, ax=ax)
    ax.set_xlim(3.5, 5.0)  # Magnify the upper tier where inflation concentrates
    ax.set_title("Empirical Distribution of Customer Review Ratings (Rating Inflation Matrix)")
    ax.set_xlabel("Review Score Rating (Out of 5.0)")
    ax.set_ylabel("Probability Density Distribution")
    plt.tight_layout()
    plt.savefig("reports/figures/review_rating_inflation.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/review_rating_inflation.png'")

    conn.close()
    print("\n🎉 All graphical reports compiled successfully into 'reports/figures/'!")

if __name__ == "__main__":
    generate_graphical_reports()