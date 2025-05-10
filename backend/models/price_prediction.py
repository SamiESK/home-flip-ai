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
            'lot_size': ['lot_size', 'acre_lot', 'lot_sqft'],
            'year_built': ['year_built', 'built_year'],
            'stories': ['stories', 'floors'],
            'has_garage': ['has_garage', 'garage'],
            'has_pool': ['has_pool', 'pool'],
            'has_basement': ['has_basement', 'basement']
        }
        
        # Categorical features for encoding
        self.categorical_features = ['zip_code']
        
    def prepare_data(self, df):
        """Prepare data for model training"""
        try:
            # Map columns to expected names
            for target_col, source_cols in self.column_mapping.items():
                for source_col in source_cols:
                    if source_col in df.columns:
                        df[target_col] = df[source_col]
                        break
            # --- Add missing columns with default values ---
            if 'lot_size' not in df.columns:
                if 'lot_sqft' in df.columns:
                    df['lot_size'] = df['lot_sqft']
                else:
                    df['lot_size'] = 0
            for col in ['has_garage', 'has_pool', 'has_basement']:
                if col not in df.columns:
                    df[col] = 0
            # Calculate derived features
            df['price_per_sqft'] = df['list_price'] / df['sqft']
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
            
            # Prepare data
            X, y, preprocessor = self.prepare_data(historical_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Initialize models
            models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=10,
                    learning_rate=0.1,
                    random_state=42
                ),
                'xgboost': xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=10,
                    learning_rate=0.1,
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
            # Map property data to expected column names
            mapped_data = {}
            for target_col, source_cols in self.column_mapping.items():
                for source_col in source_cols:
                    if source_col in property_data:
                        mapped_data[target_col] = property_data[source_col]
                        break
                if target_col not in mapped_data:
                    # Special handling for lot_size
                    if target_col == 'lot_size' and 'lot_sqft' in property_data:
                        mapped_data[target_col] = property_data['lot_sqft']
                    else:
                        mapped_data[target_col] = 0  # Default value if not found
            # Ensure has_garage, has_pool, has_basement are present
            for col in ['has_garage', 'has_pool', 'has_basement']:
                if col not in mapped_data:
                    mapped_data[col] = 0
            # Calculate derived features
            mapped_data['price_per_sqft'] = property_data.get('list_price', 0) / mapped_data.get('sqft', 1)
            last_update = property_data.get('last_update')
            if last_update:
                mapped_data['days_since_update'] = (pd.Timestamp.now() - pd.to_datetime(last_update)).days
            else:
                mapped_data['days_since_update'] = 0
            # Add other required columns
            for col in self.feature_columns:
                if col not in mapped_data:
                    mapped_data[col] = property_data.get(col, 0)
            # Prepare property data
            features = pd.DataFrame([mapped_data])[self.feature_columns]
            features_processed = self.preprocessor.transform(features)
            # Make prediction
            predicted_price = self.model.predict(features_processed)[0]
            # Get feature importance
            if hasattr(self.model, 'feature_importances_'):
                importance = dict(zip(self.feature_columns, 
                                   self.model.feature_importances_))
                # Convert all importance values to float
                importance = {k: float(v) for k, v in importance.items()}
            else:
                importance = {}
            result = {
                'predicted_price': float(predicted_price),
                'feature_importance': importance,
                'price_per_sqft': float(predicted_price / mapped_data.get('sqft', 1))
            }
            return self.sanitize_json(result)
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