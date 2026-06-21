import duckdb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# 1. Database Connection
con = duckdb.connect('data/airbnb_warehouse.db')

# 2. Extract Data (Including 'city' as a feature)
print("Extracting multi-city data...")
query = """
    SELECT price, bedrooms, accommodates, room_type, neighbourhood_id, city
    FROM dim_listings 
    WHERE price > 0 AND price < 1000 AND bedrooms IS NOT NULL
"""
df = con.execute(query).df()

# 3. Preprocessing: One-Hot Encoding
# 'city' is now included to allow the model to learn market-specific price differences
df = pd.get_dummies(df, columns=['room_type', 'neighbourhood_id', 'city'], drop_first=True)

# Define Features (X) and Target (y)
X = df.drop('price', axis=1)
y = df['price']

# 4. Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Train Model
print("Training Random Forest model...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 6. Evaluate
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)

print(f"--- Model Results ---")
print(f"Final Model R² Score: {r2:.2f}")

# Optional: Show top drivers
importances = pd.Series(model.feature_importances_, index=X.columns)
print("\nTop 5 Price Drivers:")
print(importances.nlargest(5))

con.close()