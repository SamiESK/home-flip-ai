import requests
import logging
from typing import List, Dict, Optional
from ..config import REALTY_MOLE_API_KEY, API_BASE_URL, DEFAULT_SEARCH_RADIUS, MAX_RESULTS

logger = logging.getLogger(__name__)

class PropertyService:
    def __init__(self):
        self.headers = {
            'x-rapidapi-host': 'realty-mole-property-api.p.rapidapi.com',
            'x-rapidapi-key': REALTY_MOLE_API_KEY
        }

    def get_properties_by_location(self, city: str, state: str, zip_code: str = None) -> List[Dict]:
        """
        Fetch properties by location using the Realty Mole API
        """
        try:
            params = {
                'city': city,
                'state': state,
                'radius': DEFAULT_SEARCH_RADIUS,
                'limit': MAX_RESULTS
            }
            if zip_code:
                params['zipCode'] = zip_code

            response = requests.get(
                f'{API_BASE_URL}/properties',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            properties = response.json()
            return self._format_properties(properties)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching properties: {str(e)}")
            return []

    def get_property_details(self, property_id: str) -> Optional[Dict]:
        """
        Fetch detailed property information
        """
        try:
            response = requests.get(
                f'{API_BASE_URL}/properties/{property_id}',
                headers=self.headers
            )
            response.raise_for_status()
            
            property_data = response.json()
            return self._format_property(property_data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property details: {str(e)}")
            return None

    def get_comparable_properties(self, property_data: Dict) -> List[Dict]:
        """
        Find comparable properties based on location and characteristics
        """
        try:
            params = {
                'address': property_data.get('address'),
                'radius': DEFAULT_SEARCH_RADIUS,
                'limit': MAX_RESULTS
            }

            response = requests.get(
                f'{API_BASE_URL}/properties',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            properties = response.json()
            return self._format_properties(properties)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching comparable properties: {str(e)}")
            return []

    def _format_property(self, property_data: Dict) -> Dict:
        """
        Format raw property data into standardized format
        """
        return {
            'property_id': property_data.get('id'),
            'list_price': property_data.get('price'),
            'sqft': property_data.get('squareFootage'),
            'beds': property_data.get('bedrooms'),
            'baths': property_data.get('bathrooms'),
            'street': property_data.get('formattedAddress'),
            'city': property_data.get('city'),
            'state': property_data.get('state'),
            'zip_code': property_data.get('zipCode'),
            'photos': property_data.get('photos', []),
            'property_url': property_data.get('listingUrl'),
            'days_on_market': property_data.get('daysOnMarket'),
            'latitude': property_data.get('latitude'),
            'longitude': property_data.get('longitude'),
            'property_type': property_data.get('propertyType'),
            'year_built': property_data.get('yearBuilt'),
            'lot_size': property_data.get('lotSize'),
            'last_sold_price': property_data.get('lastSoldPrice'),
            'last_sold_date': property_data.get('lastSoldDate')
        }

    def _format_properties(self, properties: List[Dict]) -> List[Dict]:
        """
        Format a list of properties
        """
        return [self._format_property(prop) for prop in properties] 