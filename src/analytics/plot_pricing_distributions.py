import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_box_plot():
    # Setup
    os.makedirs("reports/figures", exist_ok=True)
    con = duckdb.connect("data/airbnb_warehouse.db")
    
    # Fetch pricing data for comparison
    data = con.execute("""
        SELECT price, room_type 
        FROM dim_listings 
        WHERE price > 0 AND price < 500  -- Filtering extremes for visual clarity
    """).df()
    
    # Plotting
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='room_type', y='price', data=data, palette='viridis')
    
    plt.title('Distribution of Nightly Rates: Entire Home vs. Private Room')
    plt.xlabel('Room Type')
    plt.ylabel('Nightly Price (€)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save
    plt.savefig('reports/figures/price_distribution_box.png', dpi=300)
    print("✅ Plot saved to: reports/figures/price_distribution_box.png")

if __name__ == "__main__":
    generate_box_plot()