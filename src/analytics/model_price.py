"""Train the price model ONCE and persist it, so the dashboard loads a real
trained model instead of recomputing ad-hoc arithmetic on every interaction.

This is the single source of truth for "the model" referenced in the report
(Section 7.1). The dashboard's price estimator (app.py) loads this artifact
directly -- it never re-derives pricing logic itself.

Usage:
    python3 src/model_price.py
"""
import duckdb
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

MODEL_PATH = Path("data/price_model.joblib")
META_PATH = Path("data/price_model_meta.json")

def main():
    con = duckdb.connect("data/airbnb_warehouse.db", read_only=True)

    # Pooled Madrid + Lisbon -- the two cities with usable price (see report \u00a78.2).
    # 'city' is included as a feature: Section 7.1 of the report states city
    # ranks as a top-tier driver, so it must actually be in the model.
    df = con.execute("""
        SELECT price, bedrooms, accommodates, room_type, neighbourhood_id, city
        FROM dim_listings
        WHERE price > 0 AND price < 1000
          AND bedrooms IS NOT NULL AND accommodates IS NOT NULL
    """).df()
    con.close()

    df["log_price"] = np.log1p(df["price"])

    cat_cols = ["room_type", "neighbourhood_id", "city"]
    df_enc = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    feature_cols = [c for c in df_enc.columns if c not in ("price", "log_price")]
    X = df_enc[feature_cols]
    y = df_enc["log_price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=200, max_depth=14, min_samples_leaf=5,
                                   random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    r2 = r2_score(y_test, pred)
    mae_eur = mean_absolute_error(np.expm1(y_test), np.expm1(pred))

    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    top_features = importances.head(8).to_dict()

    print(f"Test R\u00b2 (log-price): {r2:.3f}")
    print(f"Test MAE (\u20ac, back-transformed): {mae_eur:.2f}")
    print("Top features:")
    for f, imp in list(top_features.items())[:8]:
        print(f"  {f}: {imp:.3f}")

    # Persist the model AND the exact column structure it expects, so the
    # dashboard can build a matching feature row at inference time without
    # re-deriving any pricing logic itself.
    Path("data").mkdir(exist_ok=True)
    joblib.dump({"model": model, "feature_cols": feature_cols}, MODEL_PATH)

    meta = {
        "r2": round(float(r2), 3),
        "mae_eur": round(float(mae_eur), 2),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "top_features": {k: round(float(v), 4) for k, v in top_features.items()},
        "cities_used": sorted(df["city"].unique().tolist()),
        "room_types": sorted(df["room_type"].dropna().unique().tolist()),
        "neighbourhood_ids": sorted(df["neighbourhood_id"].dropna().unique().tolist()),
        "price_cap_eur": 1000,
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"\nSaved model -> {MODEL_PATH}")
    print(f"Saved metadata -> {META_PATH}")

if __name__ == "__main__":
    main()