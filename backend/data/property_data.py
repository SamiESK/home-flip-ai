import pandas as pd
from pathlib import Path
import logging
from fastapi import HTTPException
from typing import Dict, List

logger = logging.getLogger(__name__)

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
        logger.error(f"Unexpected error searching for property: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while searching for property: {str(e)}"
        )

async def get_all_properties() -> List[Dict]:
    """Get all properties from the latest data file"""
    try:
        # Get the most recent data file
        data_file = get_latest_data_file()
        
        # Read CSV with proper quoting to handle URLs correctly
        df = pd.read_csv(data_file, quoting=1)
        
        # Convert to list of dictionaries and clean up
        properties = []
        for _, row in df.iterrows():
            prop_dict = row.to_dict()
            prop_dict = {k: (None if pd.isna(v) else v) for k, v in prop_dict.items()}
            properties.append(prop_dict)
            
        return properties
        
    except Exception as e:
        logger.error(f"Error getting all properties: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error reading property database: {str(e)}"
        ) 