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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
market_analyzer = MarketAnalyzer()

__all__ = ['router', 'get_comparable_properties']

def get_latest_data_file() -> Path:
    """Get the path to the most recent HomeHarvest data file"""
    try:
        # Get absolute path to project root
        current_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = current_dir / 'data'
        
        logger.info(f"Looking for data in: {data_dir}")
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found at {data_dir}")
            
        # Get all HomeHarvest CSV files
        files = list(data_dir.glob('HomeHarvest_*.csv'))
        if not files:
            raise FileNotFoundError(f"No HomeHarvest data files found in {data_dir}")
            
        # Sort by modification time and get the most recent
        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Using data file: {latest_file}")
        return latest_file
        
    except Exception as e:
        logger.error(f"Error finding latest data file: {str(e)}")
        raise

async def get_property(property_id: str) -> Dict:
    """Get property details from database"""
    try:
        logger.info(f"\n{'='*80}\nSearching for property: {property_id}\n{'='*80}")
        
        try:
            # Get the most recent data file
            data_file = get_latest_data_file()
            logger.info(f"Using data file: {data_file}")
            
            # Read CSV with proper quoting to handle URLs correctly
            properties = pd.read_csv(data_file, quoting=1)  # QUOTE_ALL
            logger.info(f"Successfully loaded CSV with {len(properties)} properties")
            
        except Exception as e:
            logger.error(f"Error reading data file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error reading property database: {str(e)}"
            )
            
        if properties.empty:
            logger.error("Property database is empty")
            raise HTTPException(
                status_code=404,
                detail="No properties found in the database."
            )
            
        # First try numeric ID match
        try:
            property_match = properties[properties['property_id'].astype(str) == str(property_id)]
            if not property_match.empty:
                logger.info("Found property by numeric ID")
                property_dict = property_match.iloc[0].to_dict()
                property_dict = {k: (None if pd.isna(v) else v) for k, v in property_dict.items()}
                return property_dict
        except Exception as e:
            logger.warning(f"Error in numeric ID search: {str(e)}")
            
        # Try MLS number match if property_id looks like an MLS number
        if property_id.isdigit() and len(property_id) >= 8:
            try:
                property_match = properties[properties['mls_number'].astype(str) == str(property_id)]
                if not property_match.empty:
                    logger.info("Found property by MLS number")
                    property_dict = property_match.iloc[0].to_dict()
                    property_dict = {k: (None if pd.isna(v) else v) for k, v in property_dict.items()}
                    return property_dict
            except Exception as e:
                logger.warning(f"Error in MLS number search: {str(e)}")
            
        # If no match, try parsing address-based ID
        try:
            # Split on underscores first
            parts = property_id.split('_')
            if len(parts) >= 4:
                # The first part contains the street address (may contain hyphens)
                street = parts[0]
                city = parts[1]
                state = parts[2]
                # The zip code might have an MLS number after it
                zip_code = parts[3].split('_')[0]  # Take just the zip code part
                
                logger.info(f"\nParsed address components:")
                logger.info(f"Street: {street}")
                logger.info(f"City: {city}")
                logger.info(f"State: {state}")
                logger.info(f"Zip: {zip_code}")
                
                # Try exact match first (with hyphens replaced by spaces)
                property_match = properties[
                    (properties['street'].str.lower() == street.replace('-', ' ').lower()) &
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
                street_search = street.replace('-', ' ').lower()
                
                # Remove unit/apt numbers for better matching
                street_parts = street_search.split(' ')
                street_search = ' '.join(part for part in street_parts 
                                       if not (part.startswith('#') or 
                                             part.lower() in ['unit', 'apt', 'apartment'] or 
                                             part.isdigit()))
                
                # Try partial match on the street name
                property_match = properties[
                    (properties['street'].str.lower().str.contains(street_search, na=False)) &
                    (properties['city'].str.lower() == city.lower()) &
                    (properties['state'].str.lower() == state.lower()) &
                    (properties['zip_code'].astype(str) == str(zip_code))
                ]
                
                if not property_match.empty:
                    logger.info("Found property by fuzzy address match")
                    property_dict = property_match.iloc[0].to_dict()
                    property_dict = {k: (None if pd.isna(v) else v) for k, v in property_dict.items()}
                    return property_dict
        except Exception as e:
            logger.warning(f"Error in address-based search: {str(e)}")
            
        # If we get here, we couldn't find the property
        logger.error(f"Property not found: {property_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Property {property_id} not found. Please check the property ID and try again."
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
        logger.info(f"CSV columns: {df.columns.tolist()}")
        
        # Map column names to our expected format
        column_mapping = {
            'list_price': 'list_price',
            'sqft': 'sqft',
            'beds': 'beds',
            'full_baths': 'baths',
            'days_on_mls': 'days_on_market',
            'street': 'street',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'property_id': 'property_id',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'primary_photo': 'primary_photo',
            'alt_photos': 'alt_photos',
            'property_url': 'property_url',
            'status': 'status',
            'sold_price': 'sold_price'
        }
        
        # Rename columns according to mapping
        df = df.rename(columns={v: k for k, v in column_mapping.items() if v in df.columns})
        logger.info(f"Columns after mapping: {df.columns.tolist()}")
        
        # Include both PENDING and ACTIVE properties
        df = df[df['status'].str.upper().isin(['ACTIVE', 'PENDING'])]
        logger.info(f"Found {len(df)} ACTIVE/PENDING properties")
        
        # Convert numeric columns
        numeric_columns = ['list_price', 'sqft', 'beds', 'baths', 'days_on_market', 'sold_price']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                logger.info(f"Converted {col} to numeric. Sample values: {df[col].head()}")
        
        # Filter out properties with missing essential data
        before_count = len(df)
        df = df.dropna(subset=['list_price', 'sqft', 'beds'])
        after_count = len(df)
        logger.info(f"Filtered out {before_count - after_count} properties with missing data")
        
        # Filter properties in same city and similar price range
        if target_property.get('city'):
            df = df[df['city'].str.lower() == target_property['city'].lower()]
            logger.info(f"Found {len(df)} properties in {target_property['city']}")
        
        target_price = float(target_property.get('list_price', 0))
        if target_price > 0:
            price_range = (target_price * 0.7, target_price * 1.3)  # ±30% price range
            # Use sold_price for SOLD properties, list_price for PENDING
            df['comparison_price'] = df.apply(
                lambda x: float(x['sold_price']) if pd.notna(x['sold_price']) else float(x['list_price']),
                axis=1
            )
            df = df[
                (df['comparison_price'] >= price_range[0]) & 
                (df['comparison_price'] <= price_range[1])
            ]
            logger.info(f"Found {len(df)} properties in price range {price_range}")
        
        # Exclude the target property from comparables
        if 'property_id' in df.columns and 'property_id' in target_property:
            df = df[df['property_id'].astype(str) != str(target_property['property_id'])]
            logger.info(f"Excluded target property, {len(df)} properties remaining")
        
        # Calculate similarity scores
        target_sqft = float(target_property.get('sqft', 0))
        target_price = float(target_property.get('list_price', 0))
        target_beds = float(target_property.get('beds', 0))
        target_baths = float(target_property.get('full_baths', 1.0))
        
        if target_sqft == 0 or target_price == 0:
            logger.warning("Target property missing essential data (sqft or price)")
            return []
            
        logger.info(f"Target property metrics:")
        logger.info(f"- Price: ${target_price:,.2f}")
        logger.info(f"- Sqft: {target_sqft:,.0f}")
        logger.info(f"- Beds: {target_beds}")
        logger.info(f"- Baths: {target_baths}")
        
        # Calculate similarity scores for each property
        df['similarity_score'] = df.apply(
            lambda row: calculate_similarity_score(
                row,
                target_sqft,
                target_price,
                target_beds,
                target_baths
            ),
            axis=1
        )
        
        # Get top 10 most similar properties
        comparable_properties = df.nlargest(10, 'similarity_score').to_dict('records')
        logger.info(f"Found {len(comparable_properties)} comparable properties")
        
        # Clean up the comparable properties
        cleaned_comparables = []
        for prop in comparable_properties:
            # Parse photo URLs
            photos = []
            if prop.get('primary_photo'):
                photos.append(prop['primary_photo'])
            
            if prop.get('alt_photos'):
                try:
                    # Handle comma-separated URLs
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
            
            # Use sold_price if available, otherwise list_price
            final_price = float(prop['sold_price']) if pd.notna(prop.get('sold_price')) else float(prop['list_price'])
            
            cleaned_prop = {
                'property_id': prop.get('property_id'),
                'list_price': final_price,  # Use the final price (sold or list)
                'sqft': float(prop['sqft']) if pd.notna(prop.get('sqft')) else None,
                'beds': float(prop['beds']) if pd.notna(prop.get('beds')) else None,
                'baths': float(prop['baths']) if pd.notna(prop.get('baths')) else None,
                'street': prop.get('street'),
                'city': prop.get('city'),
                'state': prop.get('state'),
                'zip_code': prop.get('zip_code'),
                'days_on_market': int(prop['days_on_market']) if pd.notna(prop.get('days_on_market')) else 0,
                'similarity_score': float(prop['similarity_score']) if pd.notna(prop.get('similarity_score')) else 0,
                'latitude': float(prop['latitude']) if pd.notna(prop.get('latitude')) else None,
                'longitude': float(prop['longitude']) if pd.notna(prop.get('longitude')) else None,
                'photos': photos,
                'property_url': prop.get('property_url'),
                'status': prop.get('status', '').upper(),
                'sold_price': float(prop['sold_price']) if pd.notna(prop.get('sold_price')) else None
            }
            cleaned_comparables.append(cleaned_prop)
            logger.info(f"Comparable property: {json.dumps(cleaned_prop, indent=2)}")
        
        return cleaned_comparables
        
    except Exception as e:
        logger.error(f"Error generating comparable properties: {str(e)}", exc_info=True)
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
    logger.info(f'Received market analysis request for property ID: {property_id}')
    
    try:
        # Get target property
        logger.info("Attempting to get property details...")
        target_property = await get_property(property_id)
        if not target_property:
            logger.error(f'Property not found: {property_id}')
            raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
        logger.info(f"Found property: {target_property.get('street', 'Unknown Address')}")
        
        # Get comparable properties
        logger.info("Fetching comparable properties...")
        comparable_properties = await get_comparable_properties(target_property)
        logger.info(f'Found {len(comparable_properties)} comparable properties')
        
        # Generate analysis using the standardized analyzer
        logger.info("Generating market analysis...")
        try:
            analysis_result = market_analyzer.generate_analysis(target_property, comparable_properties)
            logger.info('Generated property analysis')
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error generating analysis: {str(e)}"
            )
        
        return {
            'property': target_property,
            'analysis': analysis_result['analysis'],
            'market_metrics': analysis_result['market_metrics'],
            'comparable_properties': comparable_properties
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error in market analysis: {str(e)}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))