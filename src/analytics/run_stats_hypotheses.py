import duckdb
import pandas as pd
import numpy as np
from scipy import stats

def get_cohen_d(g1, g2):
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2: return 0
    pooled_std = np.sqrt(((n1-1)*np.var(g1, ddof=1) + (n2-1)*np.var(g2, ddof=1)) / (n1+n2-2))
    return (np.mean(g1) - np.mean(g2)) / pooled_std

def run_hypothesis_suite():
    con = duckdb.connect("data/airbnb_warehouse.db")

    df = con.execute("""
        SELECT 
            l.listing_id,
            l.price, 
            LOG(l.price) as log_price, 
            l.room_type, 
            h.is_superhost, 
            l.review_rating,
            l.neighbourhood_id,
            l.accommodates,
            l.city 
        FROM dim_listings l
        JOIN dim_hosts h ON l.host_id = h.host_id
        WHERE l.price > 0
    """).df()
    # ^ NOTE: added l.listing_id and l.accommodates to the SELECT —
    #   H3 needs listing_id to join against fact_reviews,
    #   the H5 replacement needs accommodates.

    print("--- H1: Privacy Premium (Entire Home vs Private Room) ---")
    entire = df[df['room_type'] == 'Entire home/apt']['log_price'].dropna()
    private = df[df['room_type'] == 'Private room']['log_price'].dropna()
    t, p = stats.ttest_ind(entire, private, equal_var=False)
    print(f"P-Value: {p:.4e} | Cohen's d: {get_cohen_d(entire, private):.2f}")

    print("\n--- H2: Superhost Rating Premium ---")
    super = df[df['is_superhost'] == True]['review_rating'].dropna()
    non = df[df['is_superhost'] == False]['review_rating'].dropna()
    t, p = stats.ttest_ind(super, non, equal_var=False)
    print(f"P-Value: {p:.4e} | Cohen's d: {get_cohen_d(super, non):.2f}")

    # >>> NEW: H3 goes here <
    print("\n--- H3: Review Volume Impact on Price ---")
    review_counts = con.execute("""
        SELECT listing_id, COUNT(*) as n_reviews
        FROM fact_reviews
        GROUP BY listing_id
    """).df()
    df_h3 = df.merge(review_counts, on='listing_id', how='left')
    df_h3['n_reviews'] = df_h3['n_reviews'].fillna(0)
    high_volume = df_h3[df_h3['n_reviews'] >= 10]['log_price'].dropna()
    low_volume  = df_h3[df_h3['n_reviews'] < 10]['log_price'].dropna()
    t, p = stats.ttest_ind(high_volume, low_volume, equal_var=False)
    d = get_cohen_d(high_volume, low_volume)
    print(f"High-volume (n={len(high_volume):,}) mean log-price: {high_volume.mean():.3f}")
    print(f"Low-volume  (n={len(low_volume):,}) mean log-price: {low_volume.mean():.3f}")
    print(f"P-Value: {p:.4e} | Cohen's d: {d:.2f}")

    print("\n--- H4: Neighbourhood Price Variance (ANOVA) ---")
    groups = [group['log_price'].values for name, group in df.groupby('neighbourhood_id') if len(group) > 5]
    f_stat, p_anova = stats.f_oneway(*groups)
    print(f"ANOVA P-Value: {p_anova:.4e}")

    # >>> NEW: eta-squared goes right after the ANOVA, same H4 block <
    grand_mean = df['log_price'].mean()
    ss_between = sum(len(g) * (g['log_price'].mean() - grand_mean)**2
                      for _, g in df.groupby('neighbourhood_id') if len(g) > 5)
    ss_total = sum((df['log_price'] - grand_mean)**2)
    eta_squared = ss_between / ss_total
    print(f"Eta-squared: {eta_squared:.3f}")

    # >>> NEW: H5 replacement goes here (was the calendar-based weekday/weekend test) <
    print("\n--- H5 (Revised): Capacity-Price Relationship by City ---")
    print("NOTE: Original H5 (weekday/weekend pricing) required calendar.csv.gz, ")
    print("deprioritized due to ingestion cost late in the project. See report for rationale.")
    for city in df['city'].unique():
        city_df = df[df['city'] == city].dropna(subset=['accommodates', 'log_price'])
        corr, p_corr = stats.pearsonr(city_df['accommodates'], city_df['log_price'])
        print(f"{city.capitalize():10s} | Pearson r: {corr:.3f} | P-Value: {p_corr:.4e} | n={len(city_df):,}")

    con.close()

if __name__ == "__main__":
    run_hypothesis_suite()