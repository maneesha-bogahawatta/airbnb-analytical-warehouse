import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_box_plot():
    # Setup
    os.makedirs("reports/figures", exist_ok=True)
    con = duckdb.connect("data/airbnb_warehouse.db")
    
    # 1. Use the new 'canonical_property_type' and include 'city'
    # 2. Removed the hard '500' cap to show a true cross-city comparison
    query = """
        SELECT price, canonical_property_type, city 
        FROM dim_listings 
        WHERE price > 0 AND price < 1000 
    """
    data = con.execute(query).df()
    
    # 3. Plotting: Using 'city' as hue allows for a side-by-side comparison
    plt.figure(figsize=(12, 6))
    sns.boxplot(
        x='canonical_property_type', 
        y='price', 
        hue='city', 
        data=data, 
        palette='viridis'
    )
    
    plt.title('Distribution of Nightly Rates by Property Type and City')
    plt.xlabel('Standardized Property Type')
    plt.ylabel('Nightly Price (€)')
    plt.xticks(rotation=45) # Rotate labels for readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout() # Prevents labels from being cut off
    
    # Save
    plt.savefig('reports/figures/price_distribution_box.png', dpi=300)
    print("✅ Comparative box plot saved to: reports/figures/price_distribution_box.png")
    
    con.close()

if __name__ == "__main__":
    generate_box_plot()