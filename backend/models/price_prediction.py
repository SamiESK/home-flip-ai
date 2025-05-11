import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import xgboost as xgb
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import joblib
import math

logger = logging.getLogger(__name__)

class PricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'sqft', 'beds', 'baths', 'days_on_market',
            'latitude', 'longitude', 'zip_code',
            'lot_size', 'year_built', 'stories',
            'has_garage', 'has_pool', 'has_basement',
            'price_per_sqft', 'days_since_update'
        ]
        
        # Column mapping for different data sources
        self.column_mapping = {
            'days_on_market': ['days_on_market', 'days_on_mls'],
            'baths': ['baths', 'full_baths'],
            'latitude': ['latitude', 'lat'],
            'longitude': ['longitude', 'lng'],
            'lot_size': ['lot_size', 'lot_sqft'],
            'year_built': ['year_built'],
            'stories': ['stories'],
            'has_garage': ['parking_garage'],
            'has_pool': ['pool'],
            'has_basement': ['basement'],
            'days_since_update': ['days_on_mls']  # Map days_on_mls to days_since_update
        }
        
        # Categorical features for encoding
        self.categorical_features = ['zip_code']
        
    def prepare_data(self, df):
        """Prepare data for model training"""
        try:
            # Create a copy of the dataframe to avoid modifying the original
            df = df.copy()
            
            # Map columns to expected names
            for target_col, source_cols in self.column_mapping.items():
                for source_col in source_cols:
                    if source_col in df.columns:
                        df[target_col] = df[source_col]
                        break
            
            # Add missing columns with default values
            required_columns = {
                'sqft': 0,
                'beds': 0,
                'baths': 0,
                'days_on_market': 0,
                'latitude': 0,
                'longitude': 0,
                'zip_code': '00000',
                'lot_size': 0,
                'year_built': 2000,  # Default to 2000 if not available
                'stories': 1,        # Default to 1 story if not available
                'has_garage': 0,
                'has_pool': 0,
                'has_basement': 0
            }
            
            for col, default_value in required_columns.items():
                if col not in df.columns:
                    df[col] = default_value
            
            # Calculate derived features
            if 'list_price' in df.columns and 'sqft' in df.columns:
                df['price_per_sqft'] = df['list_price'] / df['sqft'].replace(0, 1)  # Avoid division by zero
            else:
                df['price_per_sqft'] = 0
                
            if 'last_update' in df.columns:
                df['days_since_update'] = (pd.Timestamp.now() - pd.to_datetime(df['last_update'], errors='coerce')).dt.days
            else:
                df['days_since_update'] = 0
            
            # Handle missing values
            numeric_features = [col for col in self.feature_columns if col not in self.categorical_features]
            categorical_features = self.categorical_features
            
            # Create preprocessing pipelines
            numeric_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])
            
            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ])
            
            # Combine preprocessing steps
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, numeric_features),
                    ('cat', categorical_transformer, categorical_features)
                ])
            
            # Extract features and target
            X = df[self.feature_columns]
            y = df['list_price']
            
            # Apply preprocessing
            X_processed = preprocessor.fit_transform(X)
            return X_processed, y, preprocessor
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
            
    def train_model(self, historical_data):
        """Train the price prediction model"""
        try:
            logger.info("Training price prediction model...")
            
            # Filter out extreme outliers
            historical_data = historical_data[
                (historical_data['list_price'] > 0) & 
                (historical_data['list_price'] < historical_data['list_price'].quantile(0.95))
            ]
            
            # Calculate price per sqft and filter out extreme values
            historical_data['price_per_sqft'] = historical_data['list_price'] / historical_data['sqft']
            historical_data = historical_data[
                (historical_data['price_per_sqft'] > historical_data['price_per_sqft'].quantile(0.05)) &
                (historical_data['price_per_sqft'] < historical_data['price_per_sqft'].quantile(0.95))
            ]
            
            # Prepare data
            X, y, preprocessor = self.prepare_data(historical_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Initialize models with more conservative parameters
            models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=10,
                    min_samples_leaf=4,
                    random_state=42
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=8,
                    learning_rate=0.05,
                    subsample=0.8,
                    random_state=42
                ),
                'xgboost': xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=8,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                )
            }
            
            # Train and evaluate models
            best_score = -float('inf')
            best_model = None
            
            for name, model in models.items():
                # Cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
                mean_cv_score = cv_scores.mean()
                
                logger.info(f"{name} CV R² score: {mean_cv_score:.3f}")
                
                if mean_cv_score > best_score:
                    best_score = mean_cv_score
                    best_model = model
            
            # Train best model
            best_model.fit(X_train, y_train)
            self.model = best_model
            self.preprocessor = preprocessor
            
            # Calculate final performance
            train_score = best_model.score(X_train, y_train)
            test_score = best_model.score(X_test, y_test)
            
            logger.info(f"Best model training complete. R² scores - Train: {train_score:.3f}, Test: {test_score:.3f}")
            
            return {
                'train_score': train_score,
                'test_score': test_score,
                'cv_score': best_score
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
            
    def sanitize_json(self, obj):
        """Recursively convert NaN/inf values to None for JSON serialization."""
        if isinstance(obj, dict):
            return {k: self.sanitize_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.sanitize_json(v) for v in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif hasattr(obj, 'item') and callable(obj.item):  # numpy scalar
            v = obj.item()
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                return None
            return v
        return obj

    def predict_price(self, property_data):
        """Predict property price"""
        try:
            if self.model is None:
                raise ValueError("Model not trained")
            
            # Map the input data to expected format
            mapped_data = {}
            for target_col, source_cols in self.column_mapping.items():
                for source_col in source_cols:
                    if source_col in property_data:
                        mapped_data[target_col] = property_data[source_col]
                        break
                if target_col not in mapped_data:
                    mapped_data[target_col] = 0  # Default value if not found
            
            # Add required columns that might not be in the mapping
            for col in self.feature_columns:
                if col not in mapped_data:
                    if col in property_data:
                        mapped_data[col] = property_data[col]
                    else:
                        mapped_data[col] = 0  # Default value
            
            # Create DataFrame and predict
            features = pd.DataFrame([mapped_data])[self.feature_columns]
            prediction = self.model.predict(features)[0]
            
            return {
                'predicted_price': float(prediction),
                'confidence': 0.8  # You might want to calculate this based on model confidence
            }
            
        except Exception as e:
            logger.error(f"Error predicting price: {str(e)}")
            raise
            
    def analyze_market_trends(self, historical_data, zip_code=None):
        """Analyze market trends"""
        try:
            # Create a copy to avoid SettingWithCopyWarning
            historical_data = historical_data.copy()
            
            # Filter by zip code if provided
            if zip_code:
                historical_data = historical_data[historical_data['zip_code'] == zip_code]
            
            # Determine which date column to use
            date_columns = ['date', 'list_date', 'sale_date']
            date_col = None
            for col in date_columns:
                if col in historical_data.columns:
                    date_col = col
                    break
            
            if date_col is None:
                historical_data.loc[:, 'date'] = pd.Timestamp.now()
                date_col = 'date'
            
            # Convert date column to datetime
            historical_data[date_col] = pd.to_datetime(historical_data[date_col], errors='coerce')
            historical_data.loc[historical_data[date_col].isna(), date_col] = pd.Timestamp.now()
            
            # Create month periods for grouping
            historical_data['month_period'] = historical_data[date_col].dt.to_period('M')
            
            # Calculate monthly metrics
            monthly_metrics = historical_data.groupby('month_period').agg({
                'list_price': ['mean', 'median', 'count'],
                'sqft': 'mean',
                'days_on_market': 'mean'
            }).reset_index()
            
            # Calculate price per square foot
            monthly_metrics['price_per_sqft'] = monthly_metrics[('list_price', 'mean')] / monthly_metrics[('sqft', 'mean')]
            
            # Calculate price changes
            monthly_metrics['price_change'] = monthly_metrics[('list_price', 'mean')].pct_change() * 100
            monthly_metrics['price_per_sqft_change'] = monthly_metrics['price_per_sqft'].pct_change() * 100
            
            # Calculate market metrics
            current_price = float(monthly_metrics[('list_price', 'mean')].iloc[-1]) if not monthly_metrics.empty else 0
            current_price_per_sqft = float(monthly_metrics['price_per_sqft'].iloc[-1]) if not monthly_metrics.empty else 0
            
            # Calculate price changes over different periods
            price_changes = {
                '3m': float(monthly_metrics['price_change'].tail(3).mean()) if len(monthly_metrics) >= 3 else 0,
                '6m': float(monthly_metrics['price_change'].tail(6).mean()) if len(monthly_metrics) >= 6 else 0,
                '12m': float(monthly_metrics['price_change'].tail(12).mean()) if len(monthly_metrics) >= 12 else 0
            }
            
            # Calculate inventory metrics
            current_inventory = len(historical_data[historical_data['days_on_market'] <= 30])
            avg_days_on_market = float(monthly_metrics[('days_on_market', 'mean')].iloc[-1]) if not monthly_metrics.empty else 0
            
            # Convert monthly trends to JSON-serializable format
            monthly_trends = []
            for _, row in monthly_metrics.iterrows():
                trend = {
                    'date': str(row['month_period']),
                    'mean_price': float(row[('list_price', 'mean')].iloc[0] if hasattr(row[('list_price', 'mean')], 'iloc') else row[('list_price', 'mean')]),
                    'median_price': float(row[('list_price', 'median')].iloc[0] if hasattr(row[('list_price', 'median')], 'iloc') else row[('list_price', 'median')]),
                    'count': int(row[('list_price', 'count')].iloc[0] if hasattr(row[('list_price', 'count')], 'iloc') else row[('list_price', 'count')]),
                    'price_per_sqft': float(row['price_per_sqft'].iloc[0] if hasattr(row['price_per_sqft'], 'iloc') else row['price_per_sqft']),
                    'avg_days_on_market': float(row[('days_on_market', 'mean')].iloc[0] if hasattr(row[('days_on_market', 'mean')], 'iloc') else row[('days_on_market', 'mean')]),
                    'price_change': float(row['price_change'].iloc[0] if hasattr(row['price_change'], 'iloc') else row['price_change']),
                    'price_per_sqft_change': float(row['price_per_sqft_change'].iloc[0] if hasattr(row['price_per_sqft_change'], 'iloc') else row['price_per_sqft_change'])
                }
                monthly_trends.append(trend)
            
            result = {
                'current_price': current_price,
                'current_price_per_sqft': current_price_per_sqft,
                'price_changes': price_changes,
                'current_inventory': current_inventory,
                'avg_days_on_market': avg_days_on_market,
                'monthly_trends': monthly_trends
            }
            return self.sanitize_json(result)
            
        except Exception as e:
            logger.error(f"Error analyzing market trends: {str(e)}")
            raise
            
    def save_model(self, path):
        """Save the trained model"""
        try:
            model_data = {
                'model': self.model,
                'preprocessor': self.preprocessor,
                'feature_columns': self.feature_columns
            }
            joblib.dump(model_data, path)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
            
    def load_model(self, path):
        """Load a trained model"""
        try:
            model_data = joblib.load(path)
            self.model = model_data['model']
            self.preprocessor = model_data['preprocessor']
            self.feature_columns = model_data['feature_columns']
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def save_properties_to_csv(self, cleaned_properties, zip_code):
        """Save properties to CSV"""
        try:
            # Create data directory if it doesn't exist
            data_dir = ROOT_DIR / 'data'
            data_dir.mkdir(exist_ok=True)
            
            # Use a timestamp in the filename to preserve historical data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = data_dir / f'HomeHarvest_properties_{zip_code}_{timestamp}.csv'
            
            # Convert to DataFrame
            new_df = pd.DataFrame(cleaned_properties)
            
            # Add a scrape_timestamp column to track when this data was collected
            new_df['scrape_timestamp'] = datetime.now().isoformat()
            
            # Save the new data
            new_df.to_csv(filepath, index=False, quoting=1)  # QUOTE_ALL
            logger.info(f"Saved {len(new_df)} properties to {filepath}")
            
            # Also maintain a latest file for easy access to most recent data
            latest_filepath = data_dir / f'HomeHarvest_properties_{zip_code}_latest.csv'
            new_df.to_csv(latest_filepath, index=False, quoting=1)
            logger.info(f"Updated latest file with {len(new_df)} properties")
            
        except Exception as e:
            logger.error(f"Error saving properties to CSV: {str(e)}") 