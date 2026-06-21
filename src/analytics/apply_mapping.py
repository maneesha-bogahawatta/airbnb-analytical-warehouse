import duckdb
import json

# 1. Load the mapping
with open('data/property_type_mapping.json', 'r') as f:
    mapping = json.load(f)

# 2. Connect to Database
con = duckdb.connect('data/airbnb_warehouse.db')

# 3. Create a new column 'canonical_property_type'
# We use a CASE statement to perform the mapping directly in SQL
case_stmt = "CASE " + " ".join([f"WHEN property_type = '{k}' THEN '{v}'" for k, v in mapping.items()]) + " ELSE 'Other' END"

con.execute(f"""
    ALTER TABLE dim_listings ADD COLUMN IF NOT EXISTS canonical_property_type VARCHAR;
    UPDATE dim_listings SET canonical_property_type = {case_stmt};
""")

print("Database updated with canonical categories.")
con.close()