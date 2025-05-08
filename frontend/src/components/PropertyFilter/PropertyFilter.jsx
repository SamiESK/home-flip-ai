// frontend/src/components/PropertyFilter/PropertyFilter.jsx
import React, { useState } from 'react';
import './PropertyFilter.css';
import { scrapeProperties } from '../../services/api';

const PropertyFilter = ({ onFilterChange, onPropertiesLoaded }) => {
  const [zipCode, setZipCode] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [debugProperties, setDebugProperties] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clean price before sending to API
      const cleanedMaxPrice = maxPrice.replace(/,/g, '');
      
      // Log the request
      console.log('Sending request with:', { zipCode, cleanedMaxPrice });
      
      const response = await scrapeProperties(zipCode, cleanedMaxPrice);
      console.log('Raw API Response:', response);

      if (!response?.properties) {
        throw new Error('No properties data in response');
      }

      // Ensure we have an array of properties
      const propertiesArray = Array.isArray(response.properties) ? 
        response.properties : Object.values(response.properties);

      console.log('Properties array before processing:', {
        length: propertiesArray.length,
        sample: propertiesArray[0]
      });

      const processedProperties = propertiesArray
        .filter(Boolean)
        .map(property => {
          // Add photo processing debug log
          console.log('Processing property photos:', {
            propertyId: property.property_id,
            rawPhotos: property.photos,
            altPhotos: property.alt_photos
          });

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
            zip_code: property.zip_code || '',
            list_price: Number(String(property.list_price).replace(/[^0-9.-]+/g, '')),
            sqft: Number(String(property.sqft || '0').replace(/[^0-9.-]+/g, '')),
            beds: Number(property.beds) || 0,
            full_baths: Number(property.full_baths) || 0,
            days_on_mls: Number(property.days_on_mls) || 0,
            latitude: Number(property.latitude) || 0,
            longitude: Number(property.longitude) || 0,
            agent_name: property.agent_name || '',
            agent_email: property.agent_email || '',
            agent_phones: Array.isArray(property.agent_phones) ? property.agent_phones : [],
            photos: processedPhotos,
            property_url: property.property_url || ''
          };
          
          console.log('Processed property:', {
            id: processed.property_id,
            street: processed.street,
            price: processed.list_price
          });
          
          return processed;
        });

      console.log('Final processed properties:', {
        count: processedProperties.length,
        sample: processedProperties[0]
      });

      setDebugProperties(processedProperties);
      onPropertiesLoaded(processedProperties);
      onFilterChange('zipCode', zipCode);
      onFilterChange('maxPrice', maxPrice);

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
        
        <button 
          type="button" 
          onClick={() => {
            console.log('Debug - Current properties:', {
              count: debugProperties.length,
              properties: debugProperties
            });
          }}
          className="debug-button"
          style={{ 
            marginTop: '8px', 
            padding: '8px', 
            background: '#f0f0f0',
            width: '100%',
            border: '1px solid #ddd',
            borderRadius: '4px'
          }}
        >
          Debug: Show Properties ({debugProperties.length})
        </button>
        
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
};

export default PropertyFilter;