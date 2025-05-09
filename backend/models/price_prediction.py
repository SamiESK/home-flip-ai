import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class PricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'sqft', 'beds', 'baths', 'days_on_market',
            'latitude', 'longitude', 'zip_code'
        ]
        
        # Column mapping for different data sources
        self.column_mapping = {
            'days_on_market': ['days_on_market', 'days_on_mls'],
            'baths': ['baths', 'full_baths'],
            'latitude': ['latitude', 'lat'],
            'longitude': ['longitude', 'lng']
        }
        
    def prepare_data(self, df):
        """Prepare data for model training"""
        try:
            # Map columns to expected names
            for target_col, source_cols in self.column_mapping.items():
                for source_col in source_cols:
                    if source_col in df.columns:
                        df[target_col] = df[source_col]
                        break
            
            # Convert categorical variables
            df['zip_code'] = pd.to_numeric(df['zip_code'], errors='coerce')
            
            # Handle missing values
            for col in self.feature_columns:
                if col in df.columns:
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    # If column is missing, fill with mean from other properties
                    df[col] = df[col].mean() if col in df.columns else 0
            
            # Extract features and target
            X = df[self.feature_columns]
            y = df['list_price']
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            return X_scaled, y
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
            
    def train_model(self, historical_data):
        """Train the price prediction model"""
        try:
            logger.info("Training price prediction model...")
            
            # Prepare data
            X, y = self.prepare_data(historical_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Initialize and train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            self.model.fit(X_train, y_train)
            
            # Calculate model performance
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            logger.info(f"Model training complete. R² scores - Train: {train_score:.3f}, Test: {test_score:.3f}")
            
            return {
                'train_score': train_score,
                'test_score': test_score
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
            
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
                    mapped_data[target_col] = 0  # Default value if not found
            
            # Add other required columns
            for col in self.feature_columns:
                if col not in mapped_data:
                    mapped_data[col] = property_data.get(col, 0)
            
            # Prepare property data
            features = pd.DataFrame([mapped_data])[self.feature_columns]
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            predicted_price = self.model.predict(features_scaled)[0]
            
            # Get feature importance
            importance = dict(zip(self.feature_columns, 
                               self.model.feature_importances_))
            
            return {
                'predicted_price': float(predicted_price),
                'feature_importance': importance
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
                # If no date column is found, use current date for all records
                historical_data.loc[:, 'date'] = pd.Timestamp.now()
                date_col = 'date'
            else:
                # Convert date column to datetime and handle any conversion errors
                try:
                    # First try parsing without specifying format to handle ISO dates
                    historical_data[date_col] = pd.to_datetime(historical_data[date_col], errors='coerce')
                    
                    # Check if we have any invalid dates
                    invalid_dates = historical_data[date_col].isna()
                    if invalid_dates.any():
                        logger.warning(f"Found {invalid_dates.sum()} invalid dates in {date_col}. Attempting alternative formats.")
                        # For records with invalid dates, try alternative formats
                        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
                        invalid_dates_df = historical_data[invalid_dates].copy()
                        
                        for fmt in date_formats:
                            try:
                                parsed_dates = pd.to_datetime(invalid_dates_df[date_col], format=fmt, errors='coerce')
                                # Update only the still-invalid dates that were successfully parsed with this format
                                still_invalid = parsed_dates.notna()
                                if still_invalid.any():
                                    historical_data.loc[invalid_dates_df[still_invalid].index, date_col] = parsed_dates[still_invalid]
                                    invalid_dates = historical_data[date_col].isna()
                                    if not invalid_dates.any():
                                        break
                            except Exception:
                                continue
                    
                    # Fill any remaining invalid dates with current date
                    if invalid_dates.any():
                        historical_data.loc[invalid_dates, date_col] = pd.Timestamp.now()
                        logger.warning(f"Filled {invalid_dates.sum()} unparseable dates with current date in {date_col}.")
                    
                except Exception as e:
                    logger.error(f"Error parsing dates: {str(e)}. Using current date.")
                    historical_data[date_col] = pd.Timestamp.now()
            
            # Ensure we have datetime values by forcing conversion
            historical_data[date_col] = pd.to_datetime(historical_data[date_col])
            
            # Create month periods for grouping
            historical_data['month_period'] = historical_data[date_col].dt.to_period('M')
            
            # Calculate monthly average prices
            monthly_prices = historical_data.groupby('month_period')['list_price'].agg(['mean', 'count']).reset_index()
            
            # Sort by date to ensure correct price change calculations
            monthly_prices = monthly_prices.sort_values('month_period')
            
            # Calculate price changes and handle NaN values
            monthly_prices['price_change'] = monthly_prices['mean'].pct_change() * 100
            monthly_prices['price_change'] = monthly_prices['price_change'].fillna(0)
            
            # Calculate market metrics with NaN handling
            current_price = float(monthly_prices['mean'].iloc[-1]) if not monthly_prices.empty else 0
            price_change_3m = float(monthly_prices['price_change'].tail(3).mean()) if len(monthly_prices) >= 3 else 0
            price_change_6m = float(monthly_prices['price_change'].tail(6).mean()) if len(monthly_prices) >= 6 else 0
            price_change_12m = float(monthly_prices['price_change'].tail(12).mean()) if len(monthly_prices) >= 12 else 0
            
            # Calculate days on market trend
            dom_col = 'days_on_market' if 'days_on_market' in historical_data.columns else 'days_on_mls'
            if dom_col in historical_data.columns:
                dom_trend = float(historical_data.groupby('month_period')[dom_col].mean().tail(3).mean())
            else:
                dom_trend = 0
            
            # Convert monthly trends to JSON-serializable format
            monthly_trends = []
            for _, row in monthly_prices.iterrows():
                trend = {
                    'date': str(row['month_period']),
                    'mean_price': float(row['mean']),
                    'count': int(row['count']),
                    'price_change': float(row['price_change'])
                }
                monthly_trends.append(trend)
            
            return {
                'current_price': current_price,
                'price_change_3m': price_change_3m,
                'price_change_6m': price_change_6m,
                'price_change_12m': price_change_12m,
                'avg_days_on_market': dom_trend,
                'monthly_trends': monthly_trends
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market trends: {str(e)}")
            raise
            
    def save_model(self, path):
        """Save the trained model"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
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
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise 