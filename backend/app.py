# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
import os
from typing import List, Dict, Optional
from pydantic import BaseModel
from routes import market_analysis_router, scraper_router, price_prediction_router
from routes.market_analysis import get_property, get_comparable_properties

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the root directory path
ROOT_DIR = Path(__file__).parent.parent

app = FastAPI()

# Enable CORS with more specific configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(market_analysis_router)
app.include_router(scraper_router)
app.include_router(price_prediction_router)

# Custom response class with CORS headers
class CORSResponse(JSONResponse):
    def __init__(self, content, status_code=200, headers=None, media_type=None):
        if headers is None:
            headers = {}
        headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        })
        super().__init__(content=content, status_code=status_code, headers=headers, media_type=media_type)

# Pydantic models for request/response
class PropertyPredictionRequest(BaseModel):
    price: float
    sqft: float
    beds: int
    baths: float
    days_on_market: int

# Load the sample data
def load_property_data():
    try:
        data_dir = ROOT_DIR / 'data'
        property_files = list(data_dir.glob('HomeHarvest_*.csv'))
        
        if not property_files:
            raise HTTPException(status_code=404, detail='No property data found')
        
        # Load all property files
        all_properties = []
        for file in property_files:
            try:
                df = pd.read_csv(file)
                all_properties.append(df)
            except Exception as e:
                logger.error(f"Error reading file {file}: {str(e)}")
                continue
        
        if not all_properties:
            raise HTTPException(status_code=404, detail='No valid property data found')
        
        # Combine all data
        combined_df = pd.concat(all_properties, ignore_index=True)
        
        # Remove duplicates based on property_id, keeping the most recent entry
        combined_df = combined_df.sort_values('scrape_timestamp').drop_duplicates(subset=['property_id'], keep='last')
        
        return combined_df
        
    except Exception as e:
        logger.error(f"Error loading property data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to the Home Flip AI API"}

@app.get("/api/test")
async def test():
    return {"message": "API is working!"}

@app.get("/api/properties")
async def get_properties():
    try:
        properties = load_property_data()
        properties_list = properties.to_dict('records')
        
        return {
            'properties': properties_list,
            'count': len(properties_list)
        }
    except Exception as e:
        logger.error(f"Error getting properties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict")
async def predict(request: PropertyPredictionRequest):
    try:
        logger.info(f"Received prediction request with data: {request}")

        # Initialize scoring
        score = 0
        reasons = []

        # Price per sqft analysis
        price_per_sqft = request.price / request.sqft if request.sqft > 0 else 0
        if 100 <= price_per_sqft <= 200:
            score += 30
            reasons.append("Good price per square foot")
        
        # Days on market analysis
        if request.days_on_market > 60:
            score += 20
            reasons.append("Property may be more negotiable due to longer market time")
        
        # Bed/bath ratio analysis
        if 1.5 <= request.beds/request.baths <= 2.5:
            score += 20
            reasons.append("Good bed to bath ratio")
            
        # Size analysis
        if 1000 <= request.sqft <= 3000:
            score += 30
            reasons.append("Optimal property size for flipping")

        # Calculate final prediction
        is_good_flip = score >= 60
        confidence = score

        return {
            'is_good_flip': is_good_flip,
            'confidence': confidence,
            'reasons': reasons
        }

    except ZeroDivisionError:
        logger.error("Division by zero error in prediction")
        return {
            'is_good_flip': False,
            'confidence': 0,
            'reasons': ["Invalid property data"]
        }
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def safe_float(value):
    """Convert value to float safely, handling various formats"""
    if isinstance(value, (int, float)):
        if pd.isna(value) or np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    elif isinstance(value, str):
        try:
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            if not cleaned:
                return None
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    return None

def safe_mean(series):
    """Calculate mean safely, converting NaN to None"""
    try:
        mean_value = series.mean()
        if pd.isna(mean_value) or np.isnan(mean_value) or np.isinf(mean_value):
            return None
        return float(mean_value)
    except Exception:
        return None

