import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_graphical_reports(db_path="data/airbnb_warehouse.db"):
    os.makedirs("reports/figures", exist_ok=True)
    conn = duckdb.connect(db_path)
    
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({'font.size': 11, 'axes.labelsize': 12, 'axes.titlesize': 14})
    
    print("📈 Generating high-resolution graphical reports...")

    # -----------------------------------------------------------------
    # VISUALIZATION 1: Cross-Market Price Distribution
    # -----------------------------------------------------------------
    # Removed 'city = madrid' to allow comparison across all cities
    df_prices = conn.execute("""
        SELECT price, room_type, city 
        FROM dim_listings 
        WHERE price IS NOT NULL AND price > 0;
    """).df()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=df_prices, x="price", y="room_type", hue="city", palette="Set2", log_scale=True, ax=ax)
    ax.set_title("Cross-Market Price Distribution (Log Scale)")
    ax.set_xlabel("Price (€) - Log Scaled")
    ax.set_ylabel("Room Type")
    plt.tight_layout()
    plt.savefig("reports/figures/market_price_distribution.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/market_price_distribution.png'")

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
    
    df_hosts['percent_share'] = df_hosts.groupby('city')['total_listings'].transform(lambda x: (x / x.sum()) * 100)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_hosts, x="host_segment", y="percent_share", hue="city", palette="muted", ax=ax)
    ax.set_title("Market Supply Share: Commercial vs. Casual Operators")
    ax.set_xlabel("Host Portfolio Tier")
    ax.set_ylabel("Percentage (%) of City Supply")
    plt.tight_layout()
    plt.savefig("reports/figures/market_supply_concentration.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/market_supply_concentration.png'")

    # -----------------------------------------------------------------
    # VISUALIZATION 3: Customer Review Score Inflation
    # -----------------------------------------------------------------
    df_ratings = conn.execute("SELECT city, review_rating FROM dim_listings WHERE review_rating IS NOT NULL").df()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.kdeplot(data=df_ratings, x="review_rating", hue="city", fill=True, common_norm=False, palette="dark", alpha=0.3, ax=ax)
    ax.set_xlim(3.5, 5.0)
    ax.set_title("Distribution of Customer Review Ratings by City")
    ax.set_xlabel("Review Score (out of 5.0)")
    plt.tight_layout()
    plt.savefig("reports/figures/review_rating_inflation.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/review_rating_inflation.png'")

    conn.close()
    print("\n🎉 All graphical reports compiled successfully!")

if __name__ == "__main__":
    generate_graphical_reports()