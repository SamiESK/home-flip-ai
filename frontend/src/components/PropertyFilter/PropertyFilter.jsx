import React, { useState } from 'react';
import { predictProperty } from '../../services/api';
import './PropertyFilter.css';

const PropertyFilter = ({ onFilterChange }) => {
  const [propertyData, setPropertyData] = useState({
    price: '',
    sqft: '',
    beds: '',
    baths: '',
    days_on_market: ''
  });

  // Add state for filter values
  const [filterValues, setFilterValues] = useState({
    minPrice: '',
    maxPrice: '',
    minSqft: '',
    maxSqft: '',
    onlyGoodFlips: false
  });

  // Function to format number with commas as you type
  const formatWithCommas = (value) => {
    // Remove any non-digit characters
    const number = value.replace(/\D/g, '');
    // Add commas
    return number.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Format all numeric fields with commas
    const formattedValue = formatWithCommas(value);
    setPropertyData(prev => ({
      ...prev,
      [name]: formattedValue
    }));
  };

  // New handler for filter inputs
  const handleFilterChange = (name, value) => {
    const formattedValue = formatWithCommas(value);
    setFilterValues(prev => ({
      ...prev,
      [name]: formattedValue
    }));
    onFilterChange(name, formattedValue);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Remove commas before sending to API
    const dataToSend = {
      ...propertyData,
      price: propertyData.price.replace(/,/g, ''),
      sqft: propertyData.sqft.replace(/,/g, ''),
      beds: propertyData.beds.replace(/,/g, ''),
      baths: propertyData.baths.replace(/,/g, ''),
      days_on_market: propertyData.days_on_market.replace(/,/g, '')
    };

    try {
      const result = await predictProperty(dataToSend);
      alert(`Prediction: ${result.is_good_flip ? 'Good Flip ✅' : 'Bad Flip ❌'}\nConfidence: ${result.confidence_score}%`);
    } catch (error) {
      console.error('Error in handleSubmit:', error);
      alert('Error making prediction. Please try again.');
    }
  };

  return (
    <div className="property-filter">
      <div className="filter-section">
        <h3>Filter Properties</h3>
        <div className="filter-group">
          <label>Price Range</label>
          <input 
            type="text" 
            value={filterValues.minPrice}
            placeholder="Min Price" 
            onChange={(e) => handleFilterChange('minPrice', e.target.value)} 
          />
          <input 
            type="text" 
            value={filterValues.maxPrice}
            placeholder="Max Price" 
            onChange={(e) => handleFilterChange('maxPrice', e.target.value)} 
          />
        </div>
        <div className="filter-group">
          <label>Square Footage</label>
          <input 
            type="text" 
            value={filterValues.minSqft}
            placeholder="Min Sqft" 
            onChange={(e) => handleFilterChange('minSqft', e.target.value)} 
          />
          <input 
            type="text" 
            value={filterValues.maxSqft}
            placeholder="Max Sqft" 
            onChange={(e) => handleFilterChange('maxSqft', e.target.value)} 
          />
        </div>
        <div className="filter-group">
          <label>Show Only Good Flips</label>
          <input 
            type="checkbox" 
            checked={filterValues.onlyGoodFlips}
            onChange={(e) => {
              setFilterValues(prev => ({
                ...prev,
                onlyGoodFlips: e.target.checked
              }));
              onFilterChange('onlyGoodFlips', e.target.checked);
            }} 
          />
        </div>
      </div>

      <div className="prediction-form">
        <h3>Predict New Property</h3>
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
          <button type="submit" className="submit-button">Predict Property</button>
        </form>
      </div>
    </div>
  );
};

export default PropertyFilter;