# backend/routes/market_analysis.py
from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.market_analysis import MarketAnalyzer
from typing import List, Dict
import logging
import pandas as pd
from pathlib import Path
import json
import traceback
import glob
import os
from models.property_comparator import PropertyComparator
from data.property_data import get_property, get_all_properties

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
market_analyzer = MarketAnalyzer()
property_comparator = PropertyComparator()

__all__ = ['router', 'get_comparable_properties']

def get_latest_data_file() -> Path:
    """Get the path to the most recent HomeHarvest data file"""
    try:
        # Get absolute path to project root
        current_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = current_dir / 'data'
        
        logger.info(f"Looking for data in: {data_dir}")
        
        if not data_dir.exists():
            logger.error(f"Data directory not found at {data_dir}")
            raise FileNotFoundError(f"Data directory not found. Please run a property search first.")
            
        # Get all HomeHarvest CSV files
        files = list(data_dir.glob('HomeHarvest_*.csv'))
        if not files:
            logger.error(f"No HomeHarvest data files found in {data_dir}")
            raise FileNotFoundError(f"No property data found. Please run a property search first.")
            
        # Sort by modification time and get the most recent
        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Using data file: {latest_file}")
        return latest_file
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finding latest data file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error accessing property database: {str(e)}"
        )

async def get_property(property_id: str) -> Dict:
    """Get property details from database"""
    try:
        logger.info(f"\n{'='*80}\nSearching for property: {property_id}\n{'='*80}")
        
        try:
            # Get the most recent data file
            data_file = get_latest_data_file()
            logger.info(f"Using data file: {data_file}")
            
            # Read CSV with proper quoting to handle URLs correctly
            try:
                properties = pd.read_csv(data_file, quoting=1)  # QUOTE_ALL
                logger.info(f"Successfully loaded CSV with {len(properties)} properties")
            except Exception as e:
                logger.error(f"Error reading CSV file: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error reading property data file: {str(e)}"
                )
            
            if properties.empty:
                logger.error("Property database is empty")
                raise HTTPException(
                    status_code=404,
                    detail="No properties found in the database. Please run a property search first."
                )
            
            # Convert property_id column to string
            properties['property_id'] = properties['property_id'].astype(str)
            property_id = str(property_id)
            
            # First try exact match
            property_match = properties[properties['property_id'] == property_id]
            if not property_match.empty:
                logger.info(f"Found property by exact ID match: {property_id}")
                property_dict = property_match.iloc[0].to_dict()
                property_dict = {k: (None if pd.isna(v) else v) for k, v in property_dict.items()}
                return property_dict
            
            # If no exact match, try to find by address components
            if '_' in property_id:
                parts = property_id.split('_')
                if len(parts) >= 4:
                    street = parts[0].replace('-', ' ')
                    city = parts[1]
                    state = parts[2]
                    zip_code = parts[3]
                    
                    logger.info(f"Searching by address components:")
                    logger.info(f"Street: {street}")
                    logger.info(f"City: {city}")
                    logger.info(f"State: {state}")
                    logger.info(f"Zip: {zip_code}")
                    
                    # Try exact match
                    property_match = properties[
                        (properties['street'].str.lower() == street.lower()) &
                        (properties['city'].str.lower() == city.lower()) &
                        (properties['state'].str.lower() == state.lower()) &
                        (properties['zip_code'].astype(str) == str(zip_code))
                    ]
                    
                    if not property_match.empty:
                        logger.info("Found property by exact address match")
                        property_dict = property_match.iloc[0].to_dict()
                        property_dict = {k: (None if pd.isna(v) else v) for k, v in property_dict.items()}
                        return property_dict
                        
                    # Try fuzzy match on street name
                    street_search = ' '.join(part for part in street.split() 
                                           if not (part.startswith('#') or 
                                                 part.lower() in ['unit', 'apt', 'apartment'] or 
                                                 part.isdigit()))
                    
                    property_match = properties[
                        (properties['street'].str.lower().str.contains(street_search.lower(), na=False)) &
                        (properties['city'].str.lower() == city.lower()) &
                        (properties['state'].str.lower() == state.lower()) &
                        (properties['zip_code'].astype(str) == str(zip_code))
                    ]
                    
                    if not property_match.empty:
                        logger.info("Found property by fuzzy address match")
                        property_dict = property_match.iloc[0].to_dict()
                        property_dict = {k: (None if pd.isna(v) else v) for k, v in property_dict.items()}
                        return property_dict
            
            # If we get here, we couldn't find the property
            logger.error(f"Property not found: {property_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Property {property_id} not found. Please check the property ID and try again."
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reading data file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error reading property database: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching for property: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while searching for property: {str(e)}"
        )

