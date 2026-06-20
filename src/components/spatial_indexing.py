import duckdb

def compile_spatial_warehouse_joins(db_path="data/airbnb_warehouse.db"):
    """
    Loads spatial extensions, parses geoJSON polygons, and maps assets 
    using rigorous, hardware-accelerated geometric containment tests.
    """
    conn = duckdb.connect(db_path)
    
    # 1. Initialize and load DuckDB's native spatial engine extension
    print("🧩 Installing and loading DuckDB Spatial extension...")
    conn.execute("INSTALL spatial; LOAD spatial;")
    
    # 2. Ingest geoJSON district polygons into a temporary spatial table
    # DuckDB automatically flattens properties, exposing fields like 'name' directly!
    print("🗺️ Compiling geographic spatial reference geometries...")
    conn.execute("""
        CREATE OR REPLACE TEMP TABLE tmp_spatial_neighborhoods AS
        SELECT 
            features.name::VARCHAR AS neighbourhood_name,
            features.geom AS polygon_geometry
        FROM st_read('data/spatial/madrid_districts.geojson') AS features;
    """)
    
    # 3. Run high-speed geometric point-in-polygon containment joins via ST_Contains
    print("📍 Running hardware-accelerated ST_Contains spatial join...")
    
    # Extract a sample of 5 listings to visually verify structural alignment
    enriched_listings = conn.execute("""
        SELECT 
            raw.id AS listing_id,
            raw.latitude,
            raw.longitude,
            raw.neighbourhood_cleansed AS original_text_name,
            sn.neighbourhood_name AS geo_validated_name
        FROM read_csv_auto('data/raw/madrid/listings.csv.gz', ignore_errors=True) raw
        LEFT JOIN tmp_spatial_neighborhoods sn
          ON ST_Contains(sn.polygon_geometry, ST_Point(raw.longitude::DOUBLE, raw.latitude::DOUBLE))
        WHERE raw.latitude IS NOT NULL AND raw.longitude IS NOT NULL
        LIMIT 5;
    """).df()
    
    print("\n📊 Spatial Join Verification Matrix Output:")
    print(enriched_listings.to_string(index=False))
    
    conn.close()
    print("\n🎉 Geospatial analytical indexing engine completed successfully.")

if __name__ == "__main__":
    compile_spatial_warehouse_joins()