import duckdb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

def compare_models():
    con = duckdb.connect("data/airbnb_warehouse.db")
    
    # Harmonized query: Uses only columns present in both tables
    # Note: price < 500 is used as a safe baseline filter.
    query = """
        SELECT price, room_type, 'madrid' as city
        FROM dim_listings 
        WHERE price > 0 AND price < 500
        
        UNION ALL
        
        SELECT price, room_type, 'barcelona' as city
        FROM barcelona_listings 
        WHERE price > 0 AND price < 500
    """
    
    df = con.execute(query).df()
    
    # Encoding: Converts room_type and city into machine-readable numeric flags
    df = pd.get_dummies(df, columns=['room_type', 'city'], drop_first=True)
    
    X = df.drop('price', axis=1)
    # Log-transform target to handle skewed price data
    y = np.log1p(df['price'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    
    print(f"\n{'Model':<20} | {'Train R2':<10} | {'Test R2':<10} | {'Status'}")
    print("-" * 55)
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        train_r2 = r2_score(y_train, model.predict(X_train))
        test_r2 = r2_score(y_test, model.predict(X_test))
        
        status = "Overfitting!" if (train_r2 - test_r2) > 0.1 else "Stable"
        print(f"{name:<20} | {train_r2:.3f}      | {test_r2:.3f}      | {status}")

if __name__ == "__main__":
    compare_models()