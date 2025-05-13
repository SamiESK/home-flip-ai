import React, { useState } from 'react';
import './PropertyFilter.css';
import { scrapeProperties } from '../../services/api';

const PropertyFilter = ({ onFilterChange, onPropertiesLoaded }) => {
  const [zipCode, setZipCode] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clean and validate price
      const cleanedMaxPrice = maxPrice.replace(/[^0-9.-]+/g, '');
      const maxPriceNum = Number(cleanedMaxPrice);
      
      if (isNaN(maxPriceNum) || maxPriceNum <= 0) {
        throw new Error('Please enter a valid maximum price');
      }
      
      console.log('Sending scrape request with:', { zipCode, maxPrice: maxPriceNum });
      const response = await scrapeProperties(zipCode, maxPriceNum);
      console.log('Raw API response:', response);

      if (!response?.properties) {
        throw new Error('No properties data in response');
      }

      // Ensure we have an array of properties
      const propertiesArray = Array.isArray(response.properties) ? 
        response.properties : Object.values(response.properties);
      console.log('Initial properties array:', propertiesArray);

      // Process and validate properties
      const processedProperties = propertiesArray
        .filter(property => {
          // Validate coordinates
          const lat = Number(property.latitude);
          const lng = Number(property.longitude);
          const isValid = !isNaN(lat) && !isNaN(lng) && 
                         lat >= -90 && lat <= 90 && 
                         lng >= -180 && lng <= 180;
          
          if (!isValid) {
            console.log('Property filtered out due to invalid coordinates:', {
              property_id: property.property_id,
              street: property.street,
              lat,
              lng
            });
          }
          
          return isValid;
        })
        .map(property => {
          // Handle different photo field possibilities
          let processedPhotos = [];
          if (property.photos) {
            if (Array.isArray(property.photos)) {
              processedPhotos = property.photos;
            } else if (typeof property.photos === 'string') {
              processedPhotos = [property.photos];
            }
          } else if (property.alt_photos) {
            if (Array.isArray(property.alt_photos)) {
              processedPhotos = property.alt_photos;
            } else if (typeof property.alt_photos === 'string') {
              processedPhotos = property.alt_photos.split(',').map(url => url.trim());
            }
          }

          const processed = {
            property_id: property.property_id || `temp_${Math.random()}`,
            street: property.street || 'Address not available',
            city: property.city || '',
            state: property.state || '',
            zip_code: String(property.zip_code || '').trim(),
            list_price: Number(String(property.list_price).replace(/[^0-9.-]+/g, '')),
            sqft: Number(String(property.sqft || '0').replace(/[^0-9.-]+/g, '')),
            beds: Number(property.beds) || 0,
            baths: Number(property.baths || property.full_baths) || 0,
            days_on_market: Number(property.days_on_market || property.days_on_mls) || 0,
            latitude: Number(property.latitude),
            longitude: Number(property.longitude),
            agent_name: property.agent_name || '',
            agent_email: property.agent_email || '',
            agent_phones: Array.isArray(property.agent_phones) ? property.agent_phones : [],
            photos: processedPhotos,
            property_url: property.property_url || '',
            status: property.status || ''
          };
          console.log('Processed property:', processed);
          return processed;
        });

      console.log('Final processed properties:', processedProperties);
      
      // Update filters first
      onFilterChange('zipCode', zipCode.trim());
      onFilterChange('maxPrice', maxPriceNum);
      
      // Then update properties
      onPropertiesLoaded(processedProperties);

    } catch (error) {
      console.error('Error processing properties:', error);
      setError(error.message || 'Failed to load properties');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="property-filter">
      <h2>Search Properties</h2>
      <form onSubmit={handleSubmit}>
        <div className="filter-group">
          <label htmlFor="zipCode">Zip Code:</label>
          <input
            type="text"
            id="zipCode"
            value={zipCode}
            onChange={(e) => setZipCode(e.target.value)}
            placeholder="Enter zip code"
          />
        </div>
        <div className="filter-group">
          <label htmlFor="maxPrice">Maximum Price:</label>
          <input
            type="text"
            id="maxPrice"
            value={maxPrice}
            onChange={(e) => {
              const formatted = e.target.value.replace(/\D/g, '').replace(/\B(?=(\d{3})+(?!\d))/g, ',');
              setMaxPrice(formatted);
            }}
            placeholder="Enter maximum price"
          />
        </div>
        <button 
          type="submit" 
          disabled={loading}
          className="search-button"
        >
          {loading ? 'Searching...' : 'Search Properties'}
        </button>
        
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
};

export default PropertyFilter;