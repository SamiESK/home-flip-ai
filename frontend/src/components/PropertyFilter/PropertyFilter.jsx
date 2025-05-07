// frontend/src/components/PropertyFilter/PropertyFilter.jsx
import React from 'react';
import './PropertyFilter.css';
import { scrapeProperties } from '../../services/api';

const PropertyFilter = ({ onFilterChange, onScraperComplete }) => {
  const [zipCode, setZipCode] = React.useState('');
  const [maxPrice, setMaxPrice] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Update filters
      onFilterChange('zipCode', zipCode);
      onFilterChange('maxPrice', maxPrice);

      // Run the scraper
      const response = await scrapeProperties(zipCode, maxPrice);
      console.log('Scraper response:', response);

      // Update the properties in the Dashboard
      if (response && response.properties) {
        console.log('Updating properties with:', response.properties);
        onScraperComplete(response.properties);
      }
      
    } catch (error) {
      console.error('Error running scraper:', error);
      setError('Failed to run scraper. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="property-filter">
      <h2>Filter Properties</h2>
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
            onChange={(e) => setMaxPrice(e.target.value)}
            placeholder="Enter maximum price"
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Running Scraper...' : 'Run Scraper'}
        </button>
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
};

export default PropertyFilter;