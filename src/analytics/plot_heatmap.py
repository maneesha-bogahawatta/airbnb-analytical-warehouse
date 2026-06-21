import duckdb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_heatmap():
    con = duckdb.connect("data/airbnb_warehouse.db")
    # Update the query to use 'review_rating' instead of 'review_scores_rating'
    df = con.execute("""
        SELECT price, bedrooms, accommodates, review_rating 
        FROM dim_listings 
        WHERE price > 0 AND price < 500
    """).df()
    
    # Calculate correlation matrix
    corr = df.corr()
    
    # Plot heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", square=True)
    plt.title('Feature Correlation Heatmap')
    plt.savefig('reports/figures/correlation_heatmap.png', dpi=300)
    print("✅ Heatmap saved to: reports/figures/correlation_heatmap.png")

if __name__ == "__main__":
    generate_heatmap()