async def get_comparable_properties(target_property: Dict) -> List[Dict]:
    """Get comparable properties for analysis"""
    try:
        logger.info(f"\n{'='*80}\nFetching comparable properties for property:")
        logger.info(f"Target property: {json.dumps(target_property, indent=2)}")
        
        # Get target property's zip code
        target_zip = target_property.get('zip_code')
        if not target_zip:
            logger.error("Target property missing zip code")
            return []
            
        logger.info(f"Looking for comparables in zip code: {target_zip}")
        
        # Load property data
        data_dir = Path(__file__).parent.parent.parent / 'data'
        logger.info(f"Looking for data in: {data_dir}")
        
        property_files = list(data_dir.glob('HomeHarvest_*.csv'))
        if not property_files:
            logger.error("No property data files found")
            return []
            
        latest_file = max(property_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Using data file: {latest_file}")
        
        # Read CSV with proper quoting to handle URLs correctly
        df = pd.read_csv(latest_file, quoting=1)
        logger.info(f"Loaded {len(df)} properties for comparables search")
        
        # Log unique status values and their counts
        status_counts = df['status'].value_counts()
        logger.info(f"Status distribution in data:\n{status_counts}")
        
        # Filter by zip code first
        df = df[df['zip_code'].astype(str) == str(target_zip)]
        logger.info(f"Found {len(df)} properties in zip code {target_zip}")
        
        # Log status distribution after zip code filter
        status_counts_zip = df['status'].value_counts()
        logger.info(f"Status distribution in zip code {target_zip}:\n{status_counts_zip}")
        
        # Filter by status (only sold properties)
        # Include more variations of sold status
        sold_statuses = ['SOLD', 'CLOSED', 'SOLD/CLOSED', 'SOLD CLOSED', 'CLOSED/SOLD', 'SOLD PENDING', 'PENDING SOLD']
        df = df[df['status'].str.upper().isin(sold_statuses)]
        logger.info(f"Found {len(df)} sold properties in zip code {target_zip}")
        
        if df.empty:
            logger.warning(f"No sold properties found in zip code {target_zip}")
            return []
            
        # Map column names to our expected format
        column_mapping = {
            'list_price': 'list_price',
            'sqft': 'sqft',
            'beds': 'beds',
            'baths': 'baths',
            'street': 'street',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'days_on_market': 'days_on_market',
            'primary_photo': 'primary_photo',
            'alt_photos': 'alt_photos',
            'property_url': 'property_url',
            'status': 'status',
            'latitude': 'latitude',
            'longitude': 'longitude'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
                
        # Convert to list of dictionaries
        properties = df.to_dict('records')
        
        # Clean up the properties
        cleaned_properties = []
        for prop in properties:
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
                baths = float(prop['baths']) if prop.get('baths') else None
                days_on_market = int(prop['days_on_market']) if prop.get('days_on_market') else 0
                
                # Parse coordinates
                lat = float(prop['latitude']) if prop.get('latitude') else None
                lng = float(prop['longitude']) if prop.get('longitude') else None
                
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
                    cleaned_properties.append(cleaned_prop)
                    
            except Exception as e:
                logger.warning(f"Error processing property: {str(e)}")
                continue
                
        logger.info(f"Returning {len(cleaned_properties)} cleaned comparable properties")
        return cleaned_properties
        
    except Exception as e:
        logger.error(f"Error getting comparable properties: {str(e)}", exc_info=True)
        return []

def calculate_similarity_score(property_data, target_sqft, target_price, target_beds, target_baths):
    """Calculate similarity score between property and target"""
    try:
        # Extract and validate property data
        prop_sqft = float(property_data.get('sqft', 0))
        prop_price = float(property_data.get('list_price', 0))
        prop_beds = float(property_data.get('beds', 0))
        prop_baths = float(property_data.get('baths', 0))  # Using mapped baths column
        
        # Log property comparison
        logger.debug(f"\nComparing properties:")
        logger.debug(f"Target: ${target_price:,.2f}, {target_sqft} sqft, {target_beds} beds, {target_baths} baths")
        logger.debug(f"Comp: ${prop_price:,.2f}, {prop_sqft} sqft, {prop_beds} beds, {prop_baths} baths")
        
        # Check for valid values
        if prop_sqft <= 0 or prop_price <= 0 or target_sqft <= 0 or target_price <= 0:
            logger.debug("Invalid property values, returning 0 score")
            return 0
            
        # Calculate differences with safety checks
        sqft_diff = abs(prop_sqft - target_sqft) / max(target_sqft, 1)
        price_diff = abs(prop_price - target_price) / max(target_price, 1)
        beds_diff = abs(prop_beds - target_beds) / max(target_beds, 1)
        baths_diff = abs(prop_baths - target_baths) / max(target_baths, 1)
        
        # Log differences
        logger.debug(f"Differences - Sqft: {sqft_diff:.2f}, Price: {price_diff:.2f}, Beds: {beds_diff:.2f}, Baths: {baths_diff:.2f}")
        
        # Calculate weighted score (lower is more similar)
        weights = {
            'sqft': 0.3,
            'price': 0.4,
            'beds': 0.15,
            'baths': 0.15
        }
        
        similarity = (
            sqft_diff * weights['sqft'] +
            price_diff * weights['price'] +
            beds_diff * weights['beds'] +
            baths_diff * weights['baths']
        )
        
        # Convert to similarity score (higher is more similar)
        score = max(0, min(1, 1 - similarity))
        logger.debug(f"Final similarity score: {score:.3f}")
        
        return score
        
    except (ValueError, TypeError, ZeroDivisionError) as e:
        logger.warning(f"Error calculating similarity score: {str(e)}")
        return 0

@router.get("/api/market-analysis/{property_id}")
async def get_market_analysis(property_id: str):
    """Get market analysis for a property"""
    try:
        # Get target property
        target_property = await get_property(property_id)
        if not target_property:
            raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
        
        # Get all properties for comparison
        all_properties = await get_all_properties()
        
        # Find similar properties
        similar_properties = property_comparator.find_similar_properties(target_property, all_properties)
        
        # Generate analysis
        analysis = property_comparator.generate_analysis(target_property, similar_properties)
        
        return {
            "property": target_property,
            "similar_properties": similar_properties,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error in market analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))