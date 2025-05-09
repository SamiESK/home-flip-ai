from fastapi import APIRouter, HTTPException
from models.price_prediction import PricePredictor
import pandas as pd
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()
price_predictor = PricePredictor()

@router.get("/api/price-prediction/{property_id}")
async def get_price_prediction(property_id: str):
    """Get price prediction for a property"""
    try:
        # Get property data
        from routes.market_analysis import get_property
        property_data = await get_property(property_id)
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
            
        # Load historical data
        data_dir = Path(__file__).parent.parent.parent / 'data'
        historical_files = list(data_dir.glob('HomeHarvest_*.csv'))
        
        if not historical_files:
            raise HTTPException(status_code=404, detail="No historical data found")
            
        # Load and combine historical data
        historical_data = pd.concat([
            pd.read_csv(f) for f in historical_files
        ])
        
        # Train model if not already trained
        if price_predictor.model is None:
            price_predictor.train_model(historical_data)
            
        # Get price prediction
        prediction = price_predictor.predict_price(property_data)
        
        # Get market trends
        trends = price_predictor.analyze_market_trends(
            historical_data,
            zip_code=property_data.get('zip_code')
        )
        
        return {
            'property': property_data,
            'prediction': prediction,
            'market_trends': trends
        }
        
    except Exception as e:
        logger.error(f"Error in price prediction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/market-trends/{zip_code}")
async def get_market_trends(zip_code: str):
    """Get market trends for a specific zip code"""
    try:
        # Load historical data
        data_dir = Path(__file__).parent.parent.parent / 'data'
        historical_files = list(data_dir.glob('HomeHarvest_*.csv'))
        
        if not historical_files:
            raise HTTPException(status_code=404, detail="No historical data found")
            
        # Load and combine historical data
        historical_data = pd.concat([
            pd.read_csv(f) for f in historical_files
        ])
        
        # Get market trends
        trends = price_predictor.analyze_market_trends(
            historical_data,
            zip_code=zip_code
        )
        
        return trends
        
    except Exception as e:
        logger.error(f"Error in market trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 