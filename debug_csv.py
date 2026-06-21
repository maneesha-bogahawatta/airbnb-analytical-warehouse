import pandas as pd
import os

csv_path = 'data/raw/barcelona/listings.csv'

if not os.path.exists(csv_path):
    print("File does not exist at:", csv_path)
else:
    df = pd.read_csv(csv_path)
    print("Columns in CSV:", df.columns.tolist())
    print("First 5 rows of 'price':")
    print(df['price'].head())
    print("Total rows in CSV:", len(df))