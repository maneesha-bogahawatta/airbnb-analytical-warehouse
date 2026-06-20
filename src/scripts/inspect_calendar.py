import duckdb

def inspect_calendar():
    con = duckdb.connect()
    print("--- Inspecting Data Distribution ---")
    # Check how many rows are 'f' vs 't' and how many have prices
    query = """
        SELECT 
            available, 
            COUNT(*) as row_count,
            COUNT(price) as price_count
        FROM read_csv_auto('data/raw/madrid/calendar.csv.gz', ignore_errors=True)
        GROUP BY available
    """
    print(con.execute(query).df())

if __name__ == "__main__":
    inspect_calendar()