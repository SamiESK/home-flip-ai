# trainer.py

import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

def train():
    # Load the scraped data
    df = pd.read_csv('data/HomeHarvest_20250404_213158.csv')  # Correct file path

    # Clean and preprocess the data
    df.fillna(0, inplace=True)  # Handle missing values

    # Define your features (X) and target (y)
    X = df[['price', 'sqft', 'beds', 'baths', 'days_on_mls']]  # Adjust features as needed
    y = df['is_good_flip']  # This is the target variable

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a model
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Save the trained model
    with open('model.p', 'wb') as f:
        pickle.dump(model, f)

    print("Model training complete and saved as 'model.p'")
