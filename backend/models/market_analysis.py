from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
import logging
import os
import pickle
import pandas as pd
from pathlib import Path

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
        self.min_profit_margin = 0.20  # 20% minimum profit margin
        self.max_repair_cost_percentage = 0.30  # Maximum 30% of property value for repairs
        self.estimated_holding_months = 6  # Estimated time to complete flip
        self.estimated_selling_costs_percentage = 0.10  # 10% for agent fees, closing costs, etc.
        
        # Load the house-flipper model
        try:
            ROOT_DIR = Path(__file__).parent.parent.parent
            model_path = os.path.join(ROOT_DIR, 'models', 'flip_score_model.pkl')
            with open(model_path, 'rb') as f:
                self.flip_model = pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading house-flipper model: {str(e)}")
            self.flip_model = None

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
        """Generate comprehensive market analysis for a potential flip property"""
        try:
            # Calculate basic market metrics
            market_metrics = self.calculate_market_metrics(comparable_properties)
            
            # Calculate flip-specific metrics
            flip_analysis = self.analyze_flip_potential(target_property, comparable_properties, market_metrics)
            
            # Get house-flipper prediction
            flip_prediction = self.get_flip_prediction(target_property)
            
            # Generate detailed analysis points
            analysis_points = self.generate_analysis_points(target_property, flip_analysis, market_metrics, flip_prediction)
            
            return {
                'analysis': analysis_points,
                'market_metrics': market_metrics,
                'flip_analysis': flip_analysis,
                'flip_prediction': flip_prediction
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}", exc_info=True)
            raise

    def calculate_market_metrics(self, comparable_properties: List[Dict]) -> Dict:
        """Calculate detailed market metrics from comparable properties"""
        if not comparable_properties:
            return {
                'avg_price': None,
                'median_price': None,
                'avg_price_per_sqft': None,
                'median_price_per_sqft': None,
                'avg_days_on_market': None,
                'avg_sqft': None,
                'price_trend': None,
                'absorption_rate': None
            }
            
        try:
            # Basic metrics
            prices = [p['list_price'] for p in comparable_properties if p.get('list_price')]
            sqft_values = [p['sqft'] for p in comparable_properties if p.get('sqft')]
            days_on_market = [p['days_on_market'] for p in comparable_properties if p.get('days_on_market')]
            
            # Calculate price per square foot
            price_per_sqft = []
            for prop in comparable_properties:
                if prop.get('list_price') and prop.get('sqft'):
                    price_per_sqft.append(prop['list_price'] / prop['sqft'])
            
            # Calculate trends (if we have enough data)
            price_trend = self.calculate_trend(prices) if len(prices) > 1 else None
            
            # Calculate absorption rate (properties sold per month)
            if days_on_market:
                avg_days = sum(days_on_market) / len(days_on_market)
                absorption_rate = 30 / avg_days if avg_days > 0 else None
            else:
                absorption_rate = None
            
            return {
                'avg_price': sum(prices) / len(prices) if prices else None,
                'median_price': sorted(prices)[len(prices)//2] if prices else None,
                'avg_price_per_sqft': sum(price_per_sqft) / len(price_per_sqft) if price_per_sqft else None,
                'median_price_per_sqft': sorted(price_per_sqft)[len(price_per_sqft)//2] if price_per_sqft else None,
                'avg_days_on_market': sum(days_on_market) / len(days_on_market) if days_on_market else None,
                'avg_sqft': sum(sqft_values) / len(sqft_values) if sqft_values else None,
                'price_trend': price_trend,
                'absorption_rate': absorption_rate
            }
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {str(e)}")
            return {}

    def analyze_flip_potential(self, target_property: Dict, comparable_properties: List[Dict], market_metrics: Dict) -> Dict:
        """Analyze the potential for a successful flip"""
        try:
            target_price = target_property.get('list_price', 0)
            target_sqft = target_property.get('sqft', 0)
            
            if not target_price or not target_sqft or not comparable_properties:
                return {
                    'estimated_arv': None,
                    'estimated_repair_costs': None,
                    'estimated_profit': None,
                    'roi': None,
                    'risk_score': None,
                    'confidence_score': None
                }
            
            # Calculate After Repair Value (ARV)
            avg_price_per_sqft = market_metrics.get('avg_price_per_sqft', 0)
            estimated_arv = target_sqft * avg_price_per_sqft if avg_price_per_sqft else None
            
            # Estimate repair costs (simplified for now)
            # In a real system, this would be based on property condition assessment
            estimated_repair_costs = target_price * self.max_repair_cost_percentage
            
            # Calculate potential profit
            if estimated_arv:
                estimated_profit = estimated_arv - target_price - estimated_repair_costs
                roi = (estimated_profit / (target_price + estimated_repair_costs)) * 100
            else:
                estimated_profit = None
                roi = None
            
            # Calculate risk score (0-100, higher is riskier)
            risk_factors = []
            
            # Price risk
            if market_metrics.get('price_trend'):
                if market_metrics['price_trend'] < 0:
                    risk_factors.append(30)  # High risk if prices are declining
                elif market_metrics['price_trend'] < 0.05:
                    risk_factors.append(15)  # Medium risk if prices are flat
                else:
                    risk_factors.append(5)  # Low risk if prices are rising
            
            # Market absorption risk
            if market_metrics.get('absorption_rate'):
                if market_metrics['absorption_rate'] < 0.5:
                    risk_factors.append(30)  # High risk if market is slow
                elif market_metrics['absorption_rate'] < 1:
                    risk_factors.append(15)  # Medium risk if market is moderate
                else:
                    risk_factors.append(5)  # Low risk if market is fast
            
            # Profit margin risk
            if roi is not None:
                if roi < 10:
                    risk_factors.append(40)  # Very high risk if low profit
                elif roi < 20:
                    risk_factors.append(20)  # High risk if moderate profit
                else:
                    risk_factors.append(5)  # Low risk if good profit
            
            risk_score = sum(risk_factors) / len(risk_factors) if risk_factors else 50
            
            # Calculate confidence score (0-100, higher is more confident)
            confidence_factors = []
            
            # Data quality confidence
            if len(comparable_properties) >= 5:
                confidence_factors.append(25)  # Good number of comparables
            elif len(comparable_properties) >= 3:
                confidence_factors.append(15)  # Moderate number of comparables
            else:
                confidence_factors.append(5)  # Few comparables
            
            # Market trend confidence
            if market_metrics.get('price_trend') is not None:
                confidence_factors.append(25)  # Have price trend data
            
            # Absorption rate confidence
            if market_metrics.get('absorption_rate') is not None:
                confidence_factors.append(25)  # Have absorption rate data
            
            # Profit margin confidence
            if roi is not None:
                confidence_factors.append(25)  # Have ROI calculation
            
            confidence_score = sum(confidence_factors) if confidence_factors else 0
            
            return {
                'estimated_arv': estimated_arv,
                'estimated_repair_costs': estimated_repair_costs,
                'estimated_profit': estimated_profit,
                'roi': roi,
                'risk_score': risk_score,
                'confidence_score': confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error analyzing flip potential: {str(e)}")
            return {}

    def get_flip_prediction(self, property_data: Dict) -> Dict:
        """Get prediction from house-flipper model"""
        try:
            if not self.flip_model:
                return {
                    'is_good_flip': None,
                    'confidence': None,
                    'model_available': False
                }
            
            # Convert property data to model format
            input_data = pd.DataFrame([{
                'price': float(property_data['list_price']),
                'sqft': float(property_data['sqft']),
                'beds': int(property_data['beds']),
                'baths': int(property_data['baths']),
                'days_on_market': int(property_data['days_on_market'])
            }])
            
            # Make prediction
            prediction = self.flip_model.predict(input_data)[0]
            
            # Calculate confidence
            if prediction > 0:
                confidence = 60 + (40 / (1 + abs(prediction)))
            else:
                confidence = 40 / (1 + abs(prediction))
            
            return {
                'is_good_flip': bool(prediction > 0),
                'confidence': round(confidence),
                'model_available': True
            }
            
        except Exception as e:
            logger.error(f"Error getting flip prediction: {str(e)}")
            return {
                'is_good_flip': None,
                'confidence': None,
                'model_available': False
            }

    def generate_analysis_points(self, target_property: Dict, flip_analysis: Dict, market_metrics: Dict, flip_prediction: Dict) -> List[Dict]:
        """Generate detailed analysis points for the property"""
        analysis_points = []
        
        try:
            # Add house-flipper prediction if available
            if flip_prediction.get('model_available'):
                if flip_prediction['is_good_flip']:
                    analysis_points.append({
                        'type': 'ai_prediction',
                        'title': 'AI Flip Recommendation',
                        'description': f"Based on historical data analysis, this property has a {flip_prediction['confidence']}% chance of being a successful flip.",
                        'impact': 'positive'
                    })
                else:
                    analysis_points.append({
                        'type': 'ai_prediction',
                        'title': 'AI Flip Warning',
                        'description': f"Based on historical data analysis, this property has a {flip_prediction['confidence']}% chance of being an unsuccessful flip.",
                        'impact': 'negative'
                    })
            
            # Market Overview
            if market_metrics.get('price_trend') is not None:
                trend = market_metrics['price_trend']
                if trend > 0.05:
                    analysis_points.append({
                        'type': 'market_trend',
                        'title': 'Strong Market Growth',
                        'description': f'Property values in this area are increasing at a rate of {trend:.1%} per month.',
                        'impact': 'positive'
                    })
                elif trend > 0:
                    analysis_points.append({
                        'type': 'market_trend',
                        'title': 'Stable Market',
                        'description': 'Property values in this area are stable with slight growth.',
                        'impact': 'neutral'
                    })
                else:
                    analysis_points.append({
                        'type': 'market_trend',
                        'title': 'Declining Market',
                        'description': f'Property values in this area are decreasing at a rate of {abs(trend):.1%} per month.',
                        'impact': 'negative'
                    })
            
            # ROI Analysis
            if flip_analysis.get('roi') is not None:
                roi = flip_analysis['roi']
                if roi >= 30:
                    analysis_points.append({
                        'type': 'roi',
                        'title': 'High ROI Potential',
                        'description': f'Estimated ROI of {roi:.1f}% exceeds the target of 20%.',
                        'impact': 'positive'
                    })
                elif roi >= 20:
                    analysis_points.append({
                        'type': 'roi',
                        'title': 'Good ROI Potential',
                        'description': f'Estimated ROI of {roi:.1f}% meets the target of 20%.',
                        'impact': 'positive'
                    })
                else:
                    analysis_points.append({
                        'type': 'roi',
                        'title': 'Low ROI Potential',
                        'description': f'Estimated ROI of {roi:.1f}% is below the target of 20%.',
                        'impact': 'negative'
                    })
            
            # Risk Assessment
            if flip_analysis.get('risk_score') is not None:
                risk_score = flip_analysis['risk_score']
                if risk_score >= 70:
                    analysis_points.append({
                        'type': 'risk',
                        'title': 'High Risk Investment',
                        'description': 'This property presents significant risks for flipping.',
                        'impact': 'negative'
                    })
                elif risk_score >= 50:
                    analysis_points.append({
                        'type': 'risk',
                        'title': 'Moderate Risk Investment',
                        'description': 'This property presents moderate risks for flipping.',
                        'impact': 'neutral'
                    })
                else:
                    analysis_points.append({
                        'type': 'risk',
                        'title': 'Low Risk Investment',
                        'description': 'This property presents relatively low risks for flipping.',
                        'impact': 'positive'
                    })
            
            # Market Absorption
            if market_metrics.get('absorption_rate') is not None:
                rate = market_metrics['absorption_rate']
                if rate >= 1:
                    analysis_points.append({
                        'type': 'absorption',
                        'title': 'Fast-Moving Market',
                        'description': f'Properties in this area sell quickly (average {30/rate:.1f} days).',
                        'impact': 'positive'
                    })
                elif rate >= 0.5:
                    analysis_points.append({
                        'type': 'absorption',
                        'title': 'Moderate Market',
                        'description': f'Properties in this area sell at a moderate pace (average {30/rate:.1f} days).',
                        'impact': 'neutral'
                    })
                else:
                    analysis_points.append({
                        'type': 'absorption',
                        'title': 'Slow-Moving Market',
                        'description': f'Properties in this area sell slowly (average {30/rate:.1f} days).',
                        'impact': 'negative'
                    })
            
            return analysis_points
            
        except Exception as e:
            logger.error(f"Error generating analysis points: {str(e)}")
            return []

    def calculate_trend(self, values: List[float]) -> float:
        """Calculate the trend of a series of values"""
        if len(values) < 2:
            return 0
            
        try:
            # Simple linear regression
            x = range(len(values))
            y = values
            
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(i * j for i, j in zip(x, y))
            sum_xx = sum(i * i for i in x)
            
            # Calculate slope
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
            
            # Convert to monthly rate
            return slope / (sum_y / n) if sum_y != 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return 0

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