def clean_for_json(obj):
    """Recursively clean object for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, (int, float)):
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    return obj

def safe_division(numerator: float, denominator: float, default: float = None) -> Optional[float]:
    """Safely perform division with error handling"""
    try:
        if denominator == 0 or denominator is None:
            return default
        return float(numerator) / float(denominator)
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.warning(f"Error in safe division: {str(e)}")
        return default

@app.get("/api/market-analysis/{property_id}")
async def get_market_analysis(property_id: str):
    """Get market analysis for a property"""
    logger.info(f'Received market analysis request for property ID: {property_id}')
    
    try:
        # Get target property
        target_property = await get_property(property_id)
        if not target_property:
            logger.error(f'Property not found: {property_id}')
            raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
        
        # Get comparable properties
        comparable_properties = await get_comparable_properties(target_property)
        logger.info(f'Found {len(comparable_properties)} comparable properties')
        
        # Calculate market metrics safely
        if comparable_properties:
            try:
                # Extract valid numeric values
                prices = []
                sqft_values = []
                days_on_market = []
                
                for p in comparable_properties:
                    try:
                        if p.get('list_price') is not None:
                            price = float(p['list_price'])
                            if price > 0:
                                prices.append(price)
                    except (ValueError, TypeError):
                        continue
                        
                    try:
                        if p.get('sqft') is not None:
                            sqft = float(p['sqft'])
                            if sqft > 0:
                                sqft_values.append(sqft)
                    except (ValueError, TypeError):
                        continue
                        
                    try:
                        if p.get('days_on_market') is not None:
                            dom = int(p['days_on_market'])
                            if dom >= 0:
                                days_on_market.append(dom)
                    except (ValueError, TypeError):
                        continue
                
                market_metrics = {
                    'avg_price': np.mean(prices) if prices else None,
                    'avg_sqft': np.mean(sqft_values) if sqft_values else None,
                    'avg_days_on_market': np.mean(days_on_market) if days_on_market else None,
                    'avg_price_per_sqft': None
                }
                
                # Calculate average price per sqft safely
                valid_ppsf = []
                for price, sqft in zip(prices, sqft_values):
                    ppsf = safe_division(price, sqft)
                    if ppsf is not None:
                        valid_ppsf.append(ppsf)
                
                if valid_ppsf:
                    market_metrics['avg_price_per_sqft'] = np.mean(valid_ppsf)
                
            except Exception as e:
                logger.error(f"Error calculating market metrics: {str(e)}")
                market_metrics = {
                    'avg_price': None,
                    'avg_sqft': None,
                    'avg_days_on_market': None,
                    'avg_price_per_sqft': None
                }
        else:
            market_metrics = {
                'avg_price': None,
                'avg_sqft': None,
                'avg_days_on_market': None,
                'avg_price_per_sqft': None
            }
        
        # Generate analysis
        analysis = []
        
        # Price analysis
        if market_metrics['avg_price'] and target_property.get('list_price'):
            try:
                price_diff = safe_division(
                    float(target_property['list_price']) - market_metrics['avg_price'],
                    market_metrics['avg_price']
                )
                if price_diff is not None:
                    price_diff *= 100
                    analysis.append({
                        'type': 'price',
                        'confidence': 'high',
                        'message': f'Property is {abs(price_diff):.1f}% {"below" if price_diff < 0 else "above"} market average'
                    })
            except Exception as e:
                logger.error(f"Error in price analysis: {str(e)}")
        
        # Size analysis
        if market_metrics['avg_sqft'] and target_property.get('sqft'):
            try:
                sqft_diff = safe_division(
                    float(target_property['sqft']) - market_metrics['avg_sqft'],
                    market_metrics['avg_sqft']
                )
                if sqft_diff is not None:
                    sqft_diff *= 100
                    analysis.append({
                        'type': 'size',
                        'confidence': 'high',
                        'message': f'Property is {abs(sqft_diff):.1f}% {"larger" if sqft_diff > 0 else "smaller"} than market average'
                    })
            except Exception as e:
                logger.error(f"Error in size analysis: {str(e)}")
        
        # Price per sqft analysis
        if target_property.get('list_price') and target_property.get('sqft'):
            try:
                target_ppsf = safe_division(
                    float(target_property['list_price']),
                    float(target_property['sqft'])
                )
                
                if target_ppsf is not None and market_metrics['avg_price_per_sqft']:
                    ppsf_diff = safe_division(
                        target_ppsf - market_metrics['avg_price_per_sqft'],
                        market_metrics['avg_price_per_sqft']
                    )
                    if ppsf_diff is not None:
                        ppsf_diff *= 100
                        analysis.append({
                            'type': 'value',
                            'confidence': 'high',
                            'message': f'Price per sqft is {abs(ppsf_diff):.1f}% {"below" if ppsf_diff < 0 else "above"} market average'
                        })
            except Exception as e:
                logger.error(f"Error in price per sqft analysis: {str(e)}")
        
        # Days on market analysis
        if target_property.get('days_on_market') is not None:
            try:
                dom = int(target_property['days_on_market'])
                if dom > 45:
                    analysis.append({
                        'type': 'timing',
                        'confidence': 'high',
                        'message': f'Property has been on market for {dom} days, presenting a strong negotiation opportunity'
                    })
                elif dom > 30:
                    analysis.append({
                        'type': 'timing',
                        'confidence': 'medium',
                        'message': f'Property has been on market for {dom} days, which may present a negotiation opportunity'
                    })
            except Exception as e:
                logger.error(f"Error in days on market analysis: {str(e)}")
        
        # Overall investment potential
        if len(analysis) > 0:
            try:
                positive_factors = len([
                    a for a in analysis 
                    if ('below' in a['message'].lower() and 'price' in a['type'].lower()) or
                       ('larger' in a['message'].lower() and 'size' in a['type'].lower()) or
                       ('timing' in a['type'].lower() and a['confidence'] == 'high')
                ])
                
                if positive_factors > 0:
                    confidence = 'high' if positive_factors >= 2 else 'medium'
                    analysis.append({
                        'type': 'overall',
                        'confidence': confidence,
                        'message': f'{"Multiple" if positive_factors >= 2 else "Some"} factors indicate good investment potential'
                    })
            except Exception as e:
                logger.error(f"Error in overall analysis: {str(e)}")
        
        response_data = {
            "market_metrics": clean_for_json(market_metrics),
            "property": clean_for_json(target_property),
            "comparable_properties": clean_for_json(comparable_properties),
            "analysis": clean_for_json(analysis)
        }
        
        return CORSResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error generating market analysis: {str(e)}", exc_info=True)
        return CORSResponse(
            content={"detail": str(e)},
            status_code=500
        )

def calculate_similarity_score(property_data, target_sqft, target_price, target_beds, target_baths):
    """Calculate similarity score between property and target"""
    try:
        # Normalize differences
        sqft_diff = abs(float(property_data['sqft']) - target_sqft) / target_sqft
        price_diff = abs(float(property_data['list_price']) - target_price) / target_price
        
        # Calculate bed/bath differences
        beds_diff = abs(float(property_data['beds']) - target_beds) / max(target_beds, 1)
        baths_diff = abs(float(property_data['baths']) - target_baths) / max(target_baths, 1)
        
        # Weighted score (lower is more similar)
        similarity = (
            sqft_diff * 0.3 +      # Square footage weight
            price_diff * 0.4 +     # Price weight
            beds_diff * 0.15 +     # Beds weight
            baths_diff * 0.15      # Baths weight
        )
        
        return 1 - similarity  # Convert to similarity score (higher is more similar)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0  # Return 0 for invalid comparisons

# Add this at the bottom of the file
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)