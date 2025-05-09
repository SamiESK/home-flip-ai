import pandas as pd
import os
from typing import Dict, List, Optional
import logging
import json
from datetime import datetime
import ast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_dir: str = "data"):
        """Initialize the DataProcessor with the data directory path."""
        self.data_dir = data_dir
        self.required_columns = {
            'property_url': str,
            'property_id': str,
            'list_price': float,
            'sqft': float,
            'beds': float,
            'full_baths': float,
            'half_baths': float,
            'street': str,
            'city': str,
            'state': str,
            'zip_code': str,
            'status': str,
            'days_on_mls': int,
            'primary_photo': str,
            'alt_photos': str,
            'year_built': int,
            'lot_sqft': float,
            'price_per_sqft': float,
            'style': str,
            'text': str,
            'tax': float,
            'tax_history': str,
            'assessed_value': float,
            'estimated_value': float
        }

    def get_latest_data_file(self) -> Optional[str]:
        """Get the most recent HomeHarvest data file."""
        try:
            files = [f for f in os.listdir(self.data_dir) if f.startswith('HomeHarvest_') and f.endswith('.csv') and not f.endswith('sample.csv')]
            if not files:
                logger.error("No HomeHarvest data files found")
                return None
                
            # Sort files by timestamp in filename (format: HomeHarvest_YYYYMMDD_HHMMSS.csv)
            latest_file = max(files, key=lambda x: datetime.strptime('_'.join(x.split('_')[1:3]).split('.')[0], '%Y%m%d_%H%M%S'))
            return os.path.join(self.data_dir, latest_file)
        except Exception as e:
            logger.error(f"Error finding latest data file: {str(e)}")
            return None

    def safe_json_loads(self, x):
        """Safely parse JSON or string representation of JSON."""
        if pd.isna(x):
            return []
        try:
            if isinstance(x, str):
                # Try to parse as JSON first
                try:
                    return json.loads(x)
                except:
                    # If that fails, try to parse as Python literal
                    try:
                        return ast.literal_eval(x)
                    except:
                        return x
            return x
        except:
            return x

    def load_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load data from a CSV file and perform basic validation."""
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Validate required columns
            missing_columns = set(self.required_columns.keys()) - set(df.columns)
            if missing_columns:
                logger.warning(f"Missing optional columns: {missing_columns}")
            
            # Convert columns to appropriate types
            for col, dtype in self.required_columns.items():
                if col in df.columns:
                    try:
                        if col == 'tax_history':
                            df[col] = df[col].apply(self.safe_json_loads)
                        elif dtype == str:
                            df[col] = df[col].fillna('').astype(str)
                        elif dtype == float:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        elif dtype == int:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    except Exception as e:
                        logger.error(f"Error converting column {col} to {dtype}: {str(e)}")
            
            # Basic data validation
            if df.empty:
                logger.error("DataFrame is empty")
                return None
            
            # Calculate total baths from full and half baths
            if 'full_baths' in df.columns and 'half_baths' in df.columns:
                df['baths'] = df['full_baths'].fillna(0) + 0.5 * df['half_baths'].fillna(0)
            
            # Validate numeric columns
            numeric_columns = ['list_price', 'sqft', 'beds', 'baths', 'days_on_mls', 'price_per_sqft']
            for col in numeric_columns:
                if col in df.columns and (df[col] < 0).any():
                    logger.warning(f"Negative values found in {col}")
                    df[col] = df[col].abs()  # Convert negative values to positive
            
            # Validate string columns
            string_columns = ['street', 'city', 'state', 'zip_code', 'status']
            for col in string_columns:
                if col in df.columns and df[col].isna().any():
                    logger.warning(f"Missing values found in {col}")
                    df[col] = df[col].fillna('Unknown')
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return None

    def process_data(self, df: pd.DataFrame) -> Dict:
        """Process the data and return relevant statistics."""
        try:
            stats = {
                'total_properties': len(df),
                'avg_price': df['list_price'].mean() if 'list_price' in df.columns else None,
                'avg_sqft': df['sqft'].mean() if 'sqft' in df.columns else None,
                'avg_beds': df['beds'].mean() if 'beds' in df.columns else None,
                'avg_baths': df['baths'].mean() if 'baths' in df.columns else None,
                'avg_days_on_market': df['days_on_mls'].mean() if 'days_on_mls' in df.columns else None,
                'avg_price_per_sqft': df['price_per_sqft'].mean() if 'price_per_sqft' in df.columns else None,
                'properties_by_status': df['status'].value_counts().to_dict() if 'status' in df.columns else None,
                'properties_by_city': df['city'].value_counts().to_dict() if 'city' in df.columns else None,
                'properties_by_state': df['state'].value_counts().to_dict() if 'state' in df.columns else None,
                'property_types': df['style'].value_counts().to_dict() if 'style' in df.columns else None,
                'price_ranges': {
                    'under_300k': len(df[df['list_price'] < 300000]) if 'list_price' in df.columns else 0,
                    '300k_500k': len(df[(df['list_price'] >= 300000) & (df['list_price'] < 500000)]) if 'list_price' in df.columns else 0,
                    '500k_750k': len(df[(df['list_price'] >= 500000) & (df['list_price'] < 750000)]) if 'list_price' in df.columns else 0,
                    '750k_1m': len(df[(df['list_price'] >= 750000) & (df['list_price'] < 1000000)]) if 'list_price' in df.columns else 0,
                    'over_1m': len(df[df['list_price'] >= 1000000]) if 'list_price' in df.columns else 0
                }
            }
            return stats
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            return {}

def main():
    """Main function to process the data."""
    processor = DataProcessor()
    
    # Get the latest data file
    latest_file = processor.get_latest_data_file()
    if latest_file:
        logger.info(f"Processing latest data file: {latest_file}")
        df = processor.load_data(latest_file)
        if df is not None:
            stats = processor.process_data(df)
            logger.info("Data processing completed successfully")
            logger.info(f"Statistics: {stats}")
        else:
            logger.error("Failed to load data")
    else:
        logger.error("No data file found to process")

if __name__ == "__main__":
    main() 