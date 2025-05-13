from fastapi import APIRouter, HTTPException
from models.model_trainer import ModelTrainer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
model_trainer = ModelTrainer()

@router.post("/api/train-model")
async def train_model():
    """Train the flip prediction model using latest data"""
    try:
        model_path = model_trainer.train_from_latest_data()
        return {
            "message": "Model trained successfully",
            "model_path": model_path
        }
    except Exception as e:
        logger.error(f"Error training model: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 