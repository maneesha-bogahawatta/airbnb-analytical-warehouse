import duckdb
import numpy as np
from scipy import stats

def calculate_cohen_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    return (np.mean(group1) - np.mean(group2)) / pooled_std

def run_stats():
    con = duckdb.connect("data/airbnb_warehouse.db")
    data = con.execute("SELECT price, room_type FROM dim_listings WHERE price > 0").df()
    
    entire = data[data['room_type'] == 'Entire home/apt']['price'].dropna().values
    private = data[data['room_type'] == 'Private room']['price'].dropna().values
    
    t_stat, p_val = stats.ttest_ind(entire, private, equal_var=False)
    d = calculate_cohen_d(entire, private)
    
    print(f"--- Statistical Analysis: H1 (Privacy Premium) ---")
    print(f"Entire Home Mean: €{np.mean(entire):.2f} | Private Room Mean: €{np.mean(private):.2f}")
    print(f"P-Value: {p_val:.4e} | Cohen's d (Effect Size): {d:.2f}")

if __name__ == "__main__":
    run_stats()