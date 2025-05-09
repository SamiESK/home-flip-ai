import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
REALTY_MOLE_API_KEY = os.getenv('REALTY_MOLE_API_KEY')
API_BASE_URL = 'https://realty-mole-property-api.p.rapidapi.com'

# Default search parameters
DEFAULT_SEARCH_RADIUS = 5  # miles
MAX_RESULTS = 10
MIN_COMPARABLE_PROPERTIES = 3

# Property matching weights
SIMILARITY_WEIGHTS = {
    'price': 0.4,
    'sqft': 0.3,
    'beds': 0.15,
    'baths': 0.15
}

# Cache settings
CACHE_EXPIRY = 3600  # 1 hour in seconds 