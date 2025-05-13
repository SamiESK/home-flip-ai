from fastapi import APIRouter, HTTPException
from models.flip_prediction import FlipPredictor
import logging
from routes.market_analysis import get_property

logger = logging.getLogger(__name__)
router = APIRouter()
flip_predictor = FlipPredictor()

@router.get("/api/flip-prediction/{property_id}")
async def get_flip_prediction(property_id: str):
    """Get flip prediction for a property"""
    try:
        # Get property data
        property_data = await get_property(property_id)
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
            
        # Get flip prediction
        is_good_flip, confidence = flip_predictor.predict(property_data)
        
        return {
            'property': property_data,
            'prediction': {
                'is_good_flip': is_good_flip,
                'confidence': confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Error in flip prediction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 