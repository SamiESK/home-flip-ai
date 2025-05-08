# backend/routes/market_analysis.py
from fastapi import APIRouter, HTTPException
from models.market_analysis import MarketAnalyzer
from typing import List, Dict

router = APIRouter()
market_analyzer = MarketAnalyzer()

@router.get("/api/market-analysis/{property_id}")
async def get_market_analysis(property_id: str):
    try:
        # Get target property
        target_property = await get_property(property_id)
        
        # Get all properties for comparison
        all_properties = await get_all_properties()
        
        # Get recent sales
        recent_sales = market_analyzer.get_recent_sales(target_property, all_properties)
        
        # Analyze market trends
        market_trends = market_analyzer.analyze_market_trends(recent_sales)
        
        return {
            "recent_sales": recent_sales,
            "market_trends": market_trends,
            "comparable_properties": market_analyzer.find_comparables(target_property, recent_sales)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))