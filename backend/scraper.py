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
        logger.info(f"Starting property search for zip code {zip_code} with max price ${max_price:,.2f}")
        
        # Use HomeHarvest to scrape properties with consistent parameters
        logger.info("Calling HomeHarvest API with parameters:")
        logger.info(f"- location: {zip_code}")
        logger.info(f"- listing_type: for_sale")
        
        try:
            # Get properties from HomeHarvest with consistent parameters
            logger.info(f"Calling HomeHarvest API for zip {zip_code} with max limit 10000")
            properties = scrape_property(
                location=zip_code,
                listing_type="for_sale",
                limit=10000,
                property_type=["single_family", "condos", "townhomes", "multi_family"]
            )
            if isinstance(properties, pd.DataFrame):
                logger.info(f"HomeHarvest returned {len(properties)} properties")
                # Filter out land properties if property_type column exists
                if 'property_type' in properties.columns:
                    properties = properties[~properties['property_type'].str.lower().isin(['land', 'lot', 'vacant land'])]
                    logger.info(f"After filtering out land properties: {len(properties)} properties")
                else:
                    logger.info("No property_type column found in the data, skipping land property filter")
            else:
                logger.warning("HomeHarvest did not return a DataFrame")
            
            if isinstance(properties, pd.DataFrame) and not properties.empty:
                logger.info(f"Initial API call returned {len(properties)} properties")
                
                # Now filter by max price
                properties['list_price'] = pd.to_numeric(properties['list_price'], errors='coerce')
                
                # Log price distribution before filtering
                price_stats = properties['list_price'].describe()
                logger.info(f"Price distribution before filtering:\n{price_stats}")
                
                # Filter by max price
                properties = properties[properties['list_price'] <= max_price]
                logger.info(f"After price filter: {len(properties)} properties")
                
                # Ensure consistent sorting
                if 'list_date' in properties.columns:
                    properties = properties.sort_values('list_date', ascending=False)
                elif 'days_on_market' in properties.columns:
                    properties = properties.sort_values('days_on_market', ascending=True)
                
                # Convert to list of dictionaries
                properties_list = properties.to_dict('records')
                logger.info(f"Converted to {len(properties_list)} property records")
                
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
                        # Try different possible bathroom column names
                        for col in properties.columns:
                            if 'bath' in col.lower():
                                try:
                                    baths = float(prop[col])
                                    if 0 <= baths <= 10:  # Reasonable range check
                                        logger.info(f"Found valid bathroom count {baths} in column {col}")
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        if baths is None:
                            logger.warning(f"No valid bathroom data found for property {prop.get('property_id')}")
                        
                        days_on_market = int(prop['days_on_market']) if prop.get('days_on_market') else 0
                        
                        # Parse coordinates
                        lat = float(prop['latitude']) if prop.get('latitude') else None
                        lng = float(prop['longitude']) if prop.get('longitude') else None
                        
                        # Always use the HomeHarvest property_id if available
                        property_id = prop.get('property_id')
                        if not property_id:
                            # Generate a unique property ID from address components
                            street = prop.get('street', '').replace(' ', '-')
                            city = prop.get('city', '')
                            state = prop.get('state', '')
                            zip_code = prop.get('zip_code', '')
                            property_id = f"{street}_{city}_{state}_{zip_code}"
                        
                        # Ensure property_id is a string
                        property_id = str(property_id)
                        
                        cleaned_prop = {
                            'property_id': property_id,
                            'list_price': list_price or 0,
                            'sqft': sqft or 0,
                            'beds': beds or 0,
                            'baths': baths,  # Don't default to 0, keep as None if not found
                            'full_baths': baths,  # Don't default to 0, keep as None if not found
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
                            logger.info(f"Adding property: {cleaned_prop['street']} with ID: {cleaned_prop['property_id']}")
                            cleaned_properties.append(cleaned_prop)
                        else:
                            logger.warning(f"Skipping property due to invalid coordinates: {cleaned_prop['street']} - lat: {cleaned_prop['latitude']}, lng: {cleaned_prop['longitude']}")
                            
                    except Exception as e:
                        logger.warning(f"Error processing property: {str(e)}")
                        continue
                
                # Save properties to CSV
                if cleaned_properties:
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
                
                logger.info(f"Returning {len(cleaned_properties)} cleaned properties")
                if len(properties) == 10000:
                    logger.warning("Hit the maximum limit of 10,000 properties. Some properties may be missing.")
                return cleaned_properties
            else:
                logger.error("No properties returned from HomeHarvest API")
                if properties is not None:
                    logger.error(f"Response type: {type(properties)}")
                    if isinstance(properties, pd.DataFrame):
                        logger.error(f"DataFrame info: {properties.info()}")
                    else:
                        logger.error(f"Response content: {properties}")
                return []
                
        except Exception as api_error:
            logger.error(f"Error calling HomeHarvest API: {str(api_error)}", exc_info=True)
            return []
        
    except Exception as e:
        logger.error(f"Error in scrape_properties: {str(e)}", exc_info=True)
        return [] 