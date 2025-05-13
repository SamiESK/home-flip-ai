import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.ROOT_DIR = Path(__file__).parent.parent.parent
        self.model_dir = os.path.join(self.ROOT_DIR, 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
    def prepare_data(self, df):
        """Prepare data for training"""
        try:
            # Clean and preprocess the data
            df = df.copy()
            df.fillna(0, inplace=True)
            
            # Calculate profit (if not exists)
            if 'profit' not in df.columns:
                df['profit'] = df['estimated_value'] - df['list_price']
            
            # Select features
            features = ['list_price', 'sqft', 'beds', 'baths', 'days_on_market']
            X = df[features]
            y = df['profit']
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
            
    def train_model(self, csv_path):
        """Train the model and save it"""
        try:
            # Load data
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded data from {csv_path}")
            
            # Prepare data
            X, y = self.prepare_data(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            model = XGBRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            logger.info(f"Model R² scores - Train: {train_score:.3f}, Test: {test_score:.3f}")
            
            # Save model
            model_path = os.path.join(self.model_dir, 'flip_score_model.pkl')
            joblib.dump(model, model_path)
            logger.info(f"Model saved to {model_path}")
            
            return model_path
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
            
    def train_from_latest_data(self):
        """Train model using the latest property data"""
        try:
            # Find latest data file
            data_dir = os.path.join(self.ROOT_DIR, 'data')
            files = [f for f in os.listdir(data_dir) if f.startswith('HomeHarvest_') and f.endswith('.csv')]
            if not files:
                raise ValueError("No property data files found")
                
            latest_file = max(files)
            csv_path = os.path.join(data_dir, latest_file)
            
            # Train model
            return self.train_model(csv_path)
            
        except Exception as e:
            logger.error(f"Error training from latest data: {str(e)}")
            raise 