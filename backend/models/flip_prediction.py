import pandas as pd
import pickle
import os
from pathlib import Path
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class FlipPredictor:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.initialize_model()

    def initialize_model(self):
        """Initialize the flip prediction model"""
        try:
            # Get the root directory path
            ROOT_DIR = Path(__file__).parent.parent.parent
            
            # Use proper path for the model file
            self.model_path = os.path.join(ROOT_DIR, 'src', 'model.p')
            logger.info(f"Looking for model at: {self.model_path}")
            
            if os.path.exists(self.model_path):
                # Load the trained model
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("Flip prediction model loaded successfully")
            else:
                logger.warning(f"Model file not found at {self.model_path}")
        except Exception as e:
            logger.error(f"Error initializing flip prediction model: {str(e)}")

    def predict(self, property_data: Dict) -> Tuple[bool, float]:
        """
        Make a prediction for a single property
        Returns: (is_good_flip, confidence)
        """
        try:
            if self.model is None:
                raise ValueError("Model not initialized")

            # Convert the input data to match the model's expected format
            input_data = pd.DataFrame([{
                'price': float(property_data['list_price']),
                'sqft': float(property_data['sqft']),
                'beds': int(property_data['beds']),
                'baths': int(property_data['baths']),
                'days_on_market': int(property_data['days_on_market'])
            }])

            # Make prediction
            prediction = self.model.predict(input_data)[0]
            
            # Calculate confidence based on the prediction value
            raw_prediction = float(prediction)
            if raw_prediction > 0:
                # For positive predictions, map to 60-100
                confidence = 60 + (40 / (1 + abs(raw_prediction)))
            else:
                # For negative predictions, map to 0-40
                confidence = 40 / (1 + abs(raw_prediction))
            
            # Round to whole number for simplicity
            confidence = round(confidence)

            # Convert prediction to boolean (True if > 0)
            is_good_flip = bool(prediction > 0)

            return is_good_flip, float(confidence)

        except Exception as e:
            logger.error(f"Error making flip prediction: {str(e)}")
            raise 