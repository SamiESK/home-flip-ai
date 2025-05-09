import os
from homeharvest import scrape_property
from datetime import datetime
import pandas as pd
from pathlib import Path
import sys
import logging
import json

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Get the root directory path
ROOT_DIR = Path(__file__).parent.parent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_properties(zip_code: str, max_price: float) -> list:
    """
    Filter properties from CSV data based on zip code and max price.
    """
    try:
        logger.info(f"Searching for properties in zip code {zip_code} under ${max_price:,.2f}")
        
        # Get the data directory
        data_dir = Path(__file__).resolve().parent.parent / 'data'
        if not data_dir.exists():
            logger.error(f"Data directory not found at {data_dir}")
            return []
            
        # Get the most recent CSV file
        csv_files = list(data_dir.glob('HomeHarvest_*.csv'))
        if not csv_files:
            logger.error("No HomeHarvest CSV files found")
            return []
            
        latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Using data file: {latest_file}")
        
        # Read the CSV file
        df = pd.read_csv(latest_file, quoting=1)  # Use QUOTE_ALL for proper handling of URLs
        logger.info(f"Loaded {len(df)} properties")
        
        # Filter by zip code
        df = df[df['zip_code'].astype(str) == str(zip_code)]
        logger.info(f"Found {len(df)} properties in zip code {zip_code}")
        
        # Filter by price
        df = df[pd.to_numeric(df['list_price'], errors='coerce') <= max_price]
        logger.info(f"Found {len(df)} properties under ${max_price:,.2f}")
        
        # Convert to list of dictionaries
        properties = df.to_dict('records')
        
        # Clean up the properties
        cleaned_properties = []
        for prop in properties:
            # Parse photo URLs
            photos = []
            if prop.get('primary_photo'):
                photos.append(prop['primary_photo'])
            
            if prop.get('alt_photos'):
                try:
                    if isinstance(prop['alt_photos'], str):
                        alt_photos = [url.strip() for url in prop['alt_photos'].split(',') if url.strip()]
                        photos.extend(alt_photos)
                except Exception as e:
                    logger.warning(f"Error parsing alt_photos: {str(e)}")
            
            # Filter out invalid photo URLs
            photos = [
                url for url in photos 
                if url and isinstance(url, str) and (
                    url.startswith('http://') or 
                    url.startswith('https://')
                )
            ]
            
            # Clean up numeric values
            try:
                list_price = float(prop['list_price']) if prop.get('list_price') else None
                sqft = float(prop['sqft']) if prop.get('sqft') else None
                beds = float(prop['beds']) if prop.get('beds') else None
                baths = float(prop['full_baths']) if prop.get('full_baths') else None
                days_on_market = int(prop['days_on_mls']) if prop.get('days_on_mls') else 0
                
                # Parse coordinates with detailed logging
                try:
                    lat = float(prop['latitude']) if prop.get('latitude') else None
                    lng = float(prop['longitude']) if prop.get('longitude') else None
                    logger.info(f"Parsed coordinates for {prop.get('street')}: lat={lat}, lng={lng}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing coordinates for {prop.get('street')}: {str(e)}")
                    lat = None
                    lng = None
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting numeric values: {str(e)}")
                continue
            
            cleaned_prop = {
                'property_id': prop.get('property_id'),
                'list_price': list_price or 0,
                'sqft': sqft or 0,
                'beds': beds or 0,
                'baths': baths or 0,
                'full_baths': baths or 0,
                'street': prop.get('street', ''),
                'city': prop.get('city', ''),
                'state': prop.get('state', ''),
                'zip_code': prop.get('zip_code', ''),
                'days_on_market': days_on_market or 0,
                'photos': photos or [],
                'property_url': prop.get('property_url', ''),
                'status': prop.get('status', '').upper(),
                'latitude': lat,
                'longitude': lng
            }
            
            # Add property if it has valid coordinate information
            if (cleaned_prop['latitude'] is not None and cleaned_prop['longitude'] is not None and
                -90 <= cleaned_prop['latitude'] <= 90 and -180 <= cleaned_prop['longitude'] <= 180):
                logger.info(f"Adding property: {cleaned_prop['street']} with coordinates: ({cleaned_prop['latitude']}, {cleaned_prop['longitude']})")
                cleaned_properties.append(cleaned_prop)
            else:
                logger.warning(f"Skipping property due to invalid coordinates: {cleaned_prop['street']} - lat: {cleaned_prop['latitude']}, lng: {cleaned_prop['longitude']}")
        
        logger.info(f"Returning {len(cleaned_properties)} cleaned properties")
        return cleaned_properties
        
    except Exception as e:
        logger.error(f"Error in scrape_properties: {str(e)}", exc_info=True)
        return []

if __name__ == "__main__":
    # Test with provided parameters
    results = scrape_properties("32835", 1000000)
    print(f"\nReturned {len(results)} properties") 