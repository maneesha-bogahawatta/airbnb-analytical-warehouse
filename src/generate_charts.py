import os
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu

def set_professional_style():
    """Applies a publication-grade aesthetic layout to matplotlib."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 16,
        'savefig.bbox': 'tight'
    })

def generate_analytics_and_stats():
    db_path = "data/airbnb_warehouse.db"
    output_dir = "reports/figures"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Connecting to data warehouse: {db_path}...")
    conn = duckdb.connect(db_path)
    set_professional_style()
    
    # -------------------------------------------------------------------------
    # CHART 1: Host Monopolization Spectrum
    # -------------------------------------------------------------------------
    print("Extracting Host Concentration Metrics...")
    host_query = """
        WITH host_counts AS (
            SELECT city, host_id, COUNT(*) as local_listings
            FROM dim_listings
            GROUP BY city, host_id
        ),
        segmented_hosts AS (
            SELECT city,
                CASE 
                    WHEN local_listings = 1 THEN '1: Casual Single Host'
                    WHEN local_listings BETWEEN 2 AND 4 THEN '2-4: Small Portfolio'
                    WHEN local_listings BETWEEN 5 AND 9 THEN '5-9: Medium Commercial'
                    ELSE '10+: Commercial Mega-Operator'
                END as host_tier,
                local_listings
            FROM host_counts
        )
        SELECT city, host_tier, SUM(local_listings) as total_listings_in_tier,
            ROUND(100.0 * SUM(local_listings) / SUM(SUM(local_listings)) OVER(PARTITION BY city), 2) as supply_percentage
        FROM segmented_hosts
        GROUP BY city, host_tier
        ORDER BY city, host_tier;
    """
    df_host = conn.execute(host_query).df()
    
    plt.figure(figsize=(10, 6))
    ax1 = sns.barplot(data=df_host, x="host_tier", y="supply_percentage", hue="city", palette=["#E53935", "#1E88E5"])
    plt.title("Market Supply Share by Host Operational Portfolio Tier", pad=15)
    plt.xlabel("Host Scale Classification (Properties Managed)")
    plt.ylabel("Percentage of Market Supply Inventory (%)")
    plt.legend(title="Market Destination")
    
    for p in ax1.patches:
        if p.get_height() > 0:
            ax1.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() + 1), 
                         ha='center', va='center', fontsize=10, color='black', xytext=(0, 5), textcoords='offset points')
    plt.ylim(0, 100)
    plt.savefig(f"{output_dir}/host_concentration_comparison.png", dpi=300)
    plt.close()
    print(" -> Success: Generated 'host_concentration_comparison.png'")

    # -------------------------------------------------------------------------
    # CHART 2: Regulatory Registration Status Matrix
    # -------------------------------------------------------------------------
    print("Extracting Regulatory Compliance Ratios...")
    reg_query = """
        SELECT city, regulatory_status, COUNT(*) as listing_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(PARTITION BY city), 2) as compliance_percentage
        FROM dim_listings
        GROUP BY city, regulatory_status;
    """
    df_reg = conn.execute(reg_query).df()
    
    plt.figure(figsize=(9, 6))
    ax2 = sns.barplot(data=df_reg, x="city", y="compliance_percentage", hue="regulatory_status", palette=["#43A047", "#D32F2F"])
    plt.title("Platform Regulatory Registration Compliance Matrix", pad=15)
    plt.xlabel("Market Jurisdiction")
    plt.ylabel("Proportion of Active Assets (%)")
    plt.legend(title="License Classification")
    
    for p in ax2.patches:
        if p.get_height() > 0:
            ax2.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() + 1), 
                         ha='center', va='center', fontsize=10, color='black', xytext=(0, 5), textcoords='offset points')
    plt.ylim(0, 110)
    plt.savefig(f"{output_dir}/regulatory_compliance_matrix.png", dpi=300)
    plt.close()
    print(" -> Success: Generated 'regulatory_compliance_matrix.png'")

   # -------------------------------------------------------------------------
    # ADVANCED STATISTICAL ENGINE: Non-Parametric Hypothesis Testing
    # -------------------------------------------------------------------------
    print("\n=======================================================")
    print("   RUNNING ADVANCED STATISTICAL HYPOTHESIS TESTING    ")
    print("=======================================================")
    
    # Query directly from your verified warehouse columns
    print("Extracting review rating profiles from the warehouse...")
    bcn_ratings = conn.execute("""
        SELECT CAST(review_rating AS DOUBLE) as rating 
        FROM dim_listings 
        WHERE city='barcelona' AND review_rating IS NOT NULL AND review_rating > 0;
    """).df()['rating']
    
    mad_ratings = conn.execute("""
        SELECT CAST(review_rating AS DOUBLE) as rating 
        FROM dim_listings 
        WHERE city='madrid' AND review_rating IS NOT NULL AND review_rating > 0;
    """).df()['rating']
    
    print(f"Sample Size (Barcelona Cleaned Ratings): {len(bcn_ratings):,} properties")
    print(f"Sample Size (Madrid Cleaned Ratings):    {len(mad_ratings):,} properties")
    
    # Execute Mann-Whitney U Test across review ratings
    if len(bcn_ratings) > 0 and len(mad_ratings) > 0:
        stat, p_value = mannwhitneyu(bcn_ratings, mad_ratings, alternative='two-sided')
        
        print(f"\nMann-Whitney U Statistic: {stat:,}")
        print(f"Asymptotic Significance Level (p-value): {p_value:.6g}")
        
        print("\n-------------------------------------------------------")
        print("Statistical Interpretation:")
        if p_value < 0.05:
            print(" [RESULT] REJECT THE NULL HYPOTHESIS (p < 0.05)")
            print(" -> Evidence confirms a statistically significant difference in customer satisfaction")
            print("    and review rating distributions between Barcelona and Madrid.")
        else:
            print(" [RESULT] FAIL TO REJECT THE NULL HYPOTHESIS (p >= 0.05)")
            print(" -> No statistically significant variation detected in customer rating layouts.")
    else:
        print(" ❌ Error: Insufficient rating metrics to perform hypothesis testing.")
    print("=======================================================\n")
    
    conn.close()

# Force execution immediately upon invocation
generate_analytics_and_stats()