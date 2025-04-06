import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib

def train_model(csv_path, output_path):
    df = pd.read_csv(csv_path)
    X = df[["price", "sqft", "beds", "baths", "days_on_market"]]
    y = df["profit"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = XGBRegressor()
    model.fit(X_train, y_train)

    joblib.dump(model, output_path)
    print(f"✅ Model trained and saved to {output_path}")
