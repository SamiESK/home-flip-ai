from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from scraper import scrape_properties

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(
    prefix="/api",
    tags=["scraper"]
)

class ScrapeRequest(BaseModel):
    zipCode: str
    maxPrice: float

@router.post("/scrape")
async def run_scraper(request: ScrapeRequest):
    try:
        logger.info(f"Running scraper with zip_code: {request.zipCode}, max_price: {request.maxPrice}")

        properties = scrape_properties(zip_code=request.zipCode, max_price=request.maxPrice)
        
        # Ensure properties is a list
        if not isinstance(properties, list):
            properties = []
            
        return {
            'message': 'Scraping completed successfully',
            'properties': properties,
            'properties_count': len(properties)
        }

    except Exception as e:
        logger.error(f"Scraping error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f'Scraping failed: {str(e)}') 