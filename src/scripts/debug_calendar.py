import duckdb

def debug_calendar(db_path="data/airbnb_warehouse.db"):
    con = duckdb.connect()
    # Read just the first 5 rows to inspect the structure
    sample = con.execute("SELECT * FROM read_csv_auto('data/raw/madrid/calendar.csv.gz') LIMIT 5").df()
    print("--- Calendar Data Sample ---")
    print(sample.to_string())
    print("\n--- Column Types ---")
    print(sample.dtypes)

if __name__ == "__main__":
    debug_calendar()