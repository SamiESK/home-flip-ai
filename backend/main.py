from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import market_analysis, scraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(market_analysis.router)
app.include_router(scraper.router)

@app.get("/")
async def root():
    return {"message": "Home Flip AI API is running"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Home Flip AI API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)