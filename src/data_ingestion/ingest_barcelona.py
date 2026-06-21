import duckdb
import pandas as pd

def ingest_barcelona():
    con = duckdb.connect("data/airbnb_warehouse.db")
    
    # Point directly to the uncompressed listings.csv
    file_path = "data/raw/barcelona/listings.csv"
    
    df = pd.read_csv(file_path) 
    
    # Ingest into the warehouse
    con.execute("CREATE OR REPLACE TABLE barcelona_listings AS SELECT * FROM df")
    print("✅ Barcelona data successfully ingested into warehouse.")

if __name__ == "__main__":
    ingest_barcelona()