// frontend/src/components/Dashboard/Dashboard.jsx
import React, { useCallback, useState, useEffect } from 'react';
import PropertyList from '../PropertyList/PropertyList';
import PropertyFilter from '../PropertyFilter/PropertyFilter';
import MapView from '../MapView/MapView';
import GoogleMapsLoader from '../GoogleMapsLoader/GoogleMapsLoader';
import './Dashboard.css';

const Dashboard = () => {
  const [properties, setProperties] = React.useState([]);
  const [filters, setFilters] = React.useState({});
  const [selectedProperty, setSelectedProperty] = React.useState(null);
  const [isGoogleMapsLoaded, setIsGoogleMapsLoaded] = React.useState(false);
  const [mapLoadAttempts, setMapLoadAttempts] = React.useState(0);

  const handleFilterChange = (filterName, value) => {
    console.log('Filter changed:', filterName, value);
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handlePropertiesLoaded = useCallback((newProperties) => {
    console.log('Dashboard receiving properties:', {
      hasProperties: !!newProperties,
      isArray: Array.isArray(newProperties),
      length: newProperties?.length,
      sampleProperty: newProperties?.[0]
    });

    if (Array.isArray(newProperties) && newProperties.length > 0) {
      setProperties(newProperties);
    } else {
      console.warn('Invalid or empty properties data received:', newProperties);
      setProperties([]);
    }
  }, []);

  const handlePropertySelect = useCallback((property) => {
    console.log('Selected property:', property);
    setSelectedProperty(property);
  }, []);

  const handleGoogleMapsLoad = useCallback(() => {
    console.log('Google Maps loaded, setting isGoogleMapsLoaded to true');
    setIsGoogleMapsLoaded(true);
  }, []);

  // Add this effect to handle map loading retries
  useEffect(() => {
    if (!isGoogleMapsLoaded && mapLoadAttempts < 3) {
      const timer = setTimeout(() => {
        console.log('Retrying map load, attempt:', mapLoadAttempts + 1);
        setMapLoadAttempts(prev => prev + 1);
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [isGoogleMapsLoaded, mapLoadAttempts]);

  // Filter properties based on current filters
  const filteredProperties = React.useMemo(() => {
    console.log('Filtering properties:', {
      total: properties.length,
      filters
    });
    
    if (!Array.isArray(properties)) return [];
    
    return properties.filter(property => {
      if (filters.zipCode && property.zip_code !== filters.zipCode) return false;
      if (filters.maxPrice) {
        const maxPrice = Number(filters.maxPrice.replace(/,/g, ''));
        if (property.list_price > maxPrice) return false;
      }
      return true;
    });
  }, [properties, filters]);

  console.log('Dashboard render:', {
    totalProperties: properties.length,
    filteredCount: filteredProperties.length,
    filters
  });

  return (
    <div className="dashboard">
      <GoogleMapsLoader onLoad={handleGoogleMapsLoad} />
      <h1>Boo Zaga Dashboard</h1>
      <div className="dashboard-content">
        <div className="left-panel">
          <PropertyFilter 
            onFilterChange={handleFilterChange}
            onPropertiesLoaded={handlePropertiesLoaded}
          />
          <div className="property-list-container">
            {properties.length > 0 ? (
              <PropertyList 
                properties={filteredProperties}
                onPropertySelect={handlePropertySelect}
                selectedProperty={selectedProperty}
              />
            ) : (
              <div className="no-properties">
                Enter a zip code and price to search for properties
              </div>
            )}
          </div>
        </div>
        <div className="right-panel">
          {isGoogleMapsLoaded ? (
            <MapView 
              properties={filteredProperties}
              selectedProperty={selectedProperty}
              onPropertySelect={handlePropertySelect}
            />
          ) : (
            <div className="map-loading">
              <div className="loading-spinner"></div>
              <p>Loading map... {mapLoadAttempts > 0 ? `(Attempt ${mapLoadAttempts})` : ''}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
