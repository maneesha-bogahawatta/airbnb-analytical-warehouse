import duckdb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_heatmap():
    con = duckdb.connect("data/airbnb_warehouse.db")
    
    # 1. Select numeric columns + the new standardized property type
    # We use the full range (< 1000) to keep the analysis representative
    query = """
        SELECT price, bedrooms, accommodates, review_rating 
        FROM dim_listings 
        WHERE price > 0 AND price < 1000 AND bedrooms IS NOT NULL
    """
    df = con.execute(query).df()
    
    # 2. Calculate correlation matrix
    # Note: Correlations only work on numeric data. 
    # If you want to see how property_type correlates, you would need to 
    # encode it first (like we did in the model script).
    corr = df.corr()
    
    # 3. Plot heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", square=True)
    plt.title('Feature Correlation Heatmap (Madrid, Lisbon, Barcelona)')
    plt.tight_layout() # Prevents label clipping
    plt.savefig('reports/figures/correlation_heatmap.png', dpi=300)
    print("✅ Heatmap saved to: reports/figures/correlation_heatmap.png")
    
    con.close()

if __name__ == "__main__":
    generate_heatmap()