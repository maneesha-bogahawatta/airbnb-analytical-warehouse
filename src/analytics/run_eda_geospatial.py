import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def run_geospatial_analysis(db_path="data/airbnb_warehouse.db"):
    os.makedirs("reports/figures", exist_ok=True)
    conn = duckdb.connect(db_path)
    
    print("=======================================================")
    print("      SECTION 4.2: GEOSPATIAL & NEIGHBORHOOD ANALYSIS  ")
    print("=======================================================\n")
    
    # 1. Querying Top 10 High-Density Neighborhoods (Global)
    # We must JOIN with dim_neighbourhoods to get the name
    geo_data = conn.execute("""
        SELECT 
            l.city,
            n.neighbourhood_name,
            COUNT(l.listing_id) as total_properties,
            ROUND(MEDIAN(l.price), 2) as median_price
        FROM dim_listings l
        JOIN dim_neighbourhoods n ON l.neighbourhood_id = n.neighbourhood_id
        WHERE l.price > 0
        GROUP BY l.city, n.neighbourhood_name
        ORDER BY total_properties DESC
        LIMIT 10;
    """).df()
    print(geo_data.to_string(index=False))
    print("\n")

    # 2. Extracting Room Type Clustering
    room_strat = conn.execute("""
        SELECT 
            l.city,
            n.neighbourhood_name,
            COUNT(CASE WHEN l.room_type = 'Entire home/apt' THEN 1 END) as entire_homes,
            ROUND(100.0 * COUNT(CASE WHEN l.room_type = 'Entire home/apt' THEN 1 END) / COUNT(*), 2) as entire_home_percentage
        FROM dim_listings l
        JOIN dim_neighbourhoods n ON l.neighbourhood_id = n.neighbourhood_id
        GROUP BY l.city, n.neighbourhood_name
        ORDER BY entire_homes DESC
        LIMIT 10;
    """).df()
    print(room_strat.to_string(index=False))
    print("\n")

    # 3. Generating Graphical Pricing Comparison
    print("📈 Generating high-resolution neighborhood pricing gradient plot...")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    sns.barplot(
        data=geo_data, 
        x="median_price", 
        y="neighbourhood_name", 
        hue="city",
        palette="viridis", 
        ax=ax
    )
    ax.set_title("Cross-City Pricing Gradients: Madrid vs. Lisbon")
    ax.set_xlabel("Median Listing Price (€)")
    ax.set_ylabel("Neighborhood")
    
    plt.tight_layout()
    plt.savefig("reports/figures/geospatial_pricing_gradients.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/geospatial_pricing_gradients.png'")
    
    conn.close()

if __name__ == "__main__":
    run_geospatial_analysis()