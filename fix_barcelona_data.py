import duckdb
import pandas as pd
import os

# 1. Define the path to your database and raw file
db_path = 'data/airbnb_warehouse.db'
csv_path = 'data/raw/barcelona/listings.csv'

# Check if the file exists before running
if not os.path.exists(csv_path):
    print(f"Error: Could not find {csv_path}. Check your folder structure.")
    exit()

# 2. Connect to your existing database
con = duckdb.connect(db_path)

# 3. Load the raw data
print("Loading CSV...")
df = pd.read_csv(csv_path)

# 4. CLEANING: The crucial step to turn "$150.00" into 150.0
print("Cleaning price column...")
if df['price'].dtype == 'object':
    # Remove '$' and ',' then convert to float
    df['price'] = df['price'].replace(r'[\$,]', '', regex=True).astype(float)

# 5. Re-ingest into the warehouse
print("Updating database...")
con.execute("CREATE OR REPLACE TABLE barcelona_listings AS SELECT * FROM df")

# 6. Verify
result = con.execute("SELECT COUNT(*), AVG(price) FROM barcelona_listings WHERE price > 0").fetchall()
print(f"Data fixed! Found records and average price: {result}")

con.close()