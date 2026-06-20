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
    
    # 1. Querying Top 10 High-Density Neighborhood Gradients in Madrid
    print("📍 1. NEIGHBORHOOD PRICING & DENSITY MATRICES (MADRID)")
    print("-" * 70)
    madrid_geo = conn.execute("""
        SELECT 
            n.neighbourhood_name,
            COUNT(l.listing_id) as total_properties,
            ROUND(MEDIAN(l.price), 2) as median_price,
            ROUND(AVG(l.review_rating), 2) as mean_rating
        FROM dim_listings l
        JOIN dim_neighbourhoods n ON l.neighbourhood_id = n.neighbourhood_id
        WHERE l.is_current = TRUE AND l.city = 'madrid' AND l.price IS NOT NULL
        GROUP BY n.neighbourhood_name
        ORDER BY total_properties DESC
        LIMIT 10;
    """).df()
    print(madrid_geo.to_string(index=False))
    print("\n")

    # 2. Extracting Room Type Clustering across Zones
    print("🏡 2. ROOM TYPE SPATIAL STRATIFICATION MATRIX")
    print("-" * 70)
    room_strat = conn.execute("""
        SELECT 
            n.neighbourhood_name,
            COUNT(CASE WHEN l.room_type = 'Entire home/apt' THEN 1 END) as entire_homes,
            COUNT(CASE WHEN l.room_type = 'Private room' THEN 1 END) as private_rooms,
            ROUND(100.0 * COUNT(CASE WHEN l.room_type = 'Entire home/apt' THEN 1 END) / COUNT(l.listing_id), 2) as entire_home_percentage
        FROM dim_listings l
        JOIN dim_neighbourhoods n ON l.neighbourhood_id = n.neighbourhood_id
        WHERE l.is_current = TRUE AND l.city = 'madrid'
        GROUP BY n.neighbourhood_name
        ORDER BY entire_homes DESC
        LIMIT 5;
    """).df()
    print(room_strat.to_string(index=False))
    print("\n")

    # 3. Generating a Graphical Neighborhood Premium Chart
    print("📈 Generating high-resolution neighborhood pricing gradient plot...")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot top 10 neighborhoods by volume, color-coded by median price
    sns.barplot(
        data=madrid_geo, 
        x="median_price", 
        y="neighbourhood_name", 
        hue="neighbourhood_name",
        palette="flare", 
        legend=False,
        ax=ax
    )
    ax.set_title("Madrid Geographic Pricing Gradients: Central vs. Peripheral Zones")
    ax.set_xlabel("Median Listing Price (€)")
    ax.set_ylabel("Neighborhood Cleaned Designation")
    
    plt.tight_layout()
    plt.savefig("reports/figures/geospatial_pricing_gradients.png", dpi=300)
    plt.close()
    print("  -> Saved 'reports/figures/geospatial_pricing_gradients.png'")
    
    conn.close()

if __name__ == "__main__":
    run_geospatial_analysis()