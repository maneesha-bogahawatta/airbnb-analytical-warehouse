import os
import polars as pl

def profile_dataset(file_path, name):
    print(f"Profiling {name}...")
    # Read CSV natively (even if it's a compressed .gz file!)
    df = pl.read_csv(file_path, infer_schema_length=10000, ignore_errors=True)
    
    total_rows = df.height
    total_cols = df.width
    
    # Calculate null rates per column
    null_counts = df.null_count()
    profile_data = []
    
    for col in df.columns:
        nulls = null_counts[col][0]
        null_pct = (nulls / total_rows) * 100
        cardinality = df[col].n_unique()
        dtype = str(df[col].dtype)
        
        profile_data.append({
            "Column": col,
            "Type": dtype,
            "Null Count": nulls,
            "Null %": f"{null_pct:.2f}%",
            "Unique Values": cardinality
        })
        
    profile_df = pl.DataFrame(profile_data)
    return total_rows, total_cols, profile_df

def generate_report():
    raw_dir = "data/raw/barcelona/"
    report_path = "reports/data_quality_report.md"
    os.makedirs("reports", exist_ok=True)
    
    files_to_profile = {
        "listings.csv.gz": "Detailed Listings Data",
        "calendar.csv.gz": "Detailed Calendar/Availability Data",
        "reviews.csv.gz": "Detailed Customer Reviews Data"
    }
    
    with open(report_path, "w") as f:
        f.write("# Data Quality & Profiling Diagnostics Report\n\n")
        f.write(f"**Target Market Analysis:** Barcelona\n")
        f.write("Generated using High-Performance Polars Core Engine.\n\n")
        
        for filename, description in files_to_profile.items():
            full_path = os.path.join(raw_dir, filename)
            if not os.path.exists(full_path):
                print(f"Skipping {filename}, file not found.")
                continue
                
            rows, cols, df_profile = profile_dataset(full_path, filename)
            
            f.write(f"## {description} (`{filename}`)\n")
            f.write(f"* **Total Observations (Rows):** {rows:,}\n")
            f.write(f"* **Total Attributes (Columns):** {cols}\n\n")
            f.write("### Column Structural Diagnostics\n\n")
            
            # Convert Polars DataFrame to a clean Markdown table format for your report
            f.write("| Column Name | Data Type | Null Count | Null % | Unique Count |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for row in df_profile.iter_rows(named=True):
                f.write(f"| {row['Column']} | {row['Type']} | {row['Null Count']:,} | {row['Null %']} | {row['Unique Values']:,} |\n")
            f.write("\n---\n\n")
            
    print(f"\n[SUCCESS] Profiling completed! Diagnostic report written to: {report_path}")

if __name__ == "__main__":
    generate_report()