import pandas as pd
import numpy as np
from pathlib import Path
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class PropertyComparator:
    def __init__(self):
        self.ROOT_DIR = Path(__file__).parent.parent.parent
        
    def find_similar_properties(self, current_property: Dict, all_properties: List[Dict], n: int = 3) -> List[Dict]:
        """Find similar properties from the dataset"""
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(all_properties)
            
            # Calculate similarity scores
            df['similarity_score'] = df.apply(
                lambda row: self._calculate_similarity(current_property, row), axis=1
            )
            
            # Get top N most similar properties
            similar_properties = df.nlargest(n, 'similarity_score')
            
            return similar_properties.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error finding similar properties: {str(e)}")
            raise
            
    def _calculate_similarity(self, current: Dict, historical: pd.Series) -> float:
        """Calculate similarity score between current and historical property"""
        try:
            # Normalize differences
            price_diff = abs(float(current['list_price']) - float(historical['list_price'])) / float(current['list_price'])
            sqft_diff = abs(float(current['sqft']) - float(historical['sqft'])) / float(current['sqft'])
            beds_diff = abs(float(current['beds']) - float(historical['beds'])) / max(float(current['beds']), 1)
            baths_diff = abs(float(current['baths']) - float(historical['baths'])) / max(float(current['baths']), 1)
            
            # Calculate weighted similarity score (lower is more similar)
            similarity = (
                price_diff * 0.4 +  # Price is most important
                sqft_diff * 0.3 +   # Square footage is second
                beds_diff * 0.15 +  # Beds and baths are less important
                baths_diff * 0.15
            )
            
            return 1 - similarity  # Convert to similarity score (higher is more similar)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0
            
    def generate_analysis(self, current_property: Dict, similar_properties: List[Dict]) -> List[Dict]:
        """Generate analysis and justifications for the flip potential"""
        try:
            analysis = []
            
            # Price analysis
            avg_historical_price = np.mean([p['list_price'] for p in similar_properties])
            price_diff_percent = ((current_property['list_price'] - avg_historical_price) / avg_historical_price) * 100
            
            if price_diff_percent < -15:
                analysis.append({
                    'type': 'price',
                    'message': f"Excellent price point! This property is {abs(price_diff_percent):.1f}% below similar properties, indicating strong potential for value appreciation.",
                    'confidence': 'high'
                })
            elif price_diff_percent < -10:
                analysis.append({
                    'type': 'price',
                    'message': f"Good price point! This property is {abs(price_diff_percent):.1f}% below similar properties.",
                    'confidence': 'high'
                })
            
            # Square footage analysis
            avg_historical_sqft = np.mean([p['sqft'] for p in similar_properties])
            sqft_diff_percent = ((current_property['sqft'] - avg_historical_sqft) / avg_historical_sqft) * 100
            
            if sqft_diff_percent > 15:
                analysis.append({
                    'type': 'size',
                    'message': f"Significantly larger than average! This property is {sqft_diff_percent:.1f}% bigger than similar properties, offering more potential for value-add improvements.",
                    'confidence': 'high'
                })
            
            # Price per square foot analysis
            current_ppsf = current_property['list_price'] / current_property['sqft']
            avg_historical_ppsf = np.mean([p['list_price'] / p['sqft'] for p in similar_properties])
            ppsf_diff_percent = ((current_ppsf - avg_historical_ppsf) / avg_historical_ppsf) * 100
            
            if ppsf_diff_percent < -10:
                analysis.append({
                    'type': 'value',
                    'message': f"Excellent value! Price per square foot is {abs(ppsf_diff_percent):.1f}% below market average, indicating strong potential for appreciation.",
                    'confidence': 'high'
                })
            
            # Days on market analysis
            if current_property.get('days_on_market', 0) > 45:
                analysis.append({
                    'type': 'timing',
                    'message': "Property has been on market for over 45 days. This presents a strong negotiation opportunity and potential for a below-market purchase.",
                    'confidence': 'high'
                })
            
            # Overall recommendation
            positive_factors = sum(1 for a in analysis if a['confidence'] == 'high')
            total_factors = len(analysis)
            
            if positive_factors >= total_factors * 0.7:  # 70% or more positive factors
                analysis.append({
                    'type': 'overall',
                    'message': "Strong flip potential! Multiple positive factors indicate this property could be a good investment opportunity.",
                    'confidence': 'high'
                })
            elif positive_factors >= total_factors * 0.5:  # 50% or more positive factors
                analysis.append({
                    'type': 'overall',
                    'message': "Moderate flip potential. Consider this property if other factors align with your investment strategy.",
                    'confidence': 'medium'
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            raise 