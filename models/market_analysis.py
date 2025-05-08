# models/market_analysis.py
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from geopy.distance import geodesic

class MarketAnalyzer:
    def __init__(self, radius_miles: float = 1.0, months_lookback: int = 3):
        self.radius_miles = radius_miles
        self.months_lookback = months_lookback

    def get_recent_sales(self, target_property: Dict, all_properties: List[Dict]) -> List[Dict]:
        """Get recent sales within radius and time period"""
        target_location = (target_property['latitude'], target_property['longitude'])
        cutoff_date = datetime.now() - timedelta(days=30 * self.months_lookback)
        
        recent_sales = []
        for prop in all_properties:
            # Check if property is within radius
            prop_location = (prop['latitude'], prop['longitude'])
            distance = geodesic(target_location, prop_location).miles
            
            if distance <= self.radius_miles:
                # Check if sale is recent
                sale_date = datetime.strptime(prop['sale_date'], '%Y-%m-%d')
                if sale_date >= cutoff_date:
                    recent_sales.append(prop)
        
        return recent_sales

    def analyze_market_trends(self, properties: List[Dict]) -> Dict:
        """Analyze market trends including price per sqft, days on market, etc."""
        df = pd.DataFrame(properties)
        
        return {
            'avg_price_per_sqft': df['list_price'].mean() / df['sqft'].mean(),
            'avg_days_on_market': df['days_on_mls'].mean(),
            'price_trend': self._calculate_price_trend(df),
            'seasonal_factor': self._calculate_seasonal_factor()
        }

    def _calculate_price_trend(self, df: pd.DataFrame) -> float:
        """Calculate price trend over time"""
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df = df.sort_values('sale_date')
        
        if len(df) < 2:
            return 0
            
        first_price = df['list_price'].iloc[0]
        last_price = df['list_price'].iloc[-1]
        months = (df['sale_date'].iloc[-1] - df['sale_date'].iloc[0]).days / 30
        
        return (last_price - first_price) / (first_price * months) if months > 0 else 0

    def _calculate_seasonal_factor(self) -> float:
        """Calculate seasonal adjustment factor"""
        current_month = datetime.now().month
        # Spring/Summer months (3-8) have higher activity
        if 3 <= current_month <= 8:
            return 1.1  # 10% premium
        return 0.9  # 10% discount