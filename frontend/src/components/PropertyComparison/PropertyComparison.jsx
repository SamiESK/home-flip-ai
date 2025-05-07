import React, { useState } from 'react';
import { predictProperty } from '../../services/api';
import './PropertyComparison.css';

const PropertyComparison = () => {
  const [propertyData, setPropertyData] = useState({
    price: '',
    sqft: '',
    beds: '',
    baths: '',
    days_on_market: ''
  });

  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setPropertyData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await predictProperty(propertyData);
      setComparison(result);
    } catch (error) {
      console.error('Error in comparison:', error);
      alert('Error getting property comparison. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="property-comparison">
      <h2>Compare Property</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Price</label>
          <input
            type="text"
            name="price"
            value={propertyData.price}
            onChange={handleInputChange}
            placeholder="Enter price"
            required
          />
        </div>
        <div className="form-group">
          <label>Square Footage</label>
          <input
            type="text"
            name="sqft"
            value={propertyData.sqft}
            onChange={handleInputChange}
            placeholder="Enter sqft"
            required
          />
        </div>
        <div className="form-group">
          <label>Bedrooms</label>
          <input
            type="text"
            name="beds"
            value={propertyData.beds}
            onChange={handleInputChange}
            placeholder="Enter beds"
            required
          />
        </div>
        <div className="form-group">
          <label>Bathrooms</label>
          <input
            type="text"
            name="baths"
            value={propertyData.baths}
            onChange={handleInputChange}
            placeholder="Enter baths"
            required
          />
        </div>
        <div className="form-group">
          <label>Days on Market</label>
          <input
            type="text"
            name="days_on_market"
            value={propertyData.days_on_market}
            onChange={handleInputChange}
            placeholder="Enter days"
            required
          />
        </div>
        <button type="submit" className="submit-button" disabled={loading}>
          {loading ? 'Analyzing...' : 'Compare Property'}
        </button>
      </form>

      {comparison && (
        <div className="comparison-results">
          <h3>Analysis Results</h3>
          
          <div className="prediction-summary">
            <h4>Flip Potential</h4>
            <div className={`prediction ${comparison.is_good_flip ? 'good' : 'bad'}`}>
              {comparison.is_good_flip ? 'Good Flip ✅' : 'Bad Flip ❌'}
              <span className="confidence">
                {comparison.confidence_score}% confidence
              </span>
            </div>
          </div>

          <div className="similar-properties">
            <h4>Similar Historical Properties</h4>
            {comparison.similar_properties.map((prop, index) => (
              <div key={index} className="similar-property">
                <div className="property-details">
                  <p>Price: ${prop.price.toLocaleString()}</p>
                  <p>{prop.beds} beds • {prop.baths} baths • {prop.sqft} sqft</p>
                  <p>Days on Market: {prop.days_on_market}</p>
                </div>
                <div className="property-outcome">
                  {prop.is_good_flip ? 'Successful Flip ✅' : 'Unsuccessful Flip ❌'}
                </div>
              </div>
            ))}
          </div>

          <div className="analysis-points">
            <h4>Key Insights</h4>
            {comparison.analysis.map((point, index) => (
              <div key={index} className={`analysis-point ${point.confidence}`}>
                <p>{point.message}</p>
                <span className="confidence-badge">{point.confidence}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PropertyComparison;
