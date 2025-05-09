from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def safe_division(numerator: float, denominator: float, default: float = None) -> Optional[float]:
    """Safely perform division with error handling"""
    try:
        if denominator == 0 or denominator is None:
            return default
        return float(numerator) / float(denominator)
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.warning(f"Error in safe division: {str(e)}")
        return default

class MarketAnalyzer:
    def __init__(self):
        self.analysis_types = {
            'price': {
                'icon': '💰',
                'title': 'Price Analysis'
            },
            'size': {
                'icon': '📏',
                'title': 'Size Comparison'
            },
            'market_timing': {
                'icon': '⏰',
                'title': 'Market Timing'
            },
            'location': {
                'icon': '📍',
                'title': 'Location Analysis'
            },
            'historical': {
                'icon': '📈',
                'title': 'Historical Performance'
            },
            'overall': {
                'icon': '🎯',
                'title': 'Overall Assessment'
            }
        }

    def generate_analysis(self, target_property: Dict, comparable_properties: List[Dict]) -> Dict:
        """
        Generate a standardized analysis for a property
        """
        analysis = []
        market_metrics = self._calculate_market_metrics(comparable_properties)
        
        # Price Analysis
        price_analysis = self._analyze_price(target_property, market_metrics)
        if price_analysis:
            analysis.append(price_analysis)

        # Size Analysis
        size_analysis = self._analyze_size(target_property, market_metrics)
        if size_analysis:
            analysis.append(size_analysis)

        # Market Timing Analysis
        timing_analysis = self._analyze_market_timing(target_property, market_metrics)
        if timing_analysis:
            analysis.append(timing_analysis)

        # Location Analysis
        location_analysis = self._analyze_location(target_property, comparable_properties)
        if location_analysis:
            analysis.append(location_analysis)

        # Historical Analysis
        historical_analysis = self._analyze_historical_performance(target_property, comparable_properties)
        if historical_analysis:
            analysis.append(historical_analysis)

        # Overall Assessment
        overall_analysis = self._generate_overall_assessment(analysis)
        analysis.append(overall_analysis)

        return {
            'analysis': analysis,
            'market_metrics': market_metrics,
            'comparable_properties': self._format_comparable_properties(comparable_properties)
        }

    def _calculate_market_metrics(self, comparable_properties: List[Dict]) -> Dict:
        """Calculate key market metrics from comparable properties"""
        try:
            # Extract numeric values safely
            prices = []
            sqft_values = []
            days_on_market = []
            
            for p in comparable_properties:
                try:
                    if p.get('list_price') is not None:
                        price = float(p['list_price'])
                        if price > 0:
                            prices.append(price)
                except (ValueError, TypeError):
                    continue
                    
                try:
                    if p.get('sqft') is not None:
                        sqft = float(p['sqft'])
                        if sqft > 0:
                            sqft_values.append(sqft)
                except (ValueError, TypeError):
                    continue
                    
                try:
                    if p.get('days_on_market') is not None:
                        dom = int(p['days_on_market'])
                        if dom >= 0:
                            days_on_market.append(dom)
                except (ValueError, TypeError):
                    continue
            
            # Calculate metrics with safety checks
            metrics = {
                'avg_price': np.mean(prices) if prices else None,
                'median_price': np.median(prices) if prices else None,
                'avg_sqft': np.mean(sqft_values) if sqft_values else None,
                'avg_days_on_market': np.mean(days_on_market) if days_on_market else None,
                'avg_price_per_sqft': None  # Initialize to None
            }
            
            # Calculate price per sqft only for properties with valid price and sqft
            valid_ppsf = []
            for price, sqft in zip(prices, sqft_values):
                ppsf = safe_division(price, sqft)
                if ppsf is not None:
                    valid_ppsf.append(ppsf)
            
            if valid_ppsf:
                metrics['avg_price_per_sqft'] = np.mean(valid_ppsf)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {str(e)}")
            return {
                'avg_price': None,
                'median_price': None,
                'avg_sqft': None,
                'avg_price_per_sqft': None,
                'avg_days_on_market': None
            }

    def _analyze_price(self, property: Dict, metrics: Dict) -> Optional[Dict]:
        """Generate price analysis"""
        try:
            if not property.get('list_price') or not metrics['avg_price'] or metrics['avg_price'] == 0:
                return None

            price_diff_percent = safe_division(
                float(property['list_price']) - metrics['avg_price'],
                metrics['avg_price'],
                default=None
            )
            
            if price_diff_percent is None:
                return None
                
            price_diff_percent *= 100
            
            if price_diff_percent < -15:
                return {
                    'type': 'price',
                    'confidence': 'high',
                    'message': f"Excellent opportunity! Property is {abs(price_diff_percent):.1f}% below market average, suggesting strong potential for value appreciation.",
                    'metrics': {
                        'difference_percent': price_diff_percent,
                        'market_average': metrics['avg_price']
                    }
                }
            elif price_diff_percent < -5:
                return {
                    'type': 'price',
                    'confidence': 'medium',
                    'message': f"Good value! Property is {abs(price_diff_percent):.1f}% below market average.",
                    'metrics': {
                        'difference_percent': price_diff_percent,
                        'market_average': metrics['avg_price']
                    }
                }
            else:
                return {
                    'type': 'price',
                    'confidence': 'low',
                    'message': f"Property is priced {abs(price_diff_percent):.1f}% {'above' if price_diff_percent > 0 else 'below'} market average.",
                    'metrics': {
                        'difference_percent': price_diff_percent,
                        'market_average': metrics['avg_price']
                    }
                }
        except Exception as e:
            logger.error(f"Error in price analysis: {str(e)}")
            return None

    def _analyze_size(self, property: Dict, metrics: Dict) -> Optional[Dict]:
        """Generate size analysis"""
        try:
            if not property.get('sqft') or not metrics['avg_sqft'] or metrics['avg_sqft'] == 0:
                return None

            size_diff_percent = safe_division(
                float(property['sqft']) - metrics['avg_sqft'],
                metrics['avg_sqft'],
                default=None
            )
            
            if size_diff_percent is None:
                return None
                
            size_diff_percent *= 100
            
            # Calculate price per sqft safely
            price_per_sqft = None
            if property.get('list_price') and property.get('sqft'):
                price_per_sqft = safe_division(
                    float(property['list_price']),
                    float(property['sqft'])
                )
         
            message = []
            if abs(size_diff_percent) > 10:
                message.append(f"Property is {abs(size_diff_percent):.1f}% {'larger' if size_diff_percent > 0 else 'smaller'} than average.")
            
            if price_per_sqft and metrics['avg_price_per_sqft'] and metrics['avg_price_per_sqft'] > 0:
                price_per_sqft_diff = safe_division(
                    price_per_sqft - metrics['avg_price_per_sqft'],
                    metrics['avg_price_per_sqft'],
                    default=None
                )
                
                if price_per_sqft_diff is not None:
                    price_per_sqft_diff *= 100
                    message.append(f"Price per sqft is {abs(price_per_sqft_diff):.1f}% {'above' if price_per_sqft_diff > 0 else 'below'} market average.")

            if not message:
                return None

            return {
                'type': 'size',
                'confidence': 'high' if abs(size_diff_percent) > 15 else 'medium',
                'message': ' '.join(message),
                'metrics': {
                    'size_difference_percent': size_diff_percent,
                    'price_per_sqft': price_per_sqft,
                    'market_avg_price_per_sqft': metrics['avg_price_per_sqft']
                }
            }
        except Exception as e:
            logger.error(f"Error in size analysis: {str(e)}")
            return None

    def _analyze_market_timing(self, property: Dict, metrics: Dict) -> Optional[Dict]:
        """Generate market timing analysis"""
        if not property.get('days_on_market'):
            return None

        dom = property['days_on_market']
        avg_dom = metrics['avg_days_on_market']
        
        if dom > avg_dom * 1.5:
            return {
                'type': 'market_timing',
                'confidence': 'high',
                'message': f"Property has been on market for {dom} days (vs. average {avg_dom:.0f} days). This extended duration may provide negotiating leverage.",
                'metrics': {
                    'days_on_market': dom,
                    'avg_days_on_market': avg_dom
                }
            }
        elif dom > avg_dom:
            return {
                'type': 'market_timing',
                'confidence': 'medium',
                'message': f"Property has been listed for {dom} days, slightly above the average of {avg_dom:.0f} days.",
                'metrics': {
                    'days_on_market': dom,
                    'avg_days_on_market': avg_dom
                }
            }
        else:
            return {
                'type': 'market_timing',
                'confidence': 'low',
                'message': f"Recently listed property ({dom} days on market vs. average {avg_dom:.0f} days).",
                'metrics': {
                    'days_on_market': dom,
                    'avg_days_on_market': avg_dom
                }
            }

    def _analyze_location(self, property: Dict, comparable_properties: List[Dict]) -> Optional[Dict]:
        """Generate location analysis"""
        try:
            # Get nearby properties within 1 mile radius
            nearby_properties = self._get_nearby_properties(property, comparable_properties)
            
            if not nearby_properties:
                logger.info("No nearby properties found for location analysis")
                return None

            # Calculate average price of nearby properties
            try:
                prices = [float(p['list_price']) for p in nearby_properties if p.get('list_price') and float(p.get('list_price', 0)) > 0]
                avg_nearby_price = np.mean(prices) if prices else None
            except Exception as e:
                logger.warning(f"Error calculating average nearby price: {str(e)}")
                avg_nearby_price = None

            # Calculate price trend
            try:
                price_trend = self._calculate_price_trend(nearby_properties)
            except Exception as e:
                logger.warning(f"Error calculating price trend: {str(e)}")
                price_trend = None

            # Build analysis message
            message = []
            if avg_nearby_price and property.get('list_price') and avg_nearby_price > 0:
                try:
                    price_diff = safe_division(
                        float(property['list_price']) - avg_nearby_price,
                        avg_nearby_price,
                        default=None
                    )
                    if price_diff is not None:
                        price_diff *= 100
                        message.append(f"Property is priced {abs(price_diff):.1f}% {'above' if price_diff > 0 else 'below'} nearby properties.")
                except (ValueError, ZeroDivisionError) as e:
                    logger.warning(f"Error calculating price difference: {str(e)}")
            
            if price_trend is not None:
                message.append(f"Area prices have {'increased' if price_trend > 0 else 'decreased'} {abs(price_trend):.1f}% recently.")

            if not message:
                logger.info("No location analysis messages generated")
                return None

            return {
                'type': 'location',
                'confidence': 'high' if len(nearby_properties) >= 3 else 'medium',
                'message': ' '.join(message),
                'metrics': {
                    'nearby_properties_count': len(nearby_properties),
                    'avg_nearby_price': avg_nearby_price,
                    'price_trend': price_trend
                }
            }
        except Exception as e:
            logger.error(f"Error in location analysis: {str(e)}", exc_info=True)
            return None

    def _analyze_historical_performance(self, property: Dict, comparable_properties: List[Dict]) -> Optional[Dict]:
        """Generate historical performance analysis"""
        successful_flips = [p for p in comparable_properties if p.get('is_good_flip')]
        if not successful_flips:
            return None

        success_rate = len(successful_flips) / len(comparable_properties) * 100
        avg_roi = np.mean([p.get('roi', 0) for p in successful_flips if p.get('roi')])

        return {
            'type': 'historical',
            'confidence': 'high' if success_rate > 60 else 'medium',
            'message': f"{success_rate:.1f}% of similar properties were successful flips with average ROI of {avg_roi:.1f}%.",
            'metrics': {
                'success_rate': success_rate,
                'avg_roi': avg_roi
            }
        }

    def _generate_overall_assessment(self, analyses: List[Dict]) -> Dict:
        """Generate overall assessment based on individual analyses"""
        if not analyses:
            return {
                'type': 'overall',
                'confidence': 'low',
                'message': "Insufficient data available for a comprehensive analysis.",
                'metrics': {
                    'score': 0,
                    'high_confidence_factors': 0,
                    'medium_confidence_factors': 0
                }
            }
            
        high_confidence = len([a for a in analyses if a['confidence'] == 'high'])
        medium_confidence = len([a for a in analyses if a['confidence'] == 'medium'])
        
        total_score = (high_confidence * 2 + medium_confidence) / (len(analyses) * 2) * 100
        
        if total_score >= 70:
            message = "Strong investment opportunity with multiple positive indicators."
            confidence = "high"
        elif total_score >= 50:
            message = "Moderate investment opportunity with some positive indicators."
            confidence = "medium"
        else:
            message = "Exercise caution. Limited positive indicators found."
            confidence = "low"

        return {
            'type': 'overall',
            'confidence': confidence,
            'message': message,
            'metrics': {
                'score': total_score,
                'high_confidence_factors': high_confidence,
                'medium_confidence_factors': medium_confidence
            }
        }

    def _get_nearby_properties(self, property: Dict, comparable_properties: List[Dict], radius_miles: float = 1.0) -> List[Dict]:
        """Get properties within specified radius"""
        try:
            if not property.get('latitude') or not property.get('longitude'):
                logger.warning("Target property missing latitude/longitude")
                return []

            nearby = []
            for comp in comparable_properties:
                try:
                    if not comp.get('latitude') or not comp.get('longitude'):
                        continue
                        
                    distance = self._calculate_distance(
                        float(property['latitude']), float(property['longitude']),
                        float(comp['latitude']), float(comp['longitude'])
                    )
                    if distance <= radius_miles:
                        nearby.append(comp)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error calculating distance for property: {str(e)}")
                    continue
                    
            return nearby
        except Exception as e:
            logger.error(f"Error finding nearby properties: {str(e)}")
            return []

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula"""
        R = 3959.87433  # Earth's radius in miles

        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c

    def _calculate_price_trend(self, properties: List[Dict]) -> float:
        """Calculate price trend as percentage change over time"""
        try:
            if not properties:
                return 0.0

            # Sort properties by date
            dated_properties = [(p.get('list_date', ''), p.get('list_price', 0)) 
                            for p in properties 
                            if p.get('list_date') and p.get('list_price') and float(p.get('list_price', 0)) > 0]
            
            if not dated_properties:
                return 0.0

            dated_properties.sort(key=lambda x: x[0])
            
            if len(dated_properties) < 2:
                return 0.0

            first_price = float(dated_properties[0][1])
            last_price = float(dated_properties[-1][1])
            
            if first_price == 0:  # Prevent division by zero
                return 0.0
                
            return ((last_price - first_price) / first_price) * 100
        except Exception as e:
            logger.error(f"Error calculating price trend: {str(e)}")
            return 0.0

    def _format_comparable_properties(self, properties: List[Dict]) -> List[Dict]:
        """Format comparable properties for frontend display"""
        formatted_properties = []
        for p in properties:
            try:
                # Handle photos field
                photos = []
                raw_photos = p.get('photos', [])
                
                # Convert string representation of list to actual list
                if isinstance(raw_photos, str):
                    if raw_photos.startswith('[') and raw_photos.endswith(']'):
                        try:
                            import json
                            photos = json.loads(raw_photos)
                        except json.JSONDecodeError:
                            photos = [raw_photos]  # Use the string as a single photo URL
                    elif ',' in raw_photos:
                        photos = [url.strip() for url in raw_photos.split(',') if url.strip()]
                    elif raw_photos.strip():
                        photos = [raw_photos.strip()]
                elif isinstance(raw_photos, list):
                    photos = raw_photos
                    
                # Filter out invalid photo URLs
                photos = [
                    url for url in photos 
                    if url and isinstance(url, str) and (
                        url.startswith('http://') or 
                        url.startswith('https://')
                    )
                ]

                # Handle property URL
                property_url = p.get('property_url', '').strip()
                if not property_url or not (
                    property_url.startswith('http://') or 
                    property_url.startswith('https://')
                ):
                    property_url = None

                # Format the property data
                formatted_prop = {
                    'property_id': p.get('property_id'),
                    'list_price': float(p['list_price']) if p.get('list_price') is not None else None,
                    'sqft': float(p['sqft']) if p.get('sqft') is not None else None,
                    'beds': float(p['beds']) if p.get('beds') is not None else None,
                    'baths': float(p['baths']) if p.get('baths') is not None else None,
                    'street': p.get('street'),
                    'city': p.get('city'),
                    'state': p.get('state'),
                    'zip_code': p.get('zip_code'),
                    'photos': photos,  # Now just passing the filtered photos array, empty if none valid
                    'property_url': property_url,
                    'days_on_market': int(p['days_on_market']) if p.get('days_on_market') is not None else None,
                    'similarity_score': float(p.get('similarity_score', 0))
                }
                formatted_properties.append(formatted_prop)
            except (ValueError, TypeError) as e:
                print(f"Error formatting property: {str(e)}")
                continue
                
        return formatted_properties 