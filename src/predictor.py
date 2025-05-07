import pandas as pd
import pickle
import os
from pathlib import Path
import xgboost as xgb

def predict(property_data):
    """
    Make a prediction for a single property
    """
    try:
        # Get the root directory path
        ROOT_DIR = Path(__file__).parent.parent
        
        # Use proper path for the model file
        model_path = os.path.join(ROOT_DIR, 'models', 'flip_score_model.pkl')
        print(f"Looking for model at: {model_path}")  # Debug print
        
        # Load the trained model
        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        # Convert the input data to match the model's expected format
        # Convert string values to numeric types and use correct feature names
        input_data = pd.DataFrame([{
            'price': float(property_data['price']),
            'sqft': float(property_data['sqft']),
            'beds': int(property_data['beds']),
            'baths': int(property_data['baths']),
            'days_on_market': int(property_data['days_on_market'])
        }])

        # Make prediction
        prediction = model.predict(input_data)[0]
        
        # For XGBRegressor, we'll calculate confidence based on the prediction value
        try:
            # Get the raw prediction value
            raw_prediction = float(prediction)
            print(f"Raw prediction value: {raw_prediction}")  # Debug print
            
            # Calculate confidence based on the prediction value
            # Using a more aggressive scaling to get more distinct values
            if raw_prediction > 0:
                # For positive predictions, map to 60-100
                confidence = 60 + (40 / (1 + abs(raw_prediction)))
            else:
                # For negative predictions, map to 0-40
                confidence = 40 / (1 + abs(raw_prediction))
            
            # Round to whole number for simplicity
            confidence = round(confidence)
            
        except Exception as e:
            print(f"Error calculating confidence: {str(e)}")
            confidence = 50  # Default if calculation fails

        # Convert prediction to boolean (True if > 0)
        is_good_flip = bool(prediction > 0)

        return is_good_flip, float(confidence)

    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise