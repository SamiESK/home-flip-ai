from flask import Flask, jsonify, request
import pandas as pd
from flask_cors import CORS
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Get the root directory path
ROOT_DIR = Path(__file__).parent.parent

@app.route('/')
def test():
    logger.info("Test route accessed")
    return 'Flask server is running!'

@app.route('/api/properties', methods=['GET'])
def get_properties():
    try:
        logger.info("Received request for properties")
        # Use proper path joining for predictions.csv
        predictions_path = os.path.join(ROOT_DIR, 'predictions.csv')
        logger.info(f"Looking for predictions at: {predictions_path}")
        
        if not os.path.exists(predictions_path):
            logger.error("No predictions file found")
            return jsonify({'error': 'No predictions data available'}), 404
            
        # Read the latest predictions
        predictions_df = pd.read_csv(predictions_path)
        logger.info(f"Found {len(predictions_df)} properties")
        
        # Convert DataFrame to list of dictionaries
        properties = predictions_df.to_dict('records')
        
        return jsonify(properties)
    except pd.errors.EmptyDataError:
        logger.error("Empty predictions file")
        return jsonify({'error': 'Predictions file is empty'}), 500
    except Exception as e:
        logger.error(f"Error in get_properties: {str(e)}")
        return jsonify({'error': f'Failed to load predictions: {str(e)}'}), 500

@app.route('/api/predict', methods=['POST'])
def predict_property():
    try:
        logger.info("Received prediction request")
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400

        property_data = request.json
        logger.info(f"Received property data: {property_data}")
        
        # Validate required fields
        required_fields = ['price', 'sqft', 'beds', 'baths', 'days_on_market']
        missing_fields = [field for field in required_fields if field not in property_data]
        
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Import predictor from the correct path
        import sys
        sys.path.append(str(ROOT_DIR))
        logger.info("Attempting to import predictor")
        from src.predictor import predict
        
        try:
            logger.info("Making prediction...")
            flip_class, flip_score = predict(property_data)
            logger.info(f"Prediction successful: {flip_class}, {flip_score}")
            return jsonify({
                'is_good_flip': flip_class,
                'confidence_score': flip_score,
                'property_data': property_data
            })
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Request error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Request failed: {str(e)}'}), 500

@app.route('/api/compare', methods=['POST'])
def compare_property():
    try:
        logger.info("Received comparison request")
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        property_data = request.json
        logger.info(f"Received property data: {property_data}")
        
        # Import comparison function
        from src.comparator import find_similar_properties
        
        try:
            similar_properties = find_similar_properties(property_data)
            return jsonify({
                'current_property': property_data,
                'similar_properties': similar_properties,
                'analysis': generate_analysis(property_data, similar_properties)
            })
        except Exception as e:
            logger.error(f"Comparison error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Comparison failed: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Request error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Request failed: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    logger.info(f"Root directory: {ROOT_DIR}")
    app.run(debug=True)