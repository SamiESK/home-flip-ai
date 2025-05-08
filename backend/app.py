# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import os
import sys

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Get the root directory path
ROOT_DIR = Path(__file__).parent.parent

# Add the root directory to Python path
sys.path.append(str(ROOT_DIR))

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'Backend is working!'})

@app.route('/api/properties', methods=['GET'])
def get_properties():
    try:
        # Get the most recent property data file
        data_dir = ROOT_DIR / 'data'
        property_files = list(data_dir.glob('HomeHarvest_*.csv'))
        
        if not property_files:
            return jsonify({'error': 'No property data found'}), 404
            
        latest_file = max(property_files, key=lambda x: x.stat().st_mtime)
        
        # Read the CSV file
        properties = pd.read_csv(latest_file)
        
        # Convert to list of dictionaries
        properties_list = properties.to_dict('records')
        
        return jsonify({
            'properties': properties_list,
            'count': len(properties_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting properties: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def run_scraper():
    try:
        logger.info("Received scrape request")
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.json
        zip_code = data.get('zipCode')
        max_price = data.get('maxPrice')

        if not zip_code or not max_price:
            return jsonify({'error': 'Zip code and max price are required'}), 400

        logger.info(f"Running scraper with zip_code: {zip_code}, max_price: {max_price}")

        # Import scraper from the src directory
        from src.scraper import scrape_properties
        properties = scrape_properties(zip_code=zip_code, max_price=max_price)
        
        # Ensure properties is a list
        if not isinstance(properties, list):
            properties = []
            
        return jsonify({
            'message': 'Scraping completed successfully',
            'properties': properties,  # Send the properties array
            'properties_count': len(properties)
        })

    except Exception as e:
        logger.error(f"Scraping error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Scraping failed: {str(e)}'}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.json
        logger.info(f"Received prediction request with data: {data}")  # Add logging

        # Convert values to appropriate types
        price = float(data.get('price', 0))
        sqft = float(data.get('sqft', 0))
        beds = int(data.get('beds', 0))
        baths = float(data.get('baths', 0))
        days_on_market = int(data.get('days_on_market', 0))

        # Simple prediction logic (we can make this more sophisticated later)
        # For now, let's use some basic rules
        score = 0
        reasons = []

        # Price per sqft analysis
        price_per_sqft = price / sqft if sqft > 0 else 0
        if 100 <= price_per_sqft <= 200:
            score += 30
            reasons.append("Good price per square foot")
        
        # Days on market analysis
        if days_on_market > 60:
            score += 20
            reasons.append("Property may be more negotiable due to longer market time")
        
        # Bed/bath ratio analysis
        if 1.5 <= beds/baths <= 2.5:
            score += 20
            reasons.append("Good bed to bath ratio")
            
        # Size analysis
        if 1000 <= sqft <= 3000:
            score += 30
            reasons.append("Optimal property size for flipping")

        # Calculate final prediction
        is_good_flip = score >= 60
        confidence = score  # Using score as confidence percentage

        return jsonify({
            'is_good_flip': is_good_flip,
            'confidence': confidence,
            'reasons': reasons
        })

    except ZeroDivisionError:
        logger.error("Division by zero error in prediction")
        return jsonify({
            'is_good_flip': False,
            'confidence': 0,
            'reasons': ["Invalid property data"]
        })
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)