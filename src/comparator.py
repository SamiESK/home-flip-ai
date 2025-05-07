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
    
    if price_diff_percent < -10:
        analysis.append({
            'type': 'price',
            'message': f"Good price point! This property is {abs(price_diff_percent):.1f}% below similar historical properties.",
            'confidence': 'high'
        })
    elif price_diff_percent > 10:
        analysis.append({
            'type': 'price',
            'message': f"Price is {price_diff_percent:.1f}% higher than similar historical properties. Consider negotiating.",
            'confidence': 'medium'
        })
    
    # Square footage analysis
    avg_historical_sqft = np.mean([p['sqft'] for p in similar_properties])
    sqft_diff_percent = ((current_property['sqft'] - avg_historical_sqft) / avg_historical_sqft) * 100
    
    if sqft_diff_percent > 10:
        analysis.append({
            'type': 'size',
            'message': f"Larger than average! This property is {sqft_diff_percent:.1f}% bigger than similar properties.",
            'confidence': 'high'
        })
    
    # Days on market analysis
    if current_property['days_on_market'] > 30:
        analysis.append({
            'type': 'timing',
            'message': "Property has been on market for over 30 days. This could be a negotiation opportunity.",
            'confidence': 'medium'
        })
    
    # Add historical success rate
    successful_flips = sum(1 for p in similar_properties if p.get('is_good_flip', False))
    success_rate = (successful_flips / len(similar_properties)) * 100
    
    analysis.append({
        'type': 'historical',
        'message': f"Similar properties have a {success_rate:.1f}% success rate for flipping.",
        'confidence': 'high' if success_rate > 70 else 'medium'
    })
    
    return analysis