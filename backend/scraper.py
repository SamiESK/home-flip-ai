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

def get_nearby_zip_codes(zip_code: str) -> list:
    """Get a list of nearby zip codes for a given zip code."""
    # For now, just return the exact zip code
    # TODO: Implement proper nearby zip code lookup
    return [zip_code]

def scrape_properties(zip_code: str, max_price: float) -> list:
    """
    Scrape properties using HomeHarvest for the given zip code and max price.
    """
    try:
        logger.info(f"\n{'='*80}\nStarting property search for zip code {zip_code} with max price ${max_price:,.2f}\n{'='*80}")
        
        try:
            # Get properties from HomeHarvest with consistent parameters
            logger.info(f"Calling HomeHarvest API for zip {zip_code}")
            properties = scrape_property(
                location=zip_code,
                listing_type="for_sale",
                limit=10000,
                property_type=["single_family", "condos", "townhomes", "multi_family"]
            )
            
            if not isinstance(properties, pd.DataFrame):
                logger.error(f"HomeHarvest returned invalid data type: {type(properties)}")
                return []
                
            if properties.empty:
                logger.error("HomeHarvest returned empty DataFrame")
                return []
                
            # Debug: Print all column names
            logger.info(f"Available columns: {properties.columns.tolist()}")
            
            # Ensure list_price column exists and is numeric
            if 'list_price' not in properties.columns:
                logger.error("No list_price column found in response")
                return []
                
            # Convert price to numeric, replacing any non-numeric values with NaN
            properties['list_price'] = pd.to_numeric(properties['list_price'], errors='coerce')
            
            # Log initial state
            logger.info(f"\nInitial state:")
            logger.info(f"Total properties: {len(properties)}")
            logger.info(f"Price range: ${properties['list_price'].min():,.2f} - ${properties['list_price'].max():,.2f}")
            logger.info(f"Properties with NaN prices: {properties['list_price'].isna().sum()}")
            logger.info(f"Properties with zero prices: {(properties['list_price'] == 0).sum()}")
            
            # Filter by max price
            properties = properties[
                (properties['list_price'].notna()) & 
                (properties['list_price'] > 0) & 
                (properties['list_price'] <= max_price)
            ]
            
            # Log filtered state
            logger.info(f"\nAfter price filtering:")
            logger.info(f"Remaining properties: {len(properties)}")
            if not properties.empty:
                # Sort by price in descending order
                properties = properties.sort_values('list_price', ascending=False)
                logger.info(f"New price range: ${properties['list_price'].min():,.2f} - ${properties['list_price'].max():,.2f}")
                
                # Log some example properties
                logger.info("\nExample properties after filtering (sorted by price):")
                for _, prop in properties.head(3).iterrows():
                    logger.info(f"Price: ${prop['list_price']:,.2f}, Address: {prop.get('street', 'N/A')}")
            else:
                logger.warning("No properties remain after price filtering!")
            
            # Convert to list of dictionaries
            properties_list = properties.to_dict('records')
            
            # Clean up the properties
            cleaned_properties = []
            for prop in properties_list:
                try:
                    # Parse photo URLs
                    photos = []
                    if prop.get('primary_photo'):
                        photos.append(prop['primary_photo'])
                    
                    if prop.get('alt_photos'):
                        if isinstance(prop['alt_photos'], list):
                            photos.extend(prop['alt_photos'])
                        elif isinstance(prop['alt_photos'], str):
                            alt_photos = [url.strip() for url in prop['alt_photos'].split(',') if url.strip()]
                            photos.extend(alt_photos)
                    
                    # Filter out invalid photo URLs
                    photos = [
                        url for url in photos 
                        if url and isinstance(url, str) and (
                            url.startswith('http://') or 
                            url.startswith('https://')
                        )
                    ]
                    
                    # Clean up numeric values
                    list_price = float(prop['list_price']) if prop.get('list_price') else None
                    sqft = float(prop['sqft']) if prop.get('sqft') else None
                    beds = float(prop['beds']) if prop.get('beds') else None
                    
                    # Enhanced bathroom processing
                    baths = None
                    for col in properties.columns:
                        if 'bath' in col.lower():
                            try:
                                baths = float(prop[col])
                                if 0 <= baths <= 10:  # Reasonable range check
                                    break
                            except (ValueError, TypeError):
                                continue
                    
                    days_on_market = int(prop['days_on_market']) if prop.get('days_on_market') else 0
                    
                    # Parse coordinates
                    lat = float(prop['latitude']) if prop.get('latitude') else None
                    lng = float(prop['longitude']) if prop.get('longitude') else None
                    
                    # Always use the HomeHarvest property_id if available
                    property_id = prop.get('property_id')
                    if not property_id:
                        street = prop.get('street', '').replace(' ', '-')
                        city = prop.get('city', '')
                        state = prop.get('state', '')
                        zip_code = prop.get('zip_code', '')
                        property_id = f"{street}_{city}_{state}_{zip_code}"
                    
                    cleaned_prop = {
                        'property_id': str(property_id),
                        'list_price': list_price or 0,
                        'sqft': sqft or 0,
                        'beds': beds or 0,
                        'baths': baths,
                        'full_baths': baths,
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
                        cleaned_properties.append(cleaned_prop)
                        
                except Exception as e:
                    logger.warning(f"Error processing property: {str(e)}")
                    continue
            
            # Log final state
            logger.info(f"\nFinal state:")
            logger.info(f"Total cleaned properties: {len(cleaned_properties)}")
            if cleaned_properties:
                prices = [p['list_price'] for p in cleaned_properties]
                logger.info(f"Final price range: ${min(prices):,.2f} - ${max(prices):,.2f}")
            
            return cleaned_properties
                
        except Exception as api_error:
            logger.error(f"Error calling HomeHarvest API: {str(api_error)}", exc_info=True)
            return []
        
    except Exception as e:
        logger.error(f"Error in scrape_properties: {str(e)}", exc_info=True)
        return [] 