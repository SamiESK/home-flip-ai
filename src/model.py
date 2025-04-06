import joblib
import pandas as pd

def load_model(model_filename='models/home_flip_model.pkl'):
    model = joblib.load(model_filename)
    return model

def predict_property_value(model, property_data):
    prediction = model.predict([property_data])
    return prediction

if __name__ == "__main__":
    model = load_model()
    
    # Example prediction: Predict profit for a property with 2000 sqft, 3 beds, 2 baths, and a price of $500k
    property_data = [500000, 2000, 3, 2, 30]  # [price, sqft, beds, baths, days_on_market]
    predicted_profit = predict_property_value(model, property_data)
    print(f"Predicted Profit: {predicted_profit}")
