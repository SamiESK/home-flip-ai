import pandas as pd
import numpy as np
from pathlib import Path
import os

def find_similar_properties(current_property):
    """
    Find similar properties from historical data
    """
    try:
        # Load historical data
        ROOT_DIR = Path(__file__).parent.parent
        historical_path = os.path.join(ROOT_DIR, 'data', 'historical_flips.csv')
        historical_df = pd.read_csv(historical_path)
        
        # Convert current property to numeric
        current = {
            'price': float(current_property['price']),
            'sqft': float(current_property['sqft']),
            'beds': int(current_property['beds']),
            'baths': int(current_property['baths']),
            'days_on_market': int(current_property['days_on_market'])
        }
        
        # Calculate similarity scores
        historical_df['similarity_score'] = historical_df.apply(
            lambda row: calculate_similarity(current, row), axis=1
        )
        
        # Get top 3 most similar properties
        similar_properties = historical_df.nlargest(3, 'similarity_score')
        
        return similar_properties.to_dict('records')
        
    except Exception as e:
        print(f"Error finding similar properties: {str(e)}")
        raise

def calculate_similarity(current, historical):
    """
    Calculate similarity score between current and historical property
    """
    # Normalize differences
    price_diff = abs(current['price'] - historical['price']) / current['price']
    sqft_diff = abs(current['sqft'] - historical['sqft']) / current['sqft']
    beds_diff = abs(current['beds'] - historical['beds']) / max(current['beds'], 1)
    baths_diff = abs(current['baths'] - historical['baths']) / max(current['baths'], 1)
    
    # Calculate weighted similarity score (lower is more similar)
    similarity = (
        price_diff * 0.4 +  # Price is most important
        sqft_diff * 0.3 +   # Square footage is second
        beds_diff * 0.15 +  # Beds and baths are less important
        baths_diff * 0.15
    )
    
    return 1 - similarity  # Convert to similarity score (higher is more similar)

def generate_analysis(current_property, similar_properties):
    """
    Generate analysis and justifications for the flip potential
    """
    analysis = []
    
    # Price analysis
    avg_historical_price = np.mean([p['price'] for p in similar_properties])
    price_diff_percent = ((current_property['price'] - avg_historical_price) / avg_historical_price) * 100
    
    if price_diff_percent < -15:
        analysis.append({
            'type': 'price',
            'message': f"Excellent price point! This property is {abs(price_diff_percent):.1f}% below similar historical properties, indicating strong potential for value appreciation.",
            'confidence': 'high'
        })
    elif price_diff_percent < -10:
        analysis.append({
            'type': 'price',
            'message': f"Good price point! This property is {abs(price_diff_percent):.1f}% below similar historical properties.",
            'confidence': 'high'
        })
    elif price_diff_percent > 10:
        analysis.append({
            'type': 'price',
            'message': f"Price is {price_diff_percent:.1f}% higher than similar historical properties. Consider negotiating or looking for properties with better value.",
            'confidence': 'medium'
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
    elif sqft_diff_percent > 10:
        analysis.append({
            'type': 'size',
            'message': f"Larger than average! This property is {sqft_diff_percent:.1f}% bigger than similar properties.",
            'confidence': 'high'
        })
    
    # Price per square foot analysis
    current_ppsf = current_property['price'] / current_property['sqft']
    avg_historical_ppsf = np.mean([p['price'] / p['sqft'] for p in similar_properties])
    ppsf_diff_percent = ((current_ppsf - avg_historical_ppsf) / avg_historical_ppsf) * 100
    
    if ppsf_diff_percent < -10:
        analysis.append({
            'type': 'value',
            'message': f"Excellent value! Price per square foot is {abs(ppsf_diff_percent):.1f}% below market average, indicating strong potential for appreciation.",
            'confidence': 'high'
        })
    
    # Days on market analysis
    if current_property['days_on_market'] > 45:
        analysis.append({
            'type': 'timing',
            'message': "Property has been on market for over 45 days. This presents a strong negotiation opportunity and potential for a below-market purchase.",
            'confidence': 'high'
        })
    elif current_property['days_on_market'] > 30:
        analysis.append({
            'type': 'timing',
            'message': "Property has been on market for over 30 days. This could be a negotiation opportunity.",
            'confidence': 'medium'
        })
    
    # Historical success analysis
    successful_flips = sum(1 for p in similar_properties if p.get('is_good_flip', False))
    success_rate = (successful_flips / len(similar_properties)) * 100
    
    if success_rate > 80:
        analysis.append({
            'type': 'historical',
            'message': f"Excellent historical performance! Similar properties have a {success_rate:.1f}% success rate for flipping, indicating strong market conditions.",
            'confidence': 'high'
        })
    elif success_rate > 70:
        analysis.append({
            'type': 'historical',
            'message': f"Good historical performance! Similar properties have a {success_rate:.1f}% success rate for flipping.",
            'confidence': 'high'
        })
    else:
        analysis.append({
            'type': 'historical',
            'message': f"Similar properties have a {success_rate:.1f}% success rate for flipping. Consider looking for properties in more favorable market conditions.",
            'confidence': 'medium'
        })
    
    # Market trend analysis
    price_trends = [p.get('price_trend', 0) for p in similar_properties]
    avg_price_trend = np.mean(price_trends)
    
    if avg_price_trend > 0.05:  # 5% monthly growth
        analysis.append({
            'type': 'trend',
            'message': f"Strong market growth! Similar properties are appreciating at {avg_price_trend*100:.1f}% per month, indicating favorable market conditions.",
            'confidence': 'high'
        })
    elif avg_price_trend > 0:
        analysis.append({
            'type': 'trend',
            'message': f"Positive market trend! Similar properties are appreciating at {avg_price_trend*100:.1f}% per month.",
            'confidence': 'medium'
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
    else:
        analysis.append({
            'type': 'overall',
            'message': "Limited flip potential. Consider looking for properties with more favorable conditions.",
            'confidence': 'medium'
        })
    
    return analysis