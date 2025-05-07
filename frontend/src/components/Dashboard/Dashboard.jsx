// frontend/src/components/Dashboard/Dashboard.jsx
import React from 'react';
import PropertyList from '../PropertyList/PropertyList';
import PropertyFilter from '../PropertyFilter/PropertyFilter';
import { fetchProperties } from '../../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [properties, setProperties] = React.useState([]);
  const [filters, setFilters] = React.useState({});
  const [selectedProperty, setSelectedProperty] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  const loadProperties = async () => {
    try {
      setLoading(true);
      const response = await fetchProperties();
      console.log('API Response:', response);

      if (response && response.properties) {
        console.log('Setting properties:', response.properties);
        setProperties(response.properties);
      } else {
        console.error('Invalid response format:', response);
        setError('Invalid data format received');
      }
    } catch (error) {
      console.error('Error loading properties:', error);
      setError('Failed to load properties. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Load properties when component mounts
  React.useEffect(() => {
    loadProperties();
  }, []);

  const handleFilterChange = (filterName, value) => {
    console.log('Filter changed:', filterName, value);
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handlePropertySelect = (property) => {
    console.log('Selected property:', property);
    setSelectedProperty(property);
  };

  // Filter properties based on current filters
  const filteredProperties = React.useMemo(() => {
    console.log('Filtering properties:', { properties, filters });
    
    if (!Array.isArray(properties)) {
      console.warn('Properties is not an array:', properties);
      return [];
    }
    
    return properties.filter(property => {
      // Zip code filter
      if (filters.zipCode && property.zip_code !== filters.zipCode) {
        return false;
      }

      // Maximum price filter
      if (filters.maxPrice && property.list_price > Number(filters.maxPrice.replace(/,/g, ''))) {
        return false;
      }

      return true;
    });
  }, [properties, filters]);

  // Add this function to handle scraper results
  const handleScraperComplete = (newProperties) => {
    console.log('Setting new properties from scraper:', newProperties);
    setProperties(newProperties);
  };

  if (loading) {
    return (
      <div className="dashboard">
        <h1>Home Flipper AI Dashboard</h1>
        <div className="loading">Loading properties...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <h1>Home Flipper AI Dashboard</h1>
        <div className="error">{error}</div>
      </div>
    );
  }

  console.log('Rendering Dashboard with properties:', {
    totalProperties: properties.length,
    filteredProperties: filteredProperties.length
  });

  return (
    <div className="dashboard">
      <h1>Home Flipper AI Dashboard</h1>
      <div className="dashboard-content">
        <div className="property-list-container">
          <PropertyList 
            properties={filteredProperties}
            onPropertySelect={handlePropertySelect}
            selectedProperty={selectedProperty}
          />
        </div>
        <div className="details-container">
          <PropertyFilter 
            onFilterChange={handleFilterChange}
            onScraperComplete={handleScraperComplete}
          />
          {selectedProperty && (
            <div className="property-details">
              {/* Property details component will go here */